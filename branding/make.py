# Renders all branding assets from distro.env into branding/out
import json
import math
import os
import random
import re
import shutil
import subprocess
from string import Template

from PIL import Image

from font import build_font
from scenes import EXTRAS
from sprites import FONT, JET_SIDE, JET_TOP_HALF, P

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "out")
TPL = os.path.join(ROOT, "templates")
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
SKY = ["#0b1a2e", "#13284a", "#1f3b66", "#3a4f7a", "#7a5c80", "#c06c6c", "#f0a35e"]

PLYMOUTH = """[Plymouth Theme]
Name=$name
Description=$name boot splash
ModuleName=script

[script]
ImageDir=/usr/share/plymouth/themes/$slug
ScriptFile=/usr/share/plymouth/themes/$slug/$slug.script
"""

SCRIPT = """// $name boot splash
Window.SetBackgroundTopColor(0.043, 0.059, 0.078);
Window.SetBackgroundBottomColor(0.043, 0.059, 0.078);

cx = Window.GetX() + Window.GetWidth() / 2;
cy = Window.GetY() + Window.GetHeight() / 2;

// Logo and name
logo.image = Image("logo.png");
logo.sprite = Sprite(logo.image);
logo.sprite.SetPosition(cx - logo.image.GetWidth() / 2, cy - logo.image.GetHeight() + 40, 1);

word.image = Image("wordmark.png");
word.sprite = Sprite(word.image);
word.sprite.SetPosition(cx - word.image.GetWidth() / 2, cy + 70, 1);

// Progress bar
frame.image = Image("bar_frame.png");
frame.x = cx - frame.image.GetWidth() / 2;
frame.y = cy + 130;
frame.sprite = Sprite(frame.image);
frame.sprite.SetPosition(frame.x, frame.y, 1);

fill.image = Image("bar_fill.png");
fill.sprite = Sprite();
fill.sprite.SetPosition(frame.x + 4, frame.y + 4, 2);

label.image = Image("label.png");
label.sprite = Sprite(label.image);
label.sprite.SetPosition(cx - label.image.GetWidth() / 2, frame.y + 24, 1);

// Fills the bar as boot goes on
fun progress_cb(duration, progress) {
    w = Math.Int(global.fill.image.GetWidth() * progress);
    if (w > 0)
        global.fill.sprite.SetImage(global.fill.image.Scale(w, global.fill.image.GetHeight()));
}
Plymouth.SetBootProgressFunction(progress_cb);

// Password prompt for encrypted disks
fun password_cb(prompt, bullets) {
    s = prompt + "  ";
    for (i = 0; i < bullets; i++)
        s = s + "*";
    global.pw.image = Image.Text(s, 0.36, 1, 0.48);
    global.pw.sprite = Sprite(global.pw.image);
    global.pw.sprite.SetPosition(global.cx - global.pw.image.GetWidth() / 2, global.frame.y + 60, 3);
}
Plymouth.SetDisplayPasswordFunction(password_cb);

// Hides the prompt once answered
fun normal_cb() {
    global.pw.sprite = NULL;
}
Plymouth.SetDisplayNormalFunction(normal_cb);
"""


def load_name():
    # Reads NAME from distro.env in the repo root
    with open(os.path.join(ROOT, "..", "distro.env")) as f:
        for line in f:
            m = re.match(r'\s*NAME\s*=\s*"?([^"\n]*)"?', line)
            if m:
                return m.group(1).strip()
    raise SystemExit("NAME missing from distro.env")


def rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def sprite(rows, colors):
    # Turns rows of letters into an image
    assert len({len(r) for r in rows}) == 1, "Uneven sprite rows"
    img = Image.new("RGBA", (len(rows[0]), len(rows)), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, c in enumerate(row):
            if c in colors:
                img.putpixel((x, y), rgb(colors[c]) + (255,))
    return img


def up(img, n):
    # Scales up with hard pixel edges
    return img.resize((img.width * n, img.height * n), Image.NEAREST)


def text(s, color, gap=1):
    # Draws text with the 5x7 pixel font
    s = s.upper()
    img = Image.new("RGBA", (max(len(s) * (5 + gap) - gap, 1), 7), (0, 0, 0, 0))
    for i, ch in enumerate(s):
        for y, row in enumerate(FONT.get(ch, FONT[" "])):
            for x, c in enumerate(row):
                if c == "#":
                    img.putpixel((i * (5 + gap) + x, y), rgb(color) + (255,))
    return img


def emblem():
    # Jet inside a HUD reticle ring
    size, c = 48, 24
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    hud = rgb(P["H"]) + (255,)
    for y in range(size):
        for x in range(size):
            dx, dy = x + 0.5 - c, y + 0.5 - c
            r = math.hypot(dx, dy)
            a = math.degrees(math.atan2(dy, dx)) % 90
            ring = 19.5 <= r < 21.5 and abs(a - 45) > 7
            tick = 21.5 <= r < 24 and (abs(dx) < 1 or abs(dy) < 1)
            if ring or tick:
                img.putpixel((x, y), hud)
    jet = sprite([r + r[::-1] for r in JET_TOP_HALF], P)
    img.alpha_composite(jet, (8, 8))
    return img


def svg(img, scale=10):
    # Converts pixel art to a crisp SVG, merging same color runs
    w, h = img.size
    parts = []
    for y in range(h):
        x = 0
        while x < w:
            p = img.getpixel((x, y))
            if p[3] == 0:
                x += 1
                continue
            run = 1
            while x + run < w and img.getpixel((x + run, y)) == p:
                run += 1
            parts.append(f'<rect x="{x}" y="{y}" width="{run}" height="1" '
                         f'fill="#{p[0]:02x}{p[1]:02x}{p[2]:02x}"/>')
            x += run
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
            f'width="{w * scale}" height="{h * scale}" shape-rendering="crispEdges">'
            + "".join(parts) + "</svg>\n")


def wallpaper(seed=7):
    # Dusk sky, sun, ridges, airfield lights and a jet formation
    W, H, horizon = 640, 360, 260
    rnd = random.Random(seed)
    img = Image.new("RGBA", (W, H))
    px = img.load()
    sky = [rgb(c) for c in SKY]

    # Dithered sky bands
    for y in range(H):
        t = min(y / horizon, 1) * (len(sky) - 1)
        i = min(int(t), len(sky) - 2)
        f = t - i
        for x in range(W):
            px[x, y] = (sky[i + 1] if f * 16 > BAYER[y % 4][x % 4] else sky[i]) + (255,)

    # Stars
    for _ in range(90):
        px[rnd.randrange(W), rnd.randrange(90)] = rgb("#cfd8ff") + (255,)

    # Striped retro sun
    sx, sy, sr = 470, 250, 48
    top, bot = rgb("#ffd36e"), rgb("#ff8a5c")
    for y in range(sy - sr, sy + sr):
        rel = y - (sy - 6)
        if rel > 0 and rel % 8 < 1 + rel // 14:
            continue
        k = (y - (sy - sr)) / (2 * sr)
        for x in range(sx - sr, sx + sr):
            if (x - sx) ** 2 + (y - sy) ** 2 < sr * sr:
                px[x, y] = (bot if k * 16 > BAYER[y % 4][x % 4] else top) + (255,)

    # Clouds
    for _ in range(7):
        cx, cy = rnd.randrange(W), rnd.randrange(150, 235)
        w, h = rnd.randrange(30, 90), rnd.randrange(4, 9)
        for y in range(cy - h, cy + h):
            for x in range(cx - w, cx + w):
                if 0 <= x < W and ((x - cx) / w) ** 2 + ((y - cy) / h) ** 2 < 1:
                    px[x, y] = rgb("#9a7fa8" if y < cy - h // 2 else "#6b5a86") + (255,)

    # Mountain ridges, far to near
    def ridge(base, amp, color, step):
        ph = [rnd.uniform(0, 6.28) for _ in range(3)]
        for x0 in range(0, W, step):
            h = base - amp * (0.5 * math.sin(x0 / 97 + ph[0])
                              + 0.3 * math.sin(x0 / 41 + ph[1])
                              + 0.2 * math.sin(x0 / 17 + ph[2]))
            h += rnd.randint(-1, 1)
            for x in range(x0, min(x0 + step, W)):
                for y in range(max(int(h), 0), H):
                    px[x, y] = rgb(color) + (255,)

    ridge(255, 30, "#2a2440", 3)
    ridge(290, 26, "#191a33", 2)

    # Flat airfield with runway lights along its edge
    for y in range(338, H):
        for x in range(W):
            px[x, y] = rgb(P["K"]) + (255,)
    for x in range(40, 601, 10):
        px[x, 341] = rgb(P["H"] if x in (40, 600) else P["A"]) + (255,)

    # Jet formation with fading contrails
    jet = sprite(JET_SIDE, {"X": "#141428", "A": P["R"]})
    trail = rgb("#e6e0f0") + (255,)
    for jx, jy in [(330, 116), (300, 130), (270, 144)]:
        ty = jy + 5
        for x in range(60, jx):
            near = (x - 60) / (jx - 60)
            if near * 17 > BAYER[ty % 4][x % 4] + 1:
                px[x, ty] = trail
        img.alpha_composite(jet, (jx, jy))
    return img.convert("RGB")


def splash_parts(name):
    # Images used by the Plymouth theme
    hud = rgb(P["H"]) + (255,)
    frame = Image.new("RGBA", (320, 16), (0, 0, 0, 0))
    for x in range(320):
        for y in range(16):
            if x < 2 or x > 317 or y < 2 or y > 13:
                frame.putpixel((x, y), hud)
    return {
        "logo.png": up(emblem(), 5),
        "wordmark.png": up(text(name, P["H"]), 4),
        "label.png": up(text("Preflight check", P["L"]), 2),
        "bar_frame.png": frame,
        "bar_fill.png": Image.new("RGBA", (312, 8), hud),
    }


def splash_preview(parts, progress=0.6):
    # Mock of the boot screen at 1080p, same layout as the script
    W, H = 1920, 1080
    cx, cy = W // 2, H // 2
    img = Image.new("RGBA", (W, H), rgb(P["K"]) + (255,))
    lg, wd, fr, lb = parts["logo.png"], parts["wordmark.png"], parts["bar_frame.png"], parts["label.png"]
    img.alpha_composite(lg, (cx - lg.width // 2, cy - lg.height + 40))
    img.alpha_composite(wd, (cx - wd.width // 2, cy + 70))
    fx, fy = cx - fr.width // 2, cy + 130
    img.alpha_composite(fr, (fx, fy))
    fill = parts["bar_fill.png"].crop((0, 0, int(312 * progress), 8))
    img.alpha_composite(fill, (fx + 4, fy + 4))
    img.alpha_composite(lb, (cx - lb.width // 2, fy + 24))
    return img.convert("RGB")


def slug_of(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "distro"


def place(img, *parts):
    # Saves an image under out, making folders as needed
    path = os.path.join(OUT, *parts)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    return path


def render_templates(subs):
    # Copies templates into out, filling in $name, $slug and $cs
    for dirpath, _, files in os.walk(TPL):
        for fn in files:
            src = os.path.join(dirpath, fn)
            rel = os.path.relpath(src, TPL).replace("SLUG", subs["slug"])
            dst = os.path.join(OUT, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(src) as f:
                data = Template(f.read()).substitute(subs)
            with open(dst, "w") as f:
                f.write(data)


def color_scheme(name, cs):
    # KDE color scheme built from the palette
    fg = {
        "ForegroundNormal": "201,209,217", "ForegroundInactive": "139,151,163",
        "ForegroundActive": "255,176,0", "ForegroundLink": "92,255,122",
        "ForegroundVisited": "154,127,168", "ForegroundNegative": "255,90,54",
        "ForegroundNeutral": "255,176,0", "ForegroundPositive": "92,255,122",
        "DecorationFocus": "92,255,122", "DecorationHover": "92,255,122",
    }
    sections = {
        "View": ("14,19,25", "20,26,34"), "Window": ("20,26,34", "26,33,43"),
        "Button": ("34,42,54", "40,49,62"), "Tooltip": ("11,15,20", "20,26,34"),
        "Complementary": ("11,15,20", "20,26,34"), "Header": ("11,15,20", "20,26,34"),
        "Selection": ("60,207,95", "47,158,74"),
    }
    out = [f"[General]\nColorScheme={cs}\nName={name}\n"]
    for sec, (bg, alt) in sections.items():
        lines = [f"[Colors:{sec}]", f"BackgroundNormal={bg}", f"BackgroundAlternate={alt}"]
        for k, v in fg.items():
            # Dark text on the green selection
            if sec == "Selection" and k in ("ForegroundNormal", "ForegroundInactive", "ForegroundActive"):
                v = "11,15,20"
            lines.append(f"{k}={v}")
        out.append("\n".join(lines) + "\n")
    out.append("[WM]\nactiveBackground=11,15,20\nactiveForeground=201,209,217\n"
               "inactiveBackground=20,26,34\ninactiveForeground=139,151,163\n"
               "activeBlend=92,255,122\ninactiveBlend=139,151,163\n")
    return "\n".join(out)


def grub_background(em):
    # Dark screen with logo, title and HUD brackets around the menu
    W, H = 1920, 1080
    img = Image.new("RGB", (W, H), rgb(P["K"]))
    lg = up(em, 4)
    img.paste(lg, (W // 2 - lg.width // 2, 120), lg)
    t = up(text("Select system version", P["L"]), 3)
    img.paste(t, (W // 2 - t.width // 2, 360), t)
    hud = rgb(P["H"])
    x0, y0, x1, y1 = 560, 440, 1360, 820
    for x, y, sx, sy in [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]:
        for i in range(40):
            for j in range(4):
                img.putpixel((x + sx * i, y + sy * j), hud)
                img.putpixel((x + sx * j, y + sy * i), hud)
    return img


def main():
    name = load_name()
    slug = slug_of(name)
    cs = re.sub(r"\W", "", name) or "Distro"
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    render_templates({"name": name, "slug": slug, "cs": cs})

    # Pixel font for the login screen, splash and boot menu
    ttf = os.path.join(OUT, "fonts", f"{slug}-pixel.ttf")
    os.makedirs(os.path.dirname(ttf))
    build_font(f"{name} Pixel", ttf)

    # Logo and wordmark
    em = emblem()
    with open(os.path.join(OUT, "logo.svg"), "w") as f:
        f.write(svg(em))
    for n in (1, 2, 4, 8):
        up(em, n).save(os.path.join(OUT, f"logo-{48 * n}.png"))
    up(text(name, P["H"]), 4).save(os.path.join(OUT, "wordmark.png"))

    # Wallpaper package at 1080p, 1440p and 4K
    wp = wallpaper()
    for n in (3, 4, 6):
        place(up(wp, n), "wallpapers", slug, "contents", "images", f"{640 * n}x{360 * n}.png")

    # Extra wallpapers, each its own package
    extras = []
    for key, (title, draw) in EXTRAS.items():
        wid = f"{slug}-{key}"
        img = draw()
        extras.append(img)
        for n in (3, 4, 6):
            place(up(img, n), "wallpapers", wid, "contents", "images", f"{640 * n}x{360 * n}.png")
        with open(os.path.join(OUT, "wallpapers", wid, "metadata.json"), "w") as f:
            json.dump({"KPlugin": {"Authors": [{"Name": name}], "Id": wid, "License": "CC-BY-SA-4.0",
                                   "Name": f"{name} {title}"}}, f, indent=4)
    sheet = Image.new("RGB", (1920, 720))
    for i, img in enumerate([wp] + extras):
        sheet.paste(img, ((i % 3) * 640, (i // 3) * 360))
    sheet.save(os.path.join(OUT, "preview-wallpapers.png"))

    # First-boot setup wizard background, it only looks at Plasma's Next wallpaper sizes
    place(up(wp, 8), "setup", "5120x2880.png")
    tall = up(wp, 9)
    x, y = (tall.width - 1440) // 2, (tall.height - 2960) // 2
    place(tall.crop((x, y, x + 1440, y + 2960)), "setup", "1440x2960.png")

    # KDE color scheme
    os.makedirs(os.path.join(OUT, "color-schemes"))
    with open(os.path.join(OUT, "color-schemes", f"{cs}.colors"), "w") as f:
        f.write(color_scheme(name, cs))

    # Login screen
    place(up(wp, 3), "sddm", slug, "background.png")
    place(up(em, 3), "sddm", slug, "logo.png")
    shutil.copy(ttf, os.path.join(OUT, "sddm", slug, "font.ttf"))

    # Desktop startup splash
    sp = os.path.join("plasma", "look-and-feel", f"org.{slug}.desktop", "contents", "splash", "images")
    place(up(em, 4), sp, "logo.png")
    shutil.copy(ttf, os.path.join(OUT, sp, "font.ttf"))

    # Boot menu, font is made here if grub-mkfont exists, otherwise in CI
    place(grub_background(em), "grub", slug, "background.png")
    mk = shutil.which("grub2-mkfont") or shutil.which("grub-mkfont")
    if mk:
        subprocess.run([mk, "-s", "24", "-o", os.path.join(OUT, "grub", slug, "pixel-24.pf2"), ttf], check=True)
    else:
        print("grub-mkfont not found, boot menu font gets built in CI")

    # Plymouth boot splash theme
    pdir = os.path.join(OUT, "plymouth", slug)
    os.makedirs(pdir, exist_ok=True)
    parts = splash_parts(name)
    for fn, im in parts.items():
        im.save(os.path.join(pdir, fn))
    with open(os.path.join(pdir, f"{slug}.plymouth"), "w") as f:
        f.write(Template(PLYMOUTH).substitute(name=name, slug=slug))
    with open(os.path.join(pdir, f"{slug}.script"), "w") as f:
        f.write(Template(SCRIPT).substitute(name=name))

    # One preview sheet: boot splash, wallpaper, logo
    sheet = Image.new("RGB", (1920, 980), rgb(P["K"]))
    sheet.paste(splash_preview(parts).resize((960, 540), Image.NEAREST), (0, 0))
    sheet.paste(up(wp, 3).resize((960, 540), Image.NEAREST), (960, 0))
    big = up(em, 8)
    sheet.paste(big, (120, 568), big)
    wd = up(text(name, P["H"]), 10)
    sheet.paste(wd, (600, 740 - wd.height // 2), wd)
    sheet.save(os.path.join(OUT, "preview.png"))
    print("Built branding for", name, "->", OUT)


if __name__ == "__main__":
    main()
