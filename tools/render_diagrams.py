"""Рендер всех docs/diagrams/*.puml в SVG и PNG через публичный сервер Kroki.

Требует Python 3 и сеть, дополнительных пакетов не нужно (используется
только стандартная библиотека). Запуск:

    python tools/render_diagrams.py
"""

from pathlib import Path
import base64
import urllib.request
import xml.etree.ElementTree as ET
import zlib

ROOT = Path(__file__).resolve().parents[1]
DIAGRAMS_DIR = ROOT / "docs" / "diagrams"


def render(path: Path, kind: str) -> None:
    source = path.read_text(encoding="utf-8")
    compressed = zlib.compress(source.encode("utf-8"))
    encoded = base64.urlsafe_b64encode(compressed).decode("ascii")
    url = f"https://kroki.io/plantuml/{kind}/{encoded}"
    request = urllib.request.Request(
        url, headers={"User-Agent": "aps-variant-9-diagrams/1.0"}
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        data = response.read()
        if response.headers.get("X-PlantUML-Diagram-Error"):
            raise RuntimeError(response.headers["X-PlantUML-Diagram-Error"])

    if kind == "svg":
        root = ET.fromstring(data)
        if not root.tag.endswith("svg"):
            raise RuntimeError(f"Ответ сервера для {path.name} не является SVG")
        text = " ".join(root.itertext()).lower()
        if "syntax error" in text or "error line" in text:
            raise RuntimeError(f"PlantUML отклонил {path.name}")
    elif not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise RuntimeError(f"Ответ сервера для {path.name} не является PNG")

    path.with_suffix(f".{kind}").write_bytes(data)


def main() -> None:
    for path in sorted(DIAGRAMS_DIR.glob("*.puml")):
        render(path, "svg")
        render(path, "png")
        print("Отрендерено:", path.name)


if __name__ == "__main__":
    main()
