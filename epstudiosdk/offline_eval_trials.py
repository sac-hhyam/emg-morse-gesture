# -*- coding: utf-8 -*-
"""
Offline evaluation for EMG trial recordings.

Input:
- session_dir containing trial_*.npz (from realtime_record_trials.py)
  Each npz must include:
    emg: [T, C] float
    sfreq: float
    label_id: int  (0..3 by default)
    label_name: str (optional)

- ckpt .pth saved by train_cnn_4actions_simple.py (or compatible):
    model_state_dict
    per_window_norm (bool)
    mean/std (optional; used when per_window_norm=False)
    class_names (optional)

Output:
- Prints per-trial prediction + summary accuracy + confusion matrix
- Writes eval_results.csv under session_dir (or --out_csv)

Usage examples:
python offline_eval_trials.py --session_dir .\records\session_20260303_123456 --ckpt .\cnn_udlr.pth
python offline_eval_trials.py --session_dir ... --ckpt ... --win_sec 0.20 --step_sec 0.05 --vote meanprob
"""

import argparse
import json
from pathlib import Path

import numpy as np

try:
    import torch
    import torch.nn as nn
except Exception as e:
    raise RuntimeError("This script requires PyTorch. Install it first.") from e


DEFAULT_CLASS_NAMES = ["up", "down", "left", "right"]


class EMGCNN(nn.Module):
    def __init__(self, n_channels: int, n_classes: int = 4):
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


def softmax_np(x: np.ndarray, axis: int = -1) -> np.ndarray:
    x = x - np.max(x, axis=axis, keepdims=True)
    e = np.exp(x)
    return e / (np.sum(e, axis=axis, keepdims=True) + 1e-12)


def confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray, n_classes: int) -> np.ndarray:
    cm = np.zeros((n_classes, n_classes), dtype=np.int64)
    for t, p in zip(y_true, y_pred):
        if 0 <= t < n_classes and 0 <= p < n_classes:
            cm[t, p] += 1
    return cm


def prf_from_cm(cm: np.ndarray):
    # per-class precision/recall/f1
    n = cm.shape[0]
    out = []
    for k in range(n):
        tp = cm[k, k]
        fp = cm[:, k].sum() - tp
        fn = cm[k, :].sum() - tp
        prec = tp / (tp + fp + 1e-12)
        rec = tp / (tp + fn + 1e-12)
        f1 = 2 * prec * rec / (prec + rec + 1e-12)
        support = cm[k, :].sum()
        out.append((prec, rec, f1, support))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--session_dir", type=str, required=True, help="folder containing trial_*.npz")
    ap.add_argument("--ckpt", type=str, required=True, help="trained checkpoint .pth")
    ap.add_argument("--win_sec", type=float, default=0.20)
    ap.add_argument("--step_sec", type=float, default=0.05)
    ap.add_argument("--trim_head_sec", type=float, default=0.20)
    ap.add_argument("--trim_tail_sec", type=float, default=0.20)
    ap.add_argument("--vote", type=str, default="majority", choices=["majority", "meanprob"],
                    help="majority: majority vote of per-window argmax; meanprob: mean softmax then argmax")
    ap.add_argument("--use_file_sfreq", action="store_true", default=True,
                    help="use sfreq stored in each trial file (recommended)")
    ap.add_argument("--sfreq", type=float, default=1000.0, help="used only if --use_file_sfreq is False")
    ap.add_argument("--device", type=str, default="auto", choices=["auto", "cpu", "cuda"])
    ap.add_argument("--out_csv", type=str, default=None, help="output csv path; default in session_dir/eval_results.csv")
    ap.add_argument("--out_json", type=str, default=None, help="summary JSON path; default in session_dir/eval_summary.json")
    ap.add_argument("--print_limit", type=int, default=200, help="max per-trial lines printed")
    args = ap.parse_args()

    session_dir = Path(args.session_dir)
    ckpt_path = Path(args.ckpt)
    if not session_dir.exists():
        raise FileNotFoundError(session_dir)
    if not ckpt_path.exists():
        raise FileNotFoundError(ckpt_path)

    # --- load ckpt ---
    map_location = "cpu"
    ckpt = torch.load(str(ckpt_path), map_location=map_location, weights_only=False)
    state = ckpt["model_state_dict"] if isinstance(ckpt, dict) and "model_state_dict" in ckpt else ckpt
    class_names = ckpt.get("class_names", DEFAULT_CLASS_NAMES) if isinstance(ckpt, dict) else DEFAULT_CLASS_NAMES
    n_classes = len(class_names)

    # infer n_channels from state dict
    w0 = None
    for k in state.keys():
        if k.endswith("feature_extractor.0.weight"):
            w0 = state[k]
            break
    if w0 is None:
        # fallback: first conv weight key
        for k in state.keys():
            if k.endswith("weight") and len(state[k].shape) == 3:
                w0 = state[k]
                break
    if w0 is None:
        raise RuntimeError("Cannot infer input channels from checkpoint.")
    n_channels = int(w0.shape[1])

    # device
    if args.device == "auto":
        dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    elif args.device == "cuda":
        if not torch.cuda.is_available():
            print("[Warn] CUDA not available, using CPU.")
            dev = torch.device("cpu")
        else:
            dev = torch.device("cuda")
    else:
        dev = torch.device("cpu")

    model = EMGCNN(n_channels=n_channels, n_classes=n_classes)
    model.load_state_dict(state, strict=True)
    model.to(dev)
    model.eval()

    per_window_norm = True
    mean = None
    std = None
    if isinstance(ckpt, dict):
        per_window_norm = bool(ckpt.get("per_window_norm", True))
        mean = ckpt.get("mean", None)
        std = ckpt.get("std", None)
        if mean is not None:
            mean = np.asarray(mean, dtype=np.float32).reshape(1, 1, -1)
        if std is not None:
            std = np.asarray(std, dtype=np.float32).reshape(1, 1, -1)

    files = sorted(session_dir.glob("trial_*.npz"))
    if not files:
        raise FileNotFoundError(f"no trial_*.npz in {session_dir}")

    y_true = []
    y_pred = []
    rows = []

    printed = 0
    for fp in files:
        obj = np.load(fp, allow_pickle=True)
        emg = obj["emg"].astype(np.float32)  # [T,C]
        file_sfreq = float(obj["sfreq"]) if "sfreq" in obj else float(args.sfreq)
        sfreq = file_sfreq if args.use_file_sfreq else float(args.sfreq)
        lab = int(obj["label_id"]) if "label_id" in obj else -1
        lab_name = str(obj["label_name"]) if "label_name" in obj else (class_names[lab] if 0 <= lab < n_classes else "unknown")

        if emg.ndim != 2:
            continue
        if emg.shape[1] != n_channels:
            # allow if file has different channel count
            print(f"[skip] {fp.name}: channels mismatch file_C={emg.shape[1]} ckpt_C={n_channels}")
            continue

        T = emg.shape[0]
        head = int(round(args.trim_head_sec * sfreq))
        tail = int(round(args.trim_tail_sec * sfreq))
        s = min(max(head, 0), T)
        e = max(s, T - max(tail, 0))
        emg2 = emg[s:e, :]
        dur = emg2.shape[0] / sfreq if sfreq > 0 else 0.0

        win_len = int(round(args.win_sec * sfreq))
        step_len = int(round(args.step_sec * sfreq))
        if win_len <= 4 or step_len <= 0 or emg2.shape[0] < win_len:
            print(f"[skip] {fp.name}: too short for windowing (dur={dur:.2f}s)")
            continue

        probs = []
        preds = []

        with torch.no_grad():
            for start in range(0, emg2.shape[0] - win_len + 1, step_len):
                w = emg2[start:start + win_len, :]  # [win,C]

                if per_window_norm:
                    mu = w.mean(axis=0, keepdims=True)
                    sigma = w.std(axis=0, keepdims=True) + 1e-8
                    w = (w - mu) / sigma
                else:
                    if mean is None or std is None:
                        # fallback to per-window
                        mu = w.mean(axis=0, keepdims=True)
                        sigma = w.std(axis=0, keepdims=True) + 1e-8
                        w = (w - mu) / sigma
                    else:
                        w = (w - mean.reshape(1, -1)) / (std.reshape(1, -1) + 1e-8)

                x = torch.from_numpy(w.T[None, :, :])  # [1,C,T]
                x = x.to(dev)
                logits = model(x).cpu().numpy()[0]  # [K]
                p = softmax_np(logits, axis=0)
                probs.append(p)
                preds.append(int(np.argmax(p)))

        probs = np.asarray(probs, dtype=np.float32)  # [M,K]
        preds = np.asarray(preds, dtype=np.int64)    # [M]

        if args.vote == "meanprob":
            mean_p = probs.mean(axis=0)
            pred = int(np.argmax(mean_p))
            conf = float(np.max(mean_p))
        else:
            # majority vote
            binc = np.bincount(preds, minlength=n_classes)
            pred = int(np.argmax(binc))
            conf = float(binc[pred] / (preds.size + 1e-12))

        y_true.append(lab)
        y_pred.append(pred)

        rows.append({
            "file": fp.name,
            "true_id": lab,
            "true_name": lab_name,
            "pred_id": pred,
            "pred_name": class_names[pred] if 0 <= pred < n_classes else str(pred),
            "confidence": conf,
            "sfreq": sfreq,
            "dur_sec": dur,
            "n_windows": int(preds.size),
        })

        if printed < args.print_limit:
            ok = "OK" if pred == lab else "X"
            print(f"[{ok}] {fp.name}  true={lab}({lab_name})  pred={pred}({class_names[pred]})  conf={conf:.3f}  dur={dur:.2f}s  windows={preds.size}")
            printed += 1

    if not rows:
        raise RuntimeError("No valid trials evaluated.")

    y_true = np.asarray(y_true, dtype=np.int64)
    y_pred = np.asarray(y_pred, dtype=np.int64)

    acc = float((y_true == y_pred).mean())
    print("\n=== Summary ===")
    print("Trials:", y_true.size, "Accuracy:", f"{acc:.3f}")
    cm = confusion_matrix(y_true, y_pred, n_classes=n_classes)
    print("Confusion (rows=true, cols=pred):\n", cm)

    prf = prf_from_cm(cm)
    print("\nPer-class P/R/F1 (support):")
    for k, (p, r, f1, sup) in enumerate(prf):
        name = class_names[k] if k < len(class_names) else str(k)
        print(f"  {k:>2d} {name:<8s}  P={p:.3f} R={r:.3f} F1={f1:.3f}  n={int(sup)}")

    # save csv
    out_csv = Path(args.out_csv) if args.out_csv else session_dir / "eval_results.csv"
    import csv
    with open(out_csv, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print("\n[OK] wrote:", out_csv)

    out_json = Path(args.out_json) if args.out_json else session_dir / "eval_summary.json"
    summary = {
        "session_dir": str(session_dir),
        "ckpt": str(ckpt_path),
        "class_names": list(class_names),
        "vote": args.vote,
        "n_trials": int(y_true.size),
        "accuracy": acc,
        "confusion_matrix": cm.astype(int).tolist(),
        "per_class": [
            {
                "id": int(k),
                "name": class_names[k] if k < len(class_names) else str(k),
                "precision": float(p),
                "recall": float(r),
                "f1": float(f1),
                "support": int(sup),
            }
            for k, (p, r, f1, sup) in enumerate(prf)
        ],
    }
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print("[OK] wrote:", out_json)


if __name__ == "__main__":
    main()
