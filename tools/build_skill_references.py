#!/usr/bin/env python3
"""Build the skill's full course-note reference and selected image bundle."""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from urllib.parse import quote


SELECTED_IMAGES = (
    "Pasted image 20250502095312.png",
    "Pasted image 20250502100531.png",
    "Pasted image 20250502102252.png",
    "Pasted image 20250502104354.png",
    "Pasted image 20250502110035.png",
    "Pasted image 20250509202043.png",
    "Pasted image 20250509213405.png",
    "Pasted image 20250509215610.png",
    "Pasted image 20250510095552.png",
    "Pasted image 20250510184348.png",
    "Pasted image 20250510184327.png",
    "Pasted image 20250510184738.png",
    "Pasted image 20250513213300.png",
    "Pasted image 20250513213658.png",
    "Pasted image 20250513214157.png",
    "Pasted image 20250513220140.png",
    "Pasted image 20250513223236.png",
    "Pasted image 20251004223449.png",
    "Pasted image 20251004223901.png",
    "Pasted image 20251004223820.png",
    "Pasted image 20251004224138.png",
    "Pasted image 20251004224754.png",
    "Pasted image 20251002164239.png",
    "Pasted image 20251006165059.png",
)

OBSIDIAN_IMAGE = re.compile(r"!\[\[([^\]]+)\]\]")


def _validate_image_names(selected_images: tuple[str, ...]) -> None:
    if len(set(selected_images)) != len(selected_images):
        raise ValueError("selected image names must be unique")
    for name in selected_images:
        path = Path(name)
        if path.is_absolute() or path.name != name or name in {".", ".."}:
            raise ValueError(f"invalid selected image name: {name}")


def build_course_reference(
    source_note: Path,
    source_images: Path,
    destination: Path,
    selected_images: tuple[str, ...],
) -> None:
    """Generate course-notes.md and an exact selected-image directory."""
    source_note = Path(source_note)
    source_images = Path(source_images)
    destination = Path(destination)
    _validate_image_names(selected_images)

    if not source_note.is_file():
        raise FileNotFoundError(source_note)

    missing = [name for name in selected_images if not (source_images / name).is_file()]
    if missing:
        raise FileNotFoundError(f"selected source image missing: {missing[0]}")

    selected = set(selected_images)
    source_text = source_note.read_text(encoding="utf-8-sig")

    def replace_embed(match: re.Match[str]) -> str:
        name = match.group(1)
        if name in selected:
            return f"![案例图](images/{quote(name, safe='')})"
        return f"> 原图文件：{name}（未随 skill 打包）"

    generated = OBSIDIAN_IMAGE.sub(replace_embed, source_text)

    destination.mkdir(parents=True, exist_ok=True)
    images_destination = destination / "images"
    images_destination.mkdir(exist_ok=True)
    for existing in images_destination.iterdir():
        if not existing.is_file():
            raise ValueError(f"unexpected directory in generated images: {existing}")
        existing.unlink()

    for name in selected_images:
        shutil.copy2(source_images / name, images_destination / name)

    (destination / "course-notes.md").write_text(generated, encoding="utf-8")


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    build_course_reference(
        repo_root / "trend-investment.md",
        repo_root / "trend-investment-images",
        repo_root / "skills" / "tradingview-trend-investing" / "references",
        SELECTED_IMAGES,
    )
    print(f"Built course reference with {len(SELECTED_IMAGES)} selected images.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
