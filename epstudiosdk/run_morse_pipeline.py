# -*- coding: utf-8 -*-
"""Run the Morse EMG offline pipeline end to end.

Steps:
1. Build windows from one or more trial folders with build_windows_morse.py.
2. Train the CNN from all generated windows.
3. Write a checkpoint plus metrics JSON containing validation/test accuracy.

Example:
python -m epstudiosdk.run_morse_pipeline \
  --session_dirs epstudiosdk/records/npz-output/thumb-up-2026-06-27_171100 \
                 epstudiosdk/records/npz-output/two-finger-2026-06-27_171620 \
                 epstudiosdk/records/npz-output/fist-2026-06-27_171620 \
  --ckpt epstudiosdk/cnn_morse.pth
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run(cmd):
    print("\n[run]", " ".join(str(x) for x in cmd))
    subprocess.run(cmd, check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--session_dirs", nargs="+", required=True,
                    help="folders containing trial_*.npz files")
    ap.add_argument("--ckpt", default="cnn_morse.pth")
    ap.add_argument("--metrics_json", default=None)
    ap.add_argument("--skip_windowing", action="store_true",
                    help="reuse existing X_single_windows.npy/y_single_labels.npy")

    # Windowing parameters.
    ap.add_argument("--win_sec", type=float, default=0.50)
    ap.add_argument("--step_sec", type=float, default=0.10)
    ap.add_argument("--trim_head_sec", type=float, default=0.50)
    ap.add_argument("--trim_tail_sec", type=float, default=0.50)
    ap.add_argument("--min_trial_sec", type=float, default=1.00)
    ap.add_argument("--rms_smooth_sec", type=float, default=0.05)
    ap.add_argument("--thr_q", type=float, default=0.70)
    ap.add_argument("--active_ratio_thresh", type=float, default=0.55)
    ap.add_argument("--min_window_rms_q", type=float, default=0.00)

    # Training parameters.
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--patience", type=int, default=8)
    ap.add_argument("--batch_size", type=int, default=64)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--split_mode", choices=["time_block", "group", "random"], default="time_block",
                    help="time_block is recommended for long sessions with overlapping windows")
    ap.add_argument("--gap_windows", type=int, default=5,
                    help="windows to drop between train/val/test blocks")
    ap.add_argument("--train_frac", type=float, default=0.70)
    ap.add_argument("--val_frac", type=float, default=0.15)
    norm_group = ap.add_mutually_exclusive_group()
    norm_group.add_argument("--global_norm", dest="per_window_norm", action="store_false",
                            help="fit mean/std on train set only, then apply to train/val/test (default)")
    norm_group.add_argument("--per_window_norm", dest="per_window_norm", action="store_true",
                            help="normalize each window by its own mean/std")
    ap.set_defaults(per_window_norm=False)
    ap.add_argument("--no_group_split", action="store_true",
                    help="deprecated alias for --split_mode random")
    args = ap.parse_args()

    session_dirs = [Path(p) for p in args.session_dirs]
    for session_dir in session_dirs:
        if not session_dir.exists():
            raise FileNotFoundError(session_dir)

    if not args.skip_windowing:
        for session_dir in session_dirs:
            cmd = [
                sys.executable, "-m", "epstudiosdk.build_windows_morse",
                "--in_dir", str(session_dir),
                "--win_sec", str(args.win_sec),
                "--step_sec", str(args.step_sec),
                "--trim_head_sec", str(args.trim_head_sec),
                "--trim_tail_sec", str(args.trim_tail_sec),
                "--min_trial_sec", str(args.min_trial_sec),
                "--rms_smooth_sec", str(args.rms_smooth_sec),
                "--thr_q", str(args.thr_q),
                "--active_ratio_thresh", str(args.active_ratio_thresh),
                "--min_window_rms_q", str(args.min_window_rms_q),
                "--write_index",
            ]
            run(cmd)

    metrics_json = args.metrics_json
    if metrics_json is None:
        metrics_json = str(Path(args.ckpt).with_suffix(".metrics.json"))

    train_cmd = [
        sys.executable, "-m", "epstudiosdk.train_cnn_4actions_simple",
        "--data_dirs", *[str(p) for p in session_dirs],
        "--ckpt", str(args.ckpt),
        "--metrics_json", metrics_json,
        "--epochs", str(args.epochs),
        "--patience", str(args.patience),
        "--batch_size", str(args.batch_size),
        "--lr", str(args.lr),
        "--seed", str(args.seed),
        "--split_mode", "random" if args.no_group_split else str(args.split_mode),
        "--gap_windows", str(args.gap_windows),
        "--train_frac", str(args.train_frac),
        "--val_frac", str(args.val_frac),
    ]
    train_cmd.append("--per_window_norm" if args.per_window_norm else "--global_norm")
    run(train_cmd)

    print("\n[OK] pipeline complete")
    print("[OK] checkpoint:", args.ckpt)
    print("[OK] metrics:", metrics_json)


if __name__ == "__main__":
    main()
