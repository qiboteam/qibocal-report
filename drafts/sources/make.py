"""Logo drafts for Qibocal, built on the original Qibo Q.

Everything is drawn in the coordinate space of the Qibo wordmark paths
(the `flowRoot2371` group of qibo_logo.svg), so the Q is the original
outline, untouched, with the small lower-left hole filled as the two rects
of the original file fill it. Variants add a measurement motif on top.
"""

import math
import subprocess
from pathlib import Path

OUT = Path("/tmp/logo/out")
OUT.mkdir(exist_ok=True)

# --- The original glyphs -----------------------------------------------------

# Outer silhouette of the Q: ring plus the slope running out to the right.
Q_OUTER = (
    "M 221.43789,77.595414 c -1.82831,-0.788504 -32.12188,0.399305 -51.6517,-6.124563 "
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
# The same outline, with the slope cut short just past the ring: the Q alone.
Q_OUTER_SHORT = (
    "M 180.6,76.6 c -3.4,-0.8 -7.5,-2.4 -10.81,-5.13 "
    "2.4,-2.48 3.56,-5.56 3.56,-9.48 0,-8.84 -6.71135,-15.283251 -15.67135,-15.283251 "
    "-8.88,0 -15.76,6.68 -15.76,15.28 0,8.52 7.08,15.32 16,15.32 3,0 6.15135,-1.036749 "
    "8.23135,-2.476749 2.52,1.72 4.44,2.4 7,2.4 0.16,0 0.4,0 0.72,-0.04 z"
)

# The same Q with a squarer body: a rounded square in place of the ring,
# the mountain and the short slope unchanged.
Q_SQUARE_OUTER = (
    "M 151.4,46.71 H 163.9 C 169.1,46.71 173.35,50.96 173.35,56.16 V 67.4 "
    "C 174.6,71.3 178.6,75.2 184.5,76.9 L 172.6,77.31 H 151.4 "
    "C 146.2,77.31 141.92,73.03 141.92,67.83 V 56.16 C 141.92,50.96 146.2,46.71 151.4,46.71 Z"
)
Q_SQUARE_SKY = (
    "M 147.39,63.43 V 57.9 C 147.39,54.6 150.0,52.0 153.3,52.0 H 161.9 "
    "C 165.2,52.0 167.79,54.6 167.79,57.9 V 68.63 H 165.39484 "
    "c -3.6,-3.56 -8.64,-5.72 -13.36,-5.72 -1.76,0 -3.2,0.16 -4.56,0.52 Z"
)

CX, CY = 157.63, 62.0  # ring centre
R_OUT, R_IN = 15.6, 10.2

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

TOP, BASE = 55.82, 76.79  # cap height of the letters
STEM = 3.887              # stem width of the I


def polar(cx, cy, r, degrees):
    a = math.radians(degrees)
    return cx + r * math.cos(a), cy + r * math.sin(a)


def fmt(*values):
    return " ".join(f"{v:.3f}" for v in values)


# --- Letters that Qibo does not have: C, A, L in the same geometric style ----

def letter_c(x):
    """A ring like the O, open on the right."""
    R, r = 10.87, 7.12
    cx, cy = x + R, 66.32
    gap = 38
    p = []
    ox, oy = polar(cx, cy, R, gap)
    p.append(f"M {fmt(ox, oy)}")
    ex, ey = polar(cx, cy, R, 360 - gap)
    p.append(f"A {fmt(R, R)} 0 1 1 {fmt(ex, ey)}")
    ix, iy = polar(cx, cy, r, 360 - gap)
    p.append(f"L {fmt(ix, iy)}")
    jx, jy = polar(cx, cy, r, gap)
    p.append(f"A {fmt(r, r)} 0 1 0 {fmt(jx, jy)} Z")
    return " ".join(p), x + 2 * R


def letter_a(x):
    w, t = 21.4, STEM
    xm = x + w / 2
    rise = t * 2 * (BASE - TOP) / w
    outer = f"M {fmt(x, BASE)} L {fmt(xm, TOP)} L {fmt(x + w, BASE)} Z"
    inner = f"M {fmt(x + t, BASE)} L {fmt(xm, TOP + rise)} L {fmt(x + w - t, BASE)} Z"
    bar_y = 69.0
    # The bar spans the counter, with a little overlap into the legs.
    frac = (bar_y - (TOP + rise)) / (BASE - (TOP + rise))
    left = xm - frac * (xm - (x + t)) - 3.0
    right = xm + frac * ((x + w - t) - xm) + 3.0
    bar = f"M {fmt(left, bar_y)} H {fmt(right)} V {fmt(bar_y + 3.4)} H {fmt(left)} Z"
    return [f"{outer} {inner}", bar], x + w


def letter_l(x):
    w, t = 12.2, STEM
    return (
        f"M {fmt(x, TOP)} H {fmt(x + t)} V {fmt(BASE - 3.6)} H {fmt(x + w)} "
        f"V {fmt(BASE)} H {fmt(x)} Z"
    ), x + w


def cal_paths():
    c, x = letter_c(223.3)
    a, x = letter_a(x + 1.5)
    l, x = letter_l(x + 3.0)
    return [c, *a, l], x


# --- Measurement motifs, as overlays in the same space -----------------------

def ticks_outside():
    """Three ticks over the ring: the scale of a gauge."""
    parts = []
    for angle in (238, 270, 302):
        x1, y1 = polar(CX, CY, R_OUT + 1.6, angle)
        x2, y2 = polar(CX, CY, R_OUT + 5.4, angle)
        parts.append(f'<path d="M {fmt(x1, y1)} L {fmt(x2, y2)}" stroke="{{color}}" stroke-width="2.8" stroke-linecap="butt"/>')
    return "\n".join(parts)


def notches():
    """Notches cut into the ring, the scale of a dial engraved on the bezel."""
    parts = []
    for angle in (235, 252.5, 270, 287.5, 305):
        depth = 3.4 if angle in (235, 270, 305) else 2.2
        x1, y1 = polar(CX, CY, R_OUT + 0.3, angle)
        x2, y2 = polar(CX, CY, R_OUT - depth, angle)
        parts.append(f'<path d="M {fmt(x1, y1)} L {fmt(x2, y2)}" stroke="{{bg}}" stroke-width="1.5"/>')
    return "\n".join(parts)


def notches_inner():
    """The graduation drawn inside the bezel: ticks on the inner edge of the ring."""
    parts = []
    for angle in (235, 252.5, 270, 287.5, 305):
        depth = 3.0 if angle in (235, 270, 305) else 1.8
        x1, y1 = polar(CX, CY, R_IN + 0.4, angle)
        x2, y2 = polar(CX, CY, R_IN - depth, angle)
        parts.append(f'<path d="M {fmt(x1, y1)} L {fmt(x2, y2)}" stroke="{{color}}" stroke-width="1.5"/>')
    return "\n".join(parts)


def ruler(x_start, x_end, y_at, count):
    """Ticks standing on the slope: the mountain, measured."""
    parts = []
    for i in range(count):
        x = x_start + (x_end - x_start) * (i + 0.5) / count
        y = y_at(x)
        h = 3.4 if i % 2 == 0 else 2.0
        parts.append(f'<path d="M {fmt(x, y)} L {fmt(x, y + h)}" stroke="{{color}}" stroke-width="1.5"/>')
    return "\n".join(parts)


def slope_y(x):
    """The upper edge of the original slope, from the ring to its tip."""
    # Linear fit of the cubic between (169.79, 71.47) and (221.44, 77.60).
    return 77.4


def summit_point():
    """A data point with its error bar, planted on the summit."""
    x, y = 153.4, 60.2
    return (
        f'<path d="M {fmt(x, y - 3.6)} V {fmt(y + 3.6)}" stroke="{{color}}" stroke-width="1.2"/>'
        f'<path d="M {fmt(x - 1.7, y - 3.6)} H {fmt(x + 1.7)} M {fmt(x - 1.7, y + 3.6)} H {fmt(x + 1.7)}" stroke="{{color}}" stroke-width="1.2"/>'
        f'<circle cx="{x:.3f}" cy="{y:.3f}" r="1.9" fill="{{color}}"/>'
        f'<circle cx="{x:.3f}" cy="{y:.3f}" r="3.2" stroke="{{bg}}" stroke-width="1.1" fill="none"/>'
    )


def crosshair():
    """A reticle over the sky: the target of a measurement."""
    x, y = 159.4, 58.3
    r = 4.6
    return (
        f'<circle cx="{x}" cy="{y}" r="{r}" stroke="{{color}}" stroke-width="1.4" fill="none"/>'
        f'<path d="M {fmt(x - r - 1.6, y)} H {fmt(x - r + 1.8)} M {fmt(x + r - 1.8, y)} H {fmt(x + r + 1.6)} '
        f'M {fmt(x, y - r - 1.6)} V {fmt(y - r + 1.8)} M {fmt(x, y + r - 1.8)} V {fmt(y + r + 1.6)}" '
        f'stroke="{{color}}" stroke-width="1.4"/>'
    )


def ticks_outside_square():
    parts = []
    for x in (149.5, 157.63, 165.8):
        parts.append(f'<path d="M {fmt(x, 45.0)} V {fmt(41.4)}" stroke="{{color}}" stroke-width="2.8"/>')
    return "\n".join(parts)


def notches_square():
    parts = []
    for i, x in enumerate((149.5, 153.6, 157.63, 161.7, 165.8)):
        depth = 3.4 if i % 2 == 0 else 2.2
        parts.append(f'<path d="M {fmt(x, 46.4)} V {fmt(46.71 + depth)}" stroke="{{bg}}" stroke-width="1.5"/>')
    return "\n".join(parts)


SQUARE_MOTIFS = {
    "A-gauge-ticks": ticks_outside_square(),
    "B-bezel-notches": notches_square(),
    "B2-inner-notches": notches_inner(),
    "C-measured-slope": ruler(166, 184, lambda x: 77.2, 3),
    "D-summit-point": summit_point(),
    "E-reticle": crosshair(),
}


# --- Assembly ----------------------------------------------------------------

def svg(width, height, viewbox, body, bg="#ffffff", color="#000000", rounded=False):
    plate = (
        f'<rect width="{width}" height="{height}" rx="{width * 0.22:.0f}" fill="{bg}"/>'
        if rounded
        else f'<rect width="{width}" height="{height}" fill="{bg}"/>'
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
        f"{plate}<g transform=\"{viewbox}\">{body.replace('{color}', color).replace('{bg}', bg)}</g></svg>"
    )


def q_glyph(short=False, fill="{color}", square=False):
    if square:
        return f'<path fill-rule="evenodd" d="{Q_SQUARE_OUTER} {Q_SQUARE_SKY}" fill="{fill}"/>'
    outer = Q_OUTER_SHORT if short else Q_OUTER
    return f'<path fill-rule="evenodd" d="{outer} {Q_SKY}" fill="{fill}"/>'


def wordmark(motif, extended_slope=False):
    paths = [q_glyph(), f'<path d="{I_PATH}" fill="{{color}}"/>', f'<path d="{B_PATH}" fill="{{color}}"/>',
             f'<path d="{O_PATH}" fill="{{color}}"/>']
    cal, end = cal_paths()
    paths += [f'<path fill-rule="evenodd" d="{p}" fill="{{color}}"/>' for p in cal]
    if extended_slope:
        # The plain continues under CAL, at the thickness the slope reaches.
        paths.append(f'<path d="M 219.5,77.03 L {end:.2f},77.03 L {end:.2f},77.6 L 219.5,77.6 Z" fill="{{color}}"/>')
    return "\n".join(paths) + "\n" + motif, end


def render(name, markup):
    path = OUT / f"{name}.svg"
    path.write_text(markup)
    subprocess.run(["magick", "-density", "192", "-background", "none", str(path), str(OUT / f"{name}.png")], check=True)


MOTIFS = {
    "A-gauge-ticks": (ticks_outside(), ticks_outside()),
    "B-bezel-notches": (notches(), notches()),
    "B2-inner-notches": (notches_inner(), notches_inner()),
    "C-measured-slope": (ruler(175, 220, slope_y, 7), ruler(166, 184, lambda x: 77.2, 3)),
    "D-summit-point": (summit_point(), summit_point()),
    "E-reticle": (crosshair(), crosshair()),
}

# Wordmark: x 140..292, y 42..82 → scale 10.
for name, (word_motif, icon_motif) in MOTIFS.items():
    body, end = wordmark(word_motif)
    render(f"{name}-wordmark", svg(1520, 420, "translate(-1400 -420) scale(10)", body))
    # Icon: the Q alone, slope cut short, on the purple plate and in black.
    icon = q_glyph(short=True) + "\n" + icon_motif
    render(f"{name}-icon", svg(512, 512, "translate(-1241.5 -333) scale(9.5)", icon, bg="#833dff", color="#ffffff", rounded=True))
    render(f"{name}-icon-black", svg(512, 512, "translate(-1241.5 -333) scale(9.5)", icon))
    square = q_glyph(square=True) + "\n" + SQUARE_MOTIFS[name]
    render(f"{name}-icon-square", svg(512, 512, "translate(-1241.5 -333) scale(9.5)", square, bg="#833dff", color="#ffffff", rounded=True))
    render(f"{name}-icon-square-black", svg(512, 512, "translate(-1241.5 -333) scale(9.5)", square))

# The two ways the slope can meet the longer word.
body, end = wordmark(MOTIFS["A-gauge-ticks"][0], extended_slope=True)
render("slope-continued-wordmark", svg(1520, 420, "translate(-1400 -420) scale(10)", body))
body, end = wordmark("")
render("plain-wordmark", svg(1520, 420, "translate(-1400 -420) scale(10)", body))
render("plain-icon", svg(512, 512, "translate(-1241.5 -333) scale(9.5)", q_glyph(short=True), bg="#833dff", color="#ffffff", rounded=True))
render("plain-icon-square", svg(512, 512, "translate(-1241.5 -333) scale(9.5)", q_glyph(square=True), bg="#833dff", color="#ffffff", rounded=True))
print(sorted(p.name for p in OUT.iterdir()))
