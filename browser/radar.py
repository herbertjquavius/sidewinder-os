# Radar: Sidewinder's everyday browser. Pixel HUD look, built-in ad blocking and a game mode
import os
import re
import subprocess
import sys

from PySide6.QtCore import QStandardPaths, Qt, QTimer, QUrl
from PySide6.QtGui import QAction, QFontDatabase, QIcon, QKeySequence
from PySide6.QtWebEngineCore import (QWebEnginePage, QWebEngineProfile, QWebEngineScript,
                                     QWebEngineSettings, QWebEngineUrlRequestInterceptor)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QPushButton,
                               QTabWidget, QVBoxLayout, QWidget)

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.join(HERE, "..")
SHORTS = "https://www.youtube.com/shorts"
SEARCH = "https://www.google.com/search?q="

CSS = """
* { font-family: "%s"; font-size: 16px; }
QMainWindow, QWidget#chrome { background: #0b0f14; color: #c9d1d9; }
QPushButton { background: #141a22; color: #5cff7a; border: 2px solid #3a4450; padding: 4px 10px; min-height: 22px; }
QPushButton:hover { border-color: #5cff7a; }
QPushButton:checked { background: #14301c; border-color: #5cff7a; }
QLineEdit { background: #0b0f14; color: #c9d1d9; border: 2px solid #3a4450; padding: 4px 8px; }
QLineEdit:focus { border-color: #5cff7a; }
QTabWidget::pane { border: none; }
QTabBar { background: #0b0f14; }
QTabBar::tab { background: #141a22; color: #8b97a3; border: 2px solid #3a4450; border-bottom: none;
               padding: 6px 12px; margin-right: 4px; max-width: 220px; }
QTabBar::tab:selected { color: #5cff7a; border-color: #5cff7a; background: #0b0f14; }
QLabel#badge { color: #0b0f14; background: #5cff7a; padding: 2px 8px; }
QLabel#title { color: #5cff7a; }
"""


def read_env(path):
    env = {}
    try:
        with open(path) as f:
            for line in f:
                m = re.match(r'\s*([A-Z_]+)\s*=\s*"?([^"\n]*)"?', line)
                if m:
                    env[m.group(1)] = m.group(2)
    except OSError:
        pass
    return env


def find_slug():
    # Installed system first, the repo when developing
    slug = read_env("/etc/os-release").get("VARIANT_ID", "")
    if slug and os.path.exists(f"/usr/share/{slug}"):
        return slug
    name = read_env(os.path.join(REPO, "distro.env")).get("NAME", "distro")
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def first(*paths):
    return next((p for p in paths if p and os.path.exists(p)), None)


class Blocker(QWebEngineUrlRequestInterceptor):
    # Drops requests to ad and tracker hosts, plus YouTube's ad calls
    def __init__(self, hosts):
        super().__init__()
        self.hosts = hosts
        self.blocked = 0

    def interceptRequest(self, info):
        url = info.requestUrl()
        host = url.host().lower()
        parts = host.split(".")
        hit = any(".".join(parts[i:]) in self.hosts for i in range(len(parts) - 1))
        path = url.path()
        if hit or (host.endswith("youtube.com") and ("/pagead/" in path or "/api/stats/ads" in path or
                                                    "/ptracking" in path or "/get_midroll" in path)):
            info.block(True)
            self.blocked += 1


class Page(QWebEnginePage):
    # Links that want a new window open in a new tab instead
    def __init__(self, profile, browser):
        super().__init__(profile, browser)
        self.browser = browser

    def createWindow(self, _type):
        return self.browser.new_tab().page()


class Browser(QMainWindow):
    def __init__(self, profile, home, icon, shorts_only=False):
        super().__init__()
        self.profile, self.home, self.shorts_only = profile, home, shorts_only
        self.setWindowTitle("Radar" + (" Shorts" if shorts_only else ""))
        if icon:
            self.setWindowIcon(QIcon(icon))

        chrome = QWidget(objectName="chrome")
        bar = QHBoxLayout(chrome)
        bar.setContentsMargins(8, 8, 8, 6)
        bar.setSpacing(6)
        if shorts_only:
            # Shorts mode: just a title, auto-scroll and the window itself
            bar.addWidget(QLabel("RADAR // SHORTS", objectName="title"))
            bar.addStretch()
            self.auto_btn = QPushButton("AUTO-SCROLL")
            self.auto_btn.setCheckable(True)
            self.auto_btn.toggled.connect(self.set_auto)
            bar.addWidget(self.auto_btn)
        else:
            for text, slot in (("<", lambda: self.view().back()), (">", lambda: self.view().forward()),
                               ("R", lambda: self.view().reload())):
                b = QPushButton(text)
                b.clicked.connect(slot)
                bar.addWidget(b)
            self.address = QLineEdit()
            self.address.setPlaceholderText("SEARCH OR TYPE AN ADDRESS")
            self.address.returnPressed.connect(self.go)
            bar.addWidget(self.address, 1)
            plus = QPushButton("+")
            plus.clicked.connect(lambda: self.new_tab(self.home))
            bar.addWidget(plus)
        self.badge = QLabel("GAME MODE", objectName="badge")
        self.badge.setToolTip("A game is running, background tabs are paused so it gets full power")
        self.badge.hide()
        bar.addWidget(self.badge)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(not shorts_only)
        self.tabs.tabBar().setVisible(not shorts_only)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.tab_changed)

        body = QWidget()
        lay = QVBoxLayout(body)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(chrome)
        lay.addWidget(self.tabs, 1)
        self.chrome = chrome
        self.setCentralWidget(body)

        # Keyboard shortcuts like any browser
        for keys, slot in ((QKeySequence.AddTab, lambda: self.new_tab(self.home)),
                           (QKeySequence.Close, lambda: self.close_tab(self.tabs.currentIndex())),
                           (QKeySequence.Refresh, lambda: self.view().reload()),
                           (QKeySequence("Ctrl+L"), self.focus_address),
                           (QKeySequence("F11"), self.toggle_full)):
            act = QAction(self)
            act.setShortcut(keys)
            act.triggered.connect(slot)
            self.addAction(act)

        # Game mode check every few seconds
        self.game_timer = QTimer(self)
        self.game_timer.timeout.connect(self.check_game)
        self.game_timer.start(8000)

    def view(self):
        return self.tabs.currentWidget()

    def new_tab(self, url=None):
        view = QWebEngineView()
        page = Page(self.profile, self)
        view.setPage(page)
        page.fullScreenRequested.connect(self.full_screen)
        view.titleChanged.connect(lambda t, v=view: self.set_title(v, t))
        view.urlChanged.connect(lambda u, v=view: self.url_changed(v, u))
        i = self.tabs.addTab(view, "NEW TAB")
        self.tabs.setCurrentIndex(i)
        if url:
            view.setUrl(QUrl(url) if "://" in url else QUrl.fromLocalFile(url))
        return view

    def close_tab(self, i):
        if self.tabs.count() <= 1:
            self.close()
            return
        w = self.tabs.widget(i)
        self.tabs.removeTab(i)
        w.deleteLater()

    def set_title(self, view, title):
        i = self.tabs.indexOf(view)
        if i >= 0:
            self.tabs.setTabText(i, (title or "NEW TAB")[:28])
            self.tabs.setTabToolTip(i, title)

    def url_changed(self, view, url):
        if not self.shorts_only and view is self.view():
            self.address.setText("" if url.isLocalFile() else url.toString())

    def tab_changed(self, _i):
        if not self.shorts_only and self.view():
            u = self.view().url()
            self.address.setText("" if u.isLocalFile() else u.toString())

    def focus_address(self):
        if not self.shorts_only:
            self.address.setFocus()
            self.address.selectAll()

    def go(self):
        # Addresses open, anything else gets searched
        text = self.address.text().strip()
        if not text:
            return
        if re.match(r"^[a-z]+://", text):
            url = text
        elif " " not in text and "." in text:
            url = "https://" + text
        else:
            url = SEARCH + QUrl.toPercentEncoding(text).data().decode()
        self.view().setUrl(QUrl(url))

    def full_screen(self, request):
        request.accept()
        self.chrome.setVisible(not request.toggleOn())
        self.tabs.tabBar().setVisible(not request.toggleOn() and not self.shorts_only)
        self.showFullScreen() if request.toggleOn() else self.showNormal()

    def toggle_full(self):
        self.showNormal() if self.isFullScreen() else self.showFullScreen()

    def set_auto(self, on):
        self.view().page().runJavaScript(f"window.__radarAutoScroll = {'true' if on else 'false'};")

    def check_game(self):
        # GameMode tells us when a game is running; pause every tab you can't see
        try:
            out = subprocess.run(["gamemoded", "-s"], capture_output=True, text=True, timeout=2).stdout
        except (OSError, subprocess.SubprocessError):
            out = ""
        gaming = "is active" in out
        self.badge.setVisible(gaming)
        for i in range(self.tabs.count()):
            page = self.tabs.widget(i).page()
            want = QWebEnginePage.LifecycleState.Frozen if gaming and i != self.tabs.currentIndex() \
                else QWebEnginePage.LifecycleState.Active
            if page.lifecycleState() != want and (want == QWebEnginePage.LifecycleState.Active or
                                                  page.recommendedState() != QWebEnginePage.LifecycleState.Active):
                page.setLifecycleState(want)


WINDOWS = []


def open_shorts(profile, home, icon):
    w = Browser(profile, home, None, shorts_only=True)
    w.setWindowIcon(icon if isinstance(icon, QIcon) else QIcon(icon or ""))
    w.resize(460, 860)
    w.new_tab(SHORTS)
    w.show()
    WINDOWS.append(w)
    return w


def make_profile(slug):
    # One saved profile so logins stick, with the blocker and the YouTube helper
    profile = QWebEngineProfile("radar")
    profile.setHttpUserAgent(re.sub(r"QtWebEngine/\S+ ", "", profile.httpUserAgent()))
    hosts = set()
    for path in (first(f"/usr/share/{slug}/radar/blocklist.txt", os.path.join(HERE, "blocklist.txt")),):
        if path:
            with open(path) as f:
                hosts |= {l.strip() for l in f if l.strip() and not l.startswith("#")}
    blocker = Blocker(hosts)
    profile.setUrlRequestInterceptor(blocker)
    profile._blocker = blocker
    js_path = first(f"/usr/share/{slug}/radar/youtube.js", os.path.join(HERE, "youtube.js"))
    if js_path:
        script = QWebEngineScript()
        script.setName("radar-youtube")
        with open(js_path) as f:
            script.setSourceCode(f.read())
        script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentReady)
        script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
        script.setRunsOnSubFrames(False)
        profile.scripts().insert(script)
    s = profile.settings()
    s.setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
    s.setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)
    s.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
    s.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
    # Downloads go straight to the Downloads folder
    downloads = QStandardPaths.writableLocation(QStandardPaths.DownloadLocation)

    def download(item):
        item.setDownloadDirectory(downloads)
        item.accept()
    profile.downloadRequested.connect(download)
    return profile


def main():
    args = sys.argv[1:]
    app = QApplication(sys.argv)
    app.setApplicationName("Radar")
    app.setDesktopFileName(f"{find_slug()}-radar")
    slug = find_slug()
    font = first(f"/usr/share/fonts/{slug}/{slug}-pixel.ttf",
                 os.path.join(REPO, "branding", "out", "fonts", f"{slug}-pixel.ttf"))
    family = "monospace"
    if font:
        fams = QFontDatabase.applicationFontFamilies(QFontDatabase.addApplicationFont(font))
        family = fams[0] if fams else family
    app.setStyleSheet(CSS % family)
    home = first(f"/usr/share/{slug}/startpage/index.html",
                 os.path.join(REPO, "branding", "out", "startpage", "index.html")) or "about:blank"
    icon = first(f"/usr/share/icons/hicolor/96x96/apps/{slug}-radar.png",
                 os.path.join(REPO, "branding", "out", "icons", "96x96", f"{slug}-radar.png"))
    profile = make_profile(slug)

    shot = args[args.index("--shot") + 1] if "--shot" in args else None
    if "--shorts" in args:
        win = open_shorts(profile, home, icon)
    else:
        win = Browser(profile, home, icon)
        urls = [a for a in args if "://" in a or a.startswith("www.")]
        if urls:
            for u in urls:
                win.new_tab(u if "://" in u else "https://" + u)
        else:
            win.new_tab(home)
        win.resize(1280, 800)
        win.show()

    # Saves a screenshot for previews
    if shot:
        QTimer.singleShot(3500, lambda: (win.grab().save(shot), app.quit()))
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
