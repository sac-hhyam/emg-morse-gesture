#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_windows_split.py — Leakage-free windowing with raw-signal-level train/test split.

Problem with the previous approach (build_windows_morse.py)
------------------------------------------------------------
The old pipeline windows the FULL signal first, then train_cnn_4actions_simple.py
splits the resulting window array.  With 80 % overlap (0.50 s window / 0.10 s step)
adjacent windows share 80 % of their samples, so "train" and "test" windows from
the same recording share most of their underlying raw samples — data leakage that
inflates within-session accuracy.

Fix
---
Split the RAW EMG signal at the train_ratio time-point FIRST, then window each
half independently.  No raw sample appears in both a train window and a test window.

The activity-filter threshold is computed from the TRAIN half only and applied
unchanged to the TEST half, so no test-set statistics influence the keep/drop
decision.

Output (written to out_dir, one set per session)
-------------------------------------------------
X_train.npy          float32  [N_train, win_len, C]
y_train.npy          int64    [N_train]
X_test.npy           float32  [N_test,  win_len, C]
y_test.npy           int64    [N_test]
split_index.csv      per-window traceability (split, trial, start_sample,
                     active_ratio, thr_value, keep)
gesture_to_id_single.csv  label-name → id (same format as build_windows_morse.py,
                           so train_cnn_4actions_simple.py can still read class names)

Usage
-----
python -m epstudiosdk.build_windows_split \\
    --in_dir  epstudiosdk/records/npz-output/thumb-up-2026-06-27_171100 \\
    --train_ratio 0.80 \\
    --win_sec 0.50 --step_sec 0.10 \\
    --thr_q 0.60 --active_ratio_thresh 0.45 --rms_smooth_sec 0.05 \\
    --trim_head_sec 0.50 --trim_tail_sec 0.50
"""

import argparse
import csv
from pathlib import Path

import numpy as np

LABELS = {1: "down", 2: "tapping", 3: "fist"}


def _smooth_ma(x: np.ndarray, k: int) -> np.ndarray:
    if k <= 1:
        return x
    return np.convolve(x, np.ones(k, dtype=np.float32) / k, mode="same").astype(np.float32)


def _window_half(
    emg: np.ndarray,
    win_len: int,
    step_len: int,
    rms_smooth_k: int,
    thr_value: float,
    active_ratio_thresh: float,
    rest_active_ratio_max: float,
    label: int,
    split: str,
    trial_file: str,
    trial_order: int,
    global_offset: int,
) -> tuple:
    """Slide windows over one EMG half-segment and apply the activity filter.

    thr_value must be pre-computed from the TRAIN half so the test half uses no
    information derived from its own signal statistics.

    Returns (X_list, y_list, index_rows).
    """
    X_list: list = []
    y_list: list = []
    rows:   list = []

    if emg.shape[0] < win_len:
        return X_list, y_list, rows

    rms   = np.sqrt(np.mean(emg ** 2, axis=1)).astype(np.float32)
    rms_s = _smooth_ma(rms, rms_smooth_k)
    active = (rms_s >= thr_value).astype(np.float32)

    for i, st in enumerate(range(0, emg.shape[0] - win_len + 1, step_len)):
        act_ratio = float(active[st:st + win_len].mean())

        # REST windows are kept when QUIET; gesture windows are kept when ACTIVE.
        if label == 0:
            keep = act_ratio <= rest_active_ratio_max
        else:
            keep = act_ratio >= active_ratio_thresh

        if keep:
            X_list.append(emg[st:st + win_len].copy())
            y_list.append(label)

        rows.append({
            "split":                   split,
            "trial_order":             trial_order,
            "trial_file":              trial_file,
            "label_id":                label,
            "label_name":              LABELS.get(label, str(label)),
            "win_idx_in_half":         i,
            "win_start_sample_in_half": st,
            "win_end_sample_in_half":  st + win_len,
            "win_start_sample_global": global_offset + st,
            "active_ratio":            round(act_ratio, 5),
            "thr_value":               round(float(thr_value), 7),
            "keep":                    int(keep),
        })

    return X_list, y_list, rows


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Split raw EMG at train_ratio then window each half — fixes overlap leakage."
    )
    ap.add_argument("--in_dir",  required=True,
                    help="session folder containing trial_*.npz files")
    ap.add_argument("--out_dir", default=None,
                    help="output folder (default: same as in_dir)")
    ap.add_argument("--train_ratio", type=float, default=0.80,
                    help="fraction of trimmed signal used for training (default 0.80)")

    # Windowing — same defaults as the associate's spec
    ap.add_argument("--win_sec",            type=float, default=0.50)
    ap.add_argument("--step_sec",           type=float, default=0.10)
    ap.add_argument("--trim_head_sec",      type=float, default=0.50)
    ap.add_argument("--trim_tail_sec",      type=float, default=0.50)
    ap.add_argument("--min_trial_sec",      type=float, default=1.00)
    ap.add_argument("--rms_smooth_sec",     type=float, default=0.05)
    ap.add_argument("--thr_q",              type=float, default=0.60)
    ap.add_argument("--active_ratio_thresh",type=float, default=0.45)
    ap.add_argument("--rest_active_ratio_max", type=float, default=0.20,
                    help="for label=0/rest, keep windows with active_ratio <= this")

    args = ap.parse_args()

    in_dir  = Path(args.in_dir)
    out_dir = Path(args.out_dir) if args.out_dir else in_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(in_dir.glob("trial_*.npz"))
    if not files:
        raise FileNotFoundError(f"no trial_*.npz found in {in_dir}")

    X_train_all: list = []
    y_train_all: list = []
    X_test_all:  list = []
    y_test_all:  list = []
    all_rows:    list = []

    yield_stats = {
        lab: {"train_kept": 0, "train_drop": 0, "test_kept": 0, "test_drop": 0}
        for lab in LABELS
    }

    for trial_order, fp in enumerate(files):
        obj   = np.load(fp, allow_pickle=True)
        emg   = obj["emg"].astype(np.float32)   # [T, C]
        sfreq = float(obj["sfreq"])
        label = int(obj["label_id"])

        if label not in LABELS:
            print(f"[skip] {fp.name}: unknown label_id={label}")
            continue

        T    = emg.shape[0]
        head = int(round(args.trim_head_sec * sfreq))
        tail = int(round(args.trim_tail_sec * sfreq))
        emg_trimmed = emg[head: max(head, T - tail)]
        T2 = emg_trimmed.shape[0]

        if T2 < int(round(args.min_trial_sec * sfreq)):
            print(f"[skip] {fp.name}: too short after trim ({T2/sfreq:.2f}s)")
            continue

        # ── Raw-signal split ────────────────────────────────────────────────
        split_sample = int(round(args.train_ratio * T2))
        train_emg = emg_trimmed[:split_sample]
        test_emg  = emg_trimmed[split_sample:]

        win_len    = int(round(args.win_sec    * sfreq))
        step_len   = int(round(args.step_sec   * sfreq))
        rms_k      = max(1, int(round(args.rms_smooth_sec * sfreq)))

        print(f"  {fp.name}  label={LABELS.get(label, label)}  "
              f"dur={T2/sfreq:.1f}s  split@{split_sample/sfreq:.1f}s  "
              f"(train={split_sample} test={T2-split_sample} samples)")

        # Threshold fitted on TRAIN half only — no test statistics leak in
        if train_emg.shape[0] >= win_len:
            rms_tr = np.sqrt(np.mean(train_emg ** 2, axis=1)).astype(np.float32)
            rms_tr_s = _smooth_ma(rms_tr, rms_k)
            thr_value = float(np.quantile(rms_tr_s, np.clip(args.thr_q, 0.0, 1.0)))
        else:
            thr_value = 0.0

        # ── Window train half ───────────────────────────────────────────────
        Xt, yt, rows_tr = _window_half(
            train_emg, win_len, step_len, rms_k,
            thr_value, args.active_ratio_thresh, args.rest_active_ratio_max,
            label, "train", fp.name, trial_order, head,
        )
        X_train_all.extend(Xt)
        y_train_all.extend(yt)
        all_rows.extend(rows_tr)

        kept_tr = sum(r["keep"] for r in rows_tr)
        yield_stats[label]["train_kept"] += kept_tr
        yield_stats[label]["train_drop"] += len(rows_tr) - kept_tr

        # ── Window test half (same threshold from train) ────────────────────
        Xte, yte, rows_te = _window_half(
            test_emg, win_len, step_len, rms_k,
            thr_value, args.active_ratio_thresh, args.rest_active_ratio_max,
            label, "test", fp.name, trial_order, head + split_sample,
        )
        X_test_all.extend(Xte)
        y_test_all.extend(yte)
        all_rows.extend(rows_te)

        kept_te = sum(r["keep"] for r in rows_te)
        yield_stats[label]["test_kept"] += kept_te
        yield_stats[label]["test_drop"] += len(rows_te) - kept_te

    if not X_train_all:
        raise RuntimeError(
            "No training windows built — lower --thr_q or --active_ratio_thresh"
        )

    X_train = np.stack(X_train_all, axis=0).astype(np.float32)
    y_train = np.asarray(y_train_all, dtype=np.int64)

    if X_test_all:
        X_test = np.stack(X_test_all, axis=0).astype(np.float32)
        y_test = np.asarray(y_test_all, dtype=np.int64)
    else:
        print("[warn] no test windows built (test segment too short for windowing)")
        X_test = np.zeros((0, X_train.shape[1], X_train.shape[2]), dtype=np.float32)
        y_test = np.zeros((0,), dtype=np.int64)

    # ── Save arrays ─────────────────────────────────────────────────────────
    np.save(out_dir / "X_train.npy", X_train)
    np.save(out_dir / "y_train.npy", y_train)
    np.save(out_dir / "X_test.npy",  X_test)
    np.save(out_dir / "y_test.npy",  y_test)

    # gesture_to_id_single.csv — only write labels present in the actual data
    # so the training script doesn't create phantom classes with zero support
    present_labels = set(y_train_all)
    if y_test_all:
        present_labels |= set(y_test_all)
    with open(out_dir / "gesture_to_id_single.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        for lab_id in sorted(present_labels):
            w.writerow([LABELS.get(lab_id, f"class_{lab_id}"), lab_id])

    # split_index.csv — full per-window traceability (kept + dropped)
    if all_rows:
        with open(out_dir / "split_index.csv", "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
            w.writeheader()
            w.writerows(all_rows)

    # ── Yield report ─────────────────────────────────────────────────────────
    print()
    print("=" * 65)
    print("WINDOW YIELD REPORT  (leakage-free raw-signal split)")
    print(f"  win={args.win_sec}s  step={args.step_sec}s  "
          f"thr_q={args.thr_q}  active_ratio>={args.active_ratio_thresh}  "
          f"train_ratio={args.train_ratio}")
    print("-" * 65)
    for lab in sorted(LABELS):
        s = yield_stats[lab]
        tr_total = s["train_kept"] + s["train_drop"]
        te_total = s["test_kept"]  + s["test_drop"]
        if tr_total + te_total == 0:
            continue
        tr_rate = s["train_kept"] / tr_total if tr_total > 0 else 0.0
        te_rate = s["test_kept"]  / te_total if te_total > 0 else 0.0
        bar = "#" * int(tr_rate * 15)
        print(f"  {LABELS[lab]:12s}  "
              f"train kept={s['train_kept']:4d}/{tr_total:4d} ({tr_rate:.0%})  "
              f"test kept={s['test_kept']:3d}/{te_total:3d} ({te_rate:.0%})  {bar}")
    print("-" * 65)
    print(f"  TOTAL   X_train={X_train.shape}   X_test={X_test.shape}")
    print("=" * 65)
    print(f"[saved] {out_dir}/X_train.npy  y_train.npy  X_test.npy  y_test.npy")
    print(f"[saved] {out_dir}/split_index.csv  gesture_to_id_single.csv")


if __name__ == "__main__":
    main()