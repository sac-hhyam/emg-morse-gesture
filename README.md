# EMG Morse Gesture Classification

A wearable sEMG pipeline that decodes hand gestures as Morse code symbols for silent, hands-free communication.

## Concept

Forearm muscle signals → gesture classifier → Morse decoder → text output

| Gesture | Morse | Muscle |
|---|---|---|
| Thumb | DOT (·) | Extensor pollicis |
| Two-finger | DASH (−) | Extensor digitorum |
| Fist | SPACE ( ) | Flexor digitorum |
| Rest | silence | — |

## Hardware

- 5-channel dry electrode forearm band
- Wireless acquisition node
- Sampling rate: 992 Hz
- Filtering: 20–250 Hz Butterworth + 48–52 Hz notch

## Pipeline

```
raw sEMG (NPZ) → windowing → activity filter → X_windows.npy → CNN classifier → gesture label → Morse decoder
```

## Quickstart

```bash
pip install -r requirements.txt

# 1. Run windowing + training + held-out accuracy
python -m epstudiosdk.run_morse_pipeline \
  --session_dirs \
    ./epstudiosdk/records/npz-output/thumb-up-SESSION/ \
    ./epstudiosdk/records/npz-output/two-finger-SESSION/ \
    ./epstudiosdk/records/npz-output/fist-SESSION/ \
    ./epstudiosdk/records/npz-output/rest-SESSION/ \
  --ckpt ./epstudiosdk/cnn_morse.pth

# 2. Verify windows visually
python epstudiosdk/inspect_trial_windows_v3.py \
  --session_dir ./epstudiosdk/records/npz-output/thumb-up-SESSION/

# 3. Optional trial-level evaluation on a held-out session
python -m epstudiosdk.offline_eval_trials \
  --session_dir ./epstudiosdk/records/npz-output/thumb-up-HELDOUT/ \
  --ckpt ./epstudiosdk/cnn_morse.pth \
  --win_sec 0.50 --step_sec 0.10
```

The pipeline writes `cnn_morse.metrics.json` with validation/test accuracy,
confusion matrix, and per-class precision/recall/F1.

## Windowing Parameters

| Parameter | Value | Reason |
|---|---|---|
| win_sec | 0.50s | Gestures are 2–3s sustained contractions |
| step_sec | 0.10s | 80% overlap, 100ms real-time latency |
| thr_q | 0.60 | Threshold at 60th RMS percentile |
| active_ratio | 0.45 | 45% of window must be active muscle |
| sfreq | 992 Hz | Hardware sampling rate |

## Project Structure

```
epstudiosdk/
├── build_windows_morse.py        # windowing + activity filter
├── run_morse_pipeline.py         # windowing + training + metrics
├── search_windowing_params.py    # hyperparameter search for windowing
├── inspect_trial_windows_v3.py   # QA visualisation (reads windows_index.csv)
├── train_cnn_4actions_simple.py  # classifier training
├── realtime_record_trials.py     # data collection
└── realtime_decode_udp.py        # real-time inference
```

## Data

See [DATA.md](DATA.md) for download instructions and folder structure.

## Applications

- Assistive communication for ALS / spinal cord injury patients
- Silent input in noise-sensitive environments
- Hands-free AR/VR control
