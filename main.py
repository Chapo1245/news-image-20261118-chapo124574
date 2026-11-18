"""news-image-20261118 — sum up 18 November 2026's world news in one image.

Reads nothing, needs no network: every pixel is drawn procedurally by
this file (a 5x7 bitmap font, flat vector icons, a hand-rolled PNG
encoder) from the eight same-day stories listed in STORIES below, all
reported on Wednesday 18 November 2026 before 05:00 UTC.

Usage:  python3 main.py            # writes entry.png to ./output/
        MAKEFUN_OUTPUT_DIR=/out python3 main.py

Deterministic: running it twice produces byte-identical output.
Requires only the Python 3.13 standard library. Runs in ~2 seconds.
"""

import math
import os
import struct
import zlib

# ------------------------------------------------------------ the news -----
# Researched from same-day reporting (18 Nov 2026, up to ~05:00 UTC).
# (region kicker, headline, one-line summary, icon key, accent colour)
STORIES = [
    ("ASIA-PACIFIC",
     "TRUMP IN MANILA FOR QUAD TALKS",
     "Quad leaders meet on security and trade, ahead of Trump's China visit.",
     "flags", (16, 90, 140)),
    ("UKRAINE WAR",
     "UKRAINE HITS CRIMEA BRIDGE",
     "Second straight day of strikes on the bridge; Russia pounds Kyiv bridges.",
     "bridge", (178, 34, 34)),
    ("GULF TENSIONS",
     "IRAN DRONES TARGET U.S. RADAR IN BAHRAIN",
     "Bahrain intercepts drones aimed at U.S. radar sites; second attack in days.",
     "drone", (120, 60, 140)),
    ("ISRAEL",
     "EISENKOT TAPPED TO LEAD ISRAEL",
     "President Herzog asks ex-army chief to form a government, bypassing Netanyahu.",
     "parliament", (14, 110, 110)),
    ("EAST ASIA",
     "N. KOREA FIRES MISSILE TO SEA",
     "Ballistic missile launches toward the Sea of Japan, Seoul reports.",
     "missile", (200, 90, 20)),
    ("TRADE",
     "CANADA, CHINA EXTEND TRADE DEALS",
     "Xi meets Carney ahead of the APEC summit in Shenzhen.",
     "trade", (30, 130, 60)),
    ("DISASTER",
     "RUSSIAN PLANE CRASH KILLS 19",
     "Military transport plane goes down in Siberia's Kemerovo region.",
     "plane", (90, 90, 100)),
    ("HEALTH",
     "U.S. MEASLES CASES HIT 40-YEAR HIGH",
     "Cases reach their highest in four decades as vaccination rates fall.",
     "virus", (200, 40, 90)),
]

# ------------------------------------------------------------ palette ------
PAPER = (247, 243, 234)   # warm newsprint
CARD = (255, 255, 255)
NAVY = (15, 42, 74)
GOLD = (217, 164, 65)
INK = (20, 20, 20)
MUTED = (90, 90, 88)
LINE = (210, 205, 195)
ICON_BG = (238, 234, 224)
WHITE = (255, 255, 255)
SUN = (230, 160, 20)
SKY = (120, 180, 220)

W, H = 1024, 1024

# ------------------------------------------------------- 5x7 bitmap font --
# Fresh 5x7 font for this entry: 7 rows of 5 cells per glyph, '#' = ink.
# All image text is uppercase, so only capitals, digits and punctuation.
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ';': ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '&': ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '$': ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    '+': ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    '=': ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    '*': ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    '#': ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
}

ADVANCE = 6  # font units per character (5 glyph + 1 spacing)


def _char_width(scale, bold):
    return (ADVANCE + (1 if bold else 0)) * scale


def _text_width(s, scale, bold=False):
    return len(s) * _char_width(scale, bold) - scale


def wrap_text(s, max_width, scale, bold=False):
    """Greedy word wrap; lines fit max_width px (bold-aware)."""
    adv = _char_width(scale, bold)

    def w(t):
        return len(t) * adv - scale

    lines, cur = [], ""
    for word in s.split(" "):
        trial = word if not cur else cur + " " + word
        if w(trial) <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- canvas --
class Canvas:
    """Plain RGB raster; every draw call is integer math, so output is
    identical on every run, machine and Python version."""

    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.pix = bytearray(w * h * 3)
        self.fill_rect(0, 0, w, h, bg)

    def set_px(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.pix[i], self.pix[i + 1], self.pix[i + 2] = c

    def fill_rect(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.pix[i], self.pix[i + 1], self.pix[i + 2] = c

    def hline(self, x0, x1, y, c, t=1):
        for yy in range(y, y + t):
            for xx in range(min(x0, x1), max(x0, x1) + 1):
                self.set_px(xx, yy, c)

    def vline(self, x, y0, y1, c, t=1):
        for xx in range(x, x + t):
            for yy in range(min(y0, y1), max(y0, y1) + 1):
                self.set_px(xx, yy, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err, x, y = dx + dy, x0, y0
        while True:
            for a in range(t):
                for b in range(t):
                    self.set_px(x + a, y + b, c)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def circle(self, cx, cy, r, c, fill=True):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d2 = (xx - cx) ** 2 + (yy - cy) ** 2
                if fill:
                    if d2 <= r * r:
                        self.set_px(xx, yy, c)
                elif r * r - 2 * r <= d2 <= r * r:
                    self.set_px(xx, yy, c)

    def triangle(self, x0, y0, x1, y1, x2, y2, c):
        minx, maxx = min(x0, x1, x2), max(x0, x1, x2)
        miny, maxy = min(y0, y1, y2), max(y0, y1, y2)

        def sign(ax, ay, bx, by, cx, cy):
            return (ax - cx) * (by - cy) - (bx - cx) * (ay - cy)

        d = sign(x0, y0, x1, y1, x2, y2)
        if d == 0:
            return
        for yy in range(miny, maxy + 1):
            for xx in range(minx, maxx + 1):
                s1 = sign(xx, yy, x0, y0, x1, y1)
                s2 = sign(xx, yy, x1, y1, x2, y2)
                s3 = sign(xx, yy, x2, y2, x0, y0)
                if d < 0:
                    ok = s1 <= 0 and s2 <= 0 and s3 <= 0
                else:
                    ok = s1 >= 0 and s2 >= 0 and s3 >= 0
                if ok:
                    self.set_px(xx, yy, c)

    def rect_border(self, x, y, w, h, c, t=2):
        self.fill_rect(x, y, w, t, c)
        self.fill_rect(x, y + h - t, w, t, c)
        self.fill_rect(x, y, t, h, c)
        self.fill_rect(x + w - t, y, t, h, c)

    # ------------------------------------------------------------ text -----
    def draw_char(self, x, y, ch, scale, c, bold=False):
        g = FONT.get(ch, FONT['?'])
        for row in range(7):
            bits = g[row]
            for col in range(5):
                if bits[col] == '1':
                    self.fill_rect(x + col * scale, y + row * scale,
                                   scale, scale, c)
                    if bold:
                        self.fill_rect(x + col * scale + scale,
                                       y + row * scale, scale, scale, c)

    def draw_text(self, x, y, s, scale, c, bold=False):
        cx = x
        for ch in s.upper():
            self.draw_char(cx, y, ch, scale, c, bold)
            cx += _char_width(scale, bold)
        return cx

    def draw_text_centered(self, cx, y, s, scale, c, bold=False):
        self.draw_text(cx - _text_width(s, scale, bold) // 2, y, s, scale,
                       c, bold)


# -------------------------------------------------------------- icons ------
def draw_icon(cv, kind, x, y, s, fg):
    """One flat pictogram per story, drawn inside the (x, y, s, s) box."""
    if kind == "flags":
        # Four summit flags on poles (Quad: US, India, Japan, Australia).
        for i, col in enumerate(((178, 34, 34), (16, 90, 140),
                                (30, 130, 60), (200, 140, 20))):
            px = x + 8 + i * (s // 4)
            cv.vline(px, y + 8, y + s - 14, fg, 3)
            cv.fill_rect(px + 3, y + 10, s // 5, s // 4, col)
            cv.fill_rect(px + 3, y + 10, s // 5, 3, WHITE)
        cv.hline(x + 6, x + s - 6, y + s - 12, fg, 3)
    elif kind == "bridge":
        # Bridge deck, two towers, cables, blast burst above the deck.
        cv.hline(x + 4, x + s - 4, y + s * 2 // 3, fg, 4)
        cv.vline(x + s // 4, y + s // 4, y + s * 2 // 3, fg, 4)
        cv.vline(x + 3 * s // 4, y + s // 4, y + s * 2 // 3, fg, 4)
        cv.line(x + s // 4, y + s // 4, x + s // 2, y + s * 2 // 3, fg, 2)
        cv.line(x + 3 * s // 4, y + s // 4, x + s // 2, y + s * 2 // 3, fg, 2)
        bx, by = x + s // 2, y + s // 3
        for dx, dy in ((-14, -6), (0, -16), (14, -6), (-12, 8), (12, 8),
                       (-4, -14), (4, -14)):
            cv.line(bx, by, bx + dx, by + dy, SUN, 3)
        cv.circle(bx, by, 5, SUN)
        for i in range(3):
            cv.hline(x + 8 + i * 6, x + s - 8 - i * 4,
                     y + s - 12 + i * 4, SKY, 2)
    elif kind == "drone":
        cx, cy = x + s // 2, y + s // 2 - 4
        cv.fill_rect(cx - 14, cy - 7, 28, 14, fg)
        for dx, dy in ((-18, -14), (18, -14), (-18, 14), (18, 14)):
            cv.line(cx, cy, cx + dx, cy + dy, fg, 2)
            cv.circle(cx + dx, cy + dy, 7, fg, fill=False)
            cv.hline(cx + dx - 10, cx + dx + 10, cy + dy, fg, 2)
        for r in (8, 15, 22):  # radar arcs, bottom right
            for a in range(0, 90, 6):
                px = int(x + s - 10 + r * math.cos(math.radians(a + 270)))
                py = int(y + s - 10 + r * math.sin(math.radians(a + 270)))
                cv.set_px(px, py, SUN)
    elif kind == "parliament":
        cv.triangle(x + 6, y + s // 3, x + s - 6, y + s // 3,
                    x + s // 2, y + 8, fg)
        for i in range(4):
            px = x + 12 + i * (s - 24) // 3
            cv.vline(px, y + s // 3 + 4, y + s - 18, fg, 5)
        cv.hline(x + 6, x + s - 6, y + s - 18, fg, 4)
        cv.hline(x + 4, x + s - 4, y + s - 12, fg, 4)
        cv.hline(x + 2, x + s - 2, y + s - 6, fg, 4)
    elif kind == "missile":
        ux, uy = 0.7071, -0.7071  # up-right
        tx, ty = x + s // 4, y + 3 * s // 4      # tail
        nx, ny = x + 3 * s // 4, y + s // 6      # nose
        cv.line(tx, ty, nx, ny, fg, 7)
        cv.line(tx, ty, nx, ny, (240, 240, 235), 3)
        cv.triangle(int(nx + ux * 12), int(ny + uy * 12),
                    int(nx - uy * 7), int(ny + ux * 7),
                    int(nx + uy * 7), int(ny - ux * 7), fg)
        cv.triangle(tx, ty, int(tx - uy * 12), int(ty + ux * 12),
                    int(tx + ux * 10), int(ty + uy * 10), fg)
        fx, fy = int(tx - ux * 22), int(ty - uy * 22)
        cv.triangle(tx, ty, int(fx - uy * 6), int(fy + ux * 6),
                    int(fx + uy * 6), int(fy - ux * 6), SUN)
        for i in range(3):
            cv.hline(x + 8 + i * 8, x + s - 8 - i * 6,
                     y + s - 12 + i * 5, SKY, 2)
    elif kind == "trade":
        cv.line(x + 10, y + s // 3, x + s - 14, y + s // 3, (178, 34, 34), 4)
        cv.triangle(x + s - 14, y + s // 3 - 7, x + s - 14, y + s // 3 + 7,
                    x + s - 4, y + s // 3, (178, 34, 34))
        cv.line(x + s - 10, y + 2 * s // 3, x + 14, y + 2 * s // 3,
                (16, 90, 140), 4)
        cv.triangle(x + 14, y + 2 * s // 3 - 7, x + 14, y + 2 * s // 3 + 7,
                    x + 4, y + 2 * s // 3, (16, 90, 140))
        cv.fill_rect(x + s // 2 - 16, y + s - 22, 14, 14, (200, 140, 20))
        cv.fill_rect(x + s // 2 + 2, y + s - 22, 14, 14, (30, 130, 60))
    elif kind == "plane":
        cv.line(x + 10, y + s // 2 - 6, x + s - 12, y + s // 2 - 14, fg, 6)
        cv.triangle(x + s - 12, y + s // 2 - 20, x + s - 12, y + s // 2 - 8,
                    x + s - 2, y + s // 2 - 14, fg)
        cv.line(x + s // 2, y + s // 2 - 10, x + s // 2 - 14, y + s - 30, fg, 5)
        cv.line(x + 16, y + s // 2 - 8, x + 8, y + s // 2 - 26, fg, 4)
        cv.triangle(x + 6, y + s - 6, x + s // 3, y + s - 26,
                    x + 2 * s // 3 - 6, y + s - 6, (140, 170, 200))
        cv.triangle(x + s // 2, y + s - 6, x + 5 * s // 6, y + s - 30,
                    x + s - 4, y + s - 6, (110, 150, 190))
    elif kind == "virus":
        cx, cy = x + s // 2, y + s // 2 - 6
        for k in range(8):
            a = math.radians(k * 45)
            dx, dy = math.cos(a), math.sin(a)
            x0, y0 = int(cx + dx * 15), int(cy + dy * 15)
            x1, y1 = int(cx + dx * 25), int(cy + dy * 25)
            cv.line(x0, y0, x1, y1, fg, 3)
            cv.circle(x1, y1, 3, fg)
        cv.circle(cx, cy, 15, (200, 40, 90))
        cv.circle(cx - 5, cy - 4, 3, WHITE)
        cv.circle(cx + 5, cy + 5, 2, WHITE)
        cv.line(x + 6, y + s - 14, x + s - 8, y + s - 26, SUN, 3)
        cv.triangle(x + s - 8, y + s - 32, x + s - 8, y + s - 20,
                    x + s - 2, y + s - 26, SUN)


# ------------------------------------------------------------ the page -----
def build(out_path):
    cv = Canvas(W, H, PAPER)

    # Masthead: the date is the biggest thing on the page.
    cv.fill_rect(0, 0, W, 176, NAVY)
    cv.fill_rect(0, 176, W, 6, GOLD)
    cv.draw_text_centered(W // 2, 22, "THE WORLD TODAY", 2, GOLD, bold=True)
    cv.draw_text_centered(W // 2, 52, "18 NOVEMBER 2026", 7, WHITE, bold=True)
    cv.draw_text_centered(W // 2, 132,
                          "WEDNESDAY  -  ONE DAY, ONE IMAGE  -  8 STORIES THAT MATTERED",
                          2, (200, 210, 225))

    # Grid: 2 columns x 4 rows, one story per card.
    mx, my, gap = 16, 196, 12
    pw = (W - 2 * mx - gap) // 2
    ph = (H - my - 34 - 3 * gap) // 4
    for idx, (kicker, headline, summary, icon, accent) in enumerate(STORIES):
        col, row = idx % 2, idx // 2
        px = mx + col * (pw + gap)
        py = my + row * (ph + gap)
        cv.fill_rect(px, py, pw, ph, CARD)
        cv.rect_border(px, py, pw, ph, LINE, 2)
        cv.fill_rect(px, py, pw, 6, accent)
        ix, iy, isz = px + 14, py + 18, 96
        cv.fill_rect(ix - 4, iy - 4, isz + 8, isz + 8, ICON_BG)
        draw_icon(cv, icon, ix, iy, isz, INK)
        tx = px + 126
        tw = pw - 126 - 14
        cv.draw_text(tx, py + 20, kicker, 2, accent, bold=True)
        ly = py + 44
        for ln in wrap_text(headline, tw, 3, bold=True)[:3]:
            cv.draw_text(tx, ly, ln, 3, INK, bold=True)
            ly += 24
        ly += 6
        for ln in wrap_text(summary, tw, 2)[:3]:
            cv.draw_text(tx, ly, ln, 2, MUTED)
            ly += 17

    cv.draw_text_centered(W // 2, H - 30,
                          "SOURCES: SAME-DAY REPORTING, 18 NOV 2026  -  DRAWN BY CODE, NO PHOTOS",
                          2, MUTED)
    return save_png(cv, out_path)


# ----------------------------------------------------------- PNG writer ----
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def save_png(canvas, path):
    """Encode the canvas as a PNG. Fixed filter (none) and fixed zlib
    level make the bytes identical on every run."""
    w, h = canvas.w, canvas.h
    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)
        raw += canvas.pix[y * stride:(y + 1) * stride]
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "output")
    size = build(os.path.join(out_dir, "entry.png"))
    print("wrote %s (%d bytes)" % (os.path.join(out_dir, "entry.png"), size))


if __name__ == "__main__":
    main()
