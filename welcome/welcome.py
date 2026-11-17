# Welcome app: big buttons for updates, fixes and game mode, no terminal needed
import glob
import os
import re
import shutil
import subprocess
import sys

from PySide6.QtCore import QProcess, Qt, QTimer, QUrl
from PySide6.QtGui import QDesktopServices, QFontDatabase, QPixmap
from PySide6.QtWidgets import (QApplication, QDialog, QGridLayout, QHBoxLayout, QLabel, QMessageBox,
                               QPushButton, QVBoxLayout, QWidget)

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.join(HERE, "..")

CSS = """
QWidget { background: #0b0f14; color: #c9d1d9; font-family: "%s"; font-size: 16px; }
QPushButton { background: #141a22; border: 3px solid #3a4450; padding: 12px; }
QPushButton:hover { border-color: #5cff7a; }
QPushButton:pressed, QPushButton:checked { background: #14301c; border-color: #5cff7a; }
QPushButton:disabled { border-color: #1d242e; }
QLabel#title { color: #5cff7a; font-size: 32px; }
QLabel#big { color: #5cff7a; font-size: 24px; background: transparent; }
QLabel#small { color: #8b97a3; background: transparent; }
QLabel#status { color: #ffb000; }
QPushButton#restart { background: #5cff7a; color: #0b0f14; border: none; font-size: 24px; padding: 12px 24px; }
QPushButton#about { color: #8b97a3; border-width: 2px; padding: 6px 14px; }
QLabel a { color: #5cff7a; }
"""


def read_env(path):
    # Reads KEY="value" lines into a dict
    env = {}
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                m = re.match(r'\s*([A-Z_]+)\s*=\s*"?([^"\n]*)"?', line)
                if m:
                    env[m.group(1)] = m.group(2)
    return env


def load_info():
    # Name, slug and links from the installed system, or from the repo when developing
    slug = read_env("/etc/os-release").get("VARIANT_ID", "")
    env = read_env(f"/usr/share/{slug}/distro.env") if slug else {}
    if not env:
        env = read_env(os.path.join(REPO, "distro.env"))
        slug = re.sub(r"[^a-z0-9]+", "-", env.get("NAME", "distro").lower()).strip("-")
    return env.get("NAME", "Distro"), slug, env


# Green jet HUD look for MangoHud, list values joined with +
HUD_STYLE = ("fps,frametime=0,frame_timing,gpu_stats,gpu_temp,cpu_stats,cpu_temp,ram,position=top-left,"
             "hud_compact,round_corners=0,font_size=20,background_alpha=0.35,background_color=0B0F14,"
             "text_color=5CFF7A,gpu_color=5CFF7A,cpu_color=5CFF7A,ram_color=5CFF7A,frametime_color=5CFF7A,"
             "fps_color_change,fps_value=30+60,fps_color=FF5A36+FFB000+5CFF7A,toggle_hud=Shift_R+F12")


def read_text(path):
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return ""


def first_existing(*paths):
    return next((p for p in paths if os.path.exists(p)), None)


class BigButton(QPushButton):
    # Big button with a title and a plain explanation under it
    def __init__(self, title, text):
        super().__init__()
        self.setMinimumSize(340, 92)
        self.setCursor(Qt.PointingHandCursor)
        lay = QVBoxLayout(self)
        self.title = QLabel(title, objectName="big")
        self.text = QLabel(text, objectName="small")
        self.text.setWordWrap(True)
        for w in (self.title, self.text):
            w.setAttribute(Qt.WA_TransparentForMouseEvents)
            lay.addWidget(w)


class Welcome(QWidget):
    def __init__(self, name, slug, env, logo):
        super().__init__()
        self.name, self.env = name, env
        self.wiki = env.get("WIKI_URL", "")
        self.helper = f"/usr/libexec/{slug}-welcome-helper"
        self.setWindowTitle(f"{name} Welcome")
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 24)
        root.setSpacing(16)

        # Header with logo and greeting
        head = QHBoxLayout()
        if logo:
            pic = QLabel()
            pic.setPixmap(QPixmap(logo))
            head.addWidget(pic)
        words = QVBoxLayout()
        words.addWidget(QLabel(f"Welcome to {name}", objectName="title"))
        words.addWidget(QLabel("Everything you need is one click away.", objectName="small"))
        head.addLayout(words)
        head.addStretch()
        root.addLayout(head)

        # The big buttons
        self.update_btn = BigButton("UPDATE", "Get the newest version of everything")
        self.fix_btn = BigButton("FIX PROBLEMS", "Sound, Wi-Fi, controller or apps acting up")
        self.game_btn = BigButton("GAME MODE: OFF", "Full power for games. Best when plugged in")
        self.hud_btn = BigButton("HUD: OFF", "Fighter jet style FPS and temps in every Steam game")
        self.saves_btn = BigButton("SAVES", "Backed up every day. Open to restore one")
        self.tv_btn = BigButton("TV MODE", "Steam full screen, made for a controller")
        self.back_btn = BigButton("GO BACK", "Undo the last update if something broke")
        self.wiki_btn = BigButton("WIKI", "Help pages for everything, from games to fixes")
        self.buttons = [self.update_btn, self.fix_btn, self.game_btn, self.hud_btn,
                        self.saves_btn, self.tv_btn, self.back_btn, self.wiki_btn]
        grid = QGridLayout()
        grid.setSpacing(16)
        for i, b in enumerate(self.buttons):
            grid.addWidget(b, i // 2, i % 2)
        root.addLayout(grid)

        # Status line and restart button
        bottom = QHBoxLayout()
        self.status = QLabel("", objectName="status")
        self.status.setWordWrap(True)
        self.restart_btn = QPushButton("RESTART NOW", objectName="restart")
        self.restart_btn.hide()
        bottom.addWidget(self.status, 1)
        bottom.addWidget(self.restart_btn)
        root.addLayout(bottom)
        foot = QHBoxLayout()
        foot.addWidget(QLabel(f"Find this again in the app menu: {name} Welcome", objectName="small"), 1)
        # Battery care only shows on laptops that support a charge limit
        self.battery_btn = None
        if glob.glob("/sys/class/power_supply/BAT*/charge_control_end_threshold"):
            self.battery_btn = QPushButton("", objectName="about")
            self.battery_btn.setCheckable(True)
            self.battery_btn.setChecked(read_text(f"/etc/{slug}/battery-limit") == "on")
            self.battery_label()
            self.battery_btn.toggled.connect(self.do_battery)
            foot.addWidget(self.battery_btn)
        term_btn = QPushButton("TERMINAL", objectName="about")
        term_btn.clicked.connect(self.do_terminal)
        foot.addWidget(term_btn)
        about_btn = QPushButton("ABOUT", objectName="about")
        about_btn.clicked.connect(self.do_about)
        foot.addWidget(about_btn)
        root.addLayout(foot)

        # First boot: the game apps download in the background, say so until they're done
        self.apps_marker = f"/var/lib/{slug}/flatpaks-done"
        if os.path.exists(f"/usr/libexec/{slug}-flatpaks") and not os.path.exists(self.apps_marker):
            self.status.setText("Installing Steam and your other game apps in the background. "
                                "This can take a few minutes.")
            self.apps_timer = QTimer(self)
            self.apps_timer.timeout.connect(self.check_apps)
            self.apps_timer.start(15000)

        self.update_btn.clicked.connect(self.do_update)
        self.fix_btn.clicked.connect(self.do_fix)
        self.back_btn.clicked.connect(self.do_back)
        self.wiki_btn.clicked.connect(self.do_wiki)
        self.saves_btn.clicked.connect(self.do_saves)
        self.tv_btn.clicked.connect(self.do_tv)
        self.hud_btn.setCheckable(True)
        self.hud_btn.setChecked("MANGOHUD=1" in self.steam_overrides())
        self.hud_label()
        self.hud_btn.toggled.connect(self.do_hud)
        self.restart_btn.clicked.connect(lambda: QProcess.startDetached("systemctl", ["reboot"]))
        self.game_btn.setCheckable(True)
        self.game_btn.setChecked(self.power_profile() == "performance")
        self.game_label()
        self.game_btn.toggled.connect(self.do_game)

    # Runs commands one by one, showing a plain message for each
    def run_steps(self, steps, finish, keep_going=False):
        self.steps, self.finish, self.keep_going = list(steps), finish, keep_going
        self.failed, self.output = [], ""
        self.restart_btn.hide()
        for b in self.buttons:
            b.setEnabled(False)
        self.next_step()

    def next_step(self):
        if not self.steps:
            for b in self.buttons:
                b.setEnabled(True)
            self.finish()
            return
        msg, cmd, self.fail_msg = self.steps.pop(0)
        self.status.setText(msg)
        self.proc = QProcess(self)
        self.proc.finished.connect(self.step_done)
        self.proc.errorOccurred.connect(self.step_error)
        self.proc.start(cmd[0], cmd[1:])

    def step_done(self, code, _status=None):
        self.output += bytes(self.proc.readAllStandardOutput()).decode(errors="ignore")
        if code == 126:
            # Password window was closed
            self.failed.append("Cancelled, nothing changed.")
            self.steps = []
        elif code != 0:
            self.failed.append(self.fail_msg)
            if not self.keep_going:
                self.steps = []
        self.next_step()

    def step_error(self, err):
        # Program missing, so finished never fires
        if err == QProcess.FailedToStart:
            self.step_done(1)

    def do_update(self):
        steps = [
            ("Downloading the new system. This can take a while...", ["pkexec", self.helper, "update"],
             "Couldn't download the update. Check your Wi-Fi and try again."),
            ("Updating your apps...", ["flatpak", "update", "-y", "--noninteractive"],
             "Your apps couldn't update. Try again later."),
        ]

        def finish():
            if self.failed:
                self.status.setText(self.failed[0])
            elif "staged" in self.output:
                self.status.setText("Update ready! Restart when you're done playing.")
                self.restart_btn.show()
            else:
                self.status.setText("You already have the newest version.")
        self.run_steps(steps, finish)

    def do_fix(self):
        steps = [
            ("Restarting sound...", ["systemctl", "--user", "restart", "wireplumber", "pipewire", "pipewire-pulse"], "sound"),
            ("Restarting Wi-Fi and Bluetooth...", ["pkexec", self.helper, "fix-network"], "Wi-Fi and Bluetooth"),
            ("Checking your apps for damage...", ["flatpak", "repair", "--user"], "apps"),
        ]

        def finish():
            if self.failed:
                self.status.setText("Couldn't fix: " + ", ".join(self.failed) + " Try restarting, or check the wiki.")
            else:
                self.status.setText("All fixed up! If something's still wrong, restart the laptop.")
        self.run_steps(steps, finish, keep_going=True)

    def do_back(self):
        answer = QMessageBox.question(self, "Go back?", "Go back to the version before the last update?\n"
                                      "Your games and saves stay safe.")
        if answer != QMessageBox.Yes:
            return
        steps = [("Getting the previous version ready...", ["pkexec", self.helper, "rollback"],
                  "Couldn't go back. Check the wiki for help.")]

        def finish():
            if self.failed:
                self.status.setText(self.failed[0])
            else:
                self.status.setText("Previous version is ready. Restart to use it.")
                self.restart_btn.show()
        self.run_steps(steps, finish)

    def power_profile(self):
        try:
            return subprocess.run(["powerprofilesctl", "get"], capture_output=True, text=True, timeout=3).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return ""

    def game_label(self):
        self.game_btn.title.setText("GAME MODE: ON" if self.game_btn.isChecked() else "GAME MODE: OFF")

    def do_game(self, on):
        try:
            subprocess.run(["powerprofilesctl", "set", "performance" if on else "balanced"], check=True, timeout=5)
            self.status.setText("Game mode on. Full power!" if on else "Game mode off. Back to normal.")
        except (OSError, subprocess.SubprocessError):
            self.game_btn.blockSignals(True)
            self.game_btn.setChecked(not on)
            self.game_btn.blockSignals(False)
            self.status.setText("Couldn't change the power mode. Try restarting the laptop.")
        self.game_label()

    def do_wiki(self):
        if self.wiki:
            QDesktopServices.openUrl(QUrl(self.wiki))
        else:
            self.status.setText("The wiki is coming soon.")

    def check_apps(self):
        if os.path.exists(self.apps_marker):
            self.apps_timer.stop()
            self.status.setText("Your game apps are ready! Steam is in the panel at the bottom.")

    def do_about(self):
        # Credits for everything this is built on
        home = self.env.get("HOME_URL", "")
        text = (f"<b>{self.name}</b> is a gaming system for people who just want to play.<br><br>"
                "Built on the work of:<br>"
                "&bull; Fedora Kinoite (Fedora Project)<br>"
                "&bull; Universal Blue<br>"
                "&bull; KDE Plasma<br>"
                "&bull; CachyOS kernel and the LAVD scheduler (CachyOS, sched_ext)<br>"
                "&bull; NVIDIA driver packages (negativo17)<br>"
                "&bull; Steam (Valve), Heroic, Lutris, ProtonUp-Qt, MangoHud, GameMode<br><br>"
                f"{self.name} isn't made or endorsed by any of them. Thank you to all of them."
                + (f'<br><br><a href="{home}" style="color:#5cff7a">Project page</a>' if home else ""))
        box = QDialog(self)
        box.setWindowTitle(f"About {self.name}")
        lay = QVBoxLayout(box)
        lay.setContentsMargins(28, 24, 28, 24)
        label = QLabel(text)
        label.setWordWrap(True)
        label.setOpenExternalLinks(True)
        label.setMinimumWidth(520)
        lay.addWidget(label)
        ok = QPushButton("OK")
        ok.clicked.connect(box.accept)
        lay.addWidget(ok)
        box.exec()

    def steam_overrides(self):
        try:
            return subprocess.run(["flatpak", "override", "--user", "--show", "com.valvesoftware.Steam"],
                                  capture_output=True, text=True, timeout=5).stdout
        except (OSError, subprocess.SubprocessError):
            return ""

    def hud_label(self):
        self.hud_btn.title.setText("HUD: ON" if self.hud_btn.isChecked() else "HUD: OFF")

    def do_hud(self, on):
        # MangoHud in every Steam game, styled like a green jet HUD
        if on:
            cmd = ["flatpak", "override", "--user", "--env=MANGOHUD=1",
                   "--env=MANGOHUD_CONFIG=" + HUD_STYLE, "com.valvesoftware.Steam"]
        else:
            cmd = ["flatpak", "override", "--user", "--unset-env=MANGOHUD",
                   "--unset-env=MANGOHUD_CONFIG", "com.valvesoftware.Steam"]
        try:
            subprocess.run(cmd, check=True, timeout=10)
            self.status.setText("HUD on. Restart Steam to see it in games. Right Shift + F12 hides it."
                                if on else "HUD off. Restart Steam to remove it.")
        except (OSError, subprocess.SubprocessError):
            self.hud_btn.blockSignals(True)
            self.hud_btn.setChecked(not on)
            self.hud_btn.blockSignals(False)
            self.status.setText("Couldn't change the HUD. Is Steam installed yet?")
        self.hud_label()

    def do_saves(self):
        # Ludusavi shows every backup and restores with one click
        if QProcess.startDetached("flatpak", ["run", "com.github.mtkennerly.ludusavi"]):
            self.status.setText("Your saves are backed up every day to Game Save Backups in your home folder. "
                                "Use the Restore tab to bring one back.")
        else:
            self.status.setText("The save backup app isn't installed yet. Try again in a few minutes.")

    def do_tv(self):
        if QProcess.startDetached("flatpak", ["run", "com.valvesoftware.Steam", "steam://open/bigpicture"]):
            self.status.setText("Opening TV mode. Press the Steam or guide button on your controller to get around.")
        else:
            self.status.setText("Steam isn't installed yet. Try again in a few minutes.")

    def battery_label(self):
        self.battery_btn.setText("BATTERY CARE: ON" if self.battery_btn.isChecked() else "BATTERY CARE: OFF")

    def do_battery(self, on):
        steps = [("Saving battery setting...", ["pkexec", self.helper, "battery-on" if on else "battery-off"],
                  "Couldn't change battery care.")]

        def finish():
            if self.failed:
                self.status.setText(self.failed[0])
                self.battery_btn.blockSignals(True)
                self.battery_btn.setChecked(not on)
                self.battery_btn.blockSignals(False)
            else:
                self.status.setText("Battery care on: charging stops at 80% so the battery lasts years longer."
                                    if on else "Battery care off: charging to 100%.")
            self.battery_label()
        self.run_steps(steps, finish)

    def do_terminal(self):
        for t in ("konsole", "ptyxis", "gnome-terminal", "xterm"):
            if shutil.which(t):
                QProcess.startDetached(t, [])
                return
        self.status.setText("No terminal app found.")


def main():
    args = sys.argv[1:]
    name, slug, env = load_info()

    # Shows only once when started from autostart
    if "--first-run" in args:
        marker = os.path.expanduser(f"~/.config/{slug}/welcome-done")
        if os.path.exists(marker):
            return
        os.makedirs(os.path.dirname(marker), exist_ok=True)
        open(marker, "w").close()

    app = QApplication(sys.argv)
    family = "sans-serif"
    font = first_existing(f"/usr/share/fonts/{slug}/{slug}-pixel.ttf",
                          os.path.join(REPO, "branding", "out", "fonts", f"{slug}-pixel.ttf"))
    if font:
        fams = QFontDatabase.applicationFontFamilies(QFontDatabase.addApplicationFont(font))
        family = fams[0] if fams else family
    app.setStyleSheet(CSS % family)
    logo = first_existing(f"/usr/share/icons/hicolor/96x96/apps/{slug}.png",
                          os.path.join(REPO, "branding", "out", "logo-96.png"))
    win = Welcome(name, slug, env, logo)
    win.show()

    # Saves a screenshot for previews
    if "--shot" in args:
        win.status.setText("Update ready! Restart when you're done playing.")
        win.restart_btn.show()
        path = args[args.index("--shot") + 1]
        QTimer.singleShot(500, lambda: (win.grab().save(path), app.quit()))
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
