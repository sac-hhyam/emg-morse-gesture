# -*- coding: utf-8 -*-
"""
Convert one EPStudio-exported EDF/EDF+ recording (from the EP/ or EPFilter/ folder
of a records/<session>/ directory) into one trial_*.npz file compatible with
build_windows_from_trials.py.

Each EDF file is treated as ONE continuous recording = ONE label (the same
"one gesture per trial" convention realtime_record_trials.py uses). If your
associate records one short clip per gesture (one EDF = one thumb-tap, one
EDF = one fist-clutch, etc.), run this once per clip. If a single EDF instead
contains multiple gestures back-to-back, this script is NOT enough on its own
-- you'd need label-studio-exported region boundaries and a different slicing
step, not a single whole-file label.

LABELS below must stay in sync with the LABELS dict in build_windows_from_trials.py
(and eventually CLASS_NAMES in train_cnn_4actions_simple.py) -- this is a known
duplication in this codebase, not an oversight. If you add/rename a gesture here,
update those files too.

Usage:
    python -m epstudiosdk.edf_to_trial_npz \
        --edf epstudiosdk/records/2026-06-27_120511/EPFilter/MH3130C.01.115_default_EPFilter.edf \
        --label thumb \
        --out_dir epstudiosdk/records/session_gestures

Run it once per EDF clip, pointing --out_dir at the same session folder each
time -- trial_idx auto-increments by counting existing trial_*.npz files there,
so the files accumulate into one session just like the live recorder does.
"""

import argparse
from pathlib import Path

import numpy as np

# Keep this in sync with build_windows_from_trials.py's LABELS dict.
LABELS = {
    0: "rest",
    1: "thumb",       # dot
    2: "two_finger",  # dash
    3: "fist",        # space
}
NAME_TO_ID = {v: k for k, v in LABELS.items()}
NAME_TO_ID["tapping"] = 2   # alias: tapping == two_finger (label_id 2)


def _read_edf_header(f):
    raw = f.read(256)
    n_header_bytes = int(raw[184:192].decode().strip())
    n_records = int(raw[236:244].decode().strip())
    record_dur = float(raw[244:252].decode().strip())
    ns = int(raw[252:256].decode().strip())
    sig_block = f.read(256 * ns)
    spec = [("label", 16), ("transducer", 80), ("phys_dim", 8), ("phys_min", 8),
            ("phys_max", 8), ("dig_min", 8), ("dig_max", 8), ("prefilter", 80),
            ("samples_per_record", 8), ("reserved2", 32)]
    out = {}
    offset = 0
    for name, width in spec:
        vals = [sig_block[offset + i * width: offset + i * width + width].decode(errors="replace").strip()
                for i in range(ns)]
        out[name] = vals
        offset += width * ns
    return dict(n_header_bytes=n_header_bytes, n_records=n_records,
                record_dur=record_dur, ns=ns, **out)


def read_edf_emg(edf_path, n_channels=5):
    """Read one EPStudio EP/EPFilter .edf file -> (emg [T,C] float32 in physical units, sfreq Hz).

    sfreq is read from the file's own header (samples_per_record / record_duration),
    not asserted via a CLI flag -- this is more trustworthy than the .npz path's
    --sfreq argument.
    """
    edf_path = Path(edf_path)
    with open(edf_path, "rb") as f:
        h = _read_edf_header(f)
        spr = [int(x) for x in h["samples_per_record"]]
        phys_min = [float(x) for x in h["phys_min"][:n_channels]]
        phys_max = [float(x) for x in h["phys_max"][:n_channels]]
        dig_min = [int(x) for x in h["dig_min"][:n_channels]]
        dig_max = [int(x) for x in h["dig_max"][:n_channels]]
        f.seek(h["n_header_bytes"])
        data = f.read()

    record_size = sum(spr) * 2
    chunks = [[] for _ in range(n_channels)]
    for r in range(h["n_records"]):
        rec = data[r * record_size:(r + 1) * record_size]
        off = 0
        for i in range(n_channels):
            n = spr[i]
            arr = np.frombuffer(rec[off:off + n * 2], dtype="<i2")
            chunks[i].append(arr)
            off += n * 2

    scales = [(phys_max[i] - phys_min[i]) / (dig_max[i] - dig_min[i]) for i in range(n_channels)]
    emg = np.stack(
        [np.concatenate(chunks[i]).astype(np.float32) * scales[i] for i in range(n_channels)],
        axis=1,
    )  # [T, C]
    sfreq = spr[0] / h["record_dur"]
    return emg, float(sfreq)


def device_token_from_filename(edf_path):
    """EPStudio names files <device_name>_default_<EP|EPFilter>.edf. The MAC isn't
    in the filename, so this returns the device-name token (e.g. 'MH3130C.01.115')
    for traceability; pass --device_mac explicitly if you need the real MAC stored."""
    return Path(edf_path).stem.split("_default_")[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--edf", required=True, help="path to one EP or EPFilter .edf file")
    ap.add_argument("--label", required=True, choices=sorted(NAME_TO_ID.keys()),
                    help="gesture label for this whole recording")
    ap.add_argument("--out_dir", required=True, help="session folder to write trial_*.npz into")
    ap.add_argument("--trial_idx", type=int, default=None,
                    help="trial number; default = next available index in out_dir")
    ap.add_argument("--device_mac", type=str, default=None,
                    help="override device MAC stored in the npz (else uses the filename's device token)")
    ap.add_argument("--n_channels", type=int, default=5)
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    emg, sfreq = read_edf_emg(args.edf, n_channels=args.n_channels)
    lab_id = NAME_TO_ID[args.label]
    device_mac = args.device_mac or device_token_from_filename(args.edf)

    if args.trial_idx is None:
        trial_idx = len(list(out_dir.glob("trial_*.npz"))) + 1
    else:
        trial_idx = args.trial_idx

    fname = f"trial_{trial_idx:04d}_label{lab_id}_{args.label}.npz"
    np.savez_compressed(
        out_dir / fname,
        emg=emg.astype(np.float32),
        sfreq=float(sfreq),
        channels=np.arange(1, args.n_channels + 1, dtype=np.int32),
        device_mac=str(device_mac),
        label_id=int(lab_id),
        label_name=str(args.label),
        source_edf=str(Path(args.edf).resolve()),
    )
    print(f"[OK] wrote {out_dir / fname}  emg.shape={emg.shape}  sfreq={sfreq:.1f}Hz  "
          f"label={args.label}({lab_id})  device={device_mac}")


if __name__ == "__main__":
    main()