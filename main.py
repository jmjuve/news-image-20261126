#!/usr/bin/env python3
"""news-image-20261126: one front-page image summing up the world news
of Thursday 26 November 2026.

Pure Python 3 standard library only. No network, no third-party
packages, no external fonts. The picture is drawn with code -- flat
vector shapes and a hand-built 5x7 bitmap capital font -- and written
as a deterministic PNG (zlib level 9, no ancillary chunks), so every
run writes identical bytes.

Run:  python3 main.py            # writes out/entry.png
       MAKEFUN_OUTPUT_DIR=/output python3 main.py   # grader mode

Front page for Thursday 26 November 2026:
  Hero:  EU leaders meet in Brussels for a special European Council
         (26-27 Nov) -- long-term budget and a 45bn euro loan for
         Kyiv on the table; ECB leadership to be renewed. The summit
         opens today, so the image says leaders MEET today to decide
         and states no outcome.
  Minis: 100th Macy's Thanksgiving Day Parade, New York /
         India marks Constitution Day (adopted 26 Nov 1949) /
         World Chess Championship, Game 3 today in Geneva,
         Gukesh-Sindarov level 1-1.
"""

import math
import os
import struct
import zlib

W = 1024
H = 1024

CREAM = (246, 239, 221)    # newsprint
INK = (17, 17, 17)
RED = (176, 30, 30)        # lead story only
BLUE = (0, 47, 108)        # EU flag field
GOLD = (212, 175, 55)      # EU stars
SAFFRON = (255, 153, 51)   # Indian tricolour, top band
GREEN = (19, 136, 8)       # Indian tricolour, bottom band
NAVY = (6, 24, 84)         # Ashoka Chakra


# ------------------------------------------------------------------ font
# Bitmap capitals on a 5-wide by 7-tall grid. "#" is ink, "." is blank.
# One blank column follows each glyph, so the advance is 6 cells.
GLYPHS = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    ".": (".....", ".....", ".....", ".....", ".....", ".....", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    "/": ("....#", "...#.", "...#.", "..#..", ".#...", "#....", "#...."),
    "\u20ac": (".###.", "#....", "#....", "#####", "#....", "#....", ".###."),
}


def glyph_rows(ch):
    """Bitmap rows for a character."""
    return GLYPHS.get(ch)


# ---------------------------------------------------------------- canvas
class Page:
    """An RGB canvas backed by one flat bytearray."""

    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.buf = bytearray(w * h * 3)
        self.fill(0, 0, w, h, bg)

    def px(self, x, y, color):
        x = int(round(x))
        y = int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i] = color[0]
            self.buf[i + 1] = color[1]
            self.buf[i + 2] = color[2]

    def fill(self, x0, y0, x1, y1, color):
        x0 = max(0, int(x0))
        y0 = max(0, int(y0))
        x1 = min(self.w, int(x1))
        y1 = min(self.h, int(y1))
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(color) * (x1 - x0)
        for y in range(y0, y1):
            i = (y * self.w + x0) * 3
            self.buf[i:i + len(row)] = row

    def outline(self, x0, y0, x1, y1, color, t):
        self.fill(x0, y0, x1, y0 + t, color)
        self.fill(x0, y1 - t, x1, y1, color)
        self.fill(x0, y0, x0 + t, y1, color)
        self.fill(x1 - t, y0, x1, y1, color)

    def disc(self, cx, cy, r, color):
        cx = int(round(cx))
        cy = int(round(cy))
        r = int(max(1, round(r)))
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            for x in range(cx - dx, cx + dx + 1):
                self.px(x, cy + dy, color)

    def ellipse(self, cx, cy, rx, ry, color):
        cx = int(round(cx))
        cy = int(round(cy))
        rx = int(max(1, round(rx)))
        ry = int(max(1, round(ry)))
        for dy in range(-ry, ry + 1):
            dx = int(rx * (1.0 - (dy * dy) / float(ry * ry)) ** 0.5)
            for x in range(cx - dx, cx + dx + 1):
                self.px(x, cy + dy, color)

    def line(self, x0, y0, x1, y1, color, width=1):
        steps = int(max(abs(x1 - x0), abs(y1 - y0), 1))
        rad = max(1.0, width / 2.0)
        for i in range(steps + 1):
            t = i / steps
            self.disc(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, rad, color)

    def poly(self, points, color):
        """Fill a polygon with a scanline fill."""
        pts = [(int(round(x)), int(round(y))) for x, y in points]
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        for y in range(max(0, min(ys)), min(self.h, max(ys) + 1)):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                for x in range(int(xs[j]), int(xs[j + 1]) + 1):
                    self.px(x, y, color)

    def star(self, cx, cy, r_out, r_in, color):
        pts = []
        for k in range(10):
            r = r_out if k % 2 == 0 else r_in
            a = -math.pi / 2 + k * math.pi / 5
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        self.poly(pts, color)

    # ------------------------------------------------------------ text
    def text_w(self, s, size):
        return len(s) * 6.0 * size / 7.0

    def text(self, x, y, s, size, color):
        cell = size / 7.0
        pix = max(1, int(round(cell)))
        cx = float(x)
        for ch in s:
            if ch == " ":
                cx += 6 * cell
                continue
            rows = glyph_rows(ch)
            if rows is None:
                cx += 6 * cell
                continue
            for gy, row in enumerate(rows):
                for gx, mark in enumerate(row):
                    if mark == "#":
                        self.fill(cx + gx * cell, y + gy * cell,
                                  cx + gx * cell + pix, y + gy * cell + pix,
                                  color)
            cx += 6 * cell

    def centred(self, cx, y, s, size, color):
        self.text(cx - self.text_w(s, size) / 2.0, y, s, size, color)


# --------------------------------------------------------------------- png
def _chunk(tag, data):
    return (struct.pack(">I", len(data)) + tag + data +
            struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))


def write_png(path, page):
    raw = bytearray()
    for y in range(page.h):
        raw.append(0)  # filter: none
        start = y * page.w * 3
        raw += page.buf[start:start + page.w * 3]
    ihdr = struct.pack(">IIBBBBB", page.w, page.h, 8, 2, 0, 0, 0)
    data = (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr) +
            _chunk(b"IDAT", zlib.compress(bytes(raw), 9)) +
            _chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(data)


# -------------------------------------------------------------------- draw
def draw():
    p = Page(W, H, CREAM)
    p.outline(0, 0, W, H, INK, 6)

    # ---- Masthead ----------------------------------------------------
    p.centred(512, 22, "THURSDAY 26 NOVEMBER 2026", 40, INK)
    p.fill(48, 96, 976, 102, RED)       # red rule
    p.fill(48, 108, 976, 110, INK)     # hairline

    # ---- Hero panel --------------------------------------------------
    p.outline(40, 118, 984, 640, INK, 3)
    p.centred(512, 134, "BRUSSELS - SPECIAL EUROPEAN COUNCIL", 17, INK)
    p.centred(512, 162, "EU LEADERS MEET", 64, INK)
    p.centred(512, 234, "ON BUDGET AND", 64, INK)
    p.centred(512, 306, "UKRAINE", 64, RED)
    p.centred(512, 388, "27 LEADERS GATHER IN BRUSSELS TODAY", 19, INK)
    p.centred(512, 414, "LONG-TERM BUDGET AND A 45BN LOAN FOR KYIV", 19, INK)
    p.centred(512, 440, "ON THE TABLE - ECB CHIEF TO BE RENEWED", 19, INK)

    # Europa building, left: trapezoid roof, mullioned block, EU disc.
    p.poly([(92, 505), (478, 505), (448, 472), (122, 472)], INK)
    p.fill(100, 505, 470, 622, INK)
    for x in range(130, 460, 40):
        p.fill(x, 512, x + 3, 616, CREAM)
    p.fill(105, 560, 465, 563, CREAM)
    p.disc(285, 565, 40, BLUE)
    for k in range(12):
        a = -math.pi / 2 + k * math.pi / 6
        p.disc(285 + 30 * math.cos(a), 565 + 30 * math.sin(a), 3, GOLD)
    p.disc(285, 565, 4, GOLD)

    # The figure under discussion, in the lead story's red.
    p.centred(740, 505, "\u20ac45BN", 84, RED)
    p.centred(740, 600, "FOR KYIV IN 2027", 20, INK)
    p.fill(56, 624, 968, 628, INK)     # ground line

    # ---- Divider -----------------------------------------------------
    p.fill(40, 652, 984, 656, INK)
    p.fill(361, 668, 363, 1000, INK)
    p.fill(682, 668, 684, 1000, INK)

    # ---- Mini 1: Thanksgiving, New York ------------------------------
    p.centred(200, 676, "USA", 17, INK)
    p.fill(70, 706, 330, 836, INK)     # night sky over the parade route
    p.ellipse(200, 748, 64, 44, RED)   # giant balloon, red rim
    p.ellipse(200, 748, 58, 38, CREAM)
    p.line(172, 786, 188, 802, CREAM, 2)   # balloon strings
    p.line(228, 786, 212, 802, CREAM, 2)
    p.fill(185, 802, 215, 822, RED)    # basket
    p.fill(90, 802, 130, 836, CREAM)   # skyline
    p.fill(150, 792, 185, 836, CREAM)
    p.fill(240, 800, 275, 836, CREAM)
    p.fill(292, 794, 320, 836, CREAM)
    p.centred(200, 852, "100TH MACY'S", 28, INK)
    p.centred(200, 888, "PARADE", 28, INK)
    p.centred(200, 940, "THANKSGIVING DAY, USA", 15, INK)
    p.centred(200, 966, "NFL TRIPLEHEADER TODAY", 15, INK)

    # ---- Mini 2: India -----------------------------------------------
    p.centred(522, 676, "INDIA", 17, INK)
    p.fill(392, 706, 652, 749, SAFFRON)    # tricolour bands
    p.fill(392, 749, 652, 793, CREAM)
    p.fill(392, 793, 652, 836, GREEN)
    p.disc(522, 771, 26, NAVY)             # Ashoka Chakra
    p.disc(522, 771, 22, CREAM)
    for k in range(8):
        a = k * math.pi / 4
        p.line(522, 771, 522 + 21 * math.cos(a), 771 + 21 * math.sin(a),
               NAVY, 2)
    p.disc(522, 771, 4, NAVY)
    p.centred(522, 852, "INDIA MARKS", 28, INK)
    p.centred(522, 888, "CONSTITUTION", 28, INK)
    p.centred(522, 924, "DAY", 28, INK)
    p.centred(522, 966, "ADOPTED 26 NOV 1949", 15, INK)

    # ---- Mini 3: Chess, Geneva ---------------------------------------
    p.centred(834, 676, "GENEVA", 17, INK)
    p.outline(714, 706, 944, 836, INK, 3)
    bx, by, sq = 774, 710, 15
    for r in range(8):
        for col in range(8):
            if (r + col) % 2 == 0:
                p.fill(bx + col * sq, by + r * sq,
                       bx + (col + 1) * sq, by + (r + 1) * sq, INK)
    # King on a dark square, pawn on a light one.
    kx, ky = bx + 3 * sq, by + 2 * sq
    p.poly([(kx + 2, ky + 11), (kx + 2, ky + 3), (kx + 6, ky + 7),
            (kx + 7, ky + 1), (kx + 9, ky + 7), (kx + 13, ky + 3),
            (kx + 13, ky + 11)], CREAM)
    p.fill(kx + 1, ky + 11, kx + 14, ky + 14, CREAM)
    px_, py_ = bx + 5 * sq, by + 5 * sq
    p.disc(px_ + 7, py_ + 4, 3, INK)
    p.poly([(px_ + 3, py_ + 14), (px_ + 7, py_ + 6), (px_ + 12, py_ + 14)],
           INK)
    p.centred(834, 852, "CHESS: GAME 3", 26, INK)
    p.centred(834, 888, "TODAY", 28, INK)
    p.centred(834, 940, "GUKESH-SINDAROV 1-1", 15, INK)
    p.centred(834, 966, "AFTER TWO DRAWS", 15, INK)

    return p


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "out"
    os.makedirs(outdir, exist_ok=True)
    page = draw()
    path = os.path.join(outdir, "entry.png")
    write_png(path, page)
    print("wrote", path)


if __name__ == "__main__":
    main()
