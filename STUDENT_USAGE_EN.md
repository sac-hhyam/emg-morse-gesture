# Student Usage Guide: Collect, Train, and Run Realtime EMG Control

This guide describes the full trial-level workflow used in the summer school demo:

1. Collect and save labeled EMG trials.
2. Convert trials into training windows.
3. Train a 4-class CNN.
4. Run realtime inference, send UDP events, and control a browser game.

Run commands from the package root folder after setup:

```powershell
$env:PYTHONPATH = "."
Copy-Item config.template.ini config.ini
```

Edit `config.ini` before collecting data. At minimum, set:

- `host`
- `websocket_host`
- `device_mac`
- `channel` or `channels`
- `login_id`
- `password`
- `guinea_pig_id`

## 1. Collect and Save Trial-Level Data

```powershell
python -m epstudiosdk.realtime_record_trials --config .\config.ini --sfreq 992
```

Key controls:

- `1`: select label `up`, internal `label_id=0`
- `2`: select label `down`, internal `label_id=1`
- `3`: select label `left`, internal `label_id=2`
- `4`: select label `right`, internal `label_id=3`
- `Space`: start or stop one trial
- `Esc`: exit, stop collection, and finish cleanup

Each completed trial is saved as a file like:

```text
trial_XXXX_labelY_<label_name>.npz
```

Recommended collection rhythm:

- At least 20 to 30 trials per action.
- Each trial should last 1 to 2 seconds.
- Relax for 1 to 2 seconds between trials.
- The model becomes more stable as the dataset grows.

By default, the recorder creates a session folder under:

```text
epstudiosdk\records\session_YYYYMMDD_HHMMSS
```

The program prints the actual output folder. Use that folder in the next step.

## 2. Convert Trials Into Training Windows

Use the session folder from step 1.

```powershell
python -m epstudiosdk.build_windows_from_trials --in_dir .\epstudiosdk\records\session_YYYYMMDD_HHMMSS --win_sec 0.20 --step_sec 0.0
```

Optional visual inspection:

```powershell
python -m epstudiosdk.inspect_trial_windows --session_dir .\epstudiosdk\records\session_YYYYMMDD_HHMMSS
```

The generated training files are written to the same session folder:

```text
X_single_windows.npy    shape [N, T, C]
y_single_labels.npy     shape [N], values 0..3 for up/down/left/right
```

## 3. Train a 4-Class CNN

```powershell
python -m epstudiosdk.train_cnn_4actions_simple --data_dir .\epstudiosdk\records\session_YYYYMMDD_HHMMSS --ckpt .\epstudiosdk\cnn_student.pth
```

The checkpoint path passed to `--ckpt` is the model file you will use online.

## 4. Realtime Inference, UDP, and Game Control

Start the keyboard-mapping receiver first.

```powershell
python -m epstudiosdk.emg_udp_to_arrows --port 5005 --mode tap --cooldown_ms 120 --debug
```

Default mapping:

- label `1`: Up arrow
- label `2`: Down arrow
- label `3`: Left arrow
- label `4`: Right arrow

If a game needs `W/S/A/D`, edit `DEFAULT_MAP` in `epstudiosdk/emg_udp_to_arrows.py`.

Then start realtime decoding in another terminal:

```powershell
python -m epstudiosdk.realtime_decode_udp --config .\config.ini --ckpt .\epstudiosdk\cnn_student.pth --sfreq 992 --ip 127.0.0.1 --port_udp 5005
```

Open the browser game and click inside the game window so it has keyboard focus. When the decoder sends a UDP `event` with `state="start"`, the keyboard-mapping receiver will trigger one key press.

## Tuned Realtime Decode Example

PowerShell multiline command:

```powershell
python -m epstudiosdk.realtime_decode_udp `
  --config .\config.ini `
  --ckpt .\epstudiosdk\cnn_student.pth `
  --sfreq 992 `
  --ip 127.0.0.1 `
  --port_udp 5005 `
  --decision_min_windows 2 `
  --decision_max_windows 4 `
  --decision_vote_ratio 0.60 `
  --min_rest_sec 0.10 `
  --conf_thresh 0.60 `
  --no_show_plot
```

Windows CMD multiline command:

```bat
python -m epstudiosdk.realtime_decode_udp ^
  --config .\config.ini ^
  --ckpt .\epstudiosdk\cnn_student.pth ^
  --sfreq 992 ^
  --ip 127.0.0.1 ^
  --port_udp 5005 ^
  --decision_min_windows 2 ^
  --decision_max_windows 4 ^
  --decision_vote_ratio 0.60 ^
  --min_rest_sec 0.10 ^
  --conf_thresh 0.60 ^
  --no_show_plot
```

You can also override the device and channels from the command line:

```powershell
python -m epstudiosdk.realtime_decode_udp --config .\config.ini --ckpt .\epstudiosdk\cnn_student.pth --sfreq 992 --device_mac E3:5B:D8:05:34:E9 --channels 1,2,3,4,5 --ip 127.0.0.1 --port_udp 5005 --no_show_plot
```

If `--device_mac` and `--channels` are omitted, they are read from `config.ini`.

## Common Pitfalls

Sampling rate must be consistent:

- The `--sfreq` used during recording.
- The sampling rate assumed when building windows.
- The `--sfreq` used during realtime decoding.

Do not collect at `992` Hz and run online inference at `1000` Hz unless you intentionally trained for that difference. Window sizes and feature scales will no longer match.

Channel order must be consistent:

- The training channel order must equal the realtime stacking order `[L, C]`.
- The realtime scripts iterate through the configured `channels` list in order.
- If you trained with `1,2,3,4,5`, use the same order online.

Game focus matters:

- Click the browser game window before testing.
- If the game does not respond, check whether it expects arrow keys or `W/S/A/D`.

UDP troubleshooting:

- The keyboard receiver and realtime decoder must use the same UDP port.
- If both programs run on the same computer, use `--ip 127.0.0.1`.
- If they run on different computers, send UDP to the receiver computer's IP address and allow the port through the firewall.
