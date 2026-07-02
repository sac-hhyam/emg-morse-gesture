"""test_dashboard.py — Test the Morse dashboard without EMG hardware."""
import time
import sys
sys.path.insert(0, ".")

from epstudiosdk.morse_dashboard import MorseDashboardServer
from epstudiosdk.realtime_decode_udp import EventMsg

srv = MorseDashboardServer(port=5050)
srv.start()
print("Open http://localhost:5050 in your browser")
time.sleep(2)  # let Flask start

def ev(name, state, conf=0.92):
    return EventMsg("event", time.time(), 0, name, conf, state)

# Type "HI" in Morse:  H = ....   I = ..
sequence = [
    # H = . . . .
    ("thumb", "start"), ("thumb", "end"),
    ("thumb", "start"), ("thumb", "end"),
    ("thumb", "start"), ("thumb", "end"),
    ("thumb", "start"), ("thumb", "end"),
    ("fist",  "start"), ("fist",  "end"),   # fist commits H → word
    # I = . .
    ("thumb", "start"), ("thumb", "end"),
    ("thumb", "start"), ("thumb", "end"),
    # (no fist — let the 2 s inactivity timer commit I automatically)
]

print("Sending gesture sequence for 'HI' ...")
for name, state in sequence:
    srv.push(ev(name, state))
    time.sleep(0.45)

print("Waiting for inactivity timers (letter → 2 s, word → 4 s) ...")
time.sleep(8)
print("Done. Sentence zone should show: HI")