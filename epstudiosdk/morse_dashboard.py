"""morse_dashboard.py — Flask + SocketIO real-time Morse code web dashboard.

Receives EventMsg / FrameMsg objects from the inference loop via push() /
push_frame(). Runs entirely in daemon threads so the main loop is never
blocked. Silently unavailable if flask / flask-socketio are not installed.
"""
from __future__ import annotations
import queue
import threading
import time

try:
    from flask import Flask, jsonify, request as _freq
    from flask_socketio import SocketIO, emit as _sio_emit
    _FLASK_OK = True
except ImportError:
    _FLASK_OK = False

# ── Morse tables ──────────────────────────────────────────────────────────────

GESTURE_TO_MORSE: dict = {
    "down":    ".",
    "tapping": "-",
    "fist":    " ",
    "rest":    None,
}

MORSE_TO_LETTER: dict = {
    ".-":   "A", "-...": "B", "-.-.": "C", "-..":  "D", ".":    "E",
    "..-.": "F", "--.":  "G", "....": "H", "..":   "I", ".---": "J",
    "-.-":  "K", ".-..": "L", "--":   "M", "-.":   "N", "---":  "O",
    ".--.": "P", "--.-": "Q", ".-.":  "R", "...":  "S", "-":    "T",
    "..-":  "U", "...-": "V", ".--":  "W", "-..-": "X", "-.--": "Y",
    "--..": "Z",
    "-----": "0", ".----": "1", "..---": "2", "...--": "3",
    "....-": "4", ".....": "5", "-....": "6", "--...": "7",
    "---..": "8", "----.": "9",
}

LETTER_COMMIT_SEC = 2.0   # inactivity → auto-commit morse buffer → letter
WORD_COMMIT_SEC   = 4.0   # inactivity → auto-commit current word → sentence

# ── Inline HTML dashboard ─────────────────────────────────────────────────────

_DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AXON — Gesture to Speech</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@300;400;600;700;800&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}

:root{
  --teal:#B466D9;
  --bg:radial-gradient(ellipse at 50% 20%,#2a0a40 0%,#0d0a15 65%);
  --panel:#171320;
  --border:rgba(255,255,255,.07);
  --text:#E6DFF5;
  --muted:#5A5070;
  --dim:#2a2440;
  --card:#1e1830;
  --card-act:#241a38;
  --glow:rgba(180,102,217,.3);
  --badge-bg:#201c30;
  --badge-text:#7060a0;
}
html[data-theme="light"]{
  --teal:#660874;
  --bg:radial-gradient(ellipse at 50% 30%,#ddd5f0 0%,#e9e4f5 100%);
  --panel:#ffffff;
  --border:rgba(100,60,150,.10);
  --text:#1a1025;
  --muted:#9080a8;
  --dim:#d0c8e4;
  --card:#f5f1fb;
  --card-act:#ede5fa;
  --glow:rgba(102,8,116,.14);
  --badge-bg:#ede8f5;
  --badge-text:#9080a8;
}

html,body{height:100%;font-family:'IBM Plex Sans',sans-serif;background:var(--bg);color:var(--text);overflow:hidden}

.app{display:flex;flex-direction:column;height:100vh;padding:10px 14px;gap:8px}

/* ── Status bar ── */
.sb{display:flex;align-items:center;justify-content:space-between;height:38px;flex-shrink:0;padding:0 2px}
.sb-l{display:flex;align-items:center;gap:8px;font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.08em;color:var(--muted)}
.dot{width:8px;height:8px;border-radius:50%;background:#22c55e;box-shadow:0 0 8px #22c55e;animation:softPulse 2s ease-in-out infinite}
.dot.off{background:var(--muted);box-shadow:none;animation:none}
.sb-c{font-family:'IBM Plex Mono',monospace;font-size:12px;letter-spacing:.22em;color:var(--muted)}
.sb-r{display:flex;align-items:center;gap:14px}
.bars{display:flex;align-items:flex-end;gap:2px;height:16px}
.bar{width:3px;background:var(--teal);border-radius:1px;opacity:.2}
.bar.on{opacity:1}
.bar:nth-child(1){height:4px}.bar:nth-child(2){height:7px}
.bar:nth-child(3){height:11px}.bar:nth-child(4){height:16px}
.sig-lbl{font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:.08em;color:var(--muted)}
.timer{font-family:'IBM Plex Mono',monospace;font-size:13px;letter-spacing:.06em;min-width:46px;text-align:right}
.tbtn{font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:.1em;padding:4px 10px;border:1px solid var(--border);border-radius:20px;background:var(--panel);color:var(--muted);cursor:pointer;display:flex;align-items:center;gap:5px;transition:all .2s}
.tbtn:hover{border-color:var(--teal);color:var(--teal)}

/* ── Top row ── */
.top{display:flex;gap:8px;flex-shrink:0;height:308px}

/* ── Shared panel ── */
.panel{background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:16px;position:relative;overflow:hidden}
.plbl{font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:.2em;color:var(--muted)}

/* ── Zone 1: gesture cards ── */
.g-panel{width:24%;flex-shrink:0;display:flex;flex-direction:column}
.g-hdr{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px}
.badge{font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:.12em;padding:2px 8px;border-radius:4px;background:var(--badge-bg);color:var(--badge-text)}
.gcards{display:flex;flex-direction:column;gap:8px}
.gcard{display:flex;align-items:center;padding:11px 14px;border-radius:8px;background:var(--card);border:1.5px solid transparent;transition:border-color .2s,background .2s,box-shadow .2s}
.gcard.active{border-color:var(--teal);background:var(--card-act);animation:glowPulse 1.5s ease-in-out infinite}
.ge{font-size:26px;margin-right:12px;line-height:1;flex-shrink:0}
.gi{flex:1;min-width:0}
.gt{font-family:'IBM Plex Mono',monospace;font-size:9px;letter-spacing:.18em;color:var(--muted);margin-bottom:2px}
.gn{font-size:15px;font-weight:700;letter-spacing:.02em}
.gcard.active .gn{color:var(--teal)}
.gs{font-family:'IBM Plex Mono',monospace;font-size:22px;color:var(--dim);margin-left:8px;flex-shrink:0}
.gcard.active .gs{color:var(--teal)}

/* ── Zone 2: morse buffer ── */
.m-panel{flex:1;display:flex;flex-direction:column}
.m-hdr{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}
.m-hint{font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.12em;color:var(--teal)}
.m-disp{display:flex;align-items:center;justify-content:center;gap:18px;flex:1;flex-wrap:wrap;padding:8px 16px}
.m-ph{font-family:'IBM Plex Mono',monospace;font-size:13px;letter-spacing:.3em;color:var(--dim)}
.msym{display:flex;align-items:center;justify-content:center;animation:scaleIn .18s cubic-bezier(.34,1.56,.64,1) both}
.mdot{width:38px;height:38px;border-radius:50%;background:var(--teal)}
.mdash{width:90px;height:22px;border-radius:5px;background:var(--teal)}
.m-ref{font-family:'IBM Plex Mono',monospace;font-size:12px;color:var(--muted);text-align:center;flex-shrink:0;padding:4px 0;min-height:24px;letter-spacing:.08em}
.cd-area{flex-shrink:0;padding-top:4px;display:none}
.cd-area.show{display:block}
.cd-lbl{font-family:'IBM Plex Mono',monospace;font-size:9px;letter-spacing:.2em;color:var(--teal);margin-bottom:5px}
.cd-track{height:3px;background:var(--dim);border-radius:2px;overflow:hidden}
.cd-fill{height:100%;background:var(--teal);border-radius:2px;transition:width .25s linear}

/* ── Zone 3: current word ── */
.w-panel{flex-shrink:0;height:116px;display:flex;flex-direction:column}
.w-body{flex:1;display:flex;align-items:center;justify-content:center}
.wt{font-size:72px;font-weight:700;letter-spacing:.04em;color:var(--teal);line-height:1}
.wt.empty{font-size:22px;font-weight:400;color:var(--dim)}

/* ── Zone 4: sentence output ── */
.s-panel{flex:1;min-height:0;display:flex;flex-direction:column}
.s-hdr{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;flex-shrink:0}
.s-hist{flex:1;min-height:0;display:flex;flex-direction:column;justify-content:flex-end;overflow:hidden;gap:6px;padding-bottom:4px}
.s-prev{font-size:26px;font-weight:300;color:var(--muted);letter-spacing:.02em;line-height:1.2;animation:slideIn .3s ease}
.s-cur{font-size:88px;font-weight:800;letter-spacing:.02em;line-height:1;display:flex;align-items:baseline;flex-wrap:wrap;word-break:break-all}
.caret{display:inline-block;width:6px;height:.82em;background:var(--teal);margin-left:5px;border-radius:2px;animation:caretBlink 1s step-end infinite;vertical-align:baseline;flex-shrink:0}

/* ── Animations ── */
@keyframes scaleIn{from{transform:scale(0);opacity:0}to{transform:scale(1);opacity:1}}
@keyframes glowPulse{
  0%,100%{box-shadow:0 0 8px var(--glow),inset 0 0 6px var(--glow)}
  50%{box-shadow:0 0 24px var(--glow),inset 0 0 18px var(--glow)}
}
@keyframes softPulse{0%,100%{opacity:1}50%{opacity:.4}}
@keyframes caretBlink{0%,100%{opacity:1}50%{opacity:0}}
@keyframes slideIn{from{transform:translateX(16px);opacity:0}to{transform:translateX(0);opacity:1}}
@keyframes ringPulse{0%{transform:scale(1);opacity:.8}100%{transform:scale(2.2);opacity:0}}
</style>
</head>
<body>
<div class="app">

<!-- Status bar -->
<div class="sb">
  <div class="sb-l">
    <div class="dot" id="cdot"></div>
    <span id="clbl">EMG BAND &middot; CONNECTED</span>
  </div>
  <div class="sb-c">AXON &mdash; GESTURE TO SPEECH</div>
  <div class="sb-r">
    <div class="bars" id="bars">
      <div class="bar on"></div><div class="bar on"></div>
      <div class="bar on"></div><div class="bar on"></div>
    </div>
    <span class="sig-lbl" id="siglbl">SIGNAL OK</span>
    <span class="timer" id="timer">00:00</span>
    <button class="tbtn" onclick="toggleTheme()">
      <span id="tico">&#9733;</span><span id="tlbl">LIGHT</span>
    </button>
  </div>
</div>

<!-- Top row: Zone 1 + Zone 2 -->
<div class="top">

  <!-- Zone 1: gesture cards -->
  <div class="panel g-panel">
    <div class="g-hdr">
      <div class="plbl">LIVE GESTURE</div>
      <div class="badge" id="sbadge">REST</div>
    </div>
    <div class="gcards">
      <div class="gcard" id="c-down">
        <span class="ge">&#128071;</span>
        <div class="gi"><div class="gt">WRIST DOWN</div><div class="gn">DOT</div></div>
        <span class="gs">&middot;</span>
      </div>
      <div class="gcard" id="c-tapping">
        <span class="ge">&#129086;</span>
        <div class="gi"><div class="gt">TAPPING</div><div class="gn">DASH</div></div>
        <span class="gs">&mdash;</span>
      </div>
      <div class="gcard" id="c-fist">
        <span class="ge">&#9994;</span>
        <div class="gi"><div class="gt">FIST CLENCH</div><div class="gn">SPACE</div></div>
        <span class="gs">/</span>
      </div>
    </div>
  </div>

  <!-- Zone 2: morse buffer -->
  <div class="panel m-panel">
    <div class="m-hdr">
      <div class="plbl">MORSE BUFFER</div>
      <div class="m-hint" id="mhint"></div>
    </div>
    <div class="m-disp" id="mdisp">
      <span class="m-ph">AWAITING INPUT</span>
    </div>
    <div class="m-ref" id="mref"></div>
    <div class="cd-area" id="cda">
      <div class="cd-lbl">COMMITTING LETTER</div>
      <div class="cd-track"><div class="cd-fill" id="cdfill"></div></div>
    </div>
  </div>

</div><!-- .top -->

<!-- Zone 3: current word -->
<div class="panel w-panel">
  <div class="plbl">CURRENT WORD</div>
  <div class="w-body">
    <span class="wt empty" id="wtext">_</span>
  </div>
</div>

<!-- Zone 4: sentence output -->
<div class="panel s-panel">
  <div class="s-hdr">
    <div class="plbl">SENTENCE OUTPUT</div>
    <div class="plbl">LIVE TRANSCRIPT</div>
  </div>
  <div class="s-hist" id="shist">
    <div class="s-cur"><span id="stxt"></span><span class="caret"></span></div>
  </div>
</div>

</div><!-- .app -->

<script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
<script>
'use strict';
const socket = io();
const t0 = Date.now();
let prevBuf = '';
let prevSentence = '';
let curTheme = 'light';

// ── Session timer ──
setInterval(() => {
  const s = Math.floor((Date.now() - t0) / 1000);
  document.getElementById('timer').textContent =
    String(Math.floor(s / 60)).padStart(2, '0') + ':' + String(s % 60).padStart(2, '0');
}, 1000);

// ── Theme toggle ──
function toggleTheme() {
  curTheme = curTheme === 'light' ? 'dark' : 'light';
  document.documentElement.setAttribute('data-theme', curTheme);
  document.getElementById('tlbl').textContent = curTheme === 'light' ? 'LIGHT' : 'DARK';
  document.getElementById('tico').textContent = curTheme === 'light' ? '★' : '☽';
}

// ── Connection ──
socket.on('connect', () => {
  document.getElementById('cdot').classList.remove('off');
  document.getElementById('clbl').textContent = 'EMG BAND · CONNECTED';
  document.querySelectorAll('.bar').forEach(b => b.classList.add('on'));
  document.getElementById('siglbl').textContent = 'SIGNAL OK';
});
socket.on('disconnect', () => {
  document.getElementById('cdot').classList.add('off');
  document.getElementById('clbl').textContent = 'EMG BAND · DISCONNECTED';
  document.querySelectorAll('.bar').forEach(b => b.classList.remove('on'));
  document.getElementById('siglbl').textContent = 'NO SIGNAL';
});

// ── State update ──
socket.on('state_update', s => {
  updateCards(s.active_gesture);
  updateMorse(s.morse_buffer, s.morse_reference, s.current_letter, s.countdown);
  updateWord(s.current_word);
  updateSentence(s.sentence);
  updateBadge(s.active_gesture, s.gate_ready);
});

// ── Gesture cards ──
const CARD_MAP = {
  down: 'c-down',
  tapping: 'c-tapping',
  fist: 'c-fist',
};
function updateCards(gesture) {
  document.querySelectorAll('.gcard').forEach(c => c.classList.remove('active'));
  const id = CARD_MAP[gesture];
  if (id) document.getElementById(id).classList.add('active');
}

// ── Morse buffer ──
function makeSym(ch, animate) {
  const wrap = document.createElement('div');
  wrap.className = 'msym';
  if (!animate) wrap.style.animation = 'none';
  const inner = document.createElement('div');
  inner.className = ch === '.' ? 'mdot' : 'mdash';
  wrap.appendChild(inner);
  return wrap;
}

function updateMorse(buf, ref, letter, countdown) {
  const disp = document.getElementById('mdisp');
  const refEl = document.getElementById('mref');
  const cda = document.getElementById('cda');
  const mhint = document.getElementById('mhint');

  if (!buf) {
    if (prevBuf !== '') {
      disp.innerHTML = '<span class="m-ph">AWAITING INPUT</span>';
      prevBuf = '';
    }
    refEl.textContent = '';
    cda.classList.remove('show');
    mhint.textContent = '';
    return;
  }

  if (buf !== prevBuf) {
    if (buf.length > prevBuf.length && buf.startsWith(prevBuf)) {
      // Remove placeholder if present
      if (prevBuf === '') disp.innerHTML = '';
      // Append only new characters (with scale-in animation)
      for (let i = prevBuf.length; i < buf.length; i++) {
        disp.appendChild(makeSym(buf[i], true));
      }
    } else {
      // Full rebuild (buffer was reset or changed)
      disp.innerHTML = '';
      for (const c of buf) disp.appendChild(makeSym(c, false));
    }
    prevBuf = buf;
  }

  refEl.textContent = ref || '';
  mhint.textContent = letter ? 'DECODING → ' + letter : '';

  if (countdown > 0) {
    cda.classList.add('show');
    document.getElementById('cdfill').style.width = (countdown * 100) + '%';
  } else {
    cda.classList.remove('show');
  }
}

// ── Current word ──
function updateWord(word) {
  const el = document.getElementById('wtext');
  if (!word) {
    el.textContent = '_';
    el.className = 'wt empty';
  } else {
    el.textContent = word;
    el.className = 'wt';
  }
}

// ── Sentence output ──
function esc(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
function updateSentence(sentence) {
  if (sentence === prevSentence) return;
  prevSentence = sentence;

  const words = sentence.trim().split(/\s+/).filter(Boolean);
  const RECENT = 5;
  const curWords = words.slice(-RECENT).join(' ');
  const prevWords = words.length > RECENT ? words.slice(0, -RECENT).join(' ') : '';

  const hist = document.getElementById('shist');
  hist.innerHTML = '';

  if (prevWords) {
    const p = document.createElement('div');
    p.className = 's-prev';
    p.textContent = prevWords;
    hist.appendChild(p);
  }

  const cur = document.createElement('div');
  cur.className = 's-cur';
  cur.innerHTML = '<span>' + esc(curWords) + '</span><span class="caret"></span>';
  hist.appendChild(cur);
}

// ── State badge ──
function updateBadge(gesture, gateReady) {
  const b = document.getElementById('sbadge');
  if (!gateReady) { b.textContent = 'CALIBRATING'; return; }
  b.textContent = (!gesture || gesture === 'rest') ? 'REST' : gesture.toUpperCase();
}

// Pull initial state on load
fetch('/state')
  .then(r => r.json())
  .then(s => socket.emit('state_update', s))
  .catch(() => {});
</script>
</body>
</html>"""

# ── Morse decoder (thread-safe state machine) ─────────────────────────────────

class MorseDecoder:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.morse_buffer: str = ""
        self.current_word: str = ""
        self.sentence: str = ""
        self.active_gesture: str = "rest"
        self.confidence: float = 0.0
        self.gate_ready: bool = False
        self._last_activity: float = time.monotonic()

    def reset(self) -> None:
        with self._lock:
            self.morse_buffer = ""
            self.current_word = ""
            self.sentence = ""
            self.active_gesture = "rest"
            self.confidence = 0.0
            self._last_activity = time.monotonic()

    def _commit_letter(self) -> None:
        buf = self.morse_buffer.strip()
        if buf:
            self.current_word += MORSE_TO_LETTER.get(buf, "?")
        self.morse_buffer = ""

    def _commit_word(self) -> None:
        word = self.current_word.strip()
        if word:
            self.sentence = (self.sentence + " " + word).strip()
        self.current_word = ""

    def push_event(self, name: str, state: str, conf: float) -> bool:
        """Process one EventMsg. Returns True if display state changed."""
        with self._lock:
            self.confidence = conf
            if state == "start":
                self.active_gesture = name
                return True
            if state == "end":
                sym = GESTURE_TO_MORSE.get(name)
                if sym == ".":
                    self.morse_buffer += "."
                    self._last_activity = time.monotonic()
                elif sym == "-":
                    self.morse_buffer += "-"
                    self._last_activity = time.monotonic()
                elif sym == " ":
                    self._commit_letter()
                    self._last_activity = time.monotonic()
                self.active_gesture = "rest"
                return True
            return False  # hold — no display change

    def push_gate_ready(self, gate_ready: bool) -> bool:
        """Update calibration state. Returns True if changed."""
        with self._lock:
            changed = self.gate_ready != gate_ready
            self.gate_ready = gate_ready
            return changed

    def tick(self) -> bool:
        """Call periodically to auto-commit on inactivity. Returns True if changed."""
        with self._lock:
            elapsed = time.monotonic() - self._last_activity
            changed = False
            if self.morse_buffer and elapsed >= LETTER_COMMIT_SEC:
                self._commit_letter()
                self._last_activity = time.monotonic()
                changed = True
            elif (not self.morse_buffer) and self.current_word and elapsed >= WORD_COMMIT_SEC:
                self._commit_word()
                self._last_activity = time.monotonic()
                changed = True
            return changed

    def get_state(self) -> dict:
        with self._lock:
            buf = self.morse_buffer
            stripped = buf.strip()
            letter = MORSE_TO_LETTER.get(stripped, "") if stripped else ""
            ref = f"{letter} = {stripped}" if stripped else ""
            elapsed = time.monotonic() - self._last_activity
            countdown = round(max(0.0, 1.0 - elapsed / LETTER_COMMIT_SEC), 3) if stripped else 0.0
            return {
                "active_gesture":  self.active_gesture,
                "confidence":      round(self.confidence, 3),
                "gate_ready":      self.gate_ready,
                "morse_buffer":    buf,
                "current_letter":  letter,
                "current_word":    self.current_word,
                "sentence":        self.sentence,
                "morse_reference": ref,
                "countdown":       countdown,
            }


# ── Server ────────────────────────────────────────────────────────────────────

class MorseDashboardServer:
    """Flask + SocketIO server running in daemon threads."""

    def __init__(self, port: int = 5050, gesture_names=None) -> None:
        if not _FLASK_OK:
            raise ImportError("flask and flask-socketio are required for the web dashboard")
        self._port = port
        self._decoder = MorseDecoder()
        self._q: queue.Queue = queue.Queue(maxsize=500)
        self._running = False

        self._app = Flask(__name__)
        self._app.config["SECRET_KEY"] = "axon-morse-2025"
        self._sio = SocketIO(
            self._app,
            async_mode="threading",
            cors_allowed_origins="*",
            logger=False,
            engineio_logger=False,
        )
        self._setup_routes()

    def _setup_routes(self) -> None:
        app, sio, dec = self._app, self._sio, self._decoder

        @app.route("/")
        def index():
            return _DASHBOARD_HTML

        @app.route("/state")
        def state():
            return jsonify(dec.get_state())

        @app.route("/reset", methods=["POST"])
        def reset():
            dec.reset()
            sio.emit("state_update", dec.get_state())
            return jsonify({"ok": True})

        @sio.on("connect")
        def on_connect():
            # emit() inside an event handler targets the connecting client only
            _sio_emit("state_update", dec.get_state())

    # ── Public API ──

    def push(self, ev) -> None:
        """Enqueue an EventMsg from the inference loop (non-blocking)."""
        try:
            self._q.put_nowait(ev)
        except queue.Full:
            pass

    def push_frame(self, frame, gate_ready: bool) -> None:
        """Enqueue a FrameMsg + gate_ready flag (non-blocking)."""
        try:
            self._q.put_nowait(("__frame__", frame, gate_ready))
        except queue.Full:
            pass

    # ── Background threads ──

    def _process_loop(self) -> None:
        """Drains the event queue and updates decoder state."""
        while self._running:
            try:
                item = self._q.get(timeout=0.05)
            except queue.Empty:
                continue

            if isinstance(item, tuple) and item[0] == "__frame__":
                _, frame, gate_ready = item
                changed = self._decoder.push_gate_ready(gate_ready)
            else:
                ev = item
                if getattr(ev, "state", None) in ("start", "end"):
                    changed = self._decoder.push_event(ev.name, ev.state, ev.conf)
                else:
                    changed = False

            if changed:
                self._sio.emit("state_update", self._decoder.get_state())

    def _tick_loop(self) -> None:
        """Periodically commits on inactivity and refreshes countdown bar."""
        while self._running:
            time.sleep(0.2)
            changed = self._decoder.tick()
            state = self._decoder.get_state()
            # Always push while buffer is active (so countdown drains smoothly)
            if changed or state["morse_buffer"]:
                self._sio.emit("state_update", state)

    def start(self) -> None:
        """Start all daemon threads (non-blocking)."""
        self._running = True
        threading.Thread(target=self._process_loop, daemon=True, name="morse-proc").start()
        threading.Thread(target=self._tick_loop,    daemon=True, name="morse-tick").start()

        def _serve() -> None:
            kwargs = dict(host="0.0.0.0", port=self._port, use_reloader=False, log_output=False)
            try:
                self._sio.run(self._app, allow_unsafe_werkzeug=True, **kwargs)
            except TypeError:
                self._sio.run(self._app, **kwargs)

        threading.Thread(target=_serve, daemon=True, name="morse-flask").start()

    def stop(self) -> None:
        self._running = False