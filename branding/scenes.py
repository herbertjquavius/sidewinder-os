# Extra pixel art wallpapers, drawn at 640x360 and scaled up later
import math
import random

from PIL import Image

from sprites import JET_FRONT, JET_SIDE, JET_TOP_HALF, P

W, H = 640, 360
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) + (255,)


def new():
    img = Image.new("RGBA", (W, H))
    return img, img.load()


def sky(px, colors, horizon):
    # Dithered color bands from the top down to the horizon
    cols = [rgb(c) for c in colors]
    for y in range(H):
        t = min(y / horizon, 1) * (len(cols) - 1)
        i = min(int(t), len(cols) - 2)
        f = t - i
        for x in range(W):
            px[x, y] = cols[i + 1] if f * 16 > BAYER[y % 4][x % 4] else cols[i]


def disc(px, cx, cy, r, top, bot):
    # Sun or moon with a dithered top to bottom blend
    a, b = rgb(top), rgb(bot)
    for y in range(cy - r, cy + r):
        k = (y - (cy - r)) / (2 * r)
        for x in range(cx - r, cx + r):
            if 0 <= x < W and 0 <= y < H and (x - cx) ** 2 + (y - cy) ** 2 < r * r:
                px[x, y] = b if k * 16 > BAYER[y % 4][x % 4] else a


def blob(px, cx, cy, w, h, light, dark):
    # Flat pixel cloud, lighter on top
    for y in range(cy - h, cy + h):
        for x in range(cx - w, cx + w):
            if 0 <= x < W and 0 <= y < H and ((x - cx) / w) ** 2 + ((y - cy) / h) ** 2 < 1:
                px[x, y] = rgb(light if y < cy - h // 3 else dark)


def jet(img, px, x, y, body, trail=None, trail_from=0, scale=1):
    # Side view jet with afterburner and a fading contrail
    if trail:
        ty = y + 5 * scale
        for tx in range(trail_from, x):
            near = (tx - trail_from) / max(x - trail_from, 1)
            if near * 17 > BAYER[ty % 4][tx % 4] + 1:
                for s in range(scale):
                    px[tx, ty + s] = rgb(trail)
    spr = Image.new("RGBA", (len(JET_SIDE[0]), len(JET_SIDE)), (0, 0, 0, 0))
    for yy, row in enumerate(JET_SIDE):
        for xx, c in enumerate(row):
            if c in "XA":
                spr.putpixel((xx, yy), rgb(body if c == "X" else P["R"]))
    if scale > 1:
        spr = spr.resize((spr.width * scale, spr.height * scale), Image.NEAREST)
    img.alpha_composite(spr, (x, y))


def night_intercept(seed=11):
    # Moonlit night over a city, two jets climbing out on afterburner
    rnd = random.Random(seed)
    img, px = new()
    sky(px, ["#03050a", "#070b16", "#0c1326", "#121c36", "#1a2647", "#243158", "#33406b"], 300)
    for _ in range(320):
        px[rnd.randrange(W), rnd.randrange(260)] = rgb("#9fb0d9" if rnd.random() < 0.7 else "#e8eeff")
    # Bright stars with a little cross
    for _ in range(12):
        x, y = rnd.randrange(2, W - 2), rnd.randrange(2, 200)
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            px[x + dx, y + dy] = rgb("#ffffff")
    disc(px, 150, 85, 28, "#f2f4fa", "#c9d0e2")
    for cx, cy, r in ((142, 78, 5), (160, 95, 4), (150, 101, 3), (165, 74, 3)):
        disc(px, cx, cy, r, "#b4bccf", "#a3abc0")
    for _ in range(5):
        blob(px, rnd.randrange(W), rnd.randrange(170, 260), rnd.randrange(40, 110), rnd.randrange(2, 5), "#2c3760", "#222b4d")
    # City skyline with lit windows
    x = 0
    while x < W:
        bw, bh = rnd.randrange(6, 22), rnd.randrange(8, 46)
        xe, top = min(x + bw, W), 330 - bh
        for yy in range(top, H):
            for xx in range(x, xe):
                px[xx, yy] = rgb("#070912")
        if xe - x > 2:
            for _ in range(bw * bh // 18):
                px[rnd.randrange(x + 1, xe - 1), rnd.randrange(top + 2, 330)] = rgb(rnd.choice(["#ffb000", "#ffd36e", "#7fb2ff"]))
        x += bw + rnd.randrange(0, 3)
    for jx, jy in ((400, 120), (370, 136)):
        jet(img, px, jx, jy, "#2a3352", trail="#5b6696", trail_from=120)
        for dx, c in ((-1, P["Y"]), (-2, P["R"]), (-3, P["R"])):
            px[jx + dx, jy + 4] = rgb(c)
            px[jx + dx, jy + 5] = rgb(c)
    return img.convert("RGB")


def cloud_deck(seed=21):
    # Bright day above a sea of clouds, a three ship formation
    rnd = random.Random(seed)
    img, px = new()
    sky(px, ["#123a6b", "#1a4f8b", "#2a6aa8", "#3d86c4", "#5aa2d8", "#7fbde6", "#b5dbf2"], 240)
    disc(px, 520, 60, 16, "#fffbe8", "#ffeeb0")
    for _ in range(6):
        blob(px, rnd.randrange(W), rnd.randrange(40, 150), rnd.randrange(30, 80), rnd.randrange(2, 4), "#e6f2fb", "#cfe3f3")
    # Cloud sea in layers, back to front
    for base, n, light, dark in ((235, 26, "#dfeaf5", "#b9cbe0"), (268, 22, "#eef4fa", "#c6d4e6"), (308, 18, "#ffffff", "#d5e0ee")):
        for y in range(base + 6, H):
            for x in range(W):
                px[x, y] = rgb(dark)
        for x0 in range(-20, W + 20, W // n):
            blob(px, x0 + rnd.randrange(-8, 8), base + rnd.randrange(-6, 6),
                 rnd.randrange(22, 40), rnd.randrange(10, 20), light, dark)
    for jx, jy in ((260, 150), (232, 164), (204, 178)):
        jet(img, px, jx, jy, "#3a4450", trail="#ffffff", trail_from=40)
    return img.convert("RGB")


def desert_run(seed=33):
    # Low pass over desert mesas, the jet's shadow racing across the sand
    rnd = random.Random(seed)
    img, px = new()
    sky(px, ["#2f6fb0", "#4a88c4", "#6aa2d4", "#8fbbe0", "#b8d2e4", "#e6d6b6", "#f0c38a"], 230)
    disc(px, 110, 55, 18, "#fffdf0", "#fff1c2")

    def mesas(base, color, count):
        # Flat topped rocks with steep sides
        for _ in range(count):
            cx, w, h = rnd.randrange(W), rnd.randrange(30, 90), rnd.randrange(15, 45)
            for x in range(cx - w // 2, cx + w // 2):
                if 0 <= x < W:
                    edge = min(x - (cx - w // 2), (cx + w // 2) - x)
                    for y in range(base - h + max(0, 6 - edge) * 2, base + 1):
                        px[x, y] = rgb(color)

    mesas(232, "#b9876a", 6)
    # Sand with dune bands
    for y in range(230, H):
        for x in range(W):
            d = math.sin(y / 2.5 + math.sin(x / 45) * 3 + math.sin(x / 17) * 0.6)
            px[x, y] = rgb("#e2b077" if d > 0.3 else "#d39b5d" if d > -0.6 else "#b97d43")
    mesas(252, "#9a6247", 4)
    blob(px, 410, 300, 30, 3, "#a06a36", "#a06a36")
    jet(img, px, 380, 190, "#4a525e", scale=2)
    return img.convert("RGB")


def sprite(rows, colors, scale=1):
    # Rows of letters to an image, letters missing from colors stay clear
    img = Image.new("RGBA", (len(rows[0]), len(rows)), (0, 0, 0, 0))
    for yy, row in enumerate(rows):
        for xx, c in enumerate(row):
            if c in colors:
                img.putpixel((xx, yy), colors[c] if isinstance(colors[c], tuple) else rgb(colors[c]))
    return img.resize((img.width * scale, img.height * scale), Image.NEAREST) if scale > 1 else img


def sea_patrol(seed=44):
    # Looking straight down on two jets over tropical islands, shadows on the water
    rnd = random.Random(seed)
    img, px = new()
    deep, mid = rgb("#0e3a5c"), rgb("#145076")
    for y in range(H):
        for x in range(W):
            d = math.sin(x / 53 + math.sin(y / 31) * 2) + math.sin(y / 23 - x / 71)
            px[x, y] = mid if (d + 2) * 4 > BAYER[y % 4][x % 4] + 6 else deep
    # Islands: shallows, beach, jungle
    for cx, cy, s in ((120, 260, 1.2), (520, 80, 0.9), (560, 300, 0.6)):
        parts = [(cx + rnd.randrange(-30, 30), cy + rnd.randrange(-20, 20)) for _ in range(4)]
        for layer, (light, dark), grow in ((0, ("#3aa6c4", "#2a8bb0"), 18), (1, ("#f0dfa8", "#d9c08a"), 6), (2, ("#4f8f45", "#2f6630"), 0)):
            for px_, py_ in parts:
                blob(px, px_, py_, int((34 + grow) * s), int((22 + grow) * s), light, dark)
    # Whitecaps on open water
    for _ in range(140):
        x, y = rnd.randrange(W - 4), rnd.randrange(H)
        if px[x, y] in (deep, mid):
            for dx in range(rnd.randrange(2, 5)):
                px[x + dx, y] = rgb("#7fc4e0")
    # Jets nose to the right, shadows offset below
    top = [r + r[::-1] for r in JET_TOP_HALF]
    jet_img = sprite(top, P, 2).rotate(-90, expand=True)
    shade = sprite(top, {k: (8, 30, 48, 150) for k in P}, 2).rotate(-90, expand=True)
    for jx, jy in ((300, 120), (230, 175)):
        for t in range(jx - 160, jx + 2):
            # Two thin contrails from the engine
            if (t - jx + 160) * 17 / 160 > BAYER[jy % 4][t % 4] + 1:
                px[t, jy + 30] = rgb("#e8f4fa")
                px[t, jy + 33] = rgb("#e8f4fa")
        img.alpha_composite(shade, (jx + 40, jy + 60))
        img.alpha_composite(jet_img, (jx, jy))
    return img.convert("RGB")


def head_on(seed=55):
    # Four ship diamond coming straight at you out of the dawn
    rnd = random.Random(seed)
    img, px = new()
    sky(px, ["#1b1036", "#2c1850", "#4a2368", "#7a3576", "#b44f72", "#e47c62", "#f6b35e"], 270)
    disc(px, 320, 268, 60, "#ffd88a", "#ff9f5a")
    for _ in range(6):
        blob(px, rnd.randrange(W), rnd.randrange(150, 250), rnd.randrange(40, 100), rnd.randrange(3, 6), "#c46a7a", "#8e4470")
    for base, amp, color in ((262, 22, "#3a1f4a"), (300, 18, "#24163a"), (335, 8, "#120c22")):
        ph = rnd.uniform(0, 6.28)
        for x in range(W):
            h = int(base - amp * (0.6 * math.sin(x / 83 + ph) + 0.4 * math.sin(x / 29 + ph * 2)))
            for y in range(max(h, 0), H):
                px[x, y] = rgb(color)
    colors = {"X": "#1a1d2e", "C": P["A"], "D": "#2b3048", "K": "#000000", "W": "#3a4058"}
    # Slot, wingmen, then the lead closest to you
    for cx, cy, s in ((320, 70, 1), (210, 120, 2), (430, 120, 2), (320, 165, 4)):
        spr = sprite(JET_FRONT, colors, s)
        img.alpha_composite(spr, (cx - spr.width // 2, cy - spr.height // 2))
        # Landing light under the nose
        px[cx, cy + spr.height // 2 + 1] = rgb(P["Y"])
    return img.convert("RGB")


EXTRAS = {
    "night-intercept": ("Night Intercept", night_intercept),
    "cloud-deck": ("Cloud Deck", cloud_deck),
    "desert-run": ("Desert Run", desert_run),
    "sea-patrol": ("Sea Patrol", sea_patrol),
    "head-on": ("Head On", head_on),
}
