# EPStudio SDK Student Development Package

This package contains a cleaned development copy of the EPStudio Python SDK, example scripts, realtime EMG scripts, and small pretrained CNN checkpoints used by the summer school demos.

## Package Layout

- `epstudiosdk/`: SDK source code and realtime EMG utilities.
- `demo/`: basic examples for login, collection, stimulation, events, and websocket data.
- `docs/`: original project documentation and usage notes.
- `wheels/`: original wheel package for reference or direct installation.
- `config.template.ini`: copy this to `config.ini` and edit it for the lab network and device.
- `requirements.txt`: Python dependencies for SDK use and realtime ML demos.

The package intentionally excludes generated `records/` data and `__pycache__/` files.

## Quick Start

1. Create and activate a Python environment.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

2. Copy the config template.

```powershell
Copy-Item config.template.ini config.ini
```

3. Edit `config.ini`.

Set these values to match the classroom EPStudio machine and your assigned device:

- `host`
- `websocket_host`
- `device_mac`
- `channel` or `channels`
- `login_id`
- `password`
- `guinea_pig_id`

4. Make the source importable when running examples from this folder.

```powershell
$env:PYTHONPATH = "."
```

5. Run a basic API smoke test.

```powershell
python demo\test_EpClient.py
```

6. Follow the end-to-end EMG workflow when you are ready to collect, train, and run the game-control demo.

See `STUDENT_USAGE_EN.md`.

## Common Scripts

- `demo/test_EpClient.py`: login and basic API calls.
- `demo/test_CollectionStart.py`: receive collection data over websocket.
- `epstudiosdk/realtime_waveform.py`: live waveform display.
- `epstudiosdk/realtime_record_trials.py`: record labeled EMG trials.
- `epstudiosdk/realtime_decode_udp.py`: realtime EMG classification and UDP output.
- `epstudiosdk/emg_udp_to_arrows.py`: receive UDP classifications and trigger arrow-key events.

Example realtime decode command:

```powershell
python epstudiosdk\realtime_decode_udp.py --ckpt epstudiosdk\cnn_4actions_onset_grouped.pth --sfreq 1000 --ip 127.0.0.1 --port_udp 5005
```

If `--device_mac` or `--channels` are omitted, the scripts read them from `config.ini`.

## Configuration Priority

For SDK connection fields:

1. Explicit script arguments where supported.
2. `config.ini` next to the script or in the current working directory.
3. `epstudiosdk/data/config.ini` defaults.

For realtime scripts, command-line `--device_mac` and `--channels` override `config.ini`.

## Development Notes

- Keep generated recordings under a local `records/` folder and do not commit or redistribute them unless the class has permission.
- Avoid hard-coding lab IPs or device MACs in source files. Put them in `config.ini`.
- `demo/high_vol_stimulation.py` is hardware-specific and may require extra local dependencies; treat it as an advanced reference.
- For training or evaluation scripts, install the ML dependencies in `requirements.txt` and confirm the checkpoint file matches the number/order of channels.

## Troubleshooting

- `ModuleNotFoundError: epstudiosdk`: run from the package root and set `PYTHONPATH=.`.
- Connection refused or timeout: verify EPStudio is running, the host IP is reachable, and firewall rules allow ports `8080` and `9000`.
- No websocket data: check `websocket_host`, `websocket_port`, device connection, and `device_mac`.
- Shape mismatch in CNN: check `channel` order and count against the model checkpoint.
