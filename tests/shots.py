# Turns VM screenshots into PNGs and checks our login screen showed up
import glob
import os
import shutil
import sys

from PIL import Image

HUD = (0x5C, 0xFF, 0x7A)
SUN = (0xFF, 0xD3, 0x6E)


def count(img, color):
    # Counts pixels close to one color, on a quarter size copy
    small = img.convert("RGB").resize((img.width // 4, img.height // 4), Image.NEAREST)
    return sum(1 for p in small.getdata() if all(abs(a - b) <= 8 for a, b in zip(p, color)))


def main(folder):
    shots = sorted(glob.glob(os.path.join(folder, "shot-*.ppm")))
    if not shots:
        sys.exit("No screenshots taken")
    found = None
    for path in shots:
        img = Image.open(path)
        png = path[:-4] + ".png"
        img.save(png)
        os.remove(path)
        hud, sun = count(img, HUD), count(img, SUN)
        print(os.path.basename(png), "green:", hud, "sun:", sun)
        # Login screen has the green panel and the wallpaper sun
        if hud > 200 and sun > 200:
            found = png
    if not found:
        sys.exit("Did not reach our login screen")
    shutil.copy(found, os.path.join(folder, "login.png"))
    print("Reached our login screen")


if __name__ == "__main__":
    main(sys.argv[1])
