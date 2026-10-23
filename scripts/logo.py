"""Build the Qibocamp logo files from the Qibo Q.

The mark is the Q of the Qibo wordmark — ring, the flank of Kibo filling the
lower half of the counter, the slope running out as the base of the word —
with the graduation of a dial drawn on the inner edge of the ring: ticks all
the way round at a 17.5° pitch, long and short alternating, except where the
mountain would cover them. The wordmark adds QIBOCAMP, the first four letters
being Qibo's own; C and P are drawn in the same geometric style, the A as a
tent with its flag, and the M as two peaks under snow.

Everything is drawn in the coordinate space of the original `qibo_logo.svg`
paths, so the Q is that outline verbatim. Run from the repository root:

    python scripts/logo.py

It writes the documentation logos, the launcher's inline assets and icon, and
prints the favicon data URL for `frontend/index.html`.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent

# --- The original glyphs -----------------------------------------------------

# Outer silhouette of the Q: ring plus the slope running out to the right.
Q_OUTER = (
    "M 221.43789,77.595414 c -1.82831,-0.788504 -32.12188,0.399305 -51.6517,-6.124563 "
    "2.4,-2.48 3.56,-5.56 3.56,-9.48 0,-8.84 -6.71135,-15.283251 -15.67135,-15.283251 "
    "-8.88,0 -15.76,6.68 -15.76,15.28 0,8.52 7.08,15.32 16,15.32 3,0 6.15135,-1.036749 "
    "8.23135,-2.476749 2.52,1.72 4.44,2.4 7,2.4 0.16,0 0.4,0 0.72,-0.04 z"
)
# The same outline with the slope cut short just past the ring: the Q alone.
Q_OUTER_SHORT = (
    "M 180.6,76.6 c -3.4,-0.8 -7.5,-2.4 -10.81,-5.13 "
    "2.4,-2.48 3.56,-5.56 3.56,-9.48 0,-8.84 -6.71135,-15.283251 -15.67135,-15.283251 "
    "-8.88,0 -15.76,6.68 -15.76,15.28 0,8.52 7.08,15.32 16,15.32 3,0 6.15135,-1.036749 "
    "8.23135,-2.476749 2.52,1.72 4.44,2.4 7,2.4 0.16,0 0.4,0 0.72,-0.04 z"
)
# The sky: the counter above the mountain flank.
Q_SKY = (
    "M 165.39484,68.6276 c -3.6,-3.56 -8.64,-5.72 -13.36,-5.72 -1.76,0 -3.2,0.16 -4.56,0.52 "
    "-0.08,-0.72 -0.08,-1.04 -0.08,-1.4 0,-5.72 4.4,-10.04 10.2,-10.04 5.84,0 10.2,4.36 "
    "10.2,10.24 0,2.68 -0.8,4.76 -2.4,6.4 z"
)
I_PATH = "m 176.23806,76.7876 h 3.88732 V 55.81881 h -3.88732 z"
B_PATH = (
    "m 184.16299,76.7876 h 5.58978 c 2.32671,0 4.02919,-0.36887 5.30604,-1.163357 "
    "1.73085,-1.049858 2.72396,-2.922578 2.72396,-5.079044 0,-1.305229 -0.36887,-2.582083 "
    "-1.02149,-3.43332 -0.59586,-0.794487 -1.19173,-1.191731 -2.5537,-1.759221 "
    "1.67409,-0.879611 2.32671,-1.986219 2.32671,-3.944062 0,-1.957844 -0.87961,-3.603568 "
    "-2.38346,-4.568302 -1.24848,-0.794488 -2.55371,-1.021484 -5.67491,-1.021484 h -4.31293 z "
    "m 3.88731,-3.717066 v -5.362789 h 1.84434 c 2.69559,0 3.97244,0.879611 3.97244,2.752331 "
    "0,1.815971 -1.16336,2.610458 -3.88731,2.610458 z m 0,-9.164978 v -4.284557 h 1.58897 "
    "c 2.0146,0 3.00771,0.680989 3.00771,2.128091 0,1.503851 -0.99311,2.156466 -3.3482,2.156466 z"
)
O_PATH = (
    "m 210.61028,55.449941 c -6.2424,0 -11.06607,4.738549 -11.06607,10.867451 0,6.043778 "
    "4.88042,10.839077 11.0377,10.839077 6.10052,0 10.8107,-4.73855 10.8107,-10.867451 "
    "0,-5.98703 -4.7953,-10.839077 -10.78233,-10.839077 z m -0.0567,3.74544 c 3.88731,0 "
    "6.92339,3.1212 6.92339,7.150386 0,4.029185 -2.95095,7.065262 -6.92339,7.065262 "
    "-3.97244,0 -7.09364,-3.1212 -7.09364,-7.093637 0,-4.05756 3.06445,-7.122011 "
    "7.09364,-7.122011 z"
)

CX, CY = 157.63, 62.0  # ring centre
R_IN = 10.2  # inner radius of the ring
TOP, BASE = 55.82, 76.79  # cap height of the letters
STEM = 3.887  # stem width of the I


def polar(cx: float, cy: float, r: float, degrees: float) -> tuple[float, float]:
    a = math.radians(degrees)
    return cx + r * math.cos(a), cy + r * math.sin(a)


def fmt(*values: float) -> str:
    return " ".join(f"{v:.3f}" for v in values)


# --- C, A, L in the same geometric style -------------------------------------


def letter_c(x: float) -> tuple[list[str], float]:
    """A ring like the O, open on the right."""
    R, r = 10.87, 7.12
    cx, cy = x + R, 66.32
    gap = 38
    ox, oy = polar(cx, cy, R, gap)
    ex, ey = polar(cx, cy, R, 360 - gap)
    ix, iy = polar(cx, cy, r, 360 - gap)
    jx, jy = polar(cx, cy, r, gap)
    path = (
        f"M {fmt(ox, oy)} A {fmt(R, R)} 0 1 1 {fmt(ex, ey)} "
        f"L {fmt(ix, iy)} A {fmt(r, r)} 0 1 0 {fmt(jx, jy)} Z"
    )
    return [path], x + 2 * R


def letter_a(x: float) -> tuple[list[str], float]:
    """A tent: a solid triangle, its door a pointed arch, a pennant on a pole."""
    w = 21.8
    xm = x + w / 2
    tent = f"M {fmt(x, BASE)} L {fmt(xm, TOP)} L {fmt(x + w, BASE)} Z"
    dw, dh = 4.6, 9.4
    door = (
        f"M {fmt(xm - dw / 2, BASE)} Q {fmt(xm - dw / 2 + 0.3, BASE - dh * 0.6)} {fmt(xm, BASE - dh)} "
        f"Q {fmt(xm + dw / 2 - 0.3, BASE - dh * 0.6)} {fmt(xm + dw / 2, BASE)} Z"
    )
    pole_w, pole_h = 0.8, 4.6
    top = TOP - pole_h
    pole = f"M {fmt(xm - pole_w / 2, top)} H {fmt(xm + pole_w / 2)} V {fmt(TOP + 1.5)} H {fmt(xm - pole_w / 2)} Z"
    flag = f"M {fmt(xm + pole_w / 2, top)} L {fmt(xm + pole_w / 2 + 4.4, top + 1.15)} L {fmt(xm + pole_w / 2, top + 2.3)} Z"
    return [f"{tent} {door}", pole, flag], x + w


def _meet(p1, d1, p2, d2) -> tuple[float, float]:
    """Where the line through p1 along d1 crosses the line through p2 along d2."""
    det = d1[0] * d2[1] - d1[1] * d2[0]
    t = ((p2[0] - p1[0]) * d2[1] - (p2[1] - p1[1]) * d2[0]) / det
    return p1[0] + t * d1[0], p1[1] + t * d1[1]


SNOW_LINE = 0.6  # width of the line drawn round each cap of snow


def _polygon(points) -> str:
    head, *rest = points
    return f"M {fmt(*head)} " + " ".join(f"L {fmt(*point)}" for point in rest) + " Z"


def _inset(points, d: float) -> list[tuple[float, float]]:
    """A polygon with every edge moved inwards by d, its corners where the moved edges meet."""
    n = len(points)
    area = sum(points[i][0] * points[(i + 1) % n][1] - points[(i + 1) % n][0] * points[i][1] for i in range(n))
    side = 1 if area > 0 else -1
    edges = []
    for i in range(n):
        (x1, y1), (x2, y2) = points[i], points[(i + 1) % n]
        length = math.hypot(x2 - x1, y2 - y1)
        nx, ny = -side * (y2 - y1) / length, side * (x2 - x1) / length
        edges.append(((x1 + nx * d, y1 + ny * d), (x2 - x1, y2 - y1)))
    return [_meet(*edges[i - 1], *edges[i]) for i in range(n)]


def letter_m(x: float) -> tuple[list[str], float]:
    """Two peaks, rising a little above the letters, each with a cap of snow.

    The outer legs reach the base; the inner strokes meet in a valley above
    it, and a line round each cap of snow is cut out of the letter.
    """
    w, t = 25.0, 3.9
    peak_y = TOP - 1.6
    p1, p2 = (x + 5.2, peak_y), (x + w - 5.2, peak_y)
    xv = x + w / 2
    valley_top = (xv, 65.6)
    valley_bottom = (xv, 71.2)
    left_leg = (p1[0] - x, peak_y - BASE)
    right_leg = (p2[0] - (x + w), peak_y - BASE)
    down_left = (xv - p1[0], valley_top[1] - peak_y)
    down_right = (xv - p2[0], valley_top[1] - peak_y)
    inner_left = _meet((x + t, BASE), left_leg, valley_bottom, down_left)
    inner_right = _meet((x + w - t, BASE), right_leg, valley_bottom, down_right)
    path = (
        f"M {fmt(x, BASE)} L {fmt(*p1)} L {fmt(*valley_top)} L {fmt(*p2)} L {fmt(x + w, BASE)} "
        f"L {fmt(x + w - t, BASE)} L {fmt(*inner_right)} L {fmt(*valley_bottom)} "
        f"L {fmt(*inner_left)} L {fmt(x + t, BASE)} Z"
    )
    snow = []
    for peak, outer, inner in ((p1, left_leg, down_left), (p2, down_right, right_leg)):
        # The cap: an arrowhead under the summit, its sides along the slopes,
        # its lower edge notched like a snow line.
        tip_y, line_y, notch = peak[1] + 1.4, peak[1] + 9.4, 2.8
        side = line_y - tip_y
        lx = peak[0] + outer[0] / outer[1] * side + 0.8
        rx = peak[0] + inner[0] / inner[1] * side - 0.8
        cap = [(peak[0], tip_y), (lx, line_y), (peak[0], line_y - notch), (rx, line_y)]
        snow.append(cap)
    # The snow is a thin line cut out of the peak: the cap, and the cap drawn
    # a line's width inside it, both in the letter's path, so that even-odd
    # filling leaves the ring between them empty on any background.
    for cap in snow:
        path += " " + _polygon(cap) + " " + _polygon(_inset(cap, SNOW_LINE))
    return [path], x + w


def letter_p(x: float) -> tuple[list[str], float]:
    """A stem and a round bowl, the bowl as the B's."""
    t, tb = STEM, 3.6
    R = 6.4
    xr = x + 13.6 - R
    path = (
        f"M {fmt(x, TOP)} H {fmt(xr)} A {fmt(R, R)} 0 0 1 {fmt(xr, TOP + 2 * R)} "
        f"H {fmt(x + t)} V {fmt(BASE)} H {fmt(x)} Z "
        f"M {fmt(x + t, TOP + tb)} H {fmt(xr)} A {fmt(R - tb, R - tb)} 0 0 1 {fmt(xr, TOP + 2 * R - tb)} "
        f"H {fmt(x + t)} Z"
    )
    return [path], x + 13.6


def camp_paths() -> tuple[list[str], float]:
    # Gaps follow the image: the foot of the tent tucks under the C, the M
    # stands just past it, and the P a stem's width after.
    c, x = letter_c(223.3)
    a, x = letter_a(x - 0.4)
    m, x = letter_m(x + 0.8)
    p, x = letter_p(x + 2.4)
    return [*c, *a, *m, *p], x


# --- The graduation ----------------------------------------------------------


def _bezier(p0, p1, p2, p3, t):
    u = 1 - t
    return tuple(
        u**3 * a + 3 * u**2 * t * b + 3 * u * t**2 * c + t**3 * d
        for a, b, c, d in zip(p0, p1, p2, p3)
    )


def sky_polygon() -> list[tuple[float, float]]:
    """The counter above the mountain, sampled: the inner arc, then the flank."""
    points = []
    for i in range(121):
        angle = 172.0 + (400.5 - 172.0) * i / 120
        points.append(polar(CX, CY, R_IN, angle))
    for i in range(41):
        points.append(_bezier((165.39, 68.63), (161.79, 65.07), (156.75, 62.91), (152.03, 62.91), i / 40))
    for i in range(1, 41):
        points.append(_bezier((152.03, 62.91), (150.27, 62.91), (148.83, 63.07), (147.47, 63.43), i / 40))
    return points


def inside(point, polygon) -> bool:
    x, y = point
    hit = False
    for (x1, y1), (x2, y2) in zip(polygon, polygon[1:] + polygon[:1]):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            hit = not hit
    return hit


def ticks() -> str:
    """Ticks all the way round at the same pitch, minus those the mountain covers."""
    sky = sky_polygon()
    parts = []
    for i in range(-10, 11):
        angle = 270 + 17.5 * i
        depth = 3.0 if i % 2 == 0 else 1.8
        x1, y1 = polar(CX, CY, R_IN + 0.4, angle)
        x2, y2 = polar(CX, CY, R_IN - depth, angle)
        xm, ym = polar(CX, CY, R_IN - depth / 2, angle)
        if all(inside((x, y + 0.8), sky) for x, y in ((x2, y2), (xm, ym))):
            parts.append(f"M {fmt(x1, y1)} L {fmt(x2, y2)}")
    return " ".join(parts)


# --- Assembly ----------------------------------------------------------------

WORD_VIEWBOX = "141 45.5 172.5 33"
MARK_VIEWBOX = "133.63 38 48 48"


def mark_body(color: str) -> str:
    return (
        f'<path fill-rule="evenodd" fill="{color}" d="{Q_OUTER_SHORT} {Q_SKY}"/>'
        f'<path fill="none" stroke="{color}" stroke-width="1.5" d="{ticks()}"/>'
    )


def word_body(color: str) -> str:
    letters, _ = camp_paths()
    paths = [
        f'<path fill-rule="evenodd" fill="{color}" d="{Q_OUTER} {Q_SKY}"/>',
        f'<path fill="none" stroke="{color}" stroke-width="1.5" d="{ticks()}"/>',
        f'<path fill="{color}" d="{I_PATH}"/>',
        f'<path fill="{color}" d="{B_PATH}"/>',
        f'<path fill="{color}" d="{O_PATH}"/>',
    ]
    paths += [f'<path fill-rule="evenodd" fill="{color}" d="{path}"/>' for path in letters]
    return "".join(paths)


def svg(viewbox: str, body: str, *, size: str = "", comment: str = "") -> str:
    head = f"<!--\n{comment}\n-->\n" if comment else ""
    return (
        f'{head}<svg xmlns="http://www.w3.org/2000/svg" viewBox="{viewbox}"{size} role="img" aria-label="Qibocamp">\n'
        f"  {body}\n</svg>\n"
    )


ABOUT = (
    "  Generated by scripts/logo.py — do not edit by hand.\n"
    "  The Qibo Q, read as a dial: the ring, the flank of Kibo in the counter,\n"
    "  the slope as the base of the word, and the graduation on the inner edge."
)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)}")


def icon(size: int = 1024) -> str:
    """The mark in white on a black plate, Qibo's own colours, source of the icon set."""
    scale = size * 0.78 / 48
    translate_x = size / 2 - CX * scale
    translate_y = size / 2 - CY * scale
    return (
        f"<!--\n{ABOUT}\n  Source of the icon set, generated by `pnpm run icons`.\n-->\n"
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">\n'
        f'  <rect x="{size * 0.0625:.0f}" y="{size * 0.0625:.0f}" width="{size * 0.875:.0f}" height="{size * 0.875:.0f}" rx="{size * 0.203:.0f}" fill="#000000" />\n'
        f'  <g transform="translate({translate_x:.3f} {translate_y:.3f}) scale({scale:.4f})">{mark_body("#ffffff")}</g>\n'
        "</svg>\n"
    )


# The Q alone, cropped close: its outline runs from x 141.9 to 180.6 and y
# 46.7 to 77.3, so a 40-unit square round the middle of that box holds it
# with a hair to spare, as large as a tray slot allows.
TRAY_VIEWBOX = "141.25 41.95 40 40"


def tray(color: str) -> str:
    """The mark alone on nothing, for the system tray: no plate, as large as it fits.

    Black for the macOS menu bar, where it is a template image — only its
    shape counts, and the system paints it to suit a light or dark bar —
    and for light Windows taskbars; white for dark panels elsewhere.
    """
    return svg(TRAY_VIEWBOX, mark_body(color), size=' width="512" height="512"', comment=ABOUT)


def favicon() -> str:
    body = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{MARK_VIEWBOX}">{mark_body("#833dff")}</svg>'
    return "data:image/svg+xml," + quote(body, safe="=/:,; ")


def main() -> int:
    write(ROOT / "docs/assets/qibocamp_logo_dark.svg", svg(WORD_VIEWBOX, word_body("#000000"), comment=ABOUT))
    write(ROOT / "docs/assets/qibocamp_logo_light.svg", svg(WORD_VIEWBOX, word_body("#ffffff"), comment=ABOUT))
    write(ROOT / "docs/assets/qibocamp_mark.svg", svg(MARK_VIEWBOX, mark_body("#000000"), comment=ABOUT))
    # The launcher inlines these, so `currentColor` takes the colour of the page.
    write(ROOT / "launcher/src/assets/qibocamp-logo.svg", svg(WORD_VIEWBOX, word_body("currentColor"), comment=ABOUT))
    write(ROOT / "launcher/src/assets/qibocamp-mark.svg", svg(MARK_VIEWBOX, mark_body("currentColor"), comment=ABOUT))
    write(ROOT / "launcher/src-tauri/icon.svg", icon())
    # The tray glyphs; rasterised by `scripts/tray-icons.sh`, as the tray takes PNG.
    write(ROOT / "launcher/src-tauri/tray/tray-black.svg", tray("#000000"))
    write(ROOT / "launcher/src-tauri/tray/tray-white.svg", tray("#ffffff"))
    print("\nfavicon for frontend/index.html:\n" + favicon())
    return 0


if __name__ == "__main__":
    sys.exit(main())
