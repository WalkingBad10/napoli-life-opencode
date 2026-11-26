#!/usr/bin/env python3
"""Crea audio originale sintetizzato (nessun file protetto da copyright).

Ambiente: traffico leggero, uccelli, vento, treno in lontananza.
Musica: brano rilassante mediterraneo, melodia a pistico + basso + percussione tenera.
"""

from __future__ import annotations

import json
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public/assets/audio"
SR = 22050
RNG = np.random.default_rng(20261126)


def write_wav(name: str, data: np.ndarray) -> None:
    data = np.clip(data, -1.0, 1.0)
    pcm = (data * 32767).astype("<i2")
    with wave.open(str(OUT / name), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SR)
        f.writeframes(pcm.tobytes())


def envelope(n: int, attack=0.02, release=0.2):
    e = np.ones(n, dtype=float)
    a = max(1, int(n * attack))
    r = max(1, int(n * release))
    e[:a] = np.linspace(0, 1, a)
    e[-r:] = np.linspace(1, 0, r)
    return e


def pluck(freq: float, duration: float, harmonics=5):
    n = int(SR * duration)
    t = np.arange(n) / SR
    y = np.zeros(n, dtype=float)
    for k in range(1, harmonics + 1):
        y += (1 / k**1.4) * np.sin(2 * np.pi * freq * k * t + 0.15 * k)
    return y * np.exp(-3.2 * t) * envelope(n, 0.005, 0.5)


def ambience() -> None:
    n = SR * 8
    t = np.arange(n) / SR
    traffic = np.cumsum(RNG.normal(0, 0.035, n))
    traffic = traffic - np.convolve(traffic, np.ones(900) / 900, mode="same")
    traffic *= envelope(n, 0.05, 0.05)
    wind = 0.06 * np.sin(2 * np.pi * 0.11 * t) * np.sin(2 * np.pi * 0.037 * t + 1)
    train = 0.04 * np.sin(2 * np.pi * 46 * t) * (np.sin(2 * np.pi * 0.06 * t) > 0.5)
    birds = np.zeros(n)
    for _ in range(9):
        start = RNG.integers(0, n - SR // 2)
        dur = int(SR * RNG.uniform(0.08, 0.19))
        f0 = RNG.uniform(1700, 2900)
        tt = np.arange(dur) / SR
        chirp = 0.11 * np.sin(2 * np.pi * (f0 * tt + 400 * tt**2)) * envelope(dur, 0.1, 0.4)
        birds[start:start + dur] += chirp
    write_wav("ambience.wav", 0.85 * traffic + wind + train + birds)


def music() -> None:
    bars = 8
    beat = 0.52
    total = int(SR * bars * 4 * beat)
    out = np.zeros(total)
    # A minor / D dorian: melodia nostalgica, accompagnamento a pizzico
    scale = [220.00, 246.94, 261.63, 293.66, 329.63, 392.00, 440.00, 493.88]
    melody = [2, 4, 5, 4, 2, 1, 0, 2, 4, 6, 7, 6, 5, 4, 2, 1,
              2, 4, 5, 7, 6, 5, 4, 2, 1, 2, 4, 2, 1, 0, 1, 2]
    bass = [110.00, 146.83, 130.81, 98.00]
    for i, note in enumerate(melody):
        start = int(i * beat * SR)
        seg = pluck(scale[note], beat * 1.6, 4) * 0.16
        end = min(total, start + len(seg))
        out[start:end] += seg[:end - start]
    for b in range(bars):
        for k in range(4):
            start = int((b * 4 + k) * beat * SR)
            seg = pluck(bass[b % 4] * (2 if k == 3 else 1), beat * 1.2, 3) * 0.19
            end = min(total, start + len(seg))
            out[start:end] += seg[:end - start]
    # riverbero leggero (delay)
    delayed = np.zeros_like(out)
    delay = int(SR * 0.19)
    delayed[delay:] = out[:-delay] * 0.16
    delayed[delay * 2:] += out[:-delay * 2] * 0.08
    # percussione delicata (tamburello)
    for i in range(bars * 8):
        start = int(i * beat / 2 * SR)
        n = int(SR * 0.045)
        hit = RNG.normal(0, 0.05, n) * envelope(n, 0.01, 0.9)
        end = min(total, start + n)
        out[start:end] += hit[:end - start] * (0.6 if i % 2 else 1)
    write_wav("music.wav", out + delayed)


def sfx() -> None:
    n = int(SR * 0.13)
    t = np.arange(n) / SR
    step = (np.sin(2 * np.pi * 92 * t) * 0.4 + RNG.normal(0, 0.13, n)) * envelope(n, 0.05, 0.7)
    write_wav("step.wav", step * 0.45)

    n = int(SR * 0.3)
    t = np.arange(n) / SR
    coin = (np.sin(2 * np.pi * 880 * t) + 0.5 * np.sin(2 * np.pi * 1320 * t)) * np.exp(-9 * t) * envelope(n, 0.01, 0.6)
    write_wav("coin.wav", coin * 0.3)

    n = int(SR * 0.25)
    t = np.arange(n) / SR
    door = RNG.normal(0, 0.3, n) * np.exp(-14 * t) + 0.2 * np.sin(2 * np.pi * 180 * t) * envelope(n, 0.02, 0.8)
    write_wav("door.wav", door * 0.4)

    n = int(SR * 2.2)
    t = np.arange(n) / SR
    rumble = (np.sin(2 * np.pi * 58 * t) + 0.6 * np.sin(2 * np.pi * 116 * t)) * envelope(n, 0.12, 0.35)
    write_wav("train.wav", rumble * 0.22)


def extra_loops() -> None:
    """Loop ambientali aggiuntivi: ognuno ha un seed dedicato e stabile."""
    # Uccelli: soli cinguettii, senza traffico, per la fascia alba/giorno.
    rng = np.random.default_rng(0x62697264)
    n = SR * 8
    birds = np.zeros(n)
    for _ in range(16):
        start = int(rng.integers(0, n - SR // 2))
        dur = int(SR * rng.uniform(0.07, 0.16))
        f0 = rng.uniform(1900, 3200)
        tt = np.arange(dur) / SR
        chirp = 0.16 * np.sin(2 * np.pi * (f0 * tt + 520 * tt ** 2))
        birds[start:start + dur] += chirp * envelope(dur, 0.12, 0.42)
    write_wav("birds.wav", birds * envelope(n, 0.02, 0.02) * 0.75)

    # Notte: vento basso e grilli regolari, nessun rumore di traffico.
    rng = np.random.default_rng(0x6e696768)
    t = np.arange(n) / SR
    wind = 0.035 * np.sin(2 * np.pi * 0.07 * t) * np.sin(2 * np.pi * 0.023 * t + 0.6)
    crickets = np.zeros(n)
    for start in range(0, n - SR // 4, SR // 3):
        dur = SR // 5
        tt = np.arange(dur) / SR
        trill = 0.055 * np.sin(2 * np.pi * 4200 * tt) * (np.sin(2 * np.pi * 34 * tt) > 0)
        crickets[start:start + dur] += trill * envelope(dur, 0.08, 0.3)
    write_wav("night.wav", (wind + crickets) * envelope(n, 0.03, 0.03))

    # Folla: mormorio filtrato a banda larga, senza voci riconoscibili.
    rng = np.random.default_rng(0x63726f77)
    raw = rng.normal(0, 0.07, n)
    murmur = np.convolve(raw, np.ones(420) / 420, mode="same")
    murmur += 0.035 * np.sin(2 * np.pi * 2.3 * t) * np.sin(2 * np.pi * 0.11 * t)
    write_wav("crowd.wav", murmur * envelope(n, 0.06, 0.06) * 0.8)

    # Bar/pizzeria: mormorio più raccolto e piccoli tintinni di tazzine.
    rng = np.random.default_rng(0x62617220)
    raw = rng.normal(0, 0.055, n)
    room = np.convolve(raw, np.ones(620) / 620, mode="same")
    for _ in range(7):
        start = int(rng.integers(0, n - SR // 8))
        dur = int(SR * rng.uniform(0.05, 0.11))
        tt = np.arange(dur) / SR
        clink = np.sin(2 * np.pi * 1450 * tt) + 0.4 * np.sin(2 * np.pi * 2180 * tt)
        room[start:start + dur] += 0.06 * clink * np.exp(-26 * tt)
    write_wav("bar_murmur.wav", room * envelope(n, 0.05, 0.05))


def extra_sfx() -> None:
    """Effetti 0.5: cassa, pasto, riposo e interfaccia, tutti sintetizzati."""
    rng = np.random.default_rng(0x63617368)
    n = int(SR * 0.26)
    t = np.arange(n) / SR
    cash = 0.22 * np.sin(2 * np.pi * 1046 * t) * np.exp(-15 * t)
    cash += 0.13 * np.sin(2 * np.pi * 1568 * t) * np.exp(-11 * (t - 0.04).clip(0))
    cash += rng.normal(0, 0.035, n) * envelope(n, 0.01, 0.7)
    write_wav("cash.wav", cash)

    rng = np.random.default_rng(0x656174)
    n = int(SR * 0.36)
    t = np.arange(n) / SR
    eat = np.zeros(n)
    for start in range(0, n - SR // 12, SR // 9):
        dur = SR // 12
        tt = np.arange(dur) / SR
        eat[start:start + dur] += (rng.normal(0, 0.12, dur)
                                   + 0.06 * np.sin(2 * np.pi * 180 * tt)) * envelope(dur, 0.1, 0.75)
    write_wav("eat.wav", eat * 0.42)

    n = int(SR * 1.4)
    t = np.arange(n) / SR
    sleep = np.zeros(n)
    for i, freq in enumerate((392.0, 329.63, 261.63)):
        start = int(i * SR * 0.38)
        seg = pluck(freq, 0.62, 3) * 0.13
        end = min(n, start + len(seg))
        sleep[start:end] += seg[:end - start]
    sleep += 0.02 * np.sin(2 * np.pi * 0.5 * t)
    write_wav("sleep.wav", sleep * envelope(n, 0.04, 0.08))

    n = int(SR * 0.09)
    t = np.arange(n) / SR
    ui = (np.sin(2 * np.pi * 660 * t) + 0.35 * np.sin(2 * np.pi * 990 * t))
    write_wav("ui.wav", ui * np.exp(-22 * t) * 0.28)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ambience()
    music()
    sfx()
    extra_loops()
    extra_sfx()
    manifest = {
        "version": "0.5.0",
        "license": "Original synthetic audio generated by tools/generate_audio.py (CC0-equivalent, project-owned)",
        "sample_rate": SR,
        "files": sorted(f.name for f in OUT.glob("*.wav")),
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    total = sum(f.stat().st_size for f in OUT.glob("*.wav"))
    print(f"OK audio: {total / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
