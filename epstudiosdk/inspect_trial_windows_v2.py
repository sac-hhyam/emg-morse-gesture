"""
inspect_trial_windows_v2.py  
Same as original but colours windows GREEN (kept) vs RED (dropped)
so you can see the filter working.
"""

import argparse
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

def smooth_ma(x, k):
    if k <= 1: return x
    w = np.ones(k, dtype=np.float32) / float(k)
    return np.convolve(x, w, mode="same").astype(np.float32)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--session_dir",      required=True)
    ap.add_argument("--n",                type=int,   default=3)
    ap.add_argument("--win_sec",          type=float, default=0.50)
    ap.add_argument("--step_sec",         type=float, default=0.10)
    ap.add_argument("--trim_head_sec",    type=float, default=0.50)
    ap.add_argument("--trim_tail_sec",    type=float, default=0.50)
    ap.add_argument("--rms_smooth_sec",   type=float, default=0.05)
    ap.add_argument("--thr_q",            type=float, default=0.60)
    ap.add_argument("--active_ratio_thresh", type=float, default=0.45)
    # zoom into a time range to actually see individual windows
    ap.add_argument("--zoom_start_sec",   type=float, default=0.0)
    ap.add_argument("--zoom_end_sec",     type=float, default=30.0)
    args = ap.parse_args()

    session = Path(args.session_dir)
    files   = sorted(session.glob("trial_*.npz"))
    if not files:
        raise FileNotFoundError("no trial_*.npz found")

    rng  = np.random.default_rng(0)
    pick = rng.choice(files, size=min(args.n, len(files)), replace=False)

    for fp in pick:
        obj   = np.load(fp, allow_pickle=True)
        emg   = obj["emg"].astype(np.float32)
        sfreq = float(obj["sfreq"])
        lab   = int(obj.get("label_id", -1))
        name  = str(obj.get("label_name", ""))

        T    = emg.shape[0]
        t    = np.arange(T) / sfreq
        head = int(round(args.trim_head_sec  * sfreq))
        tail = int(round(args.trim_tail_sec  * sfreq))
        s, e = head, max(head, T - tail)

        win_len  = int(round(args.win_sec  * sfreq))
        step_len = int(round(args.step_sec * sfreq))

        rms   = np.sqrt(np.mean(emg ** 2, axis=1)).astype(np.float32)
        k     = max(int(round(args.rms_smooth_sec * sfreq)), 1)
        rms_s = smooth_ma(rms, k)
        thr   = float(np.quantile(rms_s[s:e], np.clip(args.thr_q, 0.0, 1.0)))
        active = (rms_s >= thr).astype(np.float32)

        # classify every window as kept or dropped
        kept_starts    = []
        dropped_starts = []
        for st in range(s, e - win_len + 1, step_len):
            act_ratio = float(active[st:st + win_len].mean())
            if act_ratio >= args.active_ratio_thresh:
                kept_starts.append(st)
            else:
                dropped_starts.append(st)

        # ── figure: full view + zoomed view ──
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 8))
        fig.suptitle(
            f"{fp.name}  label={lab}({name})  dur={T/sfreq:.2f}s\n"
            f"kept={len(kept_starts)}  dropped={len(dropped_starts)}  "
            f"thr={thr:.1f}µV  win={args.win_sec}s  step={args.step_sec}s",
            fontsize=10
        )

        for ax, title in [(ax1, "Full signal"), (ax2, f"Zoomed {args.zoom_start_sec}–{args.zoom_end_sec}s")]:
            ax.plot(t, rms_s, color="#2196F3", linewidth=0.8, zorder=3)
            ax.axhline(thr,  color="orange", linewidth=1.2,
                       linestyle="--", zorder=4, label=f"threshold ({thr:.1f}µV)")
            ax.axvline(t[s], color="gray",   linewidth=1.0, linestyle="--")
            ax.axvline(t[e - 1], color="gray", linewidth=1.0, linestyle="--")

            # draw kept windows GREEN, dropped windows RED
            ymax = rms_s.max() * 1.05
            for st in kept_starts:
                ax.axvspan(t[st], t[st + win_len],
                           alpha=0.18, color="green", zorder=1)
            for st in dropped_starts:
                ax.axvspan(t[st], t[st + win_len],
                           alpha=0.06, color="red", zorder=1)

            ax.set_ylabel("RMS (µV)")
            ax.set_title(title, fontsize=9)

            green_patch = mpatches.Patch(color="green", alpha=0.5, label=f"kept ({len(kept_starts)})")
            red_patch   = mpatches.Patch(color="red",   alpha=0.4, label=f"dropped ({len(dropped_starts)})")
            ax.legend(handles=[green_patch, red_patch,
                                mpatches.Patch(color="orange", label="threshold")],
                      loc="upper right", fontsize=8)

        # zoom the bottom panel
        ax2.set_xlim(args.zoom_start_sec, args.zoom_end_sec)
        ax1.set_xlabel("time (s)")
        ax2.set_xlabel("time (s)")
        plt.tight_layout()

        out = Path(fp.stem + "_windows_qa.png")
        plt.savefig(out, dpi=130)
        plt.show()
        print(f"Saved {out}")

if __name__ == "__main__":
    main()