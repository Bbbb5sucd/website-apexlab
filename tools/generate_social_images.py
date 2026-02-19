"""Generate social media images for APEX Labs products.

Formats:
  square  1080x1080  Instagram / Facebook posts
  story   1080x1920  Instagram / WhatsApp stories
  og      1200x630   Open Graph link previews

Usage:
  python tools/generate_social_images.py --all
  python tools/generate_social_images.py --product rad-140 --product mk-677
  python tools/generate_social_images.py --site-only
  python tools/generate_social_images.py --all --dry-run
  python tools/generate_social_images.py --all --format og -v
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    from bs4 import BeautifulSoup
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
except ImportError as exc:
    print(
        f"Missing dependency: {exc.name}\n"
        "Install with:  pip install Pillow arabic-reshaper python-bidi beautifulsoup4",
        file=sys.stderr,
    )
    raise SystemExit(1)

log = logging.getLogger("social-gen")


@dataclass(frozen=True)
class ProductInfo:
    slug: str
    name_en: str
    desc_ar: str
    spec_ar: str
    price: str
    image_path: Path
    page_url: str


SIZES: list[tuple[str, tuple[int, int]]] = [
    ("square", (1080, 1080)),
    ("story", (1080, 1920)),
    ("og", (1200, 630)),
]

ARABIC_RE = re.compile(r"[\u0600-\u06FF]")


def shape_text(text: str) -> str:
    """Reshape Arabic text for correct glyph rendering in Pillow."""
    text = (text or "").strip()
    if not text:
        return ""
    if not ARABIC_RE.search(text):
        return text
    return get_display(arabic_reshaper.reshape(text))


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    value = hex_color.strip().lstrip("#")
    if len(value) != 6:
        raise ValueError(f"Expected #RRGGBB, got: {hex_color}")
    return (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))


def find_font_file(candidates: Iterable[str]) -> str:
    for candidate in candidates:
        if not candidate:
            continue
        if Path(candidate).exists():
            return candidate
    raise FileNotFoundError(
        "No usable font found among: " + ", ".join(filter(None, candidates))
    )


def load_fonts() -> tuple[str, str]:
    regular = find_font_file(
        [
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/Library/Fonts/Arial Unicode.ttf",
            "/Library/Fonts/Arial.ttf",
        ]
    )
    bold = find_font_file(
        [
            "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/Library/Fonts/Arial Bold.ttf",
        ]
    )
    log.debug("Fonts: regular=%s  bold=%s", regular, bold)
    return regular, bold


def text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> int:
    bbox = draw.textbbox((0, 0), text, font=font)
    return max(0, bbox[2] - bbox[0])


def wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    max_width: int,
    max_lines: int,
) -> list[str]:
    words = (text or "").strip().split()
    if not words:
        return []

    lines: list[str] = []
    current: list[str] = []

    for word in words:
        candidate = " ".join([*current, word]) if current else word
        if text_width(draw, shape_text(candidate), font) <= max_width:
            current.append(word)
            continue

        if current:
            lines.append(" ".join(current))
            current = [word]
        else:
            lines.append(word)

        if len(lines) >= max_lines:
            return lines

    if current and len(lines) < max_lines:
        lines.append(" ".join(current))
    return lines


def draw_text_right(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    x_right: int,
    y: int,
    fill: tuple[int, int, int, int] | tuple[int, int, int],
) -> None:
    text = shape_text(text)
    w = text_width(draw, text, font)
    draw.text((x_right - w, y), text, font=font, fill=fill)


def draw_text_left(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    x_left: int,
    y: int,
    fill: tuple[int, int, int, int] | tuple[int, int, int],
) -> None:
    draw.text((x_left, y), shape_text(text), font=font, fill=fill)


def add_background(base: Image.Image) -> None:
    w, h = base.size
    blue = hex_to_rgb("#1D4ED8")
    purple = hex_to_rgb("#8B5CF6")
    teal = hex_to_rgb("#14B8A6")

    draw = ImageDraw.Draw(base)
    draw.rectangle([0, 0, w, h], fill=blue)

    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    o = ImageDraw.Draw(overlay)
    o.ellipse(
        [-int(w * 0.35), -int(h * 0.25), int(w * 0.9), int(h * 0.85)],
        fill=(purple[0], purple[1], purple[2], 110),
    )
    o.ellipse(
        [int(w * 0.35), int(h * 0.35), int(w * 1.25), int(h * 1.2)],
        fill=(teal[0], teal[1], teal[2], 90),
    )

    for x, y, r, a in [
        (int(w * 0.18), int(h * 0.72), int(min(w, h) * 0.10), 50),
        (int(w * 0.78), int(h * 0.18), int(min(w, h) * 0.08), 45),
        (int(w * 0.58), int(h * 0.55), int(min(w, h) * 0.05), 30),
    ]:
        o.ellipse([x - r, y - r, x + r, y + r], outline=(255, 255, 255, a), width=3)

    base.alpha_composite(overlay)


def card_with_shadow(
    base: Image.Image,
    x: int,
    y: int,
    w: int,
    h: int,
    radius: int,
) -> tuple[int, int, int, int]:
    mask = Image.new("L", (w, h), 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle([0, 0, w, h], radius=radius, fill=255)

    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 130))
    shadow.putalpha(mask)
    shadow = shadow.filter(ImageFilter.GaussianBlur(24))
    base.alpha_composite(shadow, (x, y + 18))

    card = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    cd = ImageDraw.Draw(card)
    cd.rounded_rectangle(
        [0, 0, w, h],
        radius=radius,
        fill=(255, 255, 255, 40),
        outline=(255, 255, 255, 90),
        width=2,
    )
    base.alpha_composite(card, (x, y))
    return (x, y, x + w, y + h)


def contain(image: Image.Image, max_size: tuple[int, int]) -> Image.Image:
    max_w, max_h = max_size
    w, h = image.size
    scale = min(max_w / w, max_h / h)
    new_w = max(1, int(w * scale))
    new_h = max(1, int(h * scale))
    return image.resize((new_w, new_h), Image.Resampling.LANCZOS)


def parse_product_page(repo_root: Path, html_path: Path) -> ProductInfo:
    slug = html_path.stem
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8", errors="replace"), "html.parser")

    h1 = soup.select_one(".product-page-info h1")
    if not h1:
        raise ValueError(f"Missing product title (<h1>) in {html_path.name}")

    name_en = (h1.get("data-en") or h1.get_text(" ", strip=True)).strip()
    name_en = BeautifulSoup(name_en, "html.parser").get_text(" ", strip=True)

    desc = soup.select_one(".product-page-desc")
    desc_ar = (desc.get("data-ar") if desc else "") or ""

    spec = soup.select_one(".product-page-specs li span")
    spec_ar = (spec.get("data-ar") if spec else "") or ""

    price_el = soup.select_one(".product-page-price .price")
    price = (price_el.get_text(" ", strip=True) if price_el else "").strip()

    img = soup.select_one(".product-page-img img")
    if not img or not img.get("src"):
        raise ValueError(f"Missing product image in {html_path.name}")
    image_path = (html_path.parent / img["src"]).resolve()
    if not image_path.exists():
        raise FileNotFoundError(f"Product image not found: {image_path}")

    canonical = soup.select_one('link[rel="canonical"]')
    page_url = canonical.get("href", "").strip() if canonical else ""

    return ProductInfo(
        slug=slug,
        name_en=name_en,
        desc_ar=desc_ar.strip(),
        spec_ar=spec_ar.strip(),
        price=price,
        image_path=image_path,
        page_url=page_url,
    )


def render_product_image(
    product: ProductInfo,
    out_path: Path,
    size: tuple[int, int],
    kind: str,
    font_regular_path: str,
    font_bold_path: str,
) -> None:
    w, h = size
    base = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    add_background(base)
    draw = ImageDraw.Draw(base)

    white = (255, 255, 255, 255)
    white_80 = (255, 255, 255, 220)
    white_70 = (255, 255, 255, 190)
    teal = (*hex_to_rgb("#14B8A6"), 255)

    title_font = ImageFont.truetype(font_bold_path, 84 if kind == "square" else 64)
    price_font = ImageFont.truetype(font_bold_path, 76 if kind == "square" else 58)
    small_font = ImageFont.truetype(font_regular_path, 34 if kind == "square" else 28)
    tiny_font = ImageFont.truetype(font_regular_path, 26 if kind == "square" else 22)

    pad = 70 if kind == "square" else 60

    # Brand (top-left)
    apex = "APEX"
    labs = "LABS"
    draw_text_left(draw, apex, ImageFont.truetype(font_bold_path, 34), pad, pad - 10, white)
    apex_w = text_width(draw, apex, ImageFont.truetype(font_bold_path, 34))
    draw_text_left(
        draw, labs, ImageFont.truetype(font_bold_path, 34), pad + apex_w + 10, pad - 10, teal
    )

    if kind == "story":
        # Story layout: title top, image bottom
        title_font = ImageFont.truetype(font_bold_path, 86)
        price_font = ImageFont.truetype(font_bold_path, 84)
        small_font = ImageFont.truetype(font_regular_path, 36)
        tiny_font = ImageFont.truetype(font_regular_path, 28)
        pad = 70

        draw_text_left(draw, product.name_en, title_font, pad, 170, white_80)

        spec_lines = wrap_text(draw, product.spec_ar, small_font, w - pad * 2, max_lines=2)
        y = 290
        for line in spec_lines:
            draw_text_right(draw, line, small_font, w - pad, y, white_70)
            y += 48

        if product.price:
            draw_text_left(draw, product.price, price_font, pad, y + 10, white)

        card_x = 140
        card_y = 720
        card_w = w - card_x * 2
        card_h = h - card_y - 240
        card_with_shadow(base, card_x, card_y, card_w, card_h, radius=60)

        img = Image.open(product.image_path).convert("RGBA")
        img = contain(img, (card_w - 140, card_h - 140))
        base.alpha_composite(
            img, (card_x + (card_w - img.width) // 2, card_y + (card_h - img.height) // 2)
        )

        draw_text_left(draw, "apex-labs.tech", tiny_font, pad, h - 120, white_70)
        draw_text_right(draw, "للأبحاث فقط", tiny_font, w - pad, h - 120, white_70)
    else:
        # Square / OG layouts: text left, image right
        if kind == "square":
            card_x, card_y = 590, 220
            card_w, card_h = 420, 640
            text_x = pad
            text_w = 500
        else:  # og
            card_x, card_y = 720, 90
            card_w, card_h = 420, 450
            text_x = pad
            text_w = 610

        card_with_shadow(base, card_x, card_y, card_w, card_h, radius=50)

        img = Image.open(product.image_path).convert("RGBA")
        img = contain(img, (card_w - 110, card_h - 110))
        base.alpha_composite(
            img, (card_x + (card_w - img.width) // 2, card_y + (card_h - img.height) // 2)
        )

        draw_text_left(draw, product.name_en, title_font, text_x, 230 if kind == "square" else 160, white_80)

        y = 340 if kind == "square" else 255
        if product.desc_ar:
            desc_lines = wrap_text(draw, product.desc_ar, tiny_font, text_w, max_lines=3)
            for line in desc_lines:
                draw_text_right(draw, line, tiny_font, text_x + text_w, y, white_70)
                y += 40

        if product.spec_ar:
            y += 10
            spec_lines = wrap_text(draw, product.spec_ar, small_font, text_w, max_lines=2)
            for line in spec_lines:
                draw_text_right(draw, line, small_font, text_x + text_w, y, white_70)
                y += 46

        if product.price:
            draw_text_left(draw, product.price, price_font, text_x, y + 18, white)

        draw_text_left(draw, "apex-labs.tech", tiny_font, pad, h - 90, white_70)
        draw_text_right(draw, "للأبحاث فقط", tiny_font, w - pad, h - 90, white_70)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    base.convert("RGB").save(out_path, quality=92, optimize=True, subsampling=1)


def parse_site_tagline(repo_root: Path) -> str:
    index_path = repo_root / "index.html"
    if not index_path.exists():
        return "مكملات رياضية ومركبات بحثية"
    soup = BeautifulSoup(index_path.read_text(encoding="utf-8", errors="replace"), "html.parser")
    meta = soup.select_one('meta[property="og:description"]') or soup.select_one('meta[name="description"]')
    content = (meta.get("content") if meta else "") or ""
    return content.strip() or "مكملات رياضية ومركبات بحثية"


def render_site_image(
    out_path: Path,
    size: tuple[int, int],
    kind: str,
    font_regular_path: str,
    font_bold_path: str,
    tagline_ar: str,
) -> None:
    w, h = size
    base = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    add_background(base)
    draw = ImageDraw.Draw(base)

    white = (255, 255, 255, 255)
    white_80 = (255, 255, 255, 220)
    white_70 = (255, 255, 255, 190)
    teal = (*hex_to_rgb("#14B8A6"), 255)

    title_font = ImageFont.truetype(font_bold_path, 110 if kind == "square" else 86)
    small_font = ImageFont.truetype(font_regular_path, 40 if kind == "square" else 30)
    tiny_font = ImageFont.truetype(font_regular_path, 28 if kind == "square" else 22)

    pad = 80 if kind == "square" else 70

    # Big brand mark
    draw_text_left(draw, "APEX", title_font, pad, int(h * 0.28), white)
    apex_w = text_width(draw, "APEX", title_font)
    draw_text_left(draw, "LABS", title_font, pad + apex_w + 20, int(h * 0.28), teal)

    # Arabic tagline under
    lines = wrap_text(draw, tagline_ar, small_font, w - pad * 2, max_lines=3)
    y = int(h * 0.28) + 150
    for line in lines:
        draw_text_right(draw, line, small_font, w - pad, y, white_80)
        y += 56

    draw_text_left(draw, "apex-labs.tech", tiny_font, pad, h - 90, white_70)
    draw_text_right(draw, "للأبحاث فقط", tiny_font, w - pad, h - 90, white_70)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    base.convert("RGB").save(out_path, quality=92, optimize=True, subsampling=1)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    out_dir_default = repo_root / "assets" / "social"

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--out", default=str(out_dir_default), help="Output directory (default: assets/social)")
    parser.add_argument("--all", action="store_true", help="Generate for all products + site")
    parser.add_argument("--product", action="append", default=[], help="Product slug(s), e.g. rad-140")
    parser.add_argument("--site-only", action="store_true", help="Only generate site branding images")
    parser.add_argument("--dry-run", action="store_true", help="Show planned output without writing files")
    parser.add_argument(
        "--format",
        choices=["square", "story", "og"],
        default=None,
        help="Generate only one format (default: all three)",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose / debug output")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(message)s",
    )

    out_dir = Path(args.out).resolve()
    sizes = [(k, s) for k, s in SIZES if args.format is None or k == args.format]

    try:
        font_regular_path, font_bold_path = load_fonts()
    except FileNotFoundError as exc:
        log.error("Font error: %s", exc)
        return 1

    generated = 0
    errors = 0
    t0 = time.monotonic()

    # --- Site images ---
    tagline = parse_site_tagline(repo_root)
    if args.all or args.site_only or (not args.product and not args.all):
        for kind, size in sizes:
            dest = out_dir / f"site-{kind}.jpg"
            if args.dry_run:
                log.info("[dry-run]  site-%-6s  %4dx%-4d  -> %s", kind, *size, dest.relative_to(repo_root))
            else:
                render_site_image(
                    out_path=dest,
                    size=size,
                    kind=kind,
                    font_regular_path=font_regular_path,
                    font_bold_path=font_bold_path,
                    tagline_ar=tagline,
                )
                log.info("OK  site-%-6s  %4dx%-4d  -> %s", kind, *size, dest.relative_to(repo_root))
            generated += 1

    if args.site_only:
        _summary(generated, errors, t0)
        return 0

    # --- Product images ---
    products_dir = repo_root / "products"
    if args.all:
        html_files = sorted(products_dir.glob("*.html"))
    else:
        wanted = {slug.strip() for slug in args.product if slug.strip()}
        if not wanted:
            _summary(generated, errors, t0)
            return 0
        html_files = [products_dir / f"{slug}.html" for slug in sorted(wanted)]

    for html in html_files:
        if not html.exists():
            log.error("ERROR  product page not found: %s", html.name)
            errors += 1
            continue

        try:
            product = parse_product_page(repo_root, html)
        except (ValueError, FileNotFoundError) as exc:
            log.error("ERROR  %s — %s", html.name, exc)
            errors += 1
            continue

        for kind, size in sizes:
            dest = out_dir / f"{product.slug}-{kind}.jpg"
            label = f"{product.slug}-{kind}"
            if args.dry_run:
                log.info("[dry-run]  %-22s  %4dx%-4d  -> %s", label, *size, dest.relative_to(repo_root))
            else:
                try:
                    render_product_image(
                        product=product,
                        out_path=dest,
                        size=size,
                        kind=kind,
                        font_regular_path=font_regular_path,
                        font_bold_path=font_bold_path,
                    )
                    log.info("OK  %-22s  %4dx%-4d  -> %s", label, *size, dest.relative_to(repo_root))
                except Exception as exc:
                    log.error("ERROR  %-22s  %s", label, exc)
                    errors += 1
                    continue
            generated += 1

    _summary(generated, errors, t0)
    return 1 if errors else 0


def _summary(generated: int, errors: int, t0: float) -> None:
    elapsed = time.monotonic() - t0
    parts = [f"{generated} image(s) in {elapsed:.1f}s"]
    if errors:
        parts.append(f"{errors} error(s)")
    log.info("Done — %s", ", ".join(parts))


if __name__ == "__main__":
    raise SystemExit(main())
