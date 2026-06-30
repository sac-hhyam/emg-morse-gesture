# -*- coding: utf-8 -*-
"""Train EMGCNN from windowed EMG data and report held-out accuracy.

The script reads X_single_windows.npy / y_single_labels.npy from one or more
window directories. If gesture_to_id_single.csv exists, class names come from
that file, so Morse labels such as rest/thumb/two_finger/fist stay consistent
from windowing to training to realtime decoding.
"""

import argparse
import csv
import json
from pathlib import Path

import numpy as np
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import GroupShuffleSplit, train_test_split

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader


LEGACY_CLASS_NAMES = ["up", "down", "left", "right"]


class EMGDataset(Dataset):
    def __init__(self, X, y, per_window_norm=True, mean=None, std=None):
        self.X = X.astype(np.float32)
        self.y = y.astype(np.int64)
        self.per_window_norm = bool(per_window_norm)
        self.mean = mean.astype(np.float32) if mean is not None else None
        self.std = std.astype(np.float32) if std is not None else None

    def __len__(self):
        return self.X.shape[0]

    def __getitem__(self, idx):
        x = self.X[idx]  # [T,C]
        if self.per_window_norm:
            mu = x.mean(axis=0, keepdims=True)
            sigma = x.std(axis=0, keepdims=True) + 1e-8
            x = (x - mu) / sigma
        else:
            assert self.mean is not None and self.std is not None
            x = (x - self.mean.squeeze(0)) / self.std.squeeze(0)
        x = x.transpose(1, 0)  # [C,T]
        return torch.from_numpy(x), torch.tensor(self.y[idx])


class EMGCNN(nn.Module):
    def __init__(self, n_channels=5, n_classes=4):
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

    def forward(self, x):
        return self.classifier(self.feature_extractor(x))


def compute_global_mean_std(X):
    mean = X.mean(axis=(0, 1), keepdims=True).astype(np.float32)
    std = (X.std(axis=(0, 1), keepdims=True) + 1e-8).astype(np.float32)
    return mean, std


def read_label_map(data_dir: Path):
    path = data_dir / "gesture_to_id_single.csv"
    if not path.exists():
        return {}
    out = {}
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        for row in csv.reader(f):
            if len(row) < 2:
                continue
            try:
                out[int(row[1])] = str(row[0])
            except ValueError:
                continue
    return out


def read_window_groups(data_dir: Path, n_windows: int):
    path = data_dir / "windows_index.csv"
    if not path.exists():
        return [f"{data_dir}:window:{i}" for i in range(n_windows)]

    groups = []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            keep = str(row.get("keep", "1")).strip()
            if keep not in ("1", "1.0", "true", "True", "TRUE"):
                continue
            session = row.get("session_name") or data_dir.name
            trial = row.get("trial_file") or row.get("trial_order") or "unknown_trial"
            groups.append(f"{data_dir}:{session}:{trial}")

    if len(groups) != n_windows:
        print(f"[warn] {path} kept rows={len(groups)} but X has {n_windows}; using per-window groups.")
        return [f"{data_dir}:window:{i}" for i in range(n_windows)]
    return groups


def read_window_blocks(data_dir: Path, n_windows: int):
    """Return one time-ordered block id per kept window.

    For a single long recording, this is usually one block. For many trials in a
    session folder, each trial becomes its own block. The returned order matches
    X_single_windows.npy because build_windows_morse.py appends kept windows in
    the same order it writes kept rows to windows_index.csv.
    """
    path = data_dir / "windows_index.csv"
    if not path.exists():
        return [f"{data_dir}:all"] * n_windows

    blocks = []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            keep = str(row.get("keep", "1")).strip()
            if keep not in ("1", "1.0", "true", "True", "TRUE"):
                continue
            session = row.get("session_name") or data_dir.name
            trial = row.get("trial_file") or row.get("trial_order") or "unknown_trial"
            blocks.append(f"{data_dir}:{session}:{trial}")

    if len(blocks) != n_windows:
        print(f"[warn] {path} kept rows={len(blocks)} but X has {n_windows}; using one block for folder.")
        return [f"{data_dir}:all"] * n_windows
    return blocks


def load_window_data(data_dirs):
    X_parts, y_parts, group_parts, block_parts = [], [], [], []
    label_map = {}
    base_shape = None

    for data_dir in data_dirs:
        X_path = data_dir / "X_single_windows.npy"
        y_path = data_dir / "y_single_labels.npy"
        if not X_path.exists() or not y_path.exists():
            raise FileNotFoundError(f"missing X/y window files in {data_dir}")

        X = np.load(X_path)
        y = np.load(y_path)
        if X.ndim != 3:
            raise ValueError(f"{X_path} must have shape [N,T,C], got {X.shape}")
        if y.ndim != 1 or y.shape[0] != X.shape[0]:
            raise ValueError(f"{y_path} must have shape [N] matching X, got {y.shape}")

        shape_tc = X.shape[1:]
        if base_shape is None:
            base_shape = shape_tc
        elif shape_tc != base_shape:
            raise ValueError(f"{data_dir} has window shape {shape_tc}; expected {base_shape}")

        label_map.update(read_label_map(data_dir))
        X_parts.append(X.astype(np.float32))
        y_parts.append(y.astype(np.int64))
        group_parts.extend(read_window_groups(data_dir, X.shape[0]))
        block_parts.extend(read_window_blocks(data_dir, X.shape[0]))

    X_all = np.concatenate(X_parts, axis=0)
    y_all = np.concatenate(y_parts, axis=0)
    groups = np.asarray(group_parts, dtype=object)
    blocks = np.asarray(block_parts, dtype=object)

    max_label = int(y_all.max()) if y_all.size else -1
    max_map = max(label_map.keys()) if label_map else -1
    n_classes = max(max_label, max_map) + 1
    if n_classes <= 0:
        raise ValueError("no labels found")

    class_names = []
    for i in range(n_classes):
        if i in label_map:
            class_names.append(label_map[i])
        elif i < len(LEGACY_CLASS_NAMES):
            class_names.append(LEGACY_CLASS_NAMES[i])
        else:
            class_names.append(f"class_{i}")

    return X_all, y_all, groups, blocks, class_names


def can_stratify(y):
    if y.size == 0:
        return False
    _, counts = np.unique(y, return_counts=True)
    return bool(np.all(counts >= 2))


def has_all_classes(y, *splits):
    classes = set(np.unique(y).tolist())
    if not classes:
        return False
    for split in splits:
        if set(np.unique(y[split]).tolist()) != classes:
            return False
    return True


def split_indices(y, groups, use_group_split=True, seed=42):
    idx = np.arange(y.shape[0])
    unique_groups = np.unique(groups)

    if use_group_split and unique_groups.size >= 3:
        splitter = GroupShuffleSplit(n_splits=1, test_size=0.30, random_state=seed)
        train_idx, temp_idx = next(splitter.split(idx, y, groups))
        temp_groups = groups[temp_idx]
        if np.unique(temp_groups).size >= 2:
            splitter2 = GroupShuffleSplit(n_splits=1, test_size=0.50, random_state=seed + 1)
            rel_val_idx, rel_test_idx = next(splitter2.split(temp_idx, y[temp_idx], temp_groups))
            val_idx = temp_idx[rel_val_idx]
            test_idx = temp_idx[rel_test_idx]
            if has_all_classes(y, train_idx, val_idx, test_idx):
                return train_idx, val_idx, test_idx, "group"
            print("[warn] group split missed at least one class in train/val/test; falling back to random split.")
        print("[warn] not enough held-out groups for val/test split; falling back to random split.")

    strat = y if can_stratify(y) else None
    train_idx, temp_idx = train_test_split(idx, test_size=0.30, random_state=seed, stratify=strat)
    strat_temp = y[temp_idx] if can_stratify(y[temp_idx]) else None
    val_idx, test_idx = train_test_split(temp_idx, test_size=0.50, random_state=seed, stratify=strat_temp)
    return train_idx, val_idx, test_idx, "random"


def split_time_block_indices(y, blocks, train_frac=0.70, val_frac=0.15, gap_windows=5):
    """Split each session/trial block by time order.

    This prevents neighboring overlapped windows from being randomly separated
    across train/val/test. gap_windows are discarded between adjacent splits.
    """
    train_parts, val_parts, test_parts = [], [], []
    gap_windows = max(0, int(gap_windows))

    for block in np.unique(blocks):
        block_idx = np.flatnonzero(blocks == block)
        n = int(block_idx.size)
        if n < 3:
            print(f"[warn] block {block} has only {n} windows; assigning all to train.")
            train_parts.append(block_idx)
            continue

        train_end = int(np.floor(n * float(train_frac)))
        val_end = int(np.floor(n * float(train_frac + val_frac)))

        train_end = min(max(train_end, 1), n - 2)
        val_start = min(train_end + gap_windows, n - 1)
        val_end = min(max(val_end, val_start + 1), n - 1)
        test_start = min(val_end + gap_windows, n)

        train_idx = block_idx[:train_end]
        val_idx = block_idx[val_start:val_end]
        test_idx = block_idx[test_start:]

        if train_idx.size:
            train_parts.append(train_idx)
        if val_idx.size:
            val_parts.append(val_idx)
        if test_idx.size:
            test_parts.append(test_idx)

        dropped = n - train_idx.size - val_idx.size - test_idx.size
        if dropped > 0:
            print(f"[split] block={block} windows={n} train={train_idx.size} val={val_idx.size} test={test_idx.size} gap_drop={dropped}")

    if not train_parts or not val_parts or not test_parts:
        raise ValueError("time_block split produced an empty train/val/test set; collect more data or lower gap_windows")

    train_idx = np.concatenate(train_parts)
    val_idx = np.concatenate(val_parts)
    test_idx = np.concatenate(test_parts)

    train_classes = set(np.unique(y[train_idx]).tolist())
    val_classes = set(np.unique(y[val_idx]).tolist())
    test_classes = set(np.unique(y[test_idx]).tolist())
    present_classes = set(np.unique(y).tolist())
    if train_classes != present_classes or val_classes != present_classes or test_classes != present_classes:
        print("[warn] time_block split does not contain every present class in train/val/test.")
        print(f"       present={sorted(present_classes)} train={sorted(train_classes)} val={sorted(val_classes)} test={sorted(test_classes)}")

    return train_idx, val_idx, test_idx, "time_block"


@torch.no_grad()
def eval_model(model, loader, device, criterion):
    model.eval()
    loss_sum = 0.0
    correct = 0
    total = 0
    for xb, yb in loader:
        xb = xb.to(device)
        yb = yb.to(device)
        logits = model(xb)
        loss = criterion(logits, yb)
        loss_sum += loss.item() * yb.size(0)
        pred = logits.argmax(dim=1)
        correct += (pred == yb).sum().item()
        total += yb.size(0)
    return loss_sum / max(total, 1), correct / max(total, 1)


def predict_all(model, loader, device):
    model.eval()
    all_p, all_t = [], []
    with torch.no_grad():
        for xb, yb in loader:
            xb = xb.to(device)
            logits = model(xb)
            all_p.append(logits.argmax(dim=1).cpu().numpy())
            all_t.append(yb.numpy())
    return np.concatenate(all_t), np.concatenate(all_p)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data_dir", type=str, default=None,
                    help="single window directory; kept for backward compatibility")
    ap.add_argument("--data_dirs", type=str, nargs="+", default=None,
                    help="one or more directories containing X_single_windows.npy/y_single_labels.npy")
    ap.add_argument("--ckpt", type=str, default="cnn_emg.pth")
    ap.add_argument("--metrics_json", type=str, default=None,
                    help="where to write accuracy/report JSON; default is <ckpt>.metrics.json")
    ap.add_argument("--batch_size", type=int, default=64)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--patience", type=int, default=8)
    ap.add_argument("--seed", type=int, default=42)
    norm_group = ap.add_mutually_exclusive_group()
    norm_group.add_argument("--global_norm", dest="per_window_norm", action="store_false",
                            help="fit mean/std on train set only, then apply to train/val/test (default)")
    norm_group.add_argument("--per_window_norm", dest="per_window_norm", action="store_true",
                            help="normalize each window by its own mean/std")
    ap.set_defaults(per_window_norm=False)
    ap.add_argument("--split_mode", choices=["time_block", "group", "random"], default="time_block",
                    help="time_block prevents overlap leakage for long sessions; random is for debugging only")
    ap.add_argument("--gap_windows", type=int, default=5,
                    help="windows to drop between train/val/test blocks to avoid overlap leakage")
    ap.add_argument("--train_frac", type=float, default=0.70)
    ap.add_argument("--val_frac", type=float, default=0.15)
    ap.add_argument("--no_group_split", action="store_true",
                    help="deprecated alias for --split_mode random")
    args = ap.parse_args()

    if args.data_dirs:
        data_dirs = [Path(p) for p in args.data_dirs]
    elif args.data_dir:
        data_dirs = [Path(args.data_dir)]
    else:
        raise ValueError("pass --data_dir or --data_dirs")

    if args.no_group_split:
        args.split_mode = "random"

    X, y, groups, blocks, class_names = load_window_data(data_dirs)
    n_classes = len(class_names)
    if np.any(y < 0) or np.any(y >= n_classes):
        raise ValueError(f"labels must be in [0,{n_classes - 1}], got min={y.min()} max={y.max()}")

    print("X:", X.shape, "y:", y.shape)
    print("classes:", {i: name for i, name in enumerate(class_names)})

    if args.split_mode == "time_block":
        train_idx, val_idx, test_idx, split_mode = split_time_block_indices(
            y,
            blocks,
            train_frac=args.train_frac,
            val_frac=args.val_frac,
            gap_windows=args.gap_windows,
        )
    elif args.split_mode == "group":
        train_idx, val_idx, test_idx, split_mode = split_indices(
            y, groups, use_group_split=True, seed=args.seed
        )
    else:
        train_idx, val_idx, test_idx, split_mode = split_indices(
            y, groups, use_group_split=False, seed=args.seed
        )
    print(f"split_mode={split_mode} train={len(train_idx)} val={len(val_idx)} test={len(test_idx)}")

    X_train, y_train = X[train_idx], y[train_idx]
    X_val, y_val = X[val_idx], y[val_idx]
    X_test, y_test = X[test_idx], y[test_idx]

    mean, std = compute_global_mean_std(X_train)

    train_ds = EMGDataset(X_train, y_train, per_window_norm=args.per_window_norm, mean=mean, std=std)
    val_ds = EMGDataset(X_val, y_val, per_window_norm=args.per_window_norm, mean=mean, std=std)
    test_ds = EMGDataset(X_test, y_test, per_window_norm=args.per_window_norm, mean=mean, std=std)

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, drop_last=False)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False, drop_last=False)
    test_loader = DataLoader(test_ds, batch_size=args.batch_size, shuffle=False, drop_last=False)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = EMGCNN(n_channels=X.shape[2], n_classes=n_classes).to(device)

    counts = np.bincount(y_train, minlength=n_classes)
    weights = len(y_train) / (n_classes * np.maximum(counts, 1))
    criterion = nn.CrossEntropyLoss(weight=torch.tensor(weights, dtype=torch.float32, device=device))
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)

    best_val = -1.0
    best_state = None
    best_epoch = 0
    no_imp = 0
    history = []

    for epoch in range(1, args.epochs + 1):
        model.train()
        loss_sum = 0.0
        corr = 0
        tot = 0
        for xb, yb in train_loader:
            xb = xb.to(device)
            yb = yb.to(device)
            optimizer.zero_grad()
            logits = model(xb)
            loss = criterion(logits, yb)
            loss.backward()
            optimizer.step()
            loss_sum += loss.item() * yb.size(0)
            pred = logits.argmax(dim=1)
            corr += (pred == yb).sum().item()
            tot += yb.size(0)

        train_loss = loss_sum / max(tot, 1)
        train_acc = corr / max(tot, 1)
        val_loss, val_acc = eval_model(model, val_loader, device, criterion)
        history.append({
            "epoch": epoch,
            "train_loss": train_loss,
            "train_acc": train_acc,
            "val_loss": val_loss,
            "val_acc": val_acc,
        })
        print(
            f"Epoch {epoch:02d}: train_loss={train_loss:.4f} train_acc={train_acc:.3f} "
            f"val_loss={val_loss:.4f} val_acc={val_acc:.3f}"
        )

        if val_acc > best_val:
            best_val = val_acc
            best_epoch = epoch
            best_state = {k: v.cpu() for k, v in model.state_dict().items()}
            no_imp = 0
        else:
            no_imp += 1
            if no_imp >= args.patience:
                print("Early stopping.")
                break

    if best_state is not None:
        model.load_state_dict(best_state)

    y_true, y_pred = predict_all(model, test_loader, device)
    test_acc = float((y_pred == y_true).mean())
    labels = list(range(n_classes))
    report_text = classification_report(
        y_true, y_pred, labels=labels, target_names=class_names, digits=3, zero_division=0
    )
    report_dict = classification_report(
        y_true, y_pred, labels=labels, target_names=class_names, digits=6,
        output_dict=True, zero_division=0
    )
    cm = confusion_matrix(y_true, y_pred, labels=labels)

    print("test_acc:", test_acc)
    print(report_text)
    print("confusion_matrix:\n", cm)

    ckpt_path = Path(args.ckpt)
    ckpt_path.parent.mkdir(parents=True, exist_ok=True)
    class_names_lower = [str(x).lower() for x in class_names]
    label_offset = 0 if class_names_lower and class_names_lower[0] == "rest" else 1
    torch.save({
        "model_state_dict": model.state_dict(),
        "mean": mean,
        "std": std,
        "per_window_norm": bool(args.per_window_norm),
        "class_names": class_names,
        "label_offset": int(label_offset),
        "split_mode": split_mode,
        "best_epoch": int(best_epoch),
        "best_val_acc": float(best_val),
        "test_acc": test_acc,
    }, ckpt_path)
    print("[OK] saved ckpt:", ckpt_path)

    metrics_path = Path(args.metrics_json) if args.metrics_json else ckpt_path.with_suffix(".metrics.json")
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics = {
        "data_dirs": [str(p) for p in data_dirs],
        "ckpt": str(ckpt_path),
        "class_names": class_names,
        "split_mode": split_mode,
        "n_windows": int(X.shape[0]),
        "window_shape": list(X.shape[1:]),
        "splits": {
            "train": int(len(train_idx)),
            "val": int(len(val_idx)),
            "test": int(len(test_idx)),
        },
        "split_params": {
            "split_mode": split_mode,
            "train_frac": float(args.train_frac),
            "val_frac": float(args.val_frac),
            "gap_windows": int(args.gap_windows),
        },
        "best_epoch": int(best_epoch),
        "best_val_acc": float(best_val),
        "test_acc": test_acc,
        "confusion_matrix": cm.astype(int).tolist(),
        "classification_report": report_dict,
        "history": history,
    }
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print("[OK] saved metrics:", metrics_path)


if __name__ == "__main__":
    main()
