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


def skyline(px, rnd, max_h, color, windows, density, ground):
    # Row of buildings standing on the ground line, returns the tallest roof spot
    x, best = 0, (0, 0, H)
    while x < W:
        bw, bh = rnd.randrange(6, 24), rnd.randrange(8, max_h)
        xe, top = min(x + bw, W), ground - bh
        for yy in range(top, ground):
            for xx in range(x, xe):
                px[xx, yy] = rgb(color)
        if xe - x > 2:
            for _ in range(int(bw * bh * density)):
                px[rnd.randrange(x + 1, xe - 1), rnd.randrange(top + 2, ground - 1)] = rgb(rnd.choice(windows))
        if bh > best[0]:
            best = (bh, (x + xe) // 2, top)
        x += bw + rnd.randrange(0, 3)
    return best


def night_intercept(seed=11):
    # Moonlit night over a harbor city, lights mirrored in the water
    rnd = random.Random(seed)
    img, px = new()
    gy = 300
    sky(px, ["#03050a", "#070b18", "#0d1430", "#151f44", "#22285a", "#3a3168", "#5a3c6a"], gy)
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
    skyline(px, rnd, 90, "#161b36", ["#3d4a7a", "#56648f"], 1 / 40, gy)
    _, lx, ly = skyline(px, rnd, 52, "#06080f", ["#ffb000", "#ffd36e", "#7fb2ff"], 1 / 14, gy)
    px[lx, ly - 1] = rgb(P["R"])
    # Harbor: the city upside down, darker, wobbling every other row
    for y in range(gy, H):
        d = y - gy
        src = gy - 1 - d
        shift = (1 if (y // 2) % 2 else -1) if d > 2 else 0
        for x in range(W):
            r, g, b, _ = px[min(max(x + shift, 0), W - 1), src]
            if r + g + b > 330 and BAYER[y % 4][x % 4] > d // 5:
                px[x, y] = (int(r * 0.85), int(g * 0.85), int(b * 0.85), 255)
            else:
                px[x, y] = (int(r * 0.3), int(g * 0.3), int(b * 0.4) + 8, 255)
    # Moonlight glinting on the water
    for y in range(gy + 3, H, 3):
        w = rnd.randint(2, 7)
        for x in range(150 - w, 150 + w):
            px[x, y] = rgb("#c9d0e2")
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


def cliffs(px, rnd, top, half, color, lit):
    # Left and right canyon walls with ragged faces, the inner faces catch the sun
    c, l = rgb(color), rgb(lit)
    for side in (-1, 1):
        lo, hi = sorted((320 + side * (half - 15), 320 + side * (half + 15)))
        edge, edges = 320 + side * half, []
        for y in range(H):
            if y % 2 == 0:
                edge = max(lo, min(hi, edge + rnd.randint(-2, 2)))
            edges.append(edge)
        t, tops = top, []
        for x in range(W):
            if x % 3 == 0:
                t = max(top - 4, min(top + 4, t + rnd.randint(-1, 1)))
            tops.append(t)
        for y in range(top - 4, H):
            e = edges[y]
            xs = range(0, max(min(e, W), 0)) if side < 0 else range(max(e, 0), W)
            for x in xs:
                if y >= tops[x]:
                    px[x, y] = l if abs(x - (e - 1 if side < 0 else e)) < 2 else c


def canyon_run(seed=66):
    # Sunset at the end of a canyon, jets coming up the river at you
    rnd = random.Random(seed)
    img, px = new()
    sky(px, ["#22163f", "#3d2257", "#6a3060", "#a64858", "#d8704a", "#f2a046", "#ffd27a"], 210)
    halo(px, 320, 205, 30, 95, "#ffc870")
    disc(px, 320, 205, 30, "#fff2c4", "#ffbf6a")
    # River fills the canyon floor, mirroring the sky: bright far away, darker toward you
    bands = [rgb(c) for c in ("#ffe7a0", "#ffd27a", "#f2a046", "#d8704a", "#a64858", "#6a3060")]
    for y in range(215, H):
        t = (y - 215) / (H - 215) * (len(bands) - 1)
        i = min(int(t), len(bands) - 2)
        for x in range(W):
            c = bands[i + 1] if (t - i) * 16 > BAYER[y % 4][x % 4] else bands[i]
            # Ripple lines, longer and further apart up close
            if y % (3 + (y - 215) // 30) == 0 and (x // (6 + (y - 215) // 12) + y) % 3 == 0:
                c = rgb("#3a1a2a")
            px[x, y] = c
    for top, half, color, lit in ((185, 45, "#c26650", "#e08a5e"), (160, 95, "#8f4650", "#c26650"),
                                  (120, 155, "#5a2a44", "#8f4650"), (75, 215, "#30162c", "#5a2a44"),
                                  (25, 285, "#140a16", "#30162c")):
        cliffs(px, rnd, top, half, color, lit)
    colors = {"X": "#140a16", "C": P["A"], "D": "#2a1a2a", "K": "#000000", "W": "#2a2030"}
    for cx, cy, s in ((345, 182, 1), (320, 250, 3)):
        spr = sprite(JET_FRONT, colors, s)
        img.alpha_composite(spr, (cx - spr.width // 2, cy - spr.height // 2))
    return img.convert("RGB")


def coast_patrol(seed=44):
    # Looking straight down: two jets heading for a coastline of farm fields
    rnd = random.Random(seed)
    img, px = new()

    def coast(y):
        return int(440 + 45 * math.sin(y / 70 + 0.5) + 14 * math.sin(y / 19))

    deep, swell = rgb("#0b3556"), rgb("#13507b")
    shallows = [rgb(c) for c in ("#5fd0d6", "#3aa6c4", "#1e7aa3", "#0b3556")]
    fields = [rgb(c) for c in ("#5f8f3f", "#6f9e45", "#8aa04e", "#a89a5a", "#7a8f3a", "#557f36")]
    hedge, road = rgb("#3f6a2c"), rgb("#d6ccb0")
    for y in range(H):
        cx = coast(y)
        for x in range(W):
            d = cx - x
            if d < -9:
                # Patchwork fields in staggered rows, hedges between them
                row = (y + 4) // 20
                fw = 20 + (row * 37) % 23
                col = (x + row * 13) // fw
                if (y + 4) % 20 == 0 or (x + row * 13) % fw == 0:
                    px[x, y] = hedge
                else:
                    px[x, y] = fields[(row * 7 + col * 13) % len(fields)]
            elif d < -2:
                px[x, y] = rgb("#f2e4b8" if (x + y) % 3 else "#e2cc92")
            elif d < 1 or (5 < d < 7 and math.sin(y / 3 + x) > 0.3):
                px[x, y] = rgb("#ffffff")
            elif d < 60:
                t = d / 60 * 3
                i = min(int(t), 2)
                px[x, y] = shallows[i + 1] if (t - i) * 16 > BAYER[y % 4][x % 4] else shallows[i]
            else:
                # Long ocean swells
                s = math.sin((x * 0.6 + y) / 7 + math.sin(x / 40) * 2)
                px[x, y] = swell if s > 0.85 else deep
    # Coast road and a small town beside it
    for y in range(H):
        rx = coast(y) + 34 + int(6 * math.sin(y / 30))
        for x in (rx, rx + 1):
            if x < W:
                px[x, y] = road
    for _ in range(70):
        y = rnd.randrange(170, 240)
        x = coast(y) + 38 + rnd.randrange(2, 30)
        if x < W - 1:
            px[x, y] = px[x + 1, y] = rgb(rnd.choice(["#c0504a", "#e8e4dc", "#9a9a9a"]))
    top = [r + r[::-1] for r in JET_TOP_HALF]
    jet_img = sprite(top, P, 2).rotate(-90, expand=True)
    shade = sprite(top, {k: (6, 24, 40, 150) for k in P}, 2).rotate(-90, expand=True)
    jets = ((230, 120), (170, 175))
    clouds = ((90, 300, 26), (330, 330, 22))
    for cx, cy, s in clouds:
        puffs(px, random.Random(cx * 7 + cy), cx + 45, cy + 40, s, "#082a45", "#082a45", "#082a45")
    for jx, jy in jets:
        img.alpha_composite(shade, (jx + 40, jy + 60))
    for cx, cy, s in clouds:
        puffs(px, random.Random(cx * 7 + cy), cx, cy, s, "#ffffff", "#e6eff7", "#b8c9dc")
    for jx, jy in jets:
        for t in range(jx - 160, jx + 2):
            if (t - jx + 160) * 17 / 160 > BAYER[jy % 4][t % 4] + 1:
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
    "coast-patrol": ("Coast Patrol", coast_patrol),
    "night-intercept": ("Night Intercept", night_intercept),
}
