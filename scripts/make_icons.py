#!/usr/bin/env python3
"""不依賴任何套件,產生 PWA 圖示 PNG(深色底 + 白色書本圖形)。"""
import os
import struct
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BG = (91, 91, 214)      # 靛藍
BG2 = (58, 58, 160)     # 底部漸層
FG = (255, 255, 255)


def make_icon(size):
    px = bytearray()
    s = size
    for y in range(s):
        px.append(0)  # filter: none
        t = y / s
        row_bg = tuple(int(BG[i] + (BG2[i] - BG[i]) * t) for i in range(3))
        for x in range(s):
            c = row_bg
            # 白色「書本」:左右兩頁,中間書脊
            u, v = x / s, y / s
            in_book = 0.22 <= u <= 0.78 and 0.30 <= v <= 0.70
            spine = abs(u - 0.5) < 0.012
            # 頁面上的三條字行
            line = False
            if in_book and not spine:
                for ly in (0.40, 0.50, 0.60):
                    if abs(v - ly) < 0.018 and 0.27 <= u <= 0.73 and abs(u - 0.5) > 0.06:
                        line = True
            if in_book:
                c = row_bg if spine else FG
                if line:
                    c = tuple(int(ch * 0.75) for ch in BG)
            px.extend(c)
    raw = zlib.compress(bytes(px), 9)

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data +
                struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", s, s, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
            chunk(b"IDAT", raw) + chunk(b"IEND", b""))


def main():
    outdir = os.path.join(ROOT, "icons")
    os.makedirs(outdir, exist_ok=True)
    for size in (192, 512):
        path = os.path.join(outdir, f"icon-{size}.png")
        with open(path, "wb") as f:
            f.write(make_icon(size))
        print(path, os.path.getsize(path), "bytes")


if __name__ == "__main__":
    main()
