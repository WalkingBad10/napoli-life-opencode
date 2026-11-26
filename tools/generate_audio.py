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


def extra_v06() -> None:
    """Audio 0.6: traffico, mercato, motori, campanello e relazioni."""
    # Traffico urbano continuo: flusso filtrato, clacson sporadici e frenate.
    rng = np.random.default_rng(0x74726166)
    n = SR * 8
    t = np.arange(n) / SR
    raw = np.cumsum(rng.normal(0, 0.028, n))
    low = np.convolve(raw, np.ones(1200) / 1200, mode="same")
    low *= envelope(n, 0.04, 0.04)
    swell = 0.045 * np.sin(2 * np.pi * 0.16 * t) * np.sin(2 * np.pi * 0.031 * t + 0.7)
    traffic = low + swell
    for start in range(SR // 2, n - SR // 2, SR * 2):
        dur = int(SR * 0.42)
        tt = np.arange(dur) / SR
        horn = 0.075 * (np.sin(2 * np.pi * 415 * tt) + 0.45 * np.sin(2 * np.pi * 623 * tt))
        horn *= envelope(dur, 0.08, 0.55)
        traffic[start:start + dur] += horn
    write_wav("traffic.wav", traffic * 0.82)

    # Mercato: voci indistinte, banchi, cassette e piccoli tintinni.
    rng = np.random.default_rng(0x6d61726b)
    raw = rng.normal(0, 0.085, n)
    voices = np.convolve(raw, np.ones(520) / 520, mode="same")
    voices += 0.03 * np.sin(2 * np.pi * 2.7 * t) * np.sin(2 * np.pi * 0.14 * t)
    market = voices
    for _ in range(24):
        start = int(rng.integers(0, n - SR // 6))
        dur = int(SR * rng.uniform(0.04, 0.10))
        tt = np.arange(dur) / SR
        clack = rng.normal(0, 0.10, dur) * np.exp(-24 * tt)
        market[start:start + dur] += clack
    write_wav("market.wav", market * envelope(n, 0.05, 0.05) * 0.75)

    # Motore: armoniche dispari con oscillazione di regime, loop breve.
    rng = np.random.default_rng(0x656e6769)
    n = int(SR * 2.4)
    t = np.arange(n) / SR
    rpm = 48 + 10 * np.sin(2 * np.pi * 0.42 * t)
    phase = 2 * np.pi * np.cumsum(rpm) / SR
    engine = np.zeros(n)
    for k in (1, 2, 3, 4):
        engine += (0.11 / k) * np.sin(phase * k + 0.18 * k)
    engine += rng.normal(0, 0.018, n)
    write_wav("engine.wav", engine * envelope(n, 0.08, 0.08) * 0.72)

    # Scooter: due tempi acuti con booster e sibilo di scarico.
    rng = np.random.default_rng(0x73636f6f)
    n = int(SR * 1.6)
    t = np.arange(n) / SR
    f = 118 + 54 * np.exp(-2.6 * t) + 7 * np.sin(2 * np.pi * 0.9 * t)
    phase = 2 * np.pi * np.cumsum(f) / SR
    scooter = 0.12 * np.sin(phase) + 0.055 * np.sin(2 * phase) + 0.03 * np.sin(3 * phase)
    scooter += 0.035 * rng.normal(0, 1, n) * np.exp(-1.8 * t)
    write_wav("scooter.wav", scooter * envelope(n, 0.02, 0.28) * 0.78)

    # Campanello da negozio: tre colpi metallici disallineati.
    n = int(SR * 0.85)
    t = np.arange(n) / SR
    bell = np.zeros(n)
    for start, freq in ((0.00, 1046), (0.11, 1318), (0.24, 1568)):
        i0 = int(start * SR)
        dur = min(n - i0, int(SR * 0.55))
        tt = np.arange(dur) / SR
        strike = (np.sin(2 * np.pi * freq * tt)
                  + 0.38 * np.sin(2 * np.pi * freq * 2.01 * tt))
        bell[i0:i0 + dur] += 0.15 * strike * np.exp(-7 * tt)
    write_wav("shop_bell.wav", bell * envelope(n, 0.01, 0.35))

    # Relazione: accordo caldo e due note colte, senza voci né campioni.
    n = int(SR * 1.3)
    t = np.arange(n) / SR
    chord = np.zeros(n)
    for freq in (261.63, 329.63, 392.00):
        chord += 0.055 * np.sin(2 * np.pi * freq * t + 0.2)
    for start, freq in ((0.28, 523.25), (0.66, 659.25)):
        i0 = int(start * SR)
        seg = pluck(freq, 0.58, 4) * 0.13
        end = min(n, i0 + len(seg))
        chord[i0:end] += seg[:end - i0]
    write_wav("relationship.wav", chord * envelope(n, 0.06, 0.30))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ambience()
    music()
    sfx()
    extra_loops()
    extra_sfx()
    extra_v06()
    manifest = {
        "version": "0.6.0",
        "license": "Original synthetic audio generated by tools/generate_audio.py (CC0-equivalent, project-owned)",
        "sample_rate": SR,
        "files": sorted(f.name for f in OUT.glob("*.wav")),
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    total = sum(f.stat().st_size for f in OUT.glob("*.wav"))
    print(f"OK audio: {total / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
