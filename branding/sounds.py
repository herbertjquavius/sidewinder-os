# Cockpit sound theme: jet flyby at login, radio blips, missile lock tone
import math
import os
import wave

import numpy as np

RATE = 44100


def secs(s):
    return np.arange(int(RATE * s)) / RATE


def fade(x, attack=0.01, release=0.1):
    # Fade in and out so nothing clicks
    a, r = max(int(RATE * attack), 1), max(int(RATE * release), 1)
    x = x.copy()
    x[:a] *= np.linspace(0, 1, a)
    x[-r:] *= np.linspace(1, 0, r)
    return x


def lowpass(x, cutoff):
    # One-pole filter, the cutoff can change over time
    c = np.broadcast_to(np.asarray(cutoff, dtype=float), x.shape)
    k = 1 - np.exp(-2 * math.pi * c / RATE)
    y, a = np.zeros_like(x), 0.0
    for i in range(len(x)):
        a += k[i] * (x[i] - a)
        y[i] = a
    return y


def tone(freq, s):
    return np.sin(2 * math.pi * freq * secs(s))


def flyby():
    # Roar that opens up as the jet passes, plus an engine whine that drops in pitch
    n = secs(3.5)
    pos = (n - 1.6) / 0.6
    loud = np.exp(-pos ** 2)
    noise = np.random.default_rng(1).standard_normal(len(n))
    roar = lowpass(noise, 400 + 2600 * loud) * 3 * loud
    freq = 1400 - 600 * np.tanh(pos * 1.5)
    whine = np.sin(2 * math.pi * np.cumsum(freq) / RATE) * 0.25 * loud
    return fade(roar + whine, 0.05, 0.6)


def blip():
    # Two radio beeps and a short squelch
    a = fade(tone(1000, 0.06), 0.005, 0.01)
    b = fade(tone(1500, 0.09), 0.005, 0.02)
    sq = lowpass(np.random.default_rng(2).standard_normal(int(RATE * 0.12)), 3000) * 0.3
    sq *= np.linspace(1, 0, len(sq))
    return np.concatenate([a, np.zeros(int(RATE * 0.03)), b, sq]) * 0.6


def chirp(up=True):
    # Quick sweep, up when something plugs in, down when it's pulled
    n = secs(0.15)
    f = np.linspace(600, 1400, len(n)) if up else np.linspace(1400, 600, len(n))
    return fade(np.sin(2 * math.pi * np.cumsum(f) / RATE), 0.005, 0.03) * 0.5


def lock():
    # Sidewinder seeker growl, then the high steady tone when it locks on
    search = tone(400, 0.6) * (0.6 + 0.4 * np.sign(np.sin(2 * math.pi * 18 * secs(0.6))))
    locked = tone(1200, 0.6)
    return fade(np.concatenate([search * 0.4, locked * 0.5]), 0.01, 0.08)


def buzz():
    # Low warning buzz, twice
    one = fade(np.sign(tone(220, 0.18)) * 0.25, 0.005, 0.03)
    return np.concatenate([one, np.zeros(int(RATE * 0.08)), one])


def tick():
    return fade(tone(1500, 0.03), 0.002, 0.01) * 0.4


def save(path, x):
    # Mono 16-bit WAV
    x = np.clip(x, -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes((x * 32767 * 0.8).astype("<i2").tobytes())


def build_sounds(name, folder):
    # Freedesktop sound theme with our sounds under the standard names
    os.makedirs(os.path.join(folder, "stereo"), exist_ok=True)
    with open(os.path.join(folder, "index.theme"), "w") as f:
        f.write(f"[Sound Theme]\nName={name}\nComment=Cockpit sounds\nDirectories=stereo\n\n"
                "[stereo]\nOutputProfile=stereo\n")
    fly = flyby()
    sounds = {
        "desktop-login": fly,
        "desktop-logout": fade(fly[::-1][: int(RATE * 1.5)], 0.05, 0.4),
        "message-new-instant": blip(), "message": blip(), "dialog-information": blip(),
        "device-added": chirp(True), "power-plug": chirp(True),
        "device-removed": chirp(False), "power-unplug": chirp(False),
        "complete": lock(),
        "dialog-warning": buzz(), "dialog-error": buzz(), "bell": buzz(),
        "audio-volume-change": tick(),
    }
    for key, audio in sounds.items():
        save(os.path.join(folder, "stereo", key + ".wav"), audio)
