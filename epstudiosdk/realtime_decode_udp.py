#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""realtime_decode_udp.py

把 realtime_waveform.py 从 EPStudio WebSocket 收到的实时 EMG 数据
接到 emg_replay_udp.py 的 1D-CNN 分类 + UDP 协议上。

输出 UDP JSON 与 emg_replay_udp.py 完全一致：
  - frame: {type:"frame", t, label, name, conf, active_ratio}
  - event: {type:"event", t, label, name, conf, state:"start"|"hold"|"end"}

依赖：epstudiosdk, torch, numpy

运行示例：
  python realtime_decode_udp.py --ckpt cnn_4actions_merged_perwin.pth --sfreq 1000 \
      --device_mac F9:DC:B2:3E:B4:BD --channels 1,2,3,4,5 --ip 127.0.0.1 --port_udp 5005

说明：
- --sfreq 必须填对（用于 win/step/rms 这些“秒 -> 点数”的换算）
- --channels 的顺序必须与你训练时喂给模型的通道顺序一致
"""

import argparse
import configparser
import json
import os
import queue
import socket
import threading
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Deque, List, Optional, Union

import numpy as np
import torch
import torch.nn as nn

try:
    import matplotlib.pyplot as plt
    from matplotlib.colors import BoundaryNorm, ListedColormap
except Exception:
    plt = None
    BoundaryNorm = None
    ListedColormap = None

from epstudiosdk.bean.collection.CollectionDeviceBean import CollectionDeviceBean
from epstudiosdk.client import EpClient
from epstudiosdk.collection.Collection import Collection
from epstudiosdk.websocket import DataReceive, DataType, EventMessage
from epstudiosdk.websocketclient import EpWebSocketClient
from epstudiosdk.request.user.UserLoginRequest import UserLoginRequest
from epstudiosdk.request.guineapig.GuineaPigSetCurrentRequest import GuineaPigSetCurrentRequest
from epstudiosdk.utils import ConfigUtil


# ----------------- 模型（与训练脚本一致） -----------------
class EMGCNN(nn.Module):
    def __init__(self, n_channels: int = 5, n_classes: int = 4):
        super().__init__()
        self.feature_extractor = nn.Sequential(
            nn.Conv1d(n_channels, 32, kernel_size=5, padding=2),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.MaxPool1d(kernel_size=2),

            nn.Conv1d(32, 64, kernel_size=5, padding=2),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.MaxPool1d(kernel_size=2),

            nn.Conv1d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.AdaptiveMaxPool1d(1),
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(64, n_classes),
        )

    def forward(self, x):
        x = self.feature_extractor(x)
        x = self.classifier(x)
        return x


def load_ckpt(ckpt_path: Path, n_channels: int):
    torch_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    ckpt = torch.load(str(ckpt_path), map_location=torch_device, weights_only=False)

    class_names = ckpt.get("class_names", None)
    if class_names is None:
        raise KeyError("ckpt 中找不到 class_names（请确认使用训练脚本保存的 .pth）")
    class_names = list(class_names)
    n_classes = len(class_names)

    model = EMGCNN(n_channels=n_channels, n_classes=n_classes).to(torch_device)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()

    mean = ckpt.get("mean", None)
    std = ckpt.get("std", None)
    per_window_norm = bool(ckpt.get("per_window_norm", False))

    if mean is not None:
        mean = np.asarray(mean, dtype=np.float32)
    if std is not None:
        std = np.asarray(std, dtype=np.float32)

    inferred_offset = 0 if class_names and str(class_names[0]).lower() == "rest" else 1
    label_offset = int(ckpt.get("label_offset", inferred_offset))
    if label_offset == 0:
        gesture_names = class_names
    else:
        gesture_names = ["rest"] + class_names
    return model, torch_device, mean, std, per_window_norm, gesture_names, label_offset

# ----------------- UDP 消息 / 事件平滑 -----------------
@dataclass
class FrameMsg:
    type: str
    t: float
    label: int
    name: str
    conf: float
    active_ratio: float


@dataclass
class EventMsg:
    type: str
    t: float
    label: int
    name: str
    conf: float
    state: str


class EventSmoother:
    """
    把滑窗级预测平滑成 start/hold/end 事件。
    关键改动：
    - 需要 rest 连续出现 min_rest_steps 次后，才允许发 start
    - end 后 refractory_sec 内屏蔽“相反动作”的 start
    - 不允许 action->action 直接切换（必须先回到 rest）
    """

    def __init__(
        self,
        gesture_names: List[str],
        hist_len: int = 5,
        switch_ratio: float = 0.7,
        min_rest_steps: int = 3,       # 例如 step=0.05s 时，3步≈150ms
        refractory_sec: float = 0.25,  # end 后 250ms 内屏蔽 opposite
    ):
        self.gesture_names = gesture_names
        self.hist_len = hist_len
        self.switch_ratio = switch_ratio

        self.min_rest_steps = int(min_rest_steps)
        self.refractory_sec = float(refractory_sec)

        self.hist: List[int] = []
        self.current_label: int = 0

        self.rest_streak: int = 0
        self.last_end_t: float = -1e9
        self.last_end_label: int = 0

        # label: 0=rest, 1=up,2=down,3=left,4=right
        self.opposite = {1: 2, 2: 1, 3: 4, 4: 3}

    def update(self, t: float, label: int, conf: float) -> List[EventMsg]:
        label = int(label)

        # 连续 rest 计数（用“当前预测 label”，更敏感）
        if label == 0:
            self.rest_streak += 1
        else:
            self.rest_streak = 0

        # 维护投票历史（用你原来的 majority 机制）
        self.hist.append(label)
        if len(self.hist) > self.hist_len:
            self.hist = self.hist[-self.hist_len :]

        vals, counts = np.unique(self.hist, return_counts=True)
        best = int(vals[int(np.argmax(counts))])
        ratio = float(np.max(counts) / len(self.hist))

        out: List[EventMsg] = []

        # ---- 当前处于 rest：允许 start，但要满足“稳定 rest + 反向抑制” ----
        if self.current_label == 0:
            if best != 0 and ratio >= self.switch_ratio:
                # 1) 必须先稳定 rest 一段时间
                if self.rest_streak < self.min_rest_steps:
                    return out

                # 2) end 后 refractory_sec 内屏蔽 opposite
                opp = self.opposite.get(self.last_end_label, -1)
                if (t - self.last_end_t) < self.refractory_sec and best == opp:
                    return out

                self.current_label = best
                out.append(EventMsg("event", t, best, self.gesture_names[best], conf, "start"))
            return out

        # ---- 当前处于某个动作：不允许直接切换到别的动作，只允许 hold 或 end ----
        if best == 0 and ratio >= self.switch_ratio:
            # end
            out.append(EventMsg("event", t, self.current_label, self.gesture_names[self.current_label], conf, "end"))
            self.last_end_t = t
            self.last_end_label = self.current_label
            self.current_label = 0
            return out

        # 其它情况都视为 hold（即便 best 变成 opposite，也不切换）
        out.append(EventMsg("event", t, self.current_label, self.gesture_names[self.current_label], conf, "hold"))
        return out

class LockedOnsetSegmentSmoother:
    """
    面向离散手势的一段一标签平滑器：
    - 不允许 action -> action 直接切换
    - 新动作开始时，不用“前两个窗立刻定类”，而是先积累若干个活动窗再锁定标签
    - 一旦锁定标签，本段尾端的其它类别预测全部忽略，直到稳定 rest 才 end

    适合当前场景：
    1) 训练窗来自整个动作段，而不是仅起始两个窗
    2) 希望减少动作尾端被误判成另一个动作
    3) 离散手势更关心“一段动作最终是什么”，而不是段内连续切换
    """
    def __init__(
        self,
        gesture_names: List[str],
        step_sec: float,
        min_rest_sec: float = 0.10,
        refractory_sec: float = 0.20,
        conf_thresh: float = 0.55,
        decision_min_windows: int = 4,
        decision_max_windows: int = 6,
        decision_vote_ratio: float = 0.60,
    ):
        self.gesture_names = gesture_names
        self.step_sec = float(step_sec)
        self.min_rest_steps = max(1, int(round(min_rest_sec / self.step_sec)))
        self.refractory_sec = float(refractory_sec)
        self.conf_thresh = float(conf_thresh)
        self.decision_min_windows = max(1, int(decision_min_windows))
        self.decision_max_windows = max(self.decision_min_windows, int(decision_max_windows))
        self.decision_vote_ratio = float(decision_vote_ratio)

        self.cur_label = 0
        self.rest_streak = self.min_rest_steps

        self.last_end_t = -1e9
        self.last_end_label = 0
        self.opposite = {1: 2, 2: 1, 3: 4, 4: 3}

        self.pending_labels: List[int] = []
        self.pending_confs: List[float] = []

    def _effective_label(self, label: int, conf: float) -> int:
        label = int(label)
        conf = float(conf)
        if label == 0:
            return 0
        return label if conf >= self.conf_thresh else 0

    def _clear_pending(self):
        self.pending_labels.clear()
        self.pending_confs.clear()

    def _make_event(self, t: float, label: int, conf: float, state: str) -> EventMsg:
        return EventMsg("event", float(t), int(label), self.gesture_names[int(label)], float(conf), state)

    def _pending_vote(self):
        n_classes = len(self.gesture_names)
        scores = np.zeros(n_classes, dtype=np.float32)
        for lab, cf in zip(self.pending_labels, self.pending_confs):
            if int(lab) > 0:
                scores[int(lab)] += float(cf)
        denom = float(scores[1:].sum())
        if denom <= 1e-8:
            return None, 0.0
        best = int(np.argmax(scores[1:]) + 1)
        ratio = float(scores[best] / denom)
        return best, ratio

    def update(self, t: float, label: int, conf: float) -> List[EventMsg]:
        eff = self._effective_label(label, conf)

        if eff == 0:
            self.rest_streak += 1
        else:
            self.rest_streak = 0

        out: List[EventMsg] = []

        # ---------- 当前处于 rest：先积累若干个活动窗，再锁定本段标签 ----------
        if self.cur_label == 0:
            if eff == 0:
                self._clear_pending()
                return out

            # 刚结束后短时间内，仍抑制“相反方向”的立即回弹
            if (t - self.last_end_t) < self.refractory_sec and eff == self.opposite.get(self.last_end_label, -1):
                self._clear_pending()
                return out

            self.pending_labels.append(int(eff))
            self.pending_confs.append(float(conf))

            if len(self.pending_labels) < self.decision_min_windows:
                return out

            voted, ratio = self._pending_vote()
            if voted is None:
                return out

            if (ratio >= self.decision_vote_ratio) or (len(self.pending_labels) >= self.decision_max_windows):
                self.cur_label = int(voted)
                self.rest_streak = 0
                self._clear_pending()
                out.append(self._make_event(t, self.cur_label, ratio, "start"))
            return out

        # ---------- 当前处于动作中：不允许切换，只允许直到稳定 rest 才 end ----------
        self._clear_pending()

        if eff == 0 and self.rest_streak >= self.min_rest_steps:
            old = self.cur_label
            self.cur_label = 0
            self.last_end_t = float(t)
            self.last_end_label = int(old)
            out.append(self._make_event(t, old, conf, "end"))
            return out

        # 段内无论出现什么其它类别，都不切换；保持当前动作锁定。
        return out

# ----------------- 高效 ring buffer -----------------
class RingBuffer:
    def __init__(self, capacity: int, n_channels: int, dtype=np.float32):
        self.capacity = int(capacity)
        self.n_channels = int(n_channels)
        self.buf = np.zeros((self.capacity, self.n_channels), dtype=dtype)
        self.size = 0
        self.w = 0

    def append_block(self, block_tc: np.ndarray) -> None:
        """block_tc: [L,C]"""
        block_tc = np.asarray(block_tc)
        if block_tc.ndim != 2 or block_tc.shape[1] != self.n_channels:
            raise ValueError(f"block shape must be [L,{self.n_channels}] but got {block_tc.shape}")

        L = int(block_tc.shape[0])
        if L <= 0:
            return

        # 若 block 比 capacity 还大，只保留最后 capacity
        if L >= self.capacity:
            block_tc = block_tc[-self.capacity :]
            L = self.capacity

        end = self.w + L
        if end <= self.capacity:
            self.buf[self.w : end] = block_tc
        else:
            k = self.capacity - self.w
            self.buf[self.w :] = block_tc[:k]
            self.buf[: end - self.capacity] = block_tc[k:]

        self.w = end % self.capacity
        self.size = min(self.capacity, self.size + L)

    def get_last(self, n: int, offset: int = 0) -> np.ndarray:
        """取最近窗口。

        n: 窗口长度
        offset: 从“最新样本末尾”往前跳过多少个样本。
                offset=0 表示窗口以最新样本结尾；
                offset=step_len 表示窗口以倒数 step_len 个样本结尾。
        """
        n = int(n)
        offset = int(offset)
        if n <= 0:
            return np.zeros((0, self.n_channels), dtype=self.buf.dtype)
        if offset < 0:
            raise ValueError("offset must be >= 0")
        if self.size < (n + offset):
            raise RuntimeError(f"ringbuffer has only {self.size} samples, need {n+offset}")

        end_excl = (self.w - offset) % self.capacity
        start = (end_excl - n) % self.capacity

        if start < end_excl:
            return self.buf[start:end_excl].copy()

        part1 = self.buf[start:]
        part2 = self.buf[:end_excl]
        return np.vstack([part1, part2]).copy()


class MaskRing:
    """存 0/1 mask，避免 bool ring buffer。"""

    def __init__(self, capacity: int):
        self.capacity = int(capacity)
        self.buf = np.zeros((self.capacity,), dtype=np.uint8)
        self.size = 0
        self.w = 0

    def append_block(self, mask: np.ndarray) -> None:
        mask = np.asarray(mask, dtype=np.uint8).reshape(-1)
        L = int(mask.shape[0])
        if L <= 0:
            return
        if L >= self.capacity:
            mask = mask[-self.capacity :]
            L = self.capacity

        end = self.w + L
        if end <= self.capacity:
            self.buf[self.w : end] = mask
        else:
            k = self.capacity - self.w
            self.buf[self.w :] = mask[:k]
            self.buf[: end - self.capacity] = mask[k:]

        self.w = end % self.capacity
        self.size = min(self.capacity, self.size + L)

    def mean_last(self, n: int, offset: int = 0) -> float:
        n = int(n)
        offset = int(offset)
        if offset < 0:
            raise ValueError("offset must be >= 0")
        if self.size < (n + offset):
            raise RuntimeError(f"mask buffer has only {self.size} samples, need {n+offset}")

        end_excl = (self.w - offset) % self.capacity
        start = (end_excl - n) % self.capacity

        if start < end_excl:
            return float(self.buf[start:end_excl].mean())
        part1 = self.buf[start:]
        part2 = self.buf[:end_excl]
        return float(np.concatenate([part1, part2]).mean())




# ----------------- 实时可视化 -----------------
class RollingBuffer:
    def __init__(self, max_samples: int, n_channels: int):
        self.max_samples = int(max_samples)
        self.n_channels = int(n_channels)
        self.buf = np.zeros((self.max_samples, self.n_channels), dtype=np.float32)
        self.write_idx = 0
        self.filled = 0
        self.lock = threading.Lock()

    def append(self, block: np.ndarray):
        if block is None or np.size(block) == 0:
            return
        block = np.asarray(block, dtype=np.float32)
        if block.ndim != 2 or block.shape[1] != self.n_channels:
            return

        n = int(block.shape[0])
        if n >= self.max_samples:
            block = block[-self.max_samples:]
            n = int(block.shape[0])

        with self.lock:
            end = self.write_idx + n
            if end <= self.max_samples:
                self.buf[self.write_idx:end] = block
            else:
                first = self.max_samples - self.write_idx
                self.buf[self.write_idx:] = block[:first]
                self.buf[: n - first] = block[first:]
            self.write_idx = (self.write_idx + n) % self.max_samples
            self.filled = min(self.max_samples, self.filled + n)

    def get_latest(self) -> np.ndarray:
        with self.lock:
            if self.filled == 0:
                return np.zeros((0, self.n_channels), dtype=np.float32)
            if self.filled < self.max_samples:
                return self.buf[:self.filled].copy()
            return np.vstack((self.buf[self.write_idx:], self.buf[:self.write_idx])).copy()


class DecodeDashboard:
    def __init__(
        self,
        sfreq: float,
        channels: List[int],
        gesture_names: List[str],
        display_seconds: float = 5.0,
        refresh_hz: float = 20.0,
        gain: float = 1.0,
        step_sec: float = 0.05,
        channel_range_uv: float = 2000.0,
    ):
        if plt is None:
            raise RuntimeError("matplotlib import failed")

        self.sfreq = float(sfreq)
        self.channels = list(channels)
        self.n_channels = len(self.channels)
        self.gesture_names = list(gesture_names)
        self.display_seconds = float(display_seconds)
        self.refresh_hz = float(refresh_hz)
        self.gain = float(gain)
        self.step_sec = float(step_sec)
        self.channel_range_uv = float(channel_range_uv)
        self.wave_offsets = np.arange(self.n_channels, dtype=np.float32) * self.channel_range_uv

        self.max_samples = max(1, int(round(self.sfreq * self.display_seconds)))
        self.max_steps = max(8, int(np.ceil(self.display_seconds / self.step_sec)) + 2)

        self.wave_buffer = RollingBuffer(max_samples=self.max_samples, n_channels=self.n_channels)
        self.pred_hist: Deque[int] = deque(maxlen=self.max_steps)
        self.stable_hist: Deque[int] = deque(maxlen=self.max_steps)

        self.latest_pred_idx = 0
        self.latest_pred_name = self.gesture_names[0]
        self.latest_stable_idx = 0
        self.latest_stable_name = self.gesture_names[0]
        self.latest_conf = 0.0
        self.latest_active_ratio = 0.0
        self.latest_gate_ready = False
        self.latest_gate_active = False
        self.latest_event_state = "-"
        self.latest_event_name = self.gesture_names[0]
        self.latest_high_th = None
        self.latest_low_th = None

        self.closed = False
        self.last_draw_t = 0.0

        plt.ion()
        self.fig = plt.figure(figsize=(14, 8))
        gs = self.fig.add_gridspec(
            2, 2,
            height_ratios=[4.5, 1.8],
            width_ratios=[4.8, 1.9],
            hspace=0.10,
            wspace=0.10,
        )
        self.ax_wave = self.fig.add_subplot(gs[0, :])
        self.ax_label = self.fig.add_subplot(gs[1, 0], sharex=self.ax_wave)
        self.ax_status = self.fig.add_subplot(gs[1, 1])

        try:
            self.fig.canvas.manager.set_window_title("Realtime EMG Decode Dashboard")
        except Exception:
            pass
        self.fig.canvas.mpl_connect("close_event", self._on_close)

        line_colors = plt.cm.tab10(np.linspace(0, 1, max(self.n_channels, 3)))
        self.lines = [self.ax_wave.plot([], [], lw=1.0, color=line_colors[i % len(line_colors)])[0] for i in range(self.n_channels)]
        self.wave_status = self.ax_wave.text(
            0.01, 1.02, "", transform=self.ax_wave.transAxes, fontsize=10,
            bbox=dict(boxstyle="round,pad=0.25", facecolor="#F7F7F7", edgecolor="#DDDDDD")
        )

        self.ax_wave.set_title("Realtime EMG")
        self.ax_wave.set_ylabel("Channels (stacked)")
        self.ax_wave.grid(True, alpha=0.25)
        self.ax_wave.set_xlim(-self.display_seconds, 0.0)
        self.ax_wave.set_ylim(
            -self.channel_range_uv / 2.0,
            self.wave_offsets[-1] + self.channel_range_uv / 2.0 if self.n_channels > 0 else self.channel_range_uv,
        )
        self.ax_wave.set_yticks(self.wave_offsets)
        self.ax_wave.set_yticklabels([f"ch{ch}" for ch in self.channels])

        # label timeline
        palette = [
            "#D9D9D9",  # rest
            "#4C78A8",
            "#F58518",
            "#54A24B",
            "#E45756",
            "#72B7B2",
            "#B279A2",
            "#FF9DA6",
            "#9D755D",
            "#BAB0AC",
        ]
        if len(self.gesture_names) > len(palette):
            extra = plt.cm.tab20(np.linspace(0, 1, len(self.gesture_names) - len(palette)))
            palette = palette + [tuple(c) for c in extra]
        self.label_cmap = ListedColormap(palette[: len(self.gesture_names)])
        self.label_norm = BoundaryNorm(np.arange(-0.5, len(self.gesture_names) + 0.5, 1), self.label_cmap.N)
        self.label_img = self.ax_label.imshow(
            np.zeros((2, self.max_steps), dtype=np.int32),
            aspect="auto",
            interpolation="nearest",
            cmap=self.label_cmap,
            norm=self.label_norm,
            extent=[-self.max_steps * self.step_sec, 0.0, 0.0, 2.0],
            origin="lower",
        )
        self.ax_label.set_ylim(0.0, 2.0)
        self.ax_label.set_xlim(-self.display_seconds, 0.0)
        self.ax_label.set_yticks([0.5, 1.5])
        self.ax_label.set_yticklabels(["Frame", "Stable"])
        self.ax_label.set_xlabel("Time (s)")
        self.ax_label.set_title("Prediction Timeline")
        self.ax_label.grid(False)

        # status panel
        self.ax_status.set_axis_off()
        self.big_label = self.ax_status.text(
            0.05, 0.82, self.latest_stable_name,
            fontsize=20, fontweight="bold", va="top"
        )
        self.small_label = self.ax_status.text(
            0.05, 0.58, "", fontsize=11, va="top"
        )
        self.event_label = self.ax_status.text(
            0.05, 0.37, "", fontsize=11, va="top"
        )
        self.gate_label = self.ax_status.text(
            0.05, 0.18, "", fontsize=10, va="top"
        )
        self.legend_label = self.ax_status.text(
            0.05, 0.02, "", fontsize=9, va="bottom"
        )

        self._refresh_legend()

    def _on_close(self, _evt):
        self.closed = True

    def _refresh_legend(self):
        items = []
        for i, name in enumerate(self.gesture_names):
            items.append(f"{i}:{name}")
        self.legend_label.set_text(" | ".join(items))

    def append_wave(self, block: np.ndarray):
        self.wave_buffer.append(block)

    def push_prediction(
        self,
        pred_idx: int,
        stable_idx: int,
        conf: float,
        active_ratio: float,
        gate_ready: bool,
        gate_active: bool,
        high_th: Optional[float],
        low_th: Optional[float],
        event_state: Optional[str],
        event_name: Optional[str],
    ):
        pred_idx = int(pred_idx)
        stable_idx = int(stable_idx)
        self.pred_hist.append(pred_idx)
        self.stable_hist.append(stable_idx)

        self.latest_pred_idx = pred_idx
        self.latest_pred_name = self.gesture_names[pred_idx]
        self.latest_stable_idx = stable_idx
        self.latest_stable_name = self.gesture_names[stable_idx]
        self.latest_conf = float(conf)
        self.latest_active_ratio = float(active_ratio)
        self.latest_gate_ready = bool(gate_ready)
        self.latest_gate_active = bool(gate_active)
        self.latest_high_th = None if high_th is None else float(high_th)
        self.latest_low_th = None if low_th is None else float(low_th)
        if event_state:
            self.latest_event_state = str(event_state)
        if event_name:
            self.latest_event_name = str(event_name)

    def update(self):
        if self.closed:
            return

        now = time.time()
        if (now - self.last_draw_t) < (1.0 / max(self.refresh_hz, 1.0)):
            return
        self.last_draw_t = now

        data = self.wave_buffer.get_latest()
        if data.shape[0] > 0:
            data = data * self.gain
            n = data.shape[0]
            x = np.linspace(-n / self.sfreq, 0.0, n, endpoint=False)

            for i, line in enumerate(self.lines):
                line.set_data(x, data[:, i] + self.wave_offsets[i])

        wave_status = (
            f"gain={self.gain:g} | gate={'READY' if self.latest_gate_ready else 'CALIBRATING'}"
            f" | active={'ON' if self.latest_gate_active else 'OFF'}"
        )
        self.wave_status.set_text(wave_status)

        pred_arr = np.zeros((self.max_steps,), dtype=np.int32)
        stable_arr = np.zeros((self.max_steps,), dtype=np.int32)
        if len(self.pred_hist) > 0:
            pred_arr[-len(self.pred_hist):] = np.asarray(self.pred_hist, dtype=np.int32)
        if len(self.stable_hist) > 0:
            stable_arr[-len(self.stable_hist):] = np.asarray(self.stable_hist, dtype=np.int32)

        img = np.vstack([pred_arr, stable_arr])
        self.label_img.set_data(img)

        self.big_label.set_text(f"Stable: {self.latest_stable_name}")
        self.small_label.set_text(
            f"Frame: {self.latest_pred_name}\n"
            f"Conf: {self.latest_conf:.2f}   Active ratio: {self.latest_active_ratio:.2f}"
        )
        self.event_label.set_text(
            f"Event: {self.latest_event_state} ({self.latest_event_name})"
        )
        if self.latest_gate_ready and self.latest_high_th is not None and self.latest_low_th is not None:
            gate_text = (
                f"Gate: {'ON' if self.latest_gate_active else 'OFF'}\n"
                f"high={self.latest_high_th:.2e}\n"
                f"low={self.latest_low_th:.2e}"
            )
        else:
            gate_text = "Gate: calibrating..."
        self.gate_label.set_text(gate_text)

        try:
            self.fig.canvas.draw_idle()
            self.fig.canvas.flush_events()
        except Exception:
            self.closed = True


# ----------------- 在线 RMS + 迟滞门控 -----------------
class OnlineGate:

    def __init__(
        self,
        sfreq: float,
        rms_win_sec: float = 0.05,
        base_pct: float = 10.0,
        high_pct: float = 90.0,
        alpha_high: float = 0.8,
        alpha_low: float = 0.3,
        calib_sec: float = 5.0,
    ):
        self.sfreq = float(sfreq)
        self.rms_win = max(1, int(round(rms_win_sec * self.sfreq)))
        self.kernel = np.ones((self.rms_win,), dtype=np.float32) / float(self.rms_win)
        self.tail = np.zeros((self.rms_win - 1,), dtype=np.float32)

        self.base_pct = float(base_pct)
        self.high_pct = float(high_pct)
        self.alpha_high = float(alpha_high)
        self.alpha_low = float(alpha_low)

        self.calib_need = max(1, int(round(calib_sec * self.sfreq)))
        self.calib_vals: List[float] = []

        self.high_th: Optional[float] = None
        self.low_th: Optional[float] = None
        self.active = False
        self.last_rms: float = 0.0

    def thresholds_ready(self) -> bool:
        return self.high_th is not None and self.low_th is not None

    def _maybe_finalize(self):
        if self.thresholds_ready():
            return
        if len(self.calib_vals) < self.calib_need:
            return
        arr = np.asarray(self.calib_vals, dtype=np.float32)
        base = float(np.percentile(arr, self.base_pct))
        high = float(np.percentile(arr, self.high_pct))
        self.high_th = (1.0 - self.alpha_high) * base + self.alpha_high * high
        self.low_th = (1.0 - self.alpha_low) * base + self.alpha_low * high
        print(f"[Gate] calibrated: high_th={self.high_th:.3e}, low_th={self.low_th:.3e}, calib_sec={len(arr)/self.sfreq:.2f}")

    def push_emg_block(self, block_tc: np.ndarray) -> np.ndarray:
        """输入 EMG block [L,C]，输出 mask [L] (0/1)"""
        block_tc = np.asarray(block_tc, dtype=np.float32)
        if block_tc.ndim != 2:
            raise ValueError("block must be 2D [L,C]")

        # power: mean over channels
        power = np.mean(block_tc * block_tc, axis=1).astype(np.float32)  # [L]

        # 平滑（与 offline compute_rms_envelope 等价的 moving average）
        if self.rms_win == 1:
            power_smooth = power
        else:
            ext = np.concatenate([self.tail, power])
            power_smooth = np.convolve(ext, self.kernel, mode="valid").astype(np.float32)
            self.tail = ext[-(self.rms_win - 1) :]

        rms = np.sqrt(np.maximum(power_smooth, 1e-12)).astype(np.float32)
        if rms.size > 0:
            self.last_rms = float(rms[-1])

        # 标定阶段：收集 rms
        if not self.thresholds_ready():
            # 不要无限增长
            need = self.calib_need - len(self.calib_vals)
            if need > 0:
                self.calib_vals.extend([float(x) for x in rms[:need]])
            self._maybe_finalize()

        # 门控
        out = np.zeros((rms.shape[0],), dtype=np.uint8)
        if not self.thresholds_ready():
            # 标定没完成前一律认为不活动
            return out

        hi = float(self.high_th)
        lo = float(self.low_th)

        # sample-by-sample hysteresis
        active = self.active
        for i in range(rms.shape[0]):
            v = float(rms[i])
            if not active:
                if v >= hi:
                    active = True
                    out[i] = 1
            else:
                out[i] = 1
                if v <= lo:
                    active = False
        self.active = active
        return out


# ----------------- WebSocket 事件：把每次收到的块对齐后塞到队列 -----------------
class BlockEvent(EventMessage):
    def __init__(self, device_mac: str, channels: List[int], block_q: queue.Queue):
        super().__init__()
        self.device_mac = device_mac
        self.channels = channels
        self.block_q = block_q

    def on_data(self, data: Union[str, dict, DataReceive]):
        if not (isinstance(data, DataReceive) and data.dataType == DataType.EP):
            return

        for device_data in data.data:
            if device_data.deviceId != self.device_mac:
                continue

            # 取出每个通道的 list，并保证长度一致
            vals = []
            min_len = None
            for ch in self.channels:
                key = str(ch)
                if key not in device_data.data:
                    return  # 缺通道就丢弃该包（更安全）
                arr = device_data.data[key]
                if min_len is None:
                    min_len = len(arr)
                else:
                    min_len = min(min_len, len(arr))
                vals.append(arr)

            if not vals or (min_len is None) or min_len <= 0:
                return

            block = np.stack([np.asarray(v[:min_len], dtype=np.float32) for v in vals], axis=1)  # [L,C]

            # 避免队列无限堆积：满了就丢最旧的一块，保留最新数据（真正的实时优先）
            try:
                self.block_q.put_nowait(block)
            except queue.Full:
                try:
                    self.block_q.get_nowait()
                except queue.Empty:
                    pass
                try:
                    self.block_q.put_nowait(block)
                except queue.Full:
                    pass


def main():
    ap = argparse.ArgumentParser()

    # 连接 / 配置（也支持从 realtime_waveform.py 的 config.ini 读取）
    ap.add_argument("--config", type=str, default=None, help="可选：config.ini 路径（同 realtime_waveform.py）")
    ap.add_argument("--host", type=str, default=None)
    ap.add_argument("--port", type=str, default=None)
    ap.add_argument("--websocket_host", type=str, default=None)
    ap.add_argument("--websocket_port", type=str, default=None)
    ap.add_argument("--login_id", type=str, default=None)
    ap.add_argument("--password", type=str, default=None)
    ap.add_argument("--guinea_pig_id", type=str, default=None)

    ap.add_argument("--device_mac", type=str, default=None)
    ap.add_argument("--channels", type=str, default=None, help="如 1,2,3,4,5；顺序要与训练一致")

    # 采样率（必须正确）
    ap.add_argument("--sfreq", type=float, required=True)

    # 模型
    ap.add_argument("--ckpt", type=str, required=True, help="cnn_4actions_merged_perwin.pth")

    # 滑窗与门控
    ap.add_argument("--win_sec", type=float, default=0.50)
    ap.add_argument("--step_sec", type=float, default=0.10)
    ap.add_argument("--active_ratio_thresh", type=float, default=0.6)

    ap.add_argument("--rms_win_sec", type=float, default=0.05)
    ap.add_argument("--base_pct", type=float, default=10.0)
    ap.add_argument("--high_pct", type=float, default=90.0)
    ap.add_argument("--alpha_high", type=float, default=0.8)
    ap.add_argument("--alpha_low", type=float, default=0.3)
    ap.add_argument("--calib_sec", type=float, default=5.0, help="开始几秒用于估计 RMS 阈值")

    # 事件平滑（v3：一段一标签，不允许 action->action 直接切换）
    ap.add_argument("--min_rest_sec", type=float, default=0.50,
                    help="动作结束判定需要连续 rest 的最短时长")
    ap.add_argument("--conf_thresh", type=float, default=0.55,
                    help="低于该置信度的非零类别按 rest 处理")
    ap.add_argument("--decision_min_windows", type=int, default=4,
                    help="新动作开始前，至少累计多少个活动窗再做段级定类")
    ap.add_argument("--decision_max_windows", type=int, default=6,
                    help="若仍未形成足够一致的投票，最多累计多少个活动窗后强制定类")
    ap.add_argument("--decision_vote_ratio", type=float, default=0.60,
                    help="段起始累计窗中，最佳类别的加权票占比至少达到该值才锁定标签")
    ap.add_argument("--refractory_sec", type=float, default=0.20,
                    help="end 后屏蔽相反方向回弹的时长")

    # 为兼容旧命令，保留但不再用于 action->action 直接切换
    ap.add_argument("--start_vote_len", type=int, default=None,
                    help="兼容旧参数；若提供且未显式设置 decision_min_windows，则作为其替代")
    ap.add_argument("--switch_vote_len", type=int, default=None,
                    help="兼容旧参数；v3 中不再使用 action->action 直接切换")

    # UDP 输出
    ap.add_argument("--ip", type=str, default="127.0.0.1")
    ap.add_argument("--port_udp", type=int, default=5005)

    # 其它
    ap.add_argument("--queue_max", type=int, default=10, help="WebSocket->分类线程的 block 队列长度")
    ap.add_argument("--ring_sec", type=float, default=10.0, help="ring buffer 保存的秒数")
    ap.add_argument("--scale", type=float, default=1.0, help="对输入幅值整体缩放（调单位用）")
    ap.add_argument("--debug", action="store_true")

    ap.add_argument("--frame_use_stable_label", dest="frame_use_stable_label", action="store_true", default=True,
                    help="UDP frame 默认发送平滑后的 stable label（推荐）")
    ap.add_argument("--frame_use_raw_label", dest="frame_use_stable_label", action="store_false",
                    help="UDP frame 改为发送模型原始逐窗 label")

    # Web dashboard
    ap.add_argument("--web_dashboard", action="store_true", default=False,
                    help="启动 Flask+SocketIO 实时 Web 仪表盘")
    ap.add_argument("--web_port", type=int, default=5050,
                    help="Web 仪表盘监听端口（默认 5050）")

    # 实时可视化
    ap.add_argument("--show_plot", dest="show_plot", action="store_true", default=True,
                    help="显示实时波形 + 标签面板（默认开启）")
    ap.add_argument("--no_show_plot", dest="show_plot", action="store_false",
                    help="关闭实时波形 + 标签面板")
    ap.add_argument("--display_seconds", type=float, default=5.0,
                    help="窗口中显示最近多少秒数据")
    ap.add_argument("--refresh_hz", type=float, default=20.0,
                    help="界面刷新频率")
    ap.add_argument("--plot_gain", type=float, default=1.0,
                    help="仅用于显示的幅值放大倍数（WebSocket 原始值已是 µV，默认不再换算）")
    ap.add_argument("--channel_range_uv", type=float, default=2000.0,
                    help="每个通道固定显示范围（µV，峰峰值），用于波形堆叠间距和 y 轴范围，不随信号方差自动缩放")

    args = ap.parse_args()

    # ----------------- 读取 config.ini（可选） -----------------
    if args.config:
        cfg = configparser.ConfigParser()
        cfg.read(args.config, encoding="utf-8")

        def _get(section, key, cur):
            if cur is not None:
                return cur
            if cfg.has_option(section, key):
                return cfg.get(section, key)
            return cur

        args.host = _get("config-data", "host", args.host)
        args.port = _get("config-data", "port", args.port)
        args.websocket_host = _get("config-data", "websocket_host", args.websocket_host)
        args.websocket_port = _get("config-data", "websocket_port", args.websocket_port)
        args.login_id = _get("config-data", "login_id", args.login_id)
        args.password = _get("config-data", "password", args.password)
        args.guinea_pig_id = _get("config-data", "guinea_pig_id", args.guinea_pig_id)
        args.device_mac = _get("app", "device_mac", args.device_mac)
        args.channels = _get("app", "channels", args.channels)
        args.channels = _get("app", "channel", args.channels)

    # 默认值
    sdk_config = ConfigUtil()

    def _config_value(keys, default):
        if isinstance(keys, str):
            keys = (keys,)
        for key in keys:
            value = sdk_config.get_data(key)
            if value is not None and value != "":
                return value
        return default

    host = (args.host or _config_value("host", "http://localhost")).split(";")[0]
    port = str(args.port or _config_value("port", "8080"))
    websocket_host = (args.websocket_host or _config_value("websocket_host", "ws://localhost")).split(";")[0]
    websocket_port = str(args.websocket_port or _config_value("websocket_port", "9000"))
    login_id = args.login_id or _config_value("login_id", "admin")
    password = args.password or _config_value("password", "admin")
    guinea_pig_id = args.guinea_pig_id or _config_value("guinea_pig_id", "20220526")
    args.device_mac = (args.device_mac or _config_value("device_mac", "E3:5B:D8:05:34:E9")).split(";")[0].strip()
    channels_value = args.channels or _config_value(("channels", "channel"), "1,2,3,4,5")

    channels = [int(x.strip()) for x in channels_value.split(",") if x.strip()]
    sdk_config.update_data({
        "host": host,
        "port": port,
        "websocket_host": websocket_host,
        "websocket_port": websocket_port,
        "login_id": login_id,
        "password": password,
        "guinea_pig_id": guinea_pig_id,
        "device_mac": args.device_mac,
        "channels": channels_value,
        "channel": channels_value,
    })
    n_channels = len(channels)

    ckpt_path = Path(args.ckpt)
    if not ckpt_path.exists():
        raise FileNotFoundError(str(ckpt_path))

    # ----------------- 模型加载 -----------------
    model, torch_device, mean, std, per_window_norm, gesture_names, label_offset = load_ckpt(
        ckpt_path, n_channels=n_channels
    )
    softmax = torch.nn.Softmax(dim=1)
    decision_min_windows = int(args.decision_min_windows)
    if args.start_vote_len is not None and ("--decision_min_windows" not in os.sys.argv):
        decision_min_windows = int(args.start_vote_len)

    smoother = LockedOnsetSegmentSmoother(
        gesture_names=gesture_names,
        step_sec=args.step_sec,
        min_rest_sec=args.min_rest_sec,
        refractory_sec=args.refractory_sec,
        conf_thresh=args.conf_thresh,
        decision_min_windows=decision_min_windows,
        decision_max_windows=int(args.decision_max_windows),
        decision_vote_ratio=float(args.decision_vote_ratio),
    )

    print(f"[Model] device={torch_device}, per_window_norm={per_window_norm}, label_offset={label_offset}")
    print(f"[Classes] 0=rest, 1..={gesture_names[1:]}")

    # ----------------- UDP socket -----------------
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    target = (args.ip, int(args.port_udp))
    print(f"[UDP] send to {target[0]}:{target[1]}")

    # ----------------- 在线门控 + ring buffer -----------------
    sfreq = float(args.sfreq)
    win_len = int(round(args.win_sec * sfreq))
    step_len = int(round(args.step_sec * sfreq))
    if win_len <= 0 or step_len <= 0:
        raise ValueError("win_len/step_len <= 0，检查 --sfreq/--win_sec/--step_sec")

    ring_cap = int(round(args.ring_sec * sfreq))
    ring_cap = max(ring_cap, win_len * 2)

    emg_ring = RingBuffer(capacity=ring_cap, n_channels=n_channels, dtype=np.float32)
    mask_ring = MaskRing(capacity=ring_cap)

    gate = OnlineGate(
        sfreq=sfreq,
        rms_win_sec=args.rms_win_sec,
        base_pct=args.base_pct,
        high_pct=args.high_pct,
        alpha_high=args.alpha_high,
        alpha_low=args.alpha_low,
        calib_sec=args.calib_sec,
    )

    morse_server = None
    if args.web_dashboard:
        try:
            from epstudiosdk.morse_dashboard import MorseDashboardServer
            morse_server = MorseDashboardServer(port=args.web_port, gesture_names=gesture_names)
            morse_server.start()
            print(f"[WEB] Morse dashboard → http://localhost:{args.web_port}")
        except ImportError:
            print("[WARN] flask / flask-socketio not installed — web dashboard disabled.")

    plotter = None
    if args.show_plot:
        if plt is None:
            print("[WARN] matplotlib not available, dashboard disabled.")
        else:
            try:
                plotter = DecodeDashboard(
                    sfreq=sfreq,
                    channels=channels,
                    gesture_names=gesture_names,
                    display_seconds=args.display_seconds,
                    refresh_hz=args.refresh_hz,
                    gain=args.plot_gain,
                    step_sec=args.step_sec,
                    channel_range_uv=args.channel_range_uv,
                )
                print("[UI] realtime dashboard enabled")
            except Exception as e:
                print(f"[WARN] failed to create realtime dashboard: {e}")
                plotter = None

    # ----------------- WebSocket / collection 启动 -----------------
    block_q: queue.Queue = queue.Queue(maxsize=int(args.queue_max))
    event_handler = BlockEvent(device_mac=args.device_mac, channels=channels, block_q=block_q)

    client = EpClient(init_user_status=True)
    login_res = client.do_action_json(UserLoginRequest(login_id, password))
    print("[EPStudio] Login:", login_res)

    set_patient_res = client.do_action_json(GuineaPigSetCurrentRequest(guinea_pig_id))
    print("[EPStudio] Set patient:", set_patient_res)

    websocket_client = EpWebSocketClient(event_msg=event_handler, enable_trace=False)
    websocket_client.start()

    collection_device = CollectionDeviceBean(args.device_mac, channelStatus=channels)
    collection = Collection(client=client, device_list=[collection_device], record_status=False)

    print("[EPStudio] Starting collection...")
    result = collection.start_collection()
    print("[EPStudio] start_collection:", result)

    # ----------------- 主循环：消费 block -> 更新 ring -> 每 step_len 做一次推理 -----------------
    samples_since_pred = 0
    first_pred_done = False
    total_samples = 0  # 从开始累计的样本点数（用于构造 t）

    try:
        while True:
            try:
                block = block_q.get(timeout=0.5)  # [L,C]
            except queue.Empty:
                if plotter is not None:
                    plotter.update()
                    if plotter.closed:
                        plotter = None
                continue

            if args.scale != 1.0:
                block = (np.asarray(block, dtype=np.float32) * float(args.scale)).astype(np.float32)
            else:
                block = np.asarray(block, dtype=np.float32)

            L = int(block.shape[0])
            if L <= 0:
                continue

            # 1) 更新门控 mask
            m = gate.push_emg_block(block)  # [L]

            # 2) 更新 ring buffer
            emg_ring.append_block(block)
            mask_ring.append_block(m)
            if plotter is not None:
                plotter.append_wave(block)

            total_samples += L
            samples_since_pred += L

            # ring 不够窗口长度就先不推理
            if emg_ring.size < win_len or mask_ring.size < win_len:
                if plotter is not None:
                    plotter.update()
                    if plotter.closed:
                        plotter = None
                continue
            if not first_pred_done:
                samples_since_pred = step_len  # 让下面 while 恰好跑一次，并且 offset=0
                first_pred_done = True
            # 3) 可能需要做多次推理（如果一下来了很多样本）
            #    用 offset 把“该预测对应的窗口末端”对齐到正确的样本位置，避免重复用同一个 last window。
            while samples_since_pred >= step_len:
                offset = samples_since_pred - step_len

                emg_win = emg_ring.get_last(win_len, offset=offset)  # [win_len,C]
                active_ratio = mask_ring.mean_last(win_len, offset=offset)

                # 以样本计数构造时间（更稳定）
                end_sample_excl = total_samples - offset
                t_center = (end_sample_excl - win_len / 2.0) / sfreq

                if active_ratio < float(args.active_ratio_thresh) or (not gate.thresholds_ready()):
                    pred_idx = 0
                    conf = 0.0
                else:
                    if per_window_norm:
                        mu = emg_win.mean(axis=0, keepdims=True)
                        sigma = emg_win.std(axis=0, keepdims=True) + 1e-8
                        emg_norm = (emg_win - mu) / sigma
                        x_np = emg_norm.T[None, :, :]  # [1,C,T]
                    else:
                        if mean is None or std is None:
                            raise RuntimeError("全局归一化模式下 ckpt 必须提供 mean/std")
                        win_tc = emg_win[None, :, :]  # [1,T,C]
                        win_norm = (win_tc - mean) / std
                        x_np = np.transpose(win_norm.astype(np.float32), (0, 2, 1))

                    x = torch.from_numpy(x_np.astype(np.float32)).to(torch_device)
                    with torch.no_grad():
                        logits = model(x)
                        prob = softmax(logits).detach().cpu().numpy()[0]
                        pred4 = int(np.argmax(prob))
                        conf = float(np.max(prob))
                    pred_idx = pred4 + label_offset

                # event（先更新状态机，再决定 frame 发 raw 还是 stable）
                evs = smoother.update(t=float(t_center), label=int(pred_idx), conf=float(conf))
                for ev in evs:
                    sock.sendto(json.dumps(ev.__dict__, ensure_ascii=False).encode("utf-8"), target)
                if morse_server is not None:
                    for ev in evs:
                        morse_server.push(ev)

                frame_label = int(smoother.cur_label) if args.frame_use_stable_label else int(pred_idx)
                frame_conf = float(conf) if frame_label != 0 else 0.0

                # frame
                frame = FrameMsg("frame", float(t_center), frame_label, gesture_names[frame_label], frame_conf, float(active_ratio))
                sock.sendto(json.dumps(frame.__dict__, ensure_ascii=False).encode("utf-8"), target)
                if morse_server is not None:
                    morse_server.push_frame(frame, gate.thresholds_ready())

                if plotter is not None:
                    last_event_state = evs[-1].state if len(evs) > 0 else None
                    last_event_name = evs[-1].name if len(evs) > 0 else None
                    plotter.push_prediction(
                        pred_idx=int(pred_idx),
                        stable_idx=int(smoother.cur_label),
                        conf=float(conf),
                        active_ratio=float(active_ratio),
                        gate_ready=gate.thresholds_ready(),
                        gate_active=gate.active,
                        high_th=gate.high_th,
                        low_th=gate.low_th,
                        event_state=last_event_state,
                        event_name=last_event_name,
                    )

                if args.debug:
                    print(f"[gate] ready={gate.thresholds_ready()} active={gate.active} last_rms={gate.last_rms:.3e} high_th={gate.high_th} low_th={gate.low_th}")
                    print(f"[frame] t={t_center:.2f} label={pred_idx} name={gesture_names[pred_idx]} conf={conf:.2f} active_ratio={active_ratio:.2f}")
                    if len(evs) > 0:
                        for ev in evs:
                            print(f"[event] state={ev.state} label={ev.label} name={ev.name} conf={ev.conf:.2f}")
                samples_since_pred -= step_len

            if plotter is not None:
                plotter.update()
                if plotter.closed:
                    plotter = None

    except KeyboardInterrupt:
        print("\n[Exit] KeyboardInterrupt")
    finally:
        if morse_server is not None:
            morse_server.stop()
        try:
            collection.stop_collection()
        except Exception:
            pass
        try:
            websocket_client.stop()
        except Exception:
            pass
        try:
            sock.close()
        except Exception:
            pass
        if plotter is not None and plt is not None:
            try:
                plt.close(plotter.fig)
            except Exception:
                pass
        print("[Done]")


if __name__ == "__main__":
    main()
