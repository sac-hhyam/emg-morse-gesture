"""
Stage 1 windowing hyperparameter search.
Runs on a single class. Optimises SNR proxy metric.
Constraint: keep_rate must be between 25% and 55%.
"""

import numpy as np
from pathlib import Path
import itertools

# ── your windowing logic inlined ──────────────────────────────
def smooth_ma(x, k):
    if k <= 1: return x
    w = np.ones(k) / k
    return np.convolve(x, w, mode="same").astype(np.float32)

def run_windowing(emg, sfreq, win_sec, step_sec,
                  trim_head_sec, trim_tail_sec,
                  rms_smooth_sec, thr_q, active_ratio_thresh):

    # trim
    head = int(round(trim_head_sec * sfreq))
    tail = int(round(trim_tail_sec * sfreq))
    emg2 = emg[head : max(head, emg.shape[0] - tail), :]

    win_len  = int(round(win_sec  * sfreq))
    step_len = int(round(step_sec * sfreq))

    # activity mask
    rms   = np.sqrt(np.mean(emg2 ** 2, axis=1))
    k     = max(int(round(rms_smooth_sec * sfreq)), 1)
    rms_s = smooth_ma(rms, k)
    thr   = float(np.quantile(rms_s, thr_q))
    active = (rms_s >= thr).astype(np.float32)

    starts = range(0, emg2.shape[0] - win_len + 1, step_len)

    kept_rms, dropped_rms = [], []
    windows = []

    for st in starts:
        act_ratio = float(active[st:st + win_len].mean())
        mean_r    = float(rms_s[st:st + win_len].mean())
        if act_ratio >= active_ratio_thresh:
            kept_rms.append(mean_r)
            windows.append(emg2[st:st + win_len, :])
        else:
            dropped_rms.append(mean_r)

    total      = len(kept_rms) + len(dropped_rms)
    keep_rate  = len(kept_rms) / total if total > 0 else 0
    snr        = (np.mean(kept_rms) / np.mean(dropped_rms)
                  if kept_rms and dropped_rms else 0)

    return {
        "n_kept":     len(kept_rms),
        "n_dropped":  len(dropped_rms),
        "keep_rate":  keep_rate,
        "snr":        snr,           # ← proxy metric to maximise
        "windows":    windows,
    }

# ── load your thumb file ──────────────────────────────────────
fp    = Path("./records/npz-output/thumb-up-2026-06-27_171100/trial_0001_label1_thumb.npz")
obj   = np.load(fp, allow_pickle=True)
emg   = obj["emg"].astype(np.float32)
sfreq = float(obj["sfreq"])
print(f"Loaded: {emg.shape}  sfreq={sfreq}Hz")

# ── search grid ───────────────────────────────────────────────
thr_q_vals          = [0.55, 0.60, 0.65, 0.70, 0.75, 0.80]
active_ratio_vals   = [0.40, 0.45, 0.50, 0.55, 0.60, 0.65]

# fixed params (tune in Stage 2)
FIXED = dict(
    win_sec        = 0.50,
    step_sec       = 0.10,
    trim_head_sec  = 0.50,
    trim_tail_sec  = 0.50,
    rms_smooth_sec = 0.05,
)

results = []
for thr_q, active_ratio in itertools.product(thr_q_vals, active_ratio_vals):
    r = run_windowing(emg, sfreq,
                      thr_q=thr_q,
                      active_ratio_thresh=active_ratio,
                      **FIXED)

    # constraint: keep_rate must be 25–55%
    valid = 0.25 <= r["keep_rate"] <= 0.55

    results.append({
        "thr_q":        thr_q,
        "active_ratio": active_ratio,
        "n_kept":       r["n_kept"],
        "keep_rate":    round(r["keep_rate"], 3),
        "snr":          round(r["snr"], 4),
        "valid":        valid,
    })

# ── print results table ───────────────────────────────────────
print(f"\n{'thr_q':>6}  {'act_ratio':>9}  {'n_kept':>6}  "
      f"{'keep_%':>7}  {'SNR':>6}  {'valid':>5}")
print("-" * 52)

valid_results = [r for r in results if r["valid"]]
# sort by SNR descending
for r in sorted(valid_results, key=lambda x: x["snr"], reverse=True):
    print(f"  {r['thr_q']:.2f}    {r['active_ratio']:.2f}      "
          f"{r['n_kept']:5d}    {r['keep_rate']*100:5.1f}%   "
          f"{r['snr']:5.3f}   ✓")

# best
best = max(valid_results, key=lambda x: x["snr"])
print(f"\n★ BEST: thr_q={best['thr_q']}  "
      f"active_ratio={best['active_ratio']}  "
      f"SNR={best['snr']}  keep_rate={best['keep_rate']*100:.1f}%  "
      f"n_kept={best['n_kept']}")