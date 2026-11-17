# Pixel cursor theme in Xcursor format, anything missing falls back to Breeze
import os
import struct

# G green outline, K dark fill
ARROW = [
    "G...........",
    "GG..........",
    "GKG.........",
    "GKKG........",
    "GKKKG.......",
    "GKKKKG......",
    "GKKKKKG.....",
    "GKKKKKKG....",
    "GKKKKKKKG...",
    "GKKKKKKKKG..",
    "GKKKKKKKKKG.",
    "GKKKKKKGGGGG",
    "GKKKGKKG....",
    "GKKGGKKG....",
    "GKG..GKKG...",
    "GG...GKKG...",
    "G.....GKKG..",
    "......GKKG..",
    ".......GG...",
]
BEAM = ["GGG.GGG", "...G..."] + ["...G..."] * 12 + ["...G...", "GGG.GGG"]
RETICLE = [
    "......G......",
    ".....GGG.....",
    "...GG.G.GG...",
    "..G...G...G..",
    ".G....G....G.",
    ".G.........G.",
    "GGGG..G..GGGG",
    ".G.........G.",
    ".G....G....G.",
    "..G...G...G..",
    "...GG.G.GG...",
    ".....GGG.....",
    "......G......",
]
COLORS = {"G": 0xFF5CFF7A, "K": 0xFF0B0F14}

# Cursor file, hotspot, and the other names that point at it
CURSORS = {
    "default": (ARROW, (0, 0), ["left_ptr", "arrow", "top_left_arrow"]),
    # Pointer: same arrow, colors swapped (green fill, dark outline)
    "pointer": ([r.replace("G", "x").replace("K", "G").replace("x", "K") for r in ARROW], (0, 0),
                ["hand1", "hand2", "pointing_hand"]),
    "text": (BEAM, (3, 8), ["xterm", "ibeam"]),
    "crosshair": (RETICLE, (6, 6), ["cross", "tcross", "wait", "watch", "progress", "left_ptr_watch"]),
}
SCALES = {24: 1, 48: 2, 72: 3}


def image(rows, scale):
    # Pixels as ARGB numbers, scaled up with hard edges
    w, h = len(rows[0]) * scale, len(rows) * scale
    px = [COLORS.get(rows[y // scale][x // scale], 0) for y in range(h) for x in range(w)]
    return w, h, px


def xcursor(rows, hot, path):
    # Xcursor file with one image per size
    chunks = []
    for nominal, scale in SCALES.items():
        w, h, px = image(rows, scale)
        body = struct.pack("<9I", 36, 0xFFFD0002, nominal, 1, w, h, hot[0] * scale, hot[1] * scale, 0)
        body += struct.pack(f"<{len(px)}I", *px)
        chunks.append((nominal, body))
    header_len = 16 + 12 * len(chunks)
    out = struct.pack("<4sIII", b"Xcur", 16, 0x10000, len(chunks))
    pos, blobs = header_len, b""
    for nominal, body in chunks:
        out += struct.pack("<III", 0xFFFD0002, nominal, pos)
        pos += len(body)
        blobs += body
    with open(path, "wb") as f:
        f.write(out + blobs)


def build_cursors(name, folder):
    for rows, _, _ in CURSORS.values():
        assert len({len(r) for r in rows}) == 1, "Uneven cursor rows"
    os.makedirs(os.path.join(folder, "cursors"), exist_ok=True)
    with open(os.path.join(folder, "index.theme"), "w") as f:
        f.write(f"[Icon Theme]\nName={name} Cursors\nComment=Pixel HUD cursors\nInherits=breeze_cursors\n")
    for key, (rows, hot, aliases) in CURSORS.items():
        xcursor(rows, hot, os.path.join(folder, "cursors", key))
        for alias in aliases:
            link = os.path.join(folder, "cursors", alias)
            if not os.path.lexists(link):
                os.symlink(key, link)
