# Data

Raw sEMG recordings are not stored in this repository (binary files, ~300MB total).

## Download

Google Drive: https://drive.google.com/drive/folders/1jnh2WNp0HAln25QXVELGWYRU0DxCpiQL?usp=share_link

Replace `#` with your actual Google Drive link after uploading.

## Folder Structure

After downloading, place sessions under `epstudiosdk/records/npz-output/`:

```
epstudiosdk/records/npz-output/
├── thumb-up-2026-06-27_171100/
│   ├── trial_0001_label1_thumb.npz
│   ├── X_single_windows.npy
│   ├── y_single_labels.npy
│   ├── gesture_to_id_single.csv
│   └── windows_index.csv
├── two-finger-2026-06-27_171620/
│   ├── trial_0001_label2_two_finger.npz
│   └── ...
└── fist-2026-06-27_171620/
    ├── trial_0001_label3_fist.npz
    └── ...
```

## Reproduce Windows from Raw NPZ

```bash
python epstudiosdk/build_windows_morse.py \
  --in_dir ./epstudiosdk/records/npz-output/thumb-up-2026-06-27_171100/ \
  --win_sec 0.50 --step_sec 0.10 \
  --trim_head_sec 0.50 --trim_tail_sec 0.50 \
  --thr_q 0.60 --active_ratio_thresh 0.45 \
  --rms_smooth_sec 0.05 --write_index
```

Run the same command for each gesture session, changing `--in_dir`.

## Session Notes

| Session | Gesture | Duration | Windows kept | Notes |
|---|---|---|---|---|
| thumb-up-2026-06-27_171100 | thumb (DOT) | 273s | 1119 | Clean signal throughout |
| two-finger-2026-06-27_171620 | two_finger (DASH) | 194s | 796 | Electrode settling first 90s — use --skip_head_sec 90 |
| fist-2026-06-27_171620 | fist (SPACE) | 206s | 872 | Clean signal throughout |
| rest | rest | — | — | Not yet recorded |

## Hardware Notes

- Electrode settling takes ~90s on first wear — sit still before starting recording
- Keep sessions under 3 minutes to avoid fatigue affecting signal amplitude
- Two-finger gesture produces weaker signal (~25–40µV) than thumb/fist (~60–110µV) due to shared extensor digitorum muscle
