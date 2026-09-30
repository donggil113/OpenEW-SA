"""Create page-complete PDF QA contact sheets from Poppler-rendered PNGs."""

import argparse
from pathlib import Path

from PIL import Image, ImageDraw


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rendered-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    pages = sorted(args.rendered_dir.glob("page-*.png"))
    if not pages:
        raise RuntimeError("no rendered PDF pages")
    if args.out.exists():
        raise RuntimeError(f"refusing to overwrite contact sheet: {args.out}")
    columns, cell_width, cell_height, header = 3, 520, 700, 24
    rows = (len(pages) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * cell_width, rows * (cell_height + header)), "white")
    draw = ImageDraw.Draw(sheet)
    for index, path in enumerate(pages):
        with Image.open(path) as source:
            page = source.convert("RGB")
            page.thumbnail((cell_width - 12, cell_height - 12))
            x = (index % columns) * cell_width + (cell_width - page.width) // 2
            y = (index // columns) * (cell_height + header) + header
            sheet.paste(page, (x, y))
        draw.text(
            ((index % columns) * cell_width + 10, (index // columns) * (cell_height + header) + 4),
            f"Page {index + 1}",
            fill="black",
        )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.out)
    print(f"{len(pages)} pages on {args.out}")


if __name__ == "__main__":
    main()
