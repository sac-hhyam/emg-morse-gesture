# International Summer School Handoff Checklist

Use this checklist before sharing the SDK with students.

## Give Students

- Clean source package zip: `SDK-0.2.12-student-dev.zip`.
- Python setup instructions: `README_STUDENT.md`.
- Dependency list: `requirements.txt`.
- Configuration template: `config.template.ini`.
- Original SDK/user docs: files under `docs/`.
- Device assignment sheet: each student/team needs a `device_mac`, channel list, and EPStudio host IP.
- Lab network notes: Wi-Fi/LAN name, IP range, firewall constraints, and whether students run code on their own laptops or lab PCs.

## Do Not Share by Default

- Raw `records/` data unless you have consent and a clear data policy.
- Personal/local `config.ini` with private IPs, device MAC assignments, or account details.
- Python caches: `__pycache__/`, `.pyc`.
- Temporary logs, large experimental outputs, or local virtual environments.

## Pre-Class Setup

- Confirm EPStudio is reachable on HTTP port `8080`.
- Confirm websocket service is reachable on port `9000`.
- Prepare one known-good `config.ini` for the instructor machine.
- Test `demo/test_EpClient.py`.
- Test `epstudiosdk/realtime_waveform.py` with one known device.
- If using ML demos, test `epstudiosdk/realtime_decode_udp.py` with the selected checkpoint.
- Decide whether students should install from source (`PYTHONPATH=.`) or from the wheel in `wheels/`.

## Suggested Student Tasks

- Read live EMG data and print packet summaries.
- Build a small visualizer using `EpWebSocketClient`.
- Record labeled trials with `realtime_record_trials.py`.
- Train or fine-tune a classifier from recorded trials.
- Send realtime decoded actions to a game or UI via UDP.
- Improve configuration handling, logging, and error messages.

## Submission Expectations

- Code changes in a small branch or folder.
- A short README explaining how to run the work.
- A clean `config.template.ini`; no personal or lab-specific secrets in committed code.
- A demo video or screenshot if hardware access is limited.
- Any generated data kept separate from source unless explicitly requested.
