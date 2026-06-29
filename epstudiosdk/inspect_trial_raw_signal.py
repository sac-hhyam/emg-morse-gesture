# -*- coding: utf-8 -*-
"""
Visual QA: show the RAW multi-channel EMG signal (not the smoothed RMS
envelope) for a trial, with the same trim-boundary and window-start markers
as inspect_trial_windows.py -- the two scripts are meant to be read side by
side: inspect_trial_windows.py shows what build_windows_from_trials.py
*computes* (the RMS activity signal), this one shows what it actually
*slices windows out of* (the raw channels).

For long recordings (e.g. a whole multi-minute EDF converted as one trial),
plotting the entire raw signal at once is unreadable -- use --start_sec and
--duration_sec to scrub through a manageable chunk at a time.

Usage:
    python -m epstudiosdk.inspect_trial_raw_signal --session_dir epstudiosdk/records/<session> --n 1
    python -m epstudiosdk.inspect_trial_raw_signal --session_dir epstudiosdk/records/<session> \
        --trial_file trial_0001_label1_thumb.npz --start_sec 30 --duration_sec 10
"""

import argparse
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--session_dir", required=True, help="folder containing trial_*.npz")
    ap.add_argument("--trial_file", type=str, default=None,
                     help="exact filename to inspect; if omitted, picks --n random trials")
    ap.add_argument("--n", type=int, default=3, help="number of random trials to show (ignored if --trial_file set)")
    ap.add_argument("--start_sec", type=float, default=0.0, help="where to start the plotted window, in seconds")
    ap.add_argument("--duration_sec", type=float, default=10.0, help="how many seconds to plot at once")
    ap.add_argument("--win_sec", type=float, default=0.20)
    ap.add_argument("--step_sec", type=float, default=0.05)
    ap.add_argument("--trim_head_sec", type=float, default=0.20)
    ap.add_argument("--trim_tail_sec", type=float, default=0.20)
    args = ap.parse_args()

    session = Path(args.session_dir)
    if args.trial_file:
        files = [session / args.trial_file]
        if not files[0].exists():
            raise FileNotFoundError(files[0])
    else:
        files = sorted(session.glob("trial_*.npz"))
        if not files:
            raise FileNotFoundError(f"no trial_*.npz in {session}")
        rng = np.random.default_rng(0)
        files = list(rng.choice(files, size=min(args.n, len(files)), replace=False))

    for fp in files:
        obj = np.load(fp, allow_pickle=True)
        emg_full = obj["emg"].astype(np.float32)  # [T,C]
        sfreq = float(obj["sfreq"])
        lab = int(obj["label_id"]) if "label_id" in obj else -1
        name = str(obj["label_name"]) if "label_name" in obj else ""
        channels = obj["channels"] if "channels" in obj else np.arange(1, emg_full.shape[1] + 1)
        full_dur = emg_full.shape[0] / sfreq

        start_idx = int(round(args.start_sec * sfreq))
        n_show = int(round(args.duration_sec * sfreq))
        end_idx = min(emg_full.shape[0], start_idx + n_show)
        if start_idx >= emg_full.shape[0]:
            print(f"[skip] {fp.name}: --start_sec {args.start_sec} is past the trial's "
                  f"duration ({full_dur:.2f}s)")
            continue

        emg = emg_full[start_idx:end_idx]
        t = (np.arange(start_idx, end_idx) / sfreq)  # absolute time within the trial

        # trim/window markers, drawn at their absolute position, only if visible in this slice
        head_t = args.trim_head_sec
        tail_t = full_dur - args.trim_tail_sec
        win_len = int(round(args.win_sec * sfreq))
        step_len = int(round(args.step_sec * sfreq))
        head_idx = int(round(args.trim_head_sec * sfreq))
        tail_idx = max(head_idx, emg_full.shape[0] - int(round(args.trim_tail_sec * sfreq)))
        win_starts = list(range(head_idx, tail_idx - win_len + 1, step_len)) if tail_idx - head_idx >= win_len else []

        n_ch = emg.shape[1]
        fig, axes = plt.subplots(n_ch, 1, figsize=(12, 1.5 * n_ch + 1), sharex=True)
        if n_ch == 1:
            axes = [axes]

        for i, ax in enumerate(axes):
            ax.plot(t, emg[:, i], linewidth=0.6, color="C0")
            if start_idx <= head_idx <= end_idx:
                ax.axvline(head_t, linestyle="--", color="gray")
            if start_idx <= tail_idx <= end_idx:
                ax.axvline(tail_t, linestyle="--", color="gray")
            for st in win_starts:
                st_t = st / sfreq
                if t[0] <= st_t <= t[-1]:
                    ax.axvline(st_t, alpha=0.08, color="C0")
            ax.set_ylabel(f"ch{channels[i]}\n(uV)")
            ax.grid(True, alpha=0.3)

        axes[-1].set_xlabel("time (s)")
        fig.suptitle(
            f"{fp.name}  label={lab}({name})  showing [{t[0]:.2f}s, {t[-1]:.2f}s] "
            f"of {full_dur:.2f}s total  sfreq={sfreq:.0f}Hz"
        )
        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    main()