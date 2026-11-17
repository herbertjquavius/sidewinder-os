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


def fill(px, y0, color):
    c = rgb(color)
    for y in range(y0, H):
        for x in range(W):
            px[x, y] = c


def disc(px, cx, cy, r, top, bot):
    # Sun or moon with a dithered top to bottom blend
    a, b = rgb(top), rgb(bot)
    for y in range(cy - r, cy + r):
        k = (y - (cy - r)) / (2 * r)
        for x in range(cx - r, cx + r):
            if 0 <= x < W and 0 <= y < H and (x - cx) ** 2 + (y - cy) ** 2 < r * r:
                px[x, y] = b if k * 16 > BAYER[y % 4][x % 4] else a


def halo(px, cx, cy, r0, r1, color):
    # Soft dithered glow around a sun or moon
    c = rgb(color)
    for y in range(max(cy - r1, 0), min(cy + r1, H)):
        for x in range(max(cx - r1, 0), min(cx + r1, W)):
            d = math.hypot(x - cx, y - cy)
            if r0 <= d < r1 and (1 - (d - r0) / (r1 - r0)) * 12 > BAYER[y % 4][x % 4]:
                px[x, y] = c


def blob(px, cx, cy, w, h, light, dark):
    # Flat pixel cloud, lighter on top
    for y in range(cy - h, cy + h):
        for x in range(cx - w, cx + w):
            if 0 <= x < W and 0 <= y < H and ((x - cx) / w) ** 2 + ((y - cy) / h) ** 2 < 1:
                px[x, y] = rgb(light if y < cy - h // 3 else dark)


def puffs(px, rnd, cx, cy, size, hi, mid, lo):
    # Cumulus made of round puffs, lit from above, lower puffs drawn first
    parts = [(cx + rnd.randint(-size, size), cy + rnd.randint(-size // 3, size // 4), rnd.randint(size // 2, size))
             for _ in range(6)]
    a, b, c = rgb(hi), rgb(mid), rgb(lo)
    for x0, y0, r in sorted(parts, key=lambda p: p[1], reverse=True):
        for y in range(max(y0 - r, 0), min(y0 + r, H)):
            for x in range(max(x0 - r, 0), min(x0 + r, W)):
                if (x - x0) ** 2 + (y - y0) ** 2 < r * r:
                    k = (y - y0) / r
                    px[x, y] = a if k < -0.35 else b if k < 0.35 else c


def sprite(rows, colors, scale=1):
    # Rows of letters to an image, letters missing from colors stay clear
    img = Image.new("RGBA", (len(rows[0]), len(rows)), (0, 0, 0, 0))
    for yy, row in enumerate(rows):
        for xx, c in enumerate(row):
            if c in colors:
                img.putpixel((xx, yy), colors[c] if isinstance(colors[c], tuple) else rgb(colors[c]))
    return img.resize((img.width * scale, img.height * scale), Image.NEAREST) if scale > 1 else img


def jet(img, px, x, y, body, trail=None, trail_from=0, scale=1, flame=False):
    # Side view jet with optional fading contrail and afterburner cone
    if trail:
        ty = y + 5 * scale
        for tx in range(trail_from, x):
            near = (tx - trail_from) / max(x - trail_from, 1)
            if near * 17 > BAYER[ty % 4][tx % 4] + 1:
                for s in range(scale):
                    px[tx, ty + s] = rgb(trail)
    if flame:
        for k in range(1, 3 * scale + 1):
            for yy in range(y + 4 * scale, y + 6 * scale):
                if 0 <= x - k < W:
                    px[x - k, yy] = rgb(P["Y"] if k <= scale else P["R"])
    img.alpha_composite(sprite(JET_SIDE, {"X": body, "A": P["R"]}, scale), (x, y))


def skyline(px, rnd, hmin, hmax, color, windows, density, ground, roofs=False):
    # Row of buildings, ground can sit below the screen so they run off the bottom
    x, bottom = 0, min(ground, H)
    while x < W:
        bw, bh = rnd.randrange(6, 24), rnd.randrange(hmin, hmax)
        xe, top = min(x + bw, W), ground - bh
        for yy in range(top, bottom):
            for xx in range(x, xe):
                px[xx, yy] = rgb(color)
        if roofs and bw > 11 and rnd.random() < 0.4:
            # Stepped top
            step = rnd.randrange(5, 14)
            for yy in range(top - step, top):
                for xx in range(x + 3, xe - 3):
                    px[xx, yy] = rgb(color)
            top -= step
        if roofs and rnd.random() < 0.25:
            # Antenna with a red light
            ax = (x + xe) // 2
            ah = rnd.randrange(4, 11)
            for yy in range(top - ah, top):
                px[ax, yy] = rgb(color)
            px[ax, top - ah - 1] = rgb(P["R"])
        if xe - x > 2:
            for _ in range(int(bw * (bottom - top) * density)):
                px[rnd.randrange(x + 1, xe - 1), rnd.randrange(top + 2, bottom)] = rgb(rnd.choice(windows))
        x += bw + rnd.randrange(0, 3)


def night_intercept(seed=11):
    # Moonlit night over a city that runs off the bottom of the screen
    rnd = random.Random(seed)
    img, px = new()
    sky(px, ["#03050a", "#070b18", "#0d1430", "#151f44", "#22285a", "#3a3168", "#5a3c6a"], 330)
    for _ in range(320):
        px[rnd.randrange(W), rnd.randrange(230)] = rgb("#9fb0d9" if rnd.random() < 0.7 else "#e8eeff")
    for _ in range(12):
        x, y = rnd.randrange(2, W - 2), rnd.randrange(2, 190)
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            px[x + dx, y + dy] = rgb("#ffffff")
    halo(px, 150, 85, 28, 80, "#1d2a55")
    disc(px, 150, 85, 28, "#f2f4fa", "#c9d0e2")
    for cx, cy, r in ((142, 78, 5), (160, 95, 4), (150, 101, 3), (165, 74, 3)):
        disc(px, cx, cy, r, "#b4bccf", "#a3abc0")
    for _ in range(5):
        blob(px, rnd.randrange(W), rnd.randrange(160, 230), rnd.randrange(40, 110), rnd.randrange(2, 5), "#3a3f70", "#2c3160")
    skyline(px, rnd, 60, 120, "#161b36", ["#3d4a7a", "#56648f"], 1 / 40, H)
    skyline(px, rnd, 70, 160, "#06080f", ["#ffb000", "#ffd36e", "#7fb2ff", "#ffb000"], 1 / 14, H + 50, roofs=True)
    for jx, jy in ((390, 110), (340, 138)):
        jet(img, px, jx, jy, "#2a3352", trail="#7d88c0", trail_from=80, scale=2, flame=True)
    return img.convert("RGB")


def cloud_tops(px, rnd, base, amp, period, colors):
    # Rolling cumulus tops: round humps, sunlit rim, shading deeper down
    rim, hi, mid, lo = (rgb(c) for c in colors)
    # Bubbles of random size along the layer, the highest one wins at each spot
    tops = [base] * W
    x = -20
    while x < W + 20:
        w = rnd.randint(period, period * 3)
        h, by = w * rnd.uniform(0.5, 0.85), base + rnd.randint(0, amp // 2)
        for xx in range(max(int(x - w), 0), min(int(x + w), W)):
            tops[xx] = min(tops[xx], int(by - h * math.sqrt(max(0.0, 1 - ((xx - x) / w) ** 2))))
        x += rnd.randint(period, period * 3)
    for x in range(W):
        facing_sun = tops[min(x + 1, W - 1)] >= tops[max(x - 1, 0)]
        for y in range(max(tops[x], 0), H):
            d = y - tops[x] + (BAYER[y % 4][x % 4] - 8) / 4
            if d < 1:
                px[x, y] = rim
            elif d < (10 if facing_sun else 6):
                px[x, y] = hi
            elif d < 22:
                px[x, y] = mid
            else:
                px[x, y] = lo


def cloud_deck(seed=21):
    # Golden hour above a sea of clouds, a three ship formation
    rnd = random.Random(seed)
    img, px = new()
    sky(px, ["#0f2d5c", "#1b4a86", "#2f6aa8", "#5a8fc4", "#9fb6cf", "#e6c99a", "#f7d58f"], 235)
    halo(px, 470, 222, 20, 85, "#fbe3a8")
    disc(px, 470, 222, 20, "#fffbe6", "#ffe39a")
    for _ in range(7):
        y, x, n = rnd.randrange(30, 170), rnd.randrange(W), rnd.randrange(40, 140)
        for xx in range(x, min(x + n, W)):
            px[xx, y] = rgb("#f2e6cc")
    cloud_tops(px, rnd, 238, 12, 9, ("#fff1d8", "#f6dcb4", "#d3bfb9", "#9aa0bd"))
    cloud_tops(px, rnd, 268, 18, 15, ("#fff6e6", "#fbe6c4", "#ddcbc6", "#a3abc6"))
    cloud_tops(px, rnd, 312, 26, 22, ("#ffffff", "#fff0d8", "#e6d6d2", "#b3bad2"))
    for jx, jy in ((330, 105), (282, 128), (234, 151)):
        jet(img, px, jx, jy, "#2b3340", trail="#fff3dc", trail_from=60, scale=2)
    return img.convert("RGB")


def striped_sun(px, cx, cy, r, top, bot, horizon):
    # Big retro sun with cut stripes on its lower half, hidden below the horizon
    a, b = rgb(top), rgb(bot)
    for y in range(cy - r, min(cy + r, horizon)):
        rel = y - (cy - 6)
        if rel > 0 and rel % 8 < 1 + rel // 14:
            continue
        k = (y - (cy - r)) / (2 * r)
        for x in range(cx - r, cx + r):
            if 0 <= x < W and (x - cx) ** 2 + (y - cy) ** 2 < r * r:
                px[x, y] = b if k * 16 > BAYER[y % 4][x % 4] else a


def mesas(px, rnd, base, height, lo, hi, color, rim):
    # Mesa skyline: steep sides, flat tops, filled down to the bottom
    c, rc = rgb(color), rgb(rim)
    ph = [rnd.uniform(0, 6.28) for _ in range(3)]
    for x in range(W):
        n = 0.5 * math.sin(x / 71 + ph[0]) + 0.3 * math.sin(x / 29 + ph[1]) + 0.2 * math.sin(x / 11 + ph[2])
        s = max(0.0, min(1.0, (n - lo) / (hi - lo)))
        # Caprock: flat top above halfway, steep slope below it
        k = 1.0 if s > 0.5 else 0.8 * (s / 0.5) ** 0.5
        top = int(base - height * k) if s > 0 else base
        for y in range(max(top, 0), H):
            px[x, y] = c
        if s > 0.6 and top >= 0:
            px[x, top] = rc


def canyon_run(seed=66):
    # Mesa country at sunset in three layers, two jets running low between them
    rnd = random.Random(seed)
    img, px = new()
    sky(px, ["#1a1034", "#351a4e", "#62285a", "#9c3a58", "#d0563f", "#ec8a3a", "#ffb85a"], 262)
    for _ in range(60):
        px[rnd.randrange(W), rnd.randrange(80)] = rgb("#e0c8ff")
    halo(px, 400, 225, 58, 120, "#ffa45e")
    striped_sun(px, 400, 225, 58, "#fff3c4", "#ff9e5a", 300)
    for _ in range(5):
        blob(px, rnd.randrange(W), rnd.randrange(110, 190), rnd.randrange(40, 100), rnd.randrange(2, 4), "#e88a6a", "#b85a62")
    mesas(px, rnd, 268, 40, -0.2, 0.3, "#b5566a", "#ffb27a")
    mesas(px, rnd, 300, 70, 0.0, 0.45, "#7a3550", "#e08a5e")
    for jx, jy in ((330, 196), (278, 218)):
        jet(img, px, jx, jy, "#1e1028", trail="#ffd9b0", trail_from=40, scale=2)
    mesas(px, rnd, 345, 150, 0.35, 0.75, "#2a1028", "#7a3550")
    return img.convert("RGB")


def open_ocean(seed=44):
    # Straight down on open ocean: swells, sun glint, clouds and two jets with their shadows
    rnd = random.Random(seed)
    img, px = new()
    tones = [rgb(c) for c in ("#082a48", "#0b3556", "#0f4468", "#14557c")]
    swell = rgb("#1d6a98")
    for y in range(H):
        for x in range(W):
            v = (math.sin(x / 97 + math.sin(y / 61) * 1.5) + math.sin(y / 73 - x / 131) + 2) / 4 * 3
            i = min(int(v), 2)
            c = tones[i + 1] if (v - i) * 16 > BAYER[y % 4][x % 4] else tones[i]
            # Long swells running across
            if math.sin((x * 0.45 + y) / 6 + math.sin(x / 47) * 2.2) > 0.94 and math.sin(x / 23 + y / 17) > -0.2:
                c = swell
            px[x, y] = c
    # Sun glint, thickest along a diagonal band
    for _ in range(900):
        t = rnd.random()
        spread = rnd.gauss(0, 1)
        x = int(60 + t * 520 + spread * 18)
        y = int(340 - t * 300 + spread * 30)
        if 0 <= x < W - 2 and 0 <= y < H:
            col = rgb("#ffffff" if abs(spread) < 0.5 else "#bfe4f4")
            for dx in range(rnd.randint(1, 3)):
                px[x + dx, y] = col
    # Whitecaps
    for _ in range(160):
        x, y = rnd.randrange(W - 4), rnd.randrange(H)
        for dx in range(rnd.randint(1, 4)):
            px[x + dx, y] = rgb("#9fd2ea")
    top = [r + r[::-1] for r in JET_TOP_HALF]
    jet_img = sprite(top, P, 2).rotate(-90, expand=True)
    shade = sprite(top, {k: (4, 20, 36, 150) for k in P}, 2).rotate(-90, expand=True)
    jets = ((330, 115), (265, 170))
    clouds = ((80, 70, 30), (520, 260, 34), (180, 320, 24), (600, 40, 22))
    for cx, cy, s in clouds:
        puffs(px, random.Random(cx * 7 + cy), cx + 50, cy + 45, s, "#082a46", "#082a46", "#082a46")
    for jx, jy in jets:
        img.alpha_composite(shade, (jx + 45, jy + 65))
    for cx, cy, s in clouds:
        puffs(px, random.Random(cx * 7 + cy), cx, cy, s, "#ffffff", "#e6eff7", "#b8c9dc")
    for jx, jy in jets:
        for t in range(jx - 180, jx + 2):
            if 0 <= t < W and (t - jx + 180) * 17 / 180 > BAYER[jy % 4][t % 4] + 1:
                px[t, jy + 30] = px[t, jy + 33] = rgb("#e8f4fa")
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
    "head-on": ("Head On", head_on),
    "cloud-deck": ("Cloud Deck", cloud_deck),
    "canyon-run": ("Canyon Run", canyon_run),
    "open-ocean": ("Open Ocean", open_ocean),
    "night-intercept": ("Night Intercept", night_intercept),
}
