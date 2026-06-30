# -*- coding: utf-8 -*-
"""
MODIFIED for Morse-tap sEMG use case.
Tuned for: sustained gestures (~2-3s), sfreq=992Hz, 5-channel forearm band.

Key changes from original:
  - win_sec       0.20 → 0.50   (gestures are 2-3s, 200ms was too thin a slice)
  - step_sec      0.05 → 0.10   (wider step, still 80% overlap on 500ms window)
  - trim_head/tail 0.30 → 0.50  (safe for 273s file, removes ramp-up artifacts)
  - thr_q         0.55 → 0.70   (threshold was at noise floor ~25µV; raise it)
  - active_ratio  0.65 → 0.55   (500ms window spans onset ramp, relax slightly)
  - rms_smooth    0.02 → 0.05   (smooth over ~50 samples at 992Hz for cleaner mask)
  - min_trial_sec 0.60 → 1.00   (gestures are 2-3s; anything shorter is bad data)
  - Added: per-class window count printed with expected yield estimate
  - Added: sfreq sanity check (warns if not ~992Hz)
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


LABELS = {
    0: "rest",
    1: "thumb",       # morse: dot
    2: "two_finger",  # morse: dash
    3: "fist",        # morse: space
}


def smooth_ma(x: np.ndarray, k: int) -> np.ndarray:
    if k <= 1:
        return x
    w = np.ones(k, dtype=np.float32) / float(k)
    return np.convolve(x, w, mode="same").astype(np.float32)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in_dir",  type=str, required=True)
    ap.add_argument("--out_dir", type=str, default=None)

    # ── CHANGED: window & step tuned to 2-3s gestures at 992Hz ──
    ap.add_argument("--win_sec",        type=float, default=0.50)   # was 0.20
    ap.add_argument("--step_sec",       type=float, default=0.10)   # was 0.05

    # ── CHANGED: trim kept small relative to 273s file ──
    ap.add_argument("--trim_head_sec",  type=float, default=0.50)   # was 0.30
    ap.add_argument("--trim_tail_sec",  type=float, default=0.50)   # was 0.30
    ap.add_argument("--min_trial_sec",  type=float, default=1.00)   # was 0.60

    # ── CHANGED: activity filter tuned to your RMS profile ──
    ap.add_argument("--rms_smooth_sec",      type=float, default=0.05)  # was 0.02
    ap.add_argument("--thr_q",               type=float, default=0.70)  # was 0.55
    ap.add_argument("--active_ratio_thresh", type=float, default=0.55)  # was 0.65
    ap.add_argument("--rest_active_ratio_max", type=float, default=0.20,
                    help="for label 0/rest, keep quiet windows with active_ratio <= this")

    ap.add_argument("--min_window_rms_q",    type=float, default=0.00)
    ap.add_argument("--write_index",         action="store_true", default=True)
    ap.add_argument("--session_name",        type=str,   default=None)

    args = ap.parse_args()

    in_dir       = Path(args.in_dir)
    out_dir      = Path(args.out_dir) if args.out_dir else in_dir
    session_name = args.session_name if args.session_name else in_dir.name
    out_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(in_dir.glob("trial_*.npz"))
    if not files:
        raise FileNotFoundError(f"no trial_*.npz found in {in_dir}")

    X_list, y_list, idx_rows = [], [], []
    drop_stats = {k: {"kept": 0, "dropped": 0} for k in LABELS}

    for trial_order, fp in enumerate(files):
        obj   = np.load(fp, allow_pickle=True)
        emg   = obj["emg"].astype(np.float32)   # [T, C]
        sfreq = float(obj["sfreq"])
        lab   = int(obj["label_id"])

        # ── NEW: sanity-check sampling rate ──
        if not (950 < sfreq < 1050):
            print(f"[warn] {fp.name}: unexpected sfreq={sfreq:.1f}Hz (expected ~992Hz)")

        if lab not in LABELS:
            print(f"[skip] {fp.name}: unknown label_id={lab}")
            continue

        T    = emg.shape[0]
        head = int(round(args.trim_head_sec * sfreq))
        tail = int(round(args.trim_tail_sec * sfreq))
        s    = head
        e    = max(s, T - tail)
        emg2 = emg[s:e, :]

        if emg2.shape[0] < int(round(args.min_trial_sec * sfreq)):
            print(f"[skip] {fp.name}: too short after trim: {emg2.shape[0]/sfreq:.2f}s")
            continue

        win_len  = int(round(args.win_sec  * sfreq))
        step_len = int(round(args.step_sec * sfreq))

        # ── activity mask ──
        rms   = np.sqrt(np.mean(emg2 ** 2, axis=1)).astype(np.float32)
        k     = max(int(round(args.rms_smooth_sec * sfreq)), 1)
        rms_s = smooth_ma(rms, k)
        thr   = float(np.quantile(rms_s, np.clip(args.thr_q, 0.0, 1.0)))
        active = (rms_s >= thr).astype(np.float32)

        win_starts    = list(range(0, emg2.shape[0] - win_len + 1, step_len))
        win_mean_rms  = np.array(
            [float(rms_s[st:st + win_len].mean()) for st in win_starts],
            dtype=np.float32
        )

        if args.min_window_rms_q > 0:
            win_rms_thr = float(np.quantile(win_mean_rms,
                                            np.clip(args.min_window_rms_q, 0, 1)))
        else:
            win_rms_thr = -np.inf

        for i, st in enumerate(win_starts):
            act_ratio = float(active[st:st + win_len].mean())
            mean_r    = float(win_mean_rms[i])
            if lab == 0:
                keep = act_ratio <= args.rest_active_ratio_max
            else:
                keep = (act_ratio >= args.active_ratio_thresh) and (mean_r >= win_rms_thr)

            if keep:
                w = emg2[st:st + win_len, :]   # [win_len, C]
                X_list.append(w)
                y_list.append(lab)
                drop_stats[lab]["kept"] += 1
            else:
                drop_stats[lab]["dropped"] += 1

            if args.write_index:
                idx_rows.append({
                    "session_name":           session_name,
                    "trial_order":            int(trial_order),
                    "trial_file":             fp.name,
                    "win_idx_in_trial":       int(i),
                    "label_id":               lab,
                    "label_name":             LABELS[lab],
                    "sfreq":                  sfreq,
                    "win_sec":                args.win_sec,
                    "step_sec":               args.step_sec,
                    "win_start_sample":       int(st),
                    "win_end_sample":         int(st + win_len),
                    "active_ratio":           act_ratio,
                    "mean_rms":               mean_r,
                    "thr_value":              thr,
                    "keep":                   int(keep),
                })

    if not X_list:
        raise RuntimeError(
            "No windows built. Try lowering --thr_q or --active_ratio_thresh"
        )

    X = np.stack(X_list, axis=0).astype(np.float32)  # [N, win_len, C]
    y = np.asarray(y_list, dtype=np.int64)

    np.save(out_dir / "X_single_windows.npy", X)
    np.save(out_dir / "y_single_labels.npy",  y)

    pd.Series({LABELS[k]: k for k in sorted(LABELS)}).to_csv(
        out_dir / "gesture_to_id_single.csv", header=False, encoding="utf-8-sig"
    )
    if args.write_index and idx_rows:
        pd.DataFrame(idx_rows).to_csv(
            out_dir / "windows_index.csv", index=False, encoding="utf-8-sig"
        )

    # ── NEW: detailed yield report ──
    print("\n" + "=" * 55)
    print("WINDOW YIELD REPORT")
    print(f"  Output shape : X={X.shape}  y={y.shape}")
    print(f"  win_sec={args.win_sec}s  step_sec={args.step_sec}s  "
          f"thr_q={args.thr_q}  active_ratio>={args.active_ratio_thresh}")
    print("-" * 55)
    for k in sorted(LABELS):
        kept    = drop_stats[k]["kept"]
        dropped = drop_stats[k]["dropped"]
        total   = kept + dropped
        rate    = kept / total if total > 0 else 0.0
        bar     = "#" * int(rate * 20)
        print(f"  {LABELS[k]:12s}: kept={kept:4d}  dropped={dropped:4d}"
              f"  keep_rate={rate:.0%}  {bar}")
    print("=" * 55)


if __name__ == "__main__":
    main()
