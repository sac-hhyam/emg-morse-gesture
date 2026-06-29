# Data

Raw sEMG recordings are not stored in this repository (binary files, ~300MB total).

## Download

Google Drive: [emg-morse-gesture-data](https://drive.google.com/drive/folders/1jnh2WNp0HAln25QXVELGWYRU0DxCpiQL?usp=share_link)

---

## Full Reproduction Chain

```
raw-edf/                        (hardware output — ground truth)
      ↓  edf_to_trial_npz.py
npz-output/                     (Python-readable trials)
      ↓  build_windows_morse.py
X_single_windows.npy            (training-ready windows)
      ↓  train_cnn_4actions_simple.py
trained classifier
```

### Step 0 — Convert EDF to NPZ

```bash
# thumb (DOT)
python epstudiosdk/edf_to_trial_npz.py \
  --edf_dir ./epstudiosdk/records/Edward/2026-06-27_171100/ \
  --out_dir ./epstudiosdk/records/npz-output/thumb-up-2026-06-27_171100/ \
  --label_id 1 \
  --label_name thumb

# two-finger (DASH)
python epstudiosdk/edf_to_trial_npz.py \
  --edf_dir ./epstudiosdk/records/Edward/2026-06-27_171620/ \
  --out_dir ./epstudiosdk/records/npz-output/two-finger-2026-06-27_171620/ \
  --label_id 2 \
  --label_name two_finger

# fist (SPACE)
python epstudiosdk/edf_to_trial_npz.py \
  --edf_dir ./epstudiosdk/records/Edward/2026-06-27_173710/ \
  --out_dir ./epstudiosdk/records/npz-output/fist-2026-06-27_173710/ \
  --label_id 3 \
  --label_name fist
```

> Note: verify exact argument names with `python epstudiosdk/edf_to_trial_npz.py --help`
> before running — flags above may differ slightly from your version.

### Step 1 — Convert NPZ to Windows

```bash
# thumb
python epstudiosdk/build_windows_morse.py \
  --in_dir ./epstudiosdk/records/npz-output/thumb-up-2026-06-27_171100/ \
  --win_sec 0.50 --step_sec 0.10 \
  --trim_head_sec 0.50 --trim_tail_sec 0.50 \
  --thr_q 0.60 --active_ratio_thresh 0.45 \
  --rms_smooth_sec 0.05 --write_index

# two-finger (add --skip_head_sec 90 for electrode settling)
python epstudiosdk/build_windows_morse.py \
  --in_dir ./epstudiosdk/records/npz-output/two-finger-2026-06-27_171620/ \
  --win_sec 0.50 --step_sec 0.10 \
  --trim_head_sec 0.50 --trim_tail_sec 0.50 \
  --thr_q 0.60 --active_ratio_thresh 0.45 \
  --rms_smooth_sec 0.05 --skip_head_sec 90 --write_index

# fist
python epstudiosdk/build_windows_morse.py \
  --in_dir ./epstudiosdk/records/npz-output/fist-2026-06-27_173710/ \
  --win_sec 0.50 --step_sec 0.10 \
  --trim_head_sec 0.50 --trim_tail_sec 0.50 \
  --thr_q 0.60 --active_ratio_thresh 0.45 \
  --rms_smooth_sec 0.05 --write_index
```

---

## Google Drive Folder Structure

<<<<<<< Updated upstream
```
emg-morse-gesture-data/
├── raw-edf/
│   ├── 2026-06-27_171100/             ← thumb session
│   │   ├── EP/
│   │   │   └── MH3130C.01.107_default_EP.edf
│   │   ├── EPFilter/
│   │   │   └── MH3130C.01.107_default_EPFilter.edf
│   │   ├── EVENT/
│   │   │   └── event.edf
│   │   └── info.txt
│   ├── 2026-06-27_171620/             ← two-finger session
│   └── 2026-06-27_173710/             ← fist session
│
└── npz-output/
    ├── thumb-up-2026-06-27_171100/
    │   ├── trial_0001_label1_thumb.npz
    │   ├── X_single_windows.npy
    │   ├── y_single_labels.npy
    │   ├── gesture_to_id_single.csv
    │   └── windows_index.csv
    ├── two-finger-2026-06-27_171620/
    │   └── ...
    └── fist-2026-06-27_173710/
        └── ...
```

After downloading, place both folders under `epstudiosdk/records/`:

```
epstudiosdk/records/
├── Edward/          ← raw-edf contents go here
└── npz-output/      ← npz-output contents go here
```

---

## EDF Session Map

| EDF Folder | Gesture | Label ID | Label Name | Duration |
|---|---|---|---|---|
| 2026-06-27_171100 | Thumb | 1 | thumb | 273s |
| 2026-06-27_171620 | Two-finger | 2 | two_finger | 194s |
| 2026-06-27_173710 | Fist | 3 | fist | 206s |
| — | Rest | 0 | rest | not yet recorded |

---

## Window Yield Summary

| Gesture | Windows kept | Keep rate | Notes |
|---|---|---|---|
| thumb (DOT) | 1119 | 41% | Clean signal throughout |
| two_finger (DASH) | 796 | 41% | Use --skip_head_sec 90 for electrode settling |
| fist (SPACE) | 872 | 43% | Clean signal throughout |
| rest | — | — | Not yet recorded |

---
=======
| Session                      | Gesture           | Duration | Windows kept | Notes                                                 |
| ---------------------------- | ----------------- | -------- | ------------ | ----------------------------------------------------- |
| thumb-up-2026-06-27_171100   | thumb (DOT)       | 273s     | 1119         | Clean signal throughout                               |
| two-finger-2026-06-27_171620 | two_finger (DASH) | 194s     | 796          | Electrode settling first 90s — use --skip_head_sec 90 |
| fist-2026-06-27_171620       | fist (SPACE)      | 206s     | 872          | Clean signal throughout                               |
| rest                         | rest              | —        | —            | Not yet recorded                                      |
>>>>>>> Stashed changes

## Hardware Notes

- Electrode settling takes ~90s on first wear — sit still before starting recording
- Keep sessions under 3 minutes to avoid fatigue affecting signal amplitude
- Two-finger gesture produces weaker signal (~25–40µV) than thumb/fist (~60–110µV)
  due to shared extensor digitorum muscle
- Sampling rate: 992Hz (not 1000Hz — use this exact value in all calculations)
