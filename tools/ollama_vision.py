#!/usr/bin/env python3
"""Analisi visiva locale con un modello multimodale Ollama (qwen2.5vl).

Nessun dato lascia il computer: le immagini vengono compresse, codificate in base64 e
inviate all'API locale di Ollama su 127.0.0.1:11434.
"""

from __future__ import annotations

import argparse
import base64
import io
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from PIL import Image

DEFAULT_MODEL = "qwen2.5vl:3b"
ENDPOINT = "http://127.0.0.1:11434/api/generate"


def prepare_image(path: Path, max_side: int = 960) -> str:
    """Riduce l'immagine a un JPEG compatto; la pixel art resta leggibile."""
    with Image.open(path) as source:
        image = source.convert("RGB")
        image.thumbnail((max_side, max_side), Image.Resampling.NEAREST)
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=82, optimize=True)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def describe(image: Path, prompt: str, model: str = DEFAULT_MODEL,
             max_side: int = 960) -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "images": [prepare_image(image, max_side)],
        "stream": False,
        "options": {"temperature": 0.2},
    }
    req = Request(ENDPOINT, data=json.dumps(payload).encode("utf-8"),
                  headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(req, timeout=600) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:800]
        raise RuntimeError(f"Ollama HTTP {exc.code}: {body}") from exc
    except URLError as exc:
        raise RuntimeError(f"Ollama non raggiungibile: {exc.reason}") from exc
    return data.get("response", "").strip()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("image", type=Path)
    ap.add_argument("prompt", nargs="?", default="Descrivi questa immagine in dettaglio.")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--max-side", type=int, default=960)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    text = describe(args.image, args.prompt, args.model, args.max_side)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
