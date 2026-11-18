# Pixel icon theme for folders, trash and system apps, everything else comes from Breeze Dark
import os

from PIL import Image

# K outline, D body, L light body, H HUD green, A amber, W white, R red
PAL = {"K": "#0b0f14", "D": "#3a4450", "L": "#56636f", "H": "#5cff7a", "A": "#ffb000",
       "W": "#c9d1d9", "R": "#ff5a36", "B": "#141a22"}

FOLDER = [
    "................",
    ".KKKKK..........",
    "KDDDDDK.........",
    "KDDDDDDKKKKKKKK.",
    "KLLLLLLLLLLLLLLK",
    "KHHHHHHHHHHHHHHK",
    "KDDDDDDDDDDDDDDK",
    "KDDDDDDDDDDDDDDK",
    "KDDDDDDDDDDDDDDK",
    "KDDDDDDDDDDDDDDK",
    "KDDDDDDDDDDDDDDK",
    "KDDDDDDDDDDDDDDK",
    "KDDDDDDDDDDDDDDK",
    "KDDDDDDDDDDDDDDK",
    ".KKKKKKKKKKKKKK.",
    "................",
]

# 6x6 marks drawn in the middle of a folder
MARKS = {
    "folder-documents": ["WWWW..", "......", "WWWWWW", "......", "WWWWW.", "......"],
    "folder-download": ["..HH..", "..HH..", "HHHHHH", ".HHHH.", "..HH..", "HHHHHH"],
    "folder-music": ["...HHH", "...H.H", "...H.H", ".HHH.H", "HHHHHH", ".HH.HH"],
    "folder-pictures": ["A.....", "......", "...H..", "..HHH.", ".HHHHH", "HHHHHH"],
    "folder-videos": ["W.WW.W", "WWWWWW", "WWWWWW", "WWWWWW", "WWWWWW", "W.WW.W"],
    "folder-games": [".W..W.", "WWWWWW", "WHWWAW", "HHHWWW", "WHWWRW", "WWWWWW"],
    "folder-desktop": ["WWWWWW", "WHHHHW", "WHHHHW", "WWWWWW", "..WW..", ".WWWW."],
    "user-home": ["..HH..", ".HHHH.", "HHHHHH", ".H..H.", ".H..H.", ".HHHH."],
    "folder": None,
}

APPS = {
    "utilities-terminal": [
        "................",
        ".KKKKKKKKKKKKKK.",
        "KDDDDDDDDDDDDDDK",
        "KBBBBBBBBBBBBBBK",
        "KBHBBBBBBBBBBBBK",
        "KBBHBBBBBBBBBBBK",
        "KBBBHBBBBBBBBBBK",
        "KBBHBBBBBBBBBBBK",
        "KBHBBBHHHHBBBBBK",
        "KBBBBBBBBBBBBBBK",
        "KBBBBBBBBBBBBBBK",
        "KBBBBBBBBBBBBBBK",
        "KBBBBBBBBBBBBBBK",
        ".KKKKKKKKKKKKKK.",
        "................",
        "................",
    ],
    "systemsettings": [
        "................",
        "......KKKK......",
        "...KK.KHHK.KK...",
        "..KHHKKHHKKHHK..",
        "..KHHHHHHHHHHK..",
        "...KHHHKKHHHK...",
        ".KKHHHK..KHHHKK.",
        ".KHHHK....KHHHK.",
        ".KHHHK....KHHHK.",
        ".KKHHHK..KHHHKK.",
        "...KHHHKKHHHK...",
        "..KHHHHHHHHHHK..",
        "..KHHKKHHKKHHK..",
        "...KK.KHHK.KK...",
        "......KKKK......",
        "................",
    ],
    "plasmadiscover": [
        "................",
        ".....KKKKKK.....",
        "....K......K....",
        "....K......K....",
        ".KKKKKKKKKKKKKK.",
        ".KDDDDDDDDDDDDK.",
        ".KDDDDDHHDDDDDK.",
        ".KDDDDDHHDDDDDK.",
        ".KDDDHHHHHHDDDK.",
        ".KDDDDHHHHDDDDK.",
        ".KDDDDDHHDDDDDK.",
        ".KDDDDDDDDDDDDK.",
        ".KDDDDDDDDDDDDK.",
        ".KKKKKKKKKKKKKK.",
        "................",
        "................",
    ],
    "user-trash": [
        "................",
        "......KKKK......",
        "..KKKKKKKKKKKK..",
        "..KLLLLLLLLLLK..",
        "..KKKKKKKKKKKK..",
        "...KDDDDDDDDK...",
        "...KDHDDHDDHK...",
        "...KDHDDHDDHK...",
        "...KDHDDHDDHK...",
        "...KDHDDHDDHK...",
        "...KDHDDHDDHK...",
        "...KDHDDHDDHK...",
        "...KDDDDDDDDK...",
        "....KKKKKKKK....",
        "................",
        "................",
    ],
}
SIZES = {16: 1, 22: None, 24: None, 32: 2, 48: 3, 64: 4, 128: 8}


def rgba(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) + (255,)


def draw(rows):
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, c in enumerate(row):
            if c in PAL:
                img.putpixel((x, y), rgba(PAL[c]))
    return img


def folder(mark):
    img = draw(FOLDER)
    if mark:
        img.alpha_composite(draw([r.ljust(16, ".") for r in mark] + ["." * 16] * 10).crop((0, 0, 6, 6)), (5, 7))
    return img


def build_icons(name, folder_out):
    icons = {key: folder(mark) for key, mark in MARKS.items()}
    icons.update({key: draw(rows) for key, rows in APPS.items()})
    # Same pictures under the other names apps ask for
    aliases = {"user-home": ["folder-home"], "system-file-manager": ["org.kde.dolphin"],
               "utilities-terminal": ["org.kde.konsole"], "systemsettings": ["preferences-system"],
               "plasmadiscover": ["org.kde.discover"], "user-trash": ["user-trash-full", "trashcan_empty"],
               "folder-download": ["folder-downloads"], "folder-games": ["applications-games"]}
    icons["system-file-manager"] = folder("..HH..|.H..H.|.H..H.|..HH..|...H..|....H.".split("|"))
    dirs = []
    for size, scale in SIZES.items():
        for context, keys in (("places", [k for k in icons if not k.startswith(("utilities", "system", "plasma"))]),
                              ("apps", ["utilities-terminal", "systemsettings", "plasmadiscover", "system-file-manager"])):
            d = f"{size}x{size}/{context}"
            os.makedirs(os.path.join(folder_out, d), exist_ok=True)
            dirs.append((d, size, context))
            for key in keys:
                img = icons[key]
                if scale:
                    out = img.resize((16 * scale, 16 * scale), Image.NEAREST)
                else:
                    # 22 and 24: the 16 pixel art centered, crisp
                    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
                    out.alpha_composite(img, ((size - 16) // 2, (size - 16) // 2))
                out.save(os.path.join(folder_out, d, key + ".png"))
                for alias in aliases.get(key) or []:
                    out.save(os.path.join(folder_out, d, alias + ".png"))
    with open(os.path.join(folder_out, "index.theme"), "w") as f:
        f.write(f"[Icon Theme]\nName={name}\nComment=Pixel icons, the rest from Breeze Dark\n"
                "Inherits=breeze-dark,hicolor\nDirectories=" + ",".join(d for d, _, _ in dirs) + "\n")
        for d, size, context in dirs:
            ctx = "Places" if context == "places" else "Applications"
            f.write(f"\n[{d}]\nSize={size}\nContext={ctx}\nType=Fixed\n")
