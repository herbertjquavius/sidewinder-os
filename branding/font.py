# Builds a TTF of the 5x7 pixel font
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen

from sprites import FONT

PX = 100  # Font units per pixel


def glyph(rows):
    # Draws each run of lit pixels as one rectangle
    pen = TTGlyphPen(None)
    for r, row in enumerate(rows):
        top, bottom = (7 - r) * PX, (6 - r) * PX
        x = 0
        while x < len(row):
            if row[x] != "#":
                x += 1
                continue
            end = x
            while end < len(row) and row[end] == "#":
                end += 1
            pen.moveTo((x * PX, bottom))
            pen.lineTo((x * PX, top))
            pen.lineTo((end * PX, top))
            pen.lineTo((end * PX, bottom))
            pen.closePath()
            x = end
    return pen.glyph()


def build_font(family, path):
    names = {ch: f"uni{ord(ch):04X}" for ch in FONT}
    cmap = {ord(ch): n for ch, n in names.items()}
    # Lowercase uses the capital shapes
    for ch in FONT:
        if ch.isalpha():
            cmap[ord(ch.lower())] = names[ch]
    glyphs = {".notdef": TTGlyphPen(None).glyph()}
    metrics = {".notdef": (6 * PX, 0)}
    for ch, n in names.items():
        glyphs[n] = glyph(FONT[ch])
        lit = [row.find("#") for row in FONT[ch] if "#" in row]
        metrics[n] = (6 * PX, min(lit) * PX if lit else 0)
    fb = FontBuilder(8 * PX, isTTF=True)
    fb.setupGlyphOrder([".notdef"] + list(names.values()))
    fb.setupCharacterMap(cmap)
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=7 * PX, descent=-PX)
    fb.setupNameTable({"familyName": family, "styleName": "Regular"})
    fb.setupOS2(sTypoAscender=7 * PX, sTypoDescender=-PX, usWinAscent=7 * PX, usWinDescent=PX)
    fb.setupPost()
    fb.save(path)
