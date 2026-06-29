"""
inspect_trial_windows_v3.py
Reads windows_index.csv produced by build_windows_morse.py
so the plot shows EXACTLY what was kept/dropped — not a recomputation.
"""

import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


def smooth_ma(x, k):
    if k <= 1: return x
    w = np.ones(k, dtype=np.float32) / float(k)
    return np.convolve(x, w, mode="same").astype(np.float32)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--session_dir",   required=True,
                    help="same folder you passed as --in_dir to build_windows_morse.py")
    ap.add_argument("--zoom_start_sec", type=float, default=0.0)
    ap.add_argument("--zoom_end_sec",   type=float, default=30.0)
    args = ap.parse_args()

    session = Path(args.session_dir)

    # ── load the index built by build_windows_morse.py ──
    index_path = session / "windows_index.csv"
    if not index_path.exists():
        raise FileNotFoundError(
            f"windows_index.csv not found in {session}\n"
            f"Re-run build_windows_morse.py with --write_index first."
        )

    idx = pd.read_csv(index_path)
    print(f"Loaded index: {len(idx)} rows  "
          f"kept={idx['keep'].sum()}  dropped={(idx['keep']==0).sum()}")

    # ── read parameters from the index itself ──
    # no need to pass them in — they're recorded in the CSV
    win_sec  = float(idx["win_sec"].iloc[0])
    step_sec = float(idx["step_sec"].iloc[0])
    print(f"Parameters from index: win_sec={win_sec}s  step_sec={step_sec}s")

    # ── plot one panel per unique trial file ──
    for trial_file, group in idx.groupby("trial_file"):
        fp = session / trial_file
        if not fp.exists():
            print(f"[skip] {trial_file} not found")
            continue

        obj   = np.load(fp, allow_pickle=True)
        emg   = obj["emg"].astype(np.float32)
        sfreq = float(group["sfreq"].iloc[0])
        lab   = int(group["label_id"].iloc[0])
        name  = str(group["label_name"].iloc[0])

        T = emg.shape[0]
        t = np.arange(T) / sfreq

        # recompute RMS just for display (not for decisions)
        rms   = np.sqrt(np.mean(emg ** 2, axis=1)).astype(np.float32)
        rms_s = smooth_ma(rms, max(int(round(0.05 * sfreq)), 1))

        # ── get kept/dropped start times DIRECTLY from index ──
        win_len = int(round(win_sec * sfreq))

        kept_group    = group[group["keep"] == 1]
        dropped_group = group[group["keep"] == 0]

        kept_starts    = kept_group["win_start_sample"].values
        dropped_starts = dropped_group["win_start_sample"].values

        # threshold value recorded in the index
        thr = float(group["thr_value"].iloc[0])

        # ── plot ──
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 8))
        fig.suptitle(
            f"{trial_file}  label={lab}({name})  dur={T/sfreq:.2f}s\n"
            f"kept={len(kept_starts)}  dropped={len(dropped_starts)}  "
            f"thr={thr:.1f}µV  win={win_sec}s  step={step_sec}s  "
            f"[SOURCE: windows_index.csv — exact match to .npy]",
            fontsize=9
        )

        for ax, title in [
            (ax1, "Full signal"),
            (ax2, f"Zoomed {args.zoom_start_sec}–{args.zoom_end_sec}s")
        ]:
            ax.plot(t, rms_s, color="#2196F3", linewidth=0.8, zorder=3)
            ax.axhline(thr, color="orange", linewidth=1.2,
                       linestyle="--", zorder=4)

            for st in kept_starts:
                ax.axvspan(t[st], t[min(st + win_len, T - 1)],
                           alpha=0.18, color="green", zorder=1)
            for st in dropped_starts:
                ax.axvspan(t[st], t[min(st + win_len, T - 1)],
                           alpha=0.06, color="red", zorder=1)

            ax.set_ylabel("RMS (µV)")
            ax.set_title(title, fontsize=9)
            ax.legend(handles=[
                mpatches.Patch(color="green",  alpha=0.5,
                               label=f"kept ({len(kept_starts)}) — exact .npy windows"),
                mpatches.Patch(color="red",    alpha=0.4,
                               label=f"dropped ({len(dropped_starts)})"),
                mpatches.Patch(color="orange", alpha=0.8,
                               label=f"threshold {thr:.1f}µV"),
            ], loc="upper right", fontsize=8)

        ax2.set_xlim(args.zoom_start_sec, args.zoom_end_sec)
        ax1.set_xlabel("time (s)")
        ax2.set_xlabel("time (s)")
        plt.tight_layout()

        out = Path(fp.stem + "_windows_qa_v3.png")
        plt.savefig(out, dpi=130)
        plt.show()
        print(f"Saved {out}")


if __name__ == "__main__":
    main()