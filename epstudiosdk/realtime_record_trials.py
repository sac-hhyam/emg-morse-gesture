# -*- coding: utf-8 -*-
"""
Realtime EMG recorder (EPStudio WebSocket) -> per-trial NPZ files
with optional real-time waveform display.

New features:
- Real-time rolling waveform display while collecting.
- Still supports keyboard-labeled recording and saving per-trial NPZ files.

Keys:
- 1: UP    (label_id=0)
- 2: DOWN  (label_id=1)
- 3: LEFT  (label_id=2)
- 4: RIGHT (label_id=3)
- SPACE: start/stop recording one trial with current label
- ESC: stop program
"""

import os
import time
import json
import argparse
import configparser
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Union, List, Optional

import numpy as np

from pynput.keyboard import Listener, Key

from epstudiosdk.bean.collection.CollectionDeviceBean import CollectionDeviceBean
from epstudiosdk.client import EpClient
from epstudiosdk.collection.Collection import Collection
from epstudiosdk.websocket import DataReceive, DataType, EventMessage
from epstudiosdk.websocketclient import EpWebSocketClient

from epstudiosdk.request.user.UserLoginRequest import UserLoginRequest
from epstudiosdk.request.guineapig.GuineaPigSetCurrentRequest import GuineaPigSetCurrentRequest
from epstudiosdk.utils import ConfigUtil

try:
    import matplotlib.pyplot as plt
except Exception:
    plt = None


LABELS = {
    0: "up",
    1: "down",
    2: "left",
    3: "right",
}

KEY_TO_LABEL = {
    '1': 0,
    '2': 1,
    '3': 2,
    '4': 3,
}


def _unix_ms_to_local_iso(ms: int) -> str:
    """Local wall-clock time from Unix ms, ISO-8601 with milliseconds."""
    return datetime.fromtimestamp(ms / 1000.0).isoformat(timespec="milliseconds")


@dataclass
class Trial:
    label_id: int
    label_name: str
    blocks: List[np.ndarray]  # list of [L,C] float32
    start_unix_ms: int  # 13-digit ms since epoch (SPACE pressed to start this trial)


class RecorderState:
    def __init__(self):
        self.cur_label_id: int = 0
        self.recording: bool = False
        self.trial: Optional[Trial] = None
        self.trial_idx: int = 0
        self.stop: bool = False

    def start_trial(self):
        if self.recording:
            return
        self.recording = True
        self.trial_idx += 1
        lab = self.cur_label_id
        start_unix_ms = int(time.time() * 1000)
        self.trial = Trial(label_id=lab, label_name=LABELS[lab], blocks=[], start_unix_ms=start_unix_ms)
        print(
            f"[REC] START trial#{self.trial_idx:04d} label={lab}({LABELS[lab]}) "
            f"start_unix_ms={start_unix_ms} ({_unix_ms_to_local_iso(start_unix_ms)})"
        )

    def stop_trial_and_save(self, out_dir: str, sfreq: float, channels: List[int], device_mac: str):
        if (not self.recording) or (self.trial is None):
            return
        self.recording = False
        trial = self.trial
        self.trial = None

        if len(trial.blocks) == 0:
            print("[REC] STOP (empty) -> skipped")
            return

        emg = np.concatenate(trial.blocks, axis=0)  # [T,C]
        fname = f"trial_{self.trial_idx:04d}_label{trial.label_id}_{trial.label_name}.npz"
        fpath = os.path.join(out_dir, fname)
        start_iso = _unix_ms_to_local_iso(trial.start_unix_ms)

        np.savez_compressed(
            fpath,
            emg=emg.astype(np.float32),
            sfreq=float(sfreq),
            channels=np.array(channels, dtype=np.int32),
            device_mac=str(device_mac),
            label_id=int(trial.label_id),
            label_name=str(trial.label_name),
            trial_start_unix_ms=np.int64(trial.start_unix_ms),
            trial_start_datetime=np.array(start_iso),
            saved_at=str(datetime.now().isoformat(timespec="seconds")),
        )
        dur = emg.shape[0] / float(sfreq)
        print(
            f"[REC] STOP -> saved {fpath}  shape={emg.shape}  dur={dur:.2f}s "
            f"start={start_iso}"
        )


class RollingBuffer:
    def __init__(self, max_samples: int, n_channels: int):
        self.max_samples = int(max_samples)
        self.n_channels = int(n_channels)
        self.buf = np.zeros((self.max_samples, self.n_channels), dtype=np.float32)
        self.write_idx = 0
        self.filled = 0
        self.lock = threading.Lock()

    def append(self, block: np.ndarray):
        if block is None or block.size == 0:
            return
        block = np.asarray(block, dtype=np.float32)
        if block.ndim != 2 or block.shape[1] != self.n_channels:
            return

        n = block.shape[0]
        if n >= self.max_samples:
            block = block[-self.max_samples:]
            n = block.shape[0]

        with self.lock:
            end = self.write_idx + n
            if end <= self.max_samples:
                self.buf[self.write_idx:end] = block
            else:
                first = self.max_samples - self.write_idx
                self.buf[self.write_idx:] = block[:first]
                self.buf[:n - first] = block[first:]
            self.write_idx = (self.write_idx + n) % self.max_samples
            self.filled = min(self.max_samples, self.filled + n)

    def get_latest(self) -> np.ndarray:
        with self.lock:
            if self.filled == 0:
                return np.zeros((0, self.n_channels), dtype=np.float32)
            if self.filled < self.max_samples:
                return self.buf[:self.filled].copy()
            return np.vstack((self.buf[self.write_idx:], self.buf[:self.write_idx])).copy()


class RealtimeWaveformPlot:
    def __init__(self, sfreq: float, channels: List[int], display_seconds: float = 5.0,
                 refresh_hz: float = 20.0, gain: float = 1e6):
        if plt is None:
            raise RuntimeError("matplotlib import failed")

        self.sfreq = float(sfreq)
        self.channels = list(channels)
        self.n_channels = len(self.channels)
        self.display_seconds = float(display_seconds)
        self.refresh_hz = float(refresh_hz)
        self.gain = float(gain)
        self.max_samples = max(1, int(round(self.sfreq * self.display_seconds)))

        self.buffer = RollingBuffer(max_samples=self.max_samples, n_channels=self.n_channels)
        self.closed = False
        self.last_draw_t = 0.0

        plt.ion()
        self.fig, self.ax = plt.subplots(figsize=(12, 6))
        self.fig.canvas.manager.set_window_title("Realtime EMG Waveform")
        self.fig.canvas.mpl_connect("close_event", self._on_close)

        self.lines = [self.ax.plot([], [], lw=1.0)[0] for _ in range(self.n_channels)]
        self.status_text = self.ax.text(0.01, 1.02, "", transform=self.ax.transAxes, fontsize=10)

        self.ax.set_title("Realtime EMG Waveform")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Channels (stacked)")
        self.ax.grid(True, alpha=0.3)
        self.ax.set_xlim(-self.display_seconds, 0.0)

    def _on_close(self, _evt):
        self.closed = True

    def append(self, block: np.ndarray):
        self.buffer.append(block)

    def update(self, recording: bool = False, current_label: str = "up"):
        if self.closed:
            return
        now = time.time()
        if (now - self.last_draw_t) < (1.0 / max(self.refresh_hz, 1.0)):
            return
        self.last_draw_t = now

        data = self.buffer.get_latest()
        if data.shape[0] == 0:
            try:
                self.fig.canvas.draw_idle()
                self.fig.canvas.flush_events()
            except Exception:
                self.closed = True
            return

        data = data * self.gain
        n = data.shape[0]
        x = np.linspace(-n / self.sfreq, 0.0, n, endpoint=False)

        # Robust dynamic spacing for stacked display
        ch_std = np.std(data, axis=0)
        base = float(np.median(ch_std[ch_std > 0])) if np.any(ch_std > 0) else 1.0
        spacing = max(base * 8.0, 1.0)
        offsets = np.arange(self.n_channels, dtype=np.float32) * spacing

        for i, line in enumerate(self.lines):
            y = data[:, i] + offsets[i]
            line.set_data(x, y)

        self.ax.set_xlim(-self.display_seconds, 0.0)
        self.ax.set_ylim(-spacing, offsets[-1] + spacing * 2.0 if self.n_channels > 0 else spacing)
        self.ax.set_yticks(offsets)
        self.ax.set_yticklabels([f"ch{ch}" for ch in self.channels])
        status = f"label={current_label} | recording={'ON' if recording else 'OFF'} | gain={self.gain:g}"
        self.status_text.set_text(status)

        try:
            self.fig.canvas.draw_idle()
            self.fig.canvas.flush_events()
            plt.pause(0.001)
        except Exception:
            self.closed = True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=str, default=None,
                    help="config.ini path; if omitted, use ./data/config.ini next to this script")
    ap.add_argument("--sfreq", type=float, default=1000.0,
                    help="sampling rate (Hz) used for saving meta and plotting")
    ap.add_argument("--out_dir", type=str, default=None,
                    help="output folder; default creates session_YYYYmmdd_HHMMSS under ./records")
    ap.add_argument("--max_list_len", type=int, default=10000,
                    help="safety: drop a websocket chunk if any channel list is longer than this")

    # realtime plot args
    ap.add_argument("--show_plot", dest="show_plot", action="store_true", default=True,
                    help="show real-time waveform plot (default: on)")
    ap.add_argument("--display_seconds", type=float, default=5.0,
                    help="seconds to show in the rolling waveform window")
    ap.add_argument("--refresh_hz", type=float, default=20.0,
                    help="plot refresh rate")
    ap.add_argument("--plot_gain", type=float, default=1e6,
                    help="multiply waveform by this factor before display")
    args = ap.parse_args()

    # --- config load (same style as ConfigUtil) ---
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_config_path = os.path.abspath(os.path.join(script_dir, "data", "config.ini"))
    if args.config is None:
        candidates = [
            os.path.abspath(os.path.join(os.getcwd(), "config.ini")),
            os.path.abspath(os.path.join(script_dir, "config.ini")),
            default_config_path,
        ]
        config_path = next((path for path in candidates if os.path.exists(path)), default_config_path)
    else:
        config_path = os.path.abspath(args.config)

    cfg = configparser.ConfigParser()
    read_paths = [default_config_path]
    if config_path != default_config_path:
        read_paths.append(config_path)
    cfg.read(read_paths, encoding="utf-8")

    host = cfg.get("config-data", "host", fallback="http://localhost").split(";")[0]
    port = cfg.get("config-data", "port", fallback="8080")
    websocket_host = cfg.get("config-data", "websocket_host", fallback="ws://localhost").split(";")[0]
    websocket_port = cfg.get("config-data", "websocket_port", fallback="9000")
    login_id = cfg.get("config-data", "login_id", fallback="admin")
    password = cfg.get("config-data", "password", fallback="admin")
    guinea_pig_id = cfg.get("config-data", "guinea_pig_id", fallback="20220527")

    device_mac = cfg.get("app", "device_mac", fallback="E9:69:BF:4B:7B:82").split(";")[0].strip()
    channels_str = cfg.get("app", "channels", fallback=cfg.get("app", "channel", fallback="1,2,3,4,5"))
    channels = [int(x.strip()) for x in channels_str.split(",") if x.strip()]
    ConfigUtil().update_data({
        "host": host,
        "port": port,
        "websocket_host": websocket_host,
        "websocket_port": websocket_port,
        "login_id": login_id,
        "password": password,
        "guinea_pig_id": guinea_pig_id,
        "device_mac": device_mac,
        "channels": channels_str,
        "channel": channels_str,
    })

    # --- output session dir ---
    if args.out_dir is None:
        out_root = os.path.join(script_dir, "records")
        os.makedirs(out_root, exist_ok=True)
        session_name = "session_" + datetime.now().strftime("%Y%m%d_%H%M%S")
        out_dir = os.path.join(out_root, session_name)
    else:
        out_dir = os.path.abspath(args.out_dir)
    os.makedirs(out_dir, exist_ok=True)

    meta = {
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        "config_path": config_path,
        "host": host,
        "port": port,
        "websocket_host": websocket_host,
        "websocket_port": websocket_port,
        "device_mac": device_mac,
        "channels": channels,
        "sfreq": float(args.sfreq),
        "label_order": LABELS,
        "keymap": {k: int(v) for k, v in KEY_TO_LABEL.items()},
        "show_plot": bool(args.show_plot),
        "display_seconds": float(args.display_seconds),
        "refresh_hz": float(args.refresh_hz),
        "plot_gain": float(args.plot_gain),
    }
    with open(os.path.join(out_dir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print("[OK] config:", config_path)
    print("[OK] device_mac:", device_mac)
    print("[OK] channels:", channels)
    print("[OK] out_dir:", out_dir)
    print("\n[Keys] 1=UP 2=DOWN 3=LEFT 4=RIGHT | SPACE=start/stop trial | ESC=quit\n")

    state = RecorderState()
    plotter = None
    if args.show_plot:
        if plt is None:
            print("[WARN] matplotlib not available, waveform plot disabled.")
        else:
            try:
                plotter = RealtimeWaveformPlot(
                    sfreq=args.sfreq,
                    channels=channels,
                    display_seconds=args.display_seconds,
                    refresh_hz=args.refresh_hz,
                    gain=args.plot_gain,
                )
                print("[OK] realtime plot enabled")
            except Exception as e:
                print(f"[WARN] failed to create realtime plot: {e}")
                plotter = None

    # --- keyboard listener thread ---
    def on_press(key):
        try:
            ch = key.char
            if ch in KEY_TO_LABEL:
                state.cur_label_id = KEY_TO_LABEL[ch]
                print(f"[UI] current label -> {state.cur_label_id}({LABELS[state.cur_label_id]})")
                return
        except Exception:
            pass

        if key == Key.space:
            if not state.recording:
                state.start_trial()
            else:
                state.stop_trial_and_save(out_dir=out_dir, sfreq=args.sfreq,
                                          channels=channels, device_mac=device_mac)
            return

        if key == Key.esc:
            state.stop = True
            print("[UI] ESC pressed -> stopping...")
            return False

    listener = Listener(on_press=on_press)
    listener.start()

    # --- websocket event handler ---
    class MyEvent(EventMessage):
        def on_data(self, data: Union[str, dict, DataReceive]):
            if not (isinstance(data, DataReceive) and data.dataType == DataType.EP):
                return
            for device_data in data.data:
                if device_data.deviceId != device_mac:
                    continue

                vals = []
                L = None
                for ch in channels:
                    arr = device_data.data.get(str(ch), None)
                    if arr is None or (not isinstance(arr, list)):
                        return
                    if len(arr) > args.max_list_len:
                        return
                    if L is None:
                        L = len(arr)
                    else:
                        if len(arr) != L:
                            L = min(L, len(arr))
                    vals.append(arr)

                if L is None or L <= 0:
                    return

                block = np.stack([np.asarray(v[:L], dtype=np.float32) for v in vals], axis=1)  # [L,C]

                if plotter is not None:
                    plotter.append(block)

                if state.recording and state.trial is not None:
                    state.trial.blocks.append(block)

    client = EpClient(init_user_status=True)
    login_res = client.do_action_json(UserLoginRequest(login_id, password))
    print("Login result:", login_res)
    set_patient_res = client.do_action_json(GuineaPigSetCurrentRequest(guinea_pig_id))
    print("Set patient result:", set_patient_res)

    event_handler = MyEvent()
    websocket_client = EpWebSocketClient(event_msg=event_handler, enable_trace=False)
    websocket_client.start()

    device = CollectionDeviceBean(device_mac, channelStatus=channels)
    collection = Collection(client=client, device_list=[device], record_status=False)

    print("Starting collection...")
    result = collection.start_collection()
    print("Collection start result:", result)

    try:
        while not state.stop:
            if plotter is not None:
                plotter.update(recording=state.recording, current_label=LABELS[state.cur_label_id])
                if plotter.closed:
                    print("[UI] plot window closed -> stopping...")
                    state.stop = True
                    break
            time.sleep(0.01)
    finally:
        if state.recording:
            state.stop_trial_and_save(out_dir=out_dir, sfreq=args.sfreq,
                                      channels=channels, device_mac=device_mac)

        try:
            collection.stop_collection()
        except Exception:
            pass
        try:
            websocket_client.stop()
        except Exception:
            pass
        try:
            listener.stop()
        except Exception:
            pass
        if plotter is not None and plt is not None:
            try:
                plt.close(plotter.fig)
            except Exception:
                pass

        print("[Done] stopped. Session saved in:", out_dir)


if __name__ == "__main__":
    main()
