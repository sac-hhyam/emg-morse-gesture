#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""train_cnn_morse_v2.py — Train EMGCNN on pre-split windows from build_windows_split.py.

Design changes vs train_cnn_4actions_simple.py
-----------------------------------------------
1. Reads X_train.npy / X_test.npy instead of X_single_windows.npy.
   The train/test split was already done at the raw-signal level by
   build_windows_split.py, so overlapping windows cannot cross the
   train/test boundary.  No data leakage.

2. Normalization (mean/std) is fit on the COMBINED training set only
   (after carving out the val set), shape [1, 1, C].  The same scaler
   is applied to val and test, and saved both inside the .pth checkpoint
   and as standalone scaler_mean.npy / scaler_std.npy files.

3. A validation set is carved from the combined training windows with a
   stratified random split (pure numpy, no sklearn).  Val is used ONLY
   for early stopping — not for reporting final metrics.

4. Early stopping monitors val_loss (lower is better, patience=8).

5. Final metrics are computed on the test set with a pure-numpy
   confusion matrix and per-class P / R / F1 — no sklearn.

Checkpoint compatibility with realtime_decode_udp.py
------------------------------------------------------
Saves the same .pth keys as train_cnn_4actions_simple.py:
  model_state_dict, mean, std, per_window_norm=False, class_names
so realtime_decode_udp.py::load_ckpt() works without modification.

IMPORTANT — label_offset note
------------------------------
realtime_decode_udp.py always does `pred_idx = pred4 + 1`, which assumes
the model does NOT have "rest" as class 0 (rest is handled by the OnlineGate).
If you train WITH rest as class 0 (all four classes: rest/thumb/two_finger/fist),
you must apply the one-line fix documented in Step 5 of the implementation notes,
or exclude rest from --data_dirs and rely on the gate for rest detection.
This script saves label_offset in the checkpoint so the fix is straightforward.

Usage
-----
python -m epstudiosdk.train_cnn_morse_v2 \\
    --data_dirs \\
        epstudiosdk/records/npz-output/thumb-up-2026-06-27_171100 \\
        epstudiosdk/records/npz-output/two-finger-2026-06-30_165001 \\
        epstudiosdk/records/npz-output/fist-2026-07-01_141435-fist-tae \\
        epstudiosdk/records/npz-output/rest-2026-06-30_165934 \\
    --ckpt epstudiosdk/cnn_morse_v2.pth
"""

import argparse
import csv
import json
from pathlib import Path
from typing import List, Tuple

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader


# ── Model — IDENTICAL to realtime_decode_udp.py — do not change ─────────────

class EMGCNN(nn.Module):
    def __init__(self, n_channels: int = 5, n_classes: int = 4):
        super().__init__()
        self.feature_extractor = nn.Sequential(
            nn.Conv1d(n_channels, 32, kernel_size=5, padding=2),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.MaxPool1d(kernel_size=2),

            nn.Conv1d(32, 64, kernel_size=5, padding=2),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.MaxPool1d(kernel_size=2),

            nn.Conv1d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.AdaptiveMaxPool1d(1),
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(64, n_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.classifier(self.feature_extractor(x))


# ── Dataset ───────────────────────────────────────────────────────────────────

class EMGDataset(Dataset):
    """Global-normalization dataset.  mean/std shapes: [1, 1, C]."""

    def __init__(self, X: np.ndarray, y: np.ndarray,
                 mean: np.ndarray, std: np.ndarray):
        self.X    = X.astype(np.float32)
        self.y    = y.astype(np.int64)
        self.mean = mean.astype(np.float32)   # [1, 1, C]
        self.std  = std.astype(np.float32)    # [1, 1, C]

    def __len__(self) -> int:
        return self.X.shape[0]

    def __getitem__(self, idx: int):
        x = self.X[idx]                                     # [T, C]
        x = (x - self.mean.squeeze(0)) / self.std.squeeze(0)  # [T, C]
        x = x.transpose(1, 0)                              # [C, T]
        return torch.from_numpy(x.copy()), torch.tensor(self.y[idx])


# ── Pure-numpy helpers (no sklearn) ──────────────────────────────────────────

def compute_mean_std(X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Fit global normalizer on X [N, T, C]. Returns (mean, std) shape [1, 1, C]."""
    mean = X.mean(axis=(0, 1), keepdims=True).astype(np.float32)
    std  = (X.std(axis=(0, 1), keepdims=True) + 1e-8).astype(np.float32)
    return mean, std


def stratified_val_split(y: np.ndarray, val_frac: float = 0.15,
                         seed: int = 42) -> Tuple[np.ndarray, np.ndarray]:
    """Proportional stratified split — pure numpy, no sklearn."""
    rng = np.random.default_rng(seed)
    train_parts: List[np.ndarray] = []
    val_parts:   List[np.ndarray] = []
    for c in np.unique(y):
        c_idx = np.where(y == c)[0]
        rng.shuffle(c_idx)
        n_val = max(1, int(round(len(c_idx) * val_frac)))
        val_parts.append(c_idx[:n_val])
        train_parts.append(c_idx[n_val:])
    return np.concatenate(train_parts), np.concatenate(val_parts)


def confusion_matrix_np(y_true: np.ndarray, y_pred: np.ndarray,
                        n_classes: int) -> np.ndarray:
    cm = np.zeros((n_classes, n_classes), dtype=np.int64)
    for t, p in zip(y_true.tolist(), y_pred.tolist()):
        if 0 <= t < n_classes and 0 <= p < n_classes:
            cm[t][p] += 1
    return cm


def prf_per_class(cm: np.ndarray) -> List[Tuple]:
    """Per-class (precision, recall, f1, support) from confusion matrix."""
    out = []
    for k in range(cm.shape[0]):
        tp  = int(cm[k, k])
        fp  = int(cm[:, k].sum()) - tp
        fn  = int(cm[k, :].sum()) - tp
        sup = int(cm[k, :].sum())
        p   = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        r   = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1  = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
        out.append((float(p), float(r), float(f1), sup))
    return out


def read_label_map(data_dir: Path) -> dict:
    path = data_dir / "gesture_to_id_single.csv"
    if not path.exists():
        return {}
    out: dict = {}
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        for row in csv.reader(f):
            if len(row) >= 2:
                try:
                    out[int(row[1])] = str(row[0])
                except ValueError:
                    pass
    return out


# ── Training utilities ────────────────────────────────────────────────────────

@torch.no_grad()
def eval_epoch(model: nn.Module, loader: DataLoader,
               device: torch.device, criterion: nn.Module) -> Tuple[float, float]:
    model.eval()
    loss_sum, correct, total = 0.0, 0, 0
    for xb, yb in loader:
        xb, yb = xb.to(device), yb.to(device)
        logits   = model(xb)
        loss_sum += criterion(logits, yb).item() * yb.size(0)
        correct  += (logits.argmax(1) == yb).sum().item()
        total    += yb.size(0)
    n = max(total, 1)
    return loss_sum / n, correct / n


@torch.no_grad()
def predict_all(model: nn.Module, loader: DataLoader,
                device: torch.device) -> Tuple[np.ndarray, np.ndarray]:
    model.eval()
    preds, trues = [], []
    for xb, yb in loader:
        logits = model(xb.to(device))
        preds.append(logits.argmax(1).cpu().numpy())
        trues.append(yb.numpy())
    return np.concatenate(trues), np.concatenate(preds)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(
        description="Train EMGCNN on pre-split windows (build_windows_split.py output)."
    )
    ap.add_argument("--data_dirs", nargs="+", required=True,
                    help="session dirs each containing X_train.npy/y_train.npy/"
                         "X_test.npy/y_test.npy from build_windows_split.py")
    ap.add_argument("--ckpt",         default="cnn_morse_v2.pth")
    ap.add_argument("--metrics_json", default=None)
    ap.add_argument("--epochs",       type=int,   default=40)
    ap.add_argument("--patience",     type=int,   default=8,
                    help="early stopping patience on val_loss")
    ap.add_argument("--batch_size",   type=int,   default=64)
    ap.add_argument("--lr",           type=float, default=1e-3)
    ap.add_argument("--val_frac",     type=float, default=0.15,
                    help="fraction of train windows withheld for early stopping")
    ap.add_argument("--seed",         type=int,   default=42)
    ap.add_argument("--test_dirs",    nargs="+",  default=None,
                    help="held-out session dirs for LOSO eval. Each must contain "
                         "X_train.npy produced by build_windows_split.py --train_ratio 1.0 "
                         "(all windows land in X_train.npy; X_test.npy is empty). "
                         "These sessions must NOT appear in --data_dirs.")
    args = ap.parse_args()

    data_dirs = [Path(p) for p in args.data_dirs]
    ckpt_path = Path(args.ckpt)
    ckpt_path.parent.mkdir(parents=True, exist_ok=True)

    # ── 1. Load pre-split windows ─────────────────────────────────────────────
    print("Loading pre-split windows …")
    X_train_parts: list = []
    y_train_parts: list = []
    X_test_parts:  list = []
    y_test_parts:  list = []
    label_map: dict     = {}
    base_shape = None

    for d in data_dirs:
        for fname in ("X_train.npy", "y_train.npy", "X_test.npy", "y_test.npy"):
            if not (d / fname).exists():
                raise FileNotFoundError(
                    f"{d / fname} not found — run build_windows_split.py on {d} first"
                )

        Xtr = np.load(d / "X_train.npy").astype(np.float32)
        ytr = np.load(d / "y_train.npy").astype(np.int64)
        Xte = np.load(d / "X_test.npy").astype(np.float32)
        yte = np.load(d / "y_test.npy").astype(np.int64)

        if base_shape is None:
            base_shape = Xtr.shape[1:]
        elif Xtr.shape[1:] != base_shape:
            raise ValueError(
                f"{d}: window shape {Xtr.shape[1:]} != expected {base_shape}"
            )

        label_map.update(read_label_map(d))
        X_train_parts.append(Xtr); y_train_parts.append(ytr)
        X_test_parts.append(Xte);  y_test_parts.append(yte)
        counts_tr = np.bincount(ytr, minlength=4)
        counts_te = np.bincount(yte, minlength=4)
        print(f"  {d.name}")
        print(f"    train={len(ytr)} {dict(enumerate(counts_tr.tolist()))}")
        print(f"    test ={len(yte)} {dict(enumerate(counts_te.tolist()))}")

    X_all_train = np.concatenate(X_train_parts, axis=0)
    y_all_train = np.concatenate(y_train_parts, axis=0)
    X_test      = np.concatenate(X_test_parts,  axis=0)
    y_test      = np.concatenate(y_test_parts,  axis=0)

    # Build class_names from label_map + fallback
    LEGACY = ["up", "down", "left", "right"]
    max_label = max(int(y_all_train.max()),
                    int(y_test.max()) if y_test.size else 0,
                    max(label_map.keys()) if label_map else 0)
    n_classes  = max_label + 1
    class_names = [label_map.get(i, LEGACY[i] if i < len(LEGACY) else f"class_{i}")
                   for i in range(n_classes)]
    n_channels = int(X_all_train.shape[2])

    print(f"\nCombined   train={len(y_all_train)}  test={len(y_test)}")
    print(f"classes    {dict(enumerate(class_names))}")
    print(f"n_channels={n_channels}  window_shape={base_shape}")

    # ── 2. Carve val from combined train (stratified, no sklearn) ─────────────
    train_idx, val_idx = stratified_val_split(
        y_all_train, val_frac=args.val_frac, seed=args.seed
    )
    X_train, y_train = X_all_train[train_idx], y_all_train[train_idx]
    X_val,   y_val   = X_all_train[val_idx],   y_all_train[val_idx]
    print(f"\nAfter val carve  train={len(y_train)}  val={len(y_val)}  test={len(y_test)}")

    # ── 3. Fit normalization on train only ────────────────────────────────────
    mean, std = compute_mean_std(X_train)
    print(f"Scaler (per channel)  mean={mean.squeeze().tolist()}  "
          f"std={std.squeeze().tolist()}")

    # ── 4. Datasets + DataLoaders ─────────────────────────────────────────────
    train_ds = EMGDataset(X_train, y_train, mean, std)
    val_ds   = EMGDataset(X_val,   y_val,   mean, std)
    test_ds  = EMGDataset(X_test,  y_test,  mean, std)

    train_loader = DataLoader(train_ds, batch_size=args.batch_size,
                              shuffle=True,  drop_last=False)
    val_loader   = DataLoader(val_ds,   batch_size=args.batch_size,
                              shuffle=False, drop_last=False)
    test_loader  = DataLoader(test_ds,  batch_size=args.batch_size,
                              shuffle=False, drop_last=False)

    # ── 5. Model / loss / optimizer ───────────────────────────────────────────
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\ndevice={device}")
    model = EMGCNN(n_channels=n_channels, n_classes=n_classes).to(device)

    counts  = np.bincount(y_train, minlength=n_classes)
    weights = len(y_train) / (n_classes * np.maximum(counts, 1))
    criterion = nn.CrossEntropyLoss(
        weight=torch.tensor(weights, dtype=torch.float32, device=device)
    )
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)

    # ── 6. Training loop — early stopping on val_loss ─────────────────────────
    best_val_loss = float("inf")
    best_state    = None
    best_epoch    = 0
    no_imp        = 0
    history       = []

    print()
    for epoch in range(1, args.epochs + 1):
        model.train()
        loss_sum, correct, total = 0.0, 0, 0
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            optimizer.zero_grad()
            logits = model(xb)
            loss   = criterion(logits, yb)
            loss.backward()
            optimizer.step()
            loss_sum += loss.item() * yb.size(0)
            correct  += (logits.argmax(1) == yb).sum().item()
            total    += yb.size(0)

        train_loss = loss_sum / max(total, 1)
        train_acc  = correct  / max(total, 1)
        val_loss, val_acc = eval_epoch(model, val_loader, device, criterion)

        history.append({
            "epoch": epoch, "train_loss": train_loss, "train_acc": train_acc,
            "val_loss": val_loss, "val_acc": val_acc,
        })
        print(f"Epoch {epoch:02d}: train_loss={train_loss:.4f} train_acc={train_acc:.3f} "
              f"val_loss={val_loss:.4f} val_acc={val_acc:.3f}")

        # Early stopping on val_loss (lower is better)
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_epoch    = epoch
            best_state    = {k: v.cpu() for k, v in model.state_dict().items()}
            no_imp        = 0
        else:
            no_imp += 1
            if no_imp >= args.patience:
                print("Early stopping.")
                break

    if best_state:
        model.load_state_dict(best_state)
    print(f"\nBest epoch={best_epoch}  best_val_loss={best_val_loss:.4f}")

    # ── 7. Test evaluation ────────────────────────────────────────────────────
    y_true, y_pred = predict_all(model, test_loader, device)
    test_acc = float((y_pred == y_true).mean())
    cm  = confusion_matrix_np(y_true, y_pred, n_classes)
    prf = prf_per_class(cm)

    print(f"\n{'='*55}")
    print(f"TEST RESULTS   accuracy={test_acc:.4f}  ({(y_pred==y_true).sum()}/{len(y_true)})")
    print(f"{'='*55}")
    print(f"  {'class':12s}  {'P':>7s}  {'R':>7s}  {'F1':>7s}  {'support':>8s}")
    precs, recs, f1s = [], [], []
    for k, (p, r, f, sup) in enumerate(prf):
        print(f"  {class_names[k]:12s}  {p:7.3f}  {r:7.3f}  {f:7.3f}  {sup:8d}")
        if sup > 0:
            precs.append(p); recs.append(r); f1s.append(f)
    macro_p = float(np.mean(precs)) if precs else 0.0
    macro_r = float(np.mean(recs))  if recs  else 0.0
    macro_f = float(np.mean(f1s))   if f1s   else 0.0
    print(f"  {'macro avg':12s}  {macro_p:7.3f}  {macro_r:7.3f}  {macro_f:7.3f}")
    print(f"\nConfusion matrix (rows=true, cols=pred):")
    print("  " + "  ".join(f"{c:>12s}" for c in class_names))
    for i, c in enumerate(class_names):
        row = "  ".join(f"{cm[i,j]:>12d}" for j in range(n_classes))
        print(f"{c:>12s}  {row}")

    # ── 8. Save checkpoint (same keys as train_cnn_4actions_simple.py) ────────
    class_names_lower = [s.lower() for s in class_names]
    # label_offset=0 when rest is class 0; =1 when model has no rest class.
    # realtime_decode_udp.py uses pred4+1 — see the label_offset fix in Step 5.
    label_offset = 0 if (class_names_lower and class_names_lower[0] == "rest") else 1

    torch.save({
        "model_state_dict": model.state_dict(),
        "mean":             mean,          # [1, 1, C] — same shape inference expects
        "std":              std,           # [1, 1, C]
        "per_window_norm":  False,         # always global norm in this script
        "class_names":      class_names,
        "label_offset":     int(label_offset),
        "split":            "raw_signal_pre_split",
        "best_epoch":       int(best_epoch),
        "best_val_loss":    float(best_val_loss),
        "test_acc":         float(test_acc),
    }, ckpt_path)
    print(f"\n[saved] checkpoint: {ckpt_path}")

    # Standalone scaler files alongside the .pth
    np.save(ckpt_path.parent / "scaler_mean.npy", mean)
    np.save(ckpt_path.parent / "scaler_std.npy",  std)
    print(f"[saved] {ckpt_path.parent}/scaler_mean.npy  shape={mean.shape}")
    print(f"[saved] {ckpt_path.parent}/scaler_std.npy   shape={std.shape}")

    # ── 9. Metrics JSON ───────────────────────────────────────────────────────
    metrics_path = (Path(args.metrics_json) if args.metrics_json
                    else ckpt_path.with_suffix(".metrics.json"))
    metrics = {
        "data_dirs":      [str(d) for d in data_dirs],
        "ckpt":           str(ckpt_path),
        "class_names":    class_names,
        "split":          "raw_signal_pre_split",
        "n_train":        int(len(y_train)),
        "n_val":          int(len(y_val)),
        "n_test":         int(len(y_test)),
        "window_shape":   list(base_shape) if base_shape else [],
        "best_epoch":     int(best_epoch),
        "best_val_loss":  float(best_val_loss),
        "test_acc":       float(test_acc),
        "macro_avg":      {"precision": macro_p, "recall": macro_r, "f1": macro_f},
        "per_class": [
            {"id": k, "name": class_names[k],
             "precision": p, "recall": r, "f1": f, "support": sup}
            for k, (p, r, f, sup) in enumerate(prf)
        ],
        "confusion_matrix": cm.tolist(),
        "history":          history,
    }
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(f"[saved] metrics:    {metrics_path}")

    # ── 10. LOSO evaluation (optional) ───────────────────────────────────────
    if args.test_dirs:
        test_dirs = [Path(p) for p in args.test_dirs]

        print("\nLoading LOSO held-out sessions …")
        X_loso_parts: list = []
        y_loso_parts: list = []
        loso_session_tags: list = []

        for d in test_dirs:
            x_path = d / "X_train.npy"   # train_ratio=1.0 puts everything here
            y_path = d / "y_train.npy"
            if not x_path.exists() or not y_path.exists():
                raise FileNotFoundError(
                    f"{x_path} not found — run build_windows_split.py "
                    f"--train_ratio 1.0 on {d} first"
                )
            Xl = np.load(x_path).astype(np.float32)
            yl = np.load(y_path).astype(np.int64)
            if Xl.shape[1:] != base_shape:
                raise ValueError(
                    f"{d}: window shape {Xl.shape[1:]} != training shape {base_shape}"
                )
            X_loso_parts.append(Xl)
            y_loso_parts.append(yl)
            loso_session_tags.extend([d.name] * len(yl))
            counts_l = np.bincount(yl, minlength=n_classes)
            print(f"  {d.name}  windows={len(yl)}  {dict(enumerate(counts_l.tolist()))}")

        X_loso = np.concatenate(X_loso_parts, axis=0)
        y_loso = np.concatenate(y_loso_parts, axis=0)
        loso_tags = np.array(loso_session_tags)

        # Apply the TRAINING scaler — no new statistics from held-out data
        loso_ds     = EMGDataset(X_loso, y_loso, mean, std)
        loso_loader = DataLoader(loso_ds, batch_size=args.batch_size,
                                 shuffle=False, drop_last=False)

        y_loso_true, y_loso_pred = predict_all(model, loso_loader, device)
        loso_acc = float((y_loso_pred == y_loso_true).mean())
        loso_cm  = confusion_matrix_np(y_loso_true, y_loso_pred, n_classes)
        loso_prf = prf_per_class(loso_cm)

        print(f"\n{'='*65}")
        print("=== LOSO TEST RESULTS (held-out sessions, never seen during training) ===")
        print(f"  overall accuracy : {loso_acc:.4f}  "
              f"({(y_loso_pred==y_loso_true).sum()}/{len(y_loso_true)})")
        print(f"{'='*65}")
        print(f"  {'class':12s}  {'P':>7s}  {'R':>7s}  {'F1':>7s}  {'support':>8s}")
        loso_precs, loso_recs, loso_f1s = [], [], []
        for k, (p, r, f, sup) in enumerate(loso_prf):
            print(f"  {class_names[k]:12s}  {p:7.3f}  {r:7.3f}  {f:7.3f}  {sup:8d}")
            if sup > 0:
                loso_precs.append(p); loso_recs.append(r); loso_f1s.append(f)
        loso_macro_p = float(np.mean(loso_precs)) if loso_precs else 0.0
        loso_macro_r = float(np.mean(loso_recs))  if loso_recs  else 0.0
        loso_macro_f = float(np.mean(loso_f1s))   if loso_f1s   else 0.0
        print(f"  {'macro avg':12s}  {loso_macro_p:7.3f}  {loso_macro_r:7.3f}  {loso_macro_f:7.3f}")

        print(f"\nConfusion matrix (rows=true, cols=pred):")
        print("  " + "  ".join(f"{c:>12s}" for c in class_names))
        for i, c in enumerate(class_names):
            row = "  ".join(f"{loso_cm[i,j]:>12d}" for j in range(n_classes))
            print(f"{c:>12s}  {row}")

        print(f"\nPer-session breakdown:")
        for tag in dict.fromkeys(loso_session_tags):   # preserve insertion order
            mask = loso_tags == tag
            yt, yp = y_loso_true[mask], y_loso_pred[mask]
            s_acc = float((yt == yp).mean())
            dominant_label = class_names[int(yt[0])] if mask.sum() > 0 else "?"
            print(f"  {tag:30s}  label={dominant_label:10s}  "
                  f"acc={s_acc:.3f}  ({(yt==yp).sum()}/{mask.sum()})")

        # Save LOSO metrics JSON
        loso_metrics_path = ckpt_path.with_suffix(".loso.metrics.json")
        loso_metrics = {
            "test_dirs":    [str(d) for d in test_dirs],
            "data_dirs":    [str(d) for d in data_dirs],
            "ckpt":         str(ckpt_path),
            "class_names":  class_names,
            "n_loso":       int(len(y_loso_true)),
            "loso_acc":     loso_acc,
            "macro_avg":    {"precision": loso_macro_p,
                             "recall":    loso_macro_r,
                             "f1":        loso_macro_f},
            "per_class": [
                {"id": k, "name": class_names[k],
                 "precision": p, "recall": r, "f1": f, "support": sup}
                for k, (p, r, f, sup) in enumerate(loso_prf)
            ],
            "confusion_matrix": loso_cm.tolist(),
            "per_session": [
                {
                    "session":   tag,
                    "n":         int((loso_tags == tag).sum()),
                    "acc":       float((y_loso_pred[loso_tags == tag] ==
                                        y_loso_true[loso_tags == tag]).mean()),
                }
                for tag in dict.fromkeys(loso_session_tags)
            ],
        }
        with open(loso_metrics_path, "w", encoding="utf-8") as f:
            json.dump(loso_metrics, f, indent=2)
        print(f"\n[saved] LOSO metrics: {loso_metrics_path}")


if __name__ == "__main__":
    main()