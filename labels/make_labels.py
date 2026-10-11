"""Render test labels with real regular and bold fonts, plus expected.json.

Run from the repo root:  python labels/make_labels.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent
FONTS = HERE / "fonts"
OUT = HERE / "all-test-cases"
W, H = 1200, 1600
CREAM = (245, 238, 220)
INK = (30, 24, 20)

WARNING_HEADER = "GOVERNMENT WARNING:"
WARNING_1 = ("(1) According to the Surgeon General, women should not drink alcoholic beverages during "
             "pregnancy because of the risk of birth defects.")
WARNING_2 = ("(2) Consumption of alcoholic beverages impairs your ability to drive a car or operate "
             "machinery, and may cause health problems.")


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTS / name), size)


def centered(d: ImageDraw.ImageDraw, y: int, text: str, name: str, size: int, max_w: int = 1000) -> None:
    f = font(name, size)
    while d.textlength(text, font=f) > max_w and size > 20:
        size -= 4
        f = font(name, size)
    d.text(((W - d.textlength(text, font=f)) / 2, y), text, font=f, fill=INK)


def draw_warning(d: ImageDraw.ImageDraw, y: int, header: str, body: str, header_bold: bool, body_bold: bool) -> None:
    size = 30
    fb, fr = font("DejaVuSans-Bold.ttf", size), font("DejaVuSans.ttf", size)
    words = [(w, fb if header_bold else fr) for w in header.split()]
    words += [(w, fb if body_bold else fr) for w in body.split()]
    x, left, right = 100, 100, W - 100
    for w, f in words:
        width = d.textlength(w + " ", font=f)
        if x + width > right:
            x, y = left, y + size + 14
        d.text((x, y), w, font=f, fill=INK)
        x += width


def base_canvas() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    im = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(im)
    d.rectangle((40, 40, W - 40, H - 40), outline=INK, width=6)
    return im, d


DEFAULT = dict(
    product_type="spirits", source="domestic",
    brand="OLD TOM DISTILLERY", class_type="Kentucky Straight Bourbon Whiskey",
    abv="45% Alc./Vol. (90 Proof)", net="750 mL",
    address=["Distilled and bottled by Old Tom Distillery", "Louisville, Kentucky"],
    warning=dict(header=WARNING_HEADER, body=WARNING_1 + " " + WARNING_2, header_bold=True, body_bold=False),
    app={},
    expect={},
)


def case(name: str, **kw):
    c = json.loads(json.dumps(DEFAULT))
    for k, v in kw.items():
        if isinstance(v, dict) and isinstance(c.get(k), dict):
            c[k].update(v)
        else:
            c[k] = v
    c["name"] = name
    return c


BEER = dict(product_type="malt", class_type="India Pale Ale", abv=None)
WINE = dict(product_type="wine", class_type="Red Table Wine")
FULL_APP = dict(class_type="Kentucky Straight Bourbon Whisky", alcohol_content="45% Alc./Vol. (90 Proof)",
                net_contents="750 mL")

CASES = [
    case("old_tom_clean", app=dict(FULL_APP), expect={
        "Brand name": "MATCH", "Class or type": "MATCH", "Alcohol content": "MATCH",
        "Net contents": "MATCH", "Name and address": "MATCH", "Government warning": "MATCH"}),
    case("stones_throw_case", brand="STONE'S THROW", app=dict(brand_name="Stone's Throw"),
         expect={"Brand name": "MATCH"}),
    case("stones_throw_curly", brand="Stone’s Throw", app=dict(brand_name="STONES THROW"),
         expect={"Brand name": "MATCH"}),
    case("brand_extra_letter", brand="OLD TOMS DISTILLERY", app=dict(brand_name="OLD TOM DISTILLERY"),
         expect={"Brand name": "DISAGREE"}),
    case("warn_title_case", warning=dict(header="Government Warning:"), expect={"Government warning": "DISAGREE"}),
    case("warn_reworded", warning=dict(body=WARNING_1 + " " + WARNING_2.replace("may cause health", "may cause serious health")),
         expect={"Government warning": "DISAGREE"}),
    case("warn_missing_2", warning=dict(body=WARNING_1), expect={"Government warning": "DISAGREE"}),
    case("warn_header_regular", warning=dict(header_bold=False), expect={"Government warning": "MATCH"}),
    case("warn_all_bold", warning=dict(body_bold=True), expect={"Government warning": "MATCH"}),
    case("warn_missing", warning=None, expect={"Government warning": "MISSING"}),
    case("proof_mismatch", abv="45% Alc./Vol. (80 Proof)", expect={"Alcohol content": "DISAGREE"}),
    case("abv_app_mismatch", app=dict(alcohol_content="40"), expect={"Alcohol content": "DISAGREE"}),
    case("abv_written_ABV", abv="45% ABV", expect={"Alcohol content": "LOOK"}),
    case("rum_35", class_type="Rum", abv="35% alc/vol", expect={"Alcohol content": "DISAGREE"}),
    case("whisky_spelling", app=dict(class_type="Kentucky Straight Bourbon Whisky"), expect={"Class or type": "MATCH"}),
    case("class_drops_straight", class_type="Bourbon Whiskey", app=dict(class_type="Straight Bourbon Whiskey"),
         expect={"Class or type": "DISAGREE"}),
    case("spirits_700ml", net="700 mL", expect={"Net contents": "MATCH"}),
    case("spirits_600ml", net="600 mL", expect={"Net contents": "DISAGREE"}),
    case("spirits_floz_only", net="25.4 FL OZ", expect={"Net contents": "DISAGREE"}),
    case("beer_ml_only", net="355 mL", expect={"Net contents": "DISAGREE"}, **BEER),
    case("beer_12oz_no_abv", net="12 FL. OZ.", expect={"Net contents": "MATCH", "Alcohol content": "MATCH"}, **BEER),
    case("table_wine_15", abv="Alc. 15% by vol.", expect={"Alcohol content": "DISAGREE"}, **WINE),
    case("table_wine_no_abv", abv=None, expect={"Alcohol content": "MATCH"}, **WINE),
    case("net_missing", net=None, expect={"Net contents": "LOOK"}),
    case("import_no_importer", source="imported", address=["Bottled by Old Tom Distillery", "Dublin, Ireland"],
         expect={"Name and address": "LOOK"}),
]

DEGRADED_BASES = ("old_tom_clean", "warn_title_case")
DEGRADATIONS = ("rot8", "persp", "glare", "blur", "jpeg40")


def render(c: dict) -> tuple[Image.Image, Image.Image]:
    front, d = base_canvas()
    centered(d, 260, c["brand"], "LiberationSerif-Bold.ttf", 120)
    centered(d, 520, c["class_type"], "LiberationSerif-Regular.ttf", 56)
    if c["abv"]:
        centered(d, 1200, c["abv"], "DejaVuSans.ttf", 44)
    if c["net"]:
        centered(d, 1290, c["net"], "DejaVuSans.ttf", 44)
    for i, ln in enumerate(c["address"]):
        centered(d, 1400 + i * 44, ln, "DejaVuSans.ttf", 30)
    back, bd = base_canvas()
    centered(bd, 120, "SEE FRONT LABEL", "LiberationSerif-Regular.ttf", 36)
    if c["warning"]:
        w = c["warning"]
        draw_warning(bd, 300, w["header"], w["body"], w["header_bold"], w["body_bold"])
    return front, back


def main() -> None:
    sys.path.insert(0, str(HERE))
    from degrade import degrade

    OUT.mkdir(exist_ok=True)
    expected: dict[str, dict] = {}
    for c in CASES:
        front, back = render(c)
        front.save(OUT / f"{c['name']}_front.png")
        back.save(OUT / f"{c['name']}_back.png")
        app = dict(product_type=c["product_type"], source=c["source"], brand_name=c["brand"])
        app.update(c["app"])
        expected[c["name"]] = dict(application=app, expect=c["expect"],
                                   images=[f"{c['name']}_front.png", f"{c['name']}_back.png"])
        if c["name"] in DEGRADED_BASES:
            for kind in DEGRADATIONS:
                n = f"{c['name']}_{kind}"
                ext = "jpg" if kind == "jpeg40" else "png"
                degrade(front, kind).save(OUT / f"{n}_front.{ext}", **({"quality": 40} if ext == "jpg" else {}))
                degrade(back, kind).save(OUT / f"{n}_back.{ext}", **({"quality": 40} if ext == "jpg" else {}))
                expected[n] = dict(application=app, expect={}, base=c["name"],
                                   images=[f"{n}_front.{ext}", f"{n}_back.{ext}"])
    (OUT / "expected.json").write_text(json.dumps(expected, indent=1), encoding="utf-8")
    print(f"wrote {len(expected)} cases to {OUT}")


if __name__ == "__main__":
    main()
