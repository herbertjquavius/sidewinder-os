# Renders the login screen and startup splash offscreen, then makes a preview sheet
import os
import sys
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image
from PySide6.QtCore import Property, QObject, Qt, QUrl, Signal, Slot
from PySide6.QtGui import QGuiApplication, QStandardItem, QStandardItemModel
from PySide6.QtQuick import QQuickView, QQuickWindow, QSGRendererInterface

from make import OUT, P, emblem, load_name, rgb, slug_of, text, up


class Sddm(QObject):
    # Stand-in for the login manager
    loginFailed = Signal()

    @Slot(str, str, int)
    def login(self, user, password, session):
        self.loginFailed.emit()

    @Slot()
    def reboot(self):
        pass

    @Slot()
    def powerOff(self):
        pass


class Users(QStandardItemModel):
    # One fake user
    def __init__(self):
        super().__init__()
        item = QStandardItem()
        item.setData("pilot", Qt.UserRole + 1)
        self.appendRow(item)

    @Property(str, constant=True)
    def lastUser(self):
        return "pilot"

    @Property(int, constant=True)
    def count(self):
        return 1


class Sessions(QObject):
    @Property(int, constant=True)
    def lastIndex(self):
        return 0


class Config(QObject):
    @Property(str, constant=True)
    def background(self):
        return "background.png"


def shot(app, qml, ctx, props=None):
    # Loads a QML file at 1080p and grabs one frame
    view = QQuickView()
    view.setResizeMode(QQuickView.SizeRootObjectToView)
    for k, v in ctx.items():
        view.rootContext().setContextProperty(k, v)
    view.setSource(QUrl.fromLocalFile(qml))
    if view.status() == QQuickView.Error:
        sys.exit("\n".join(e.toString() for e in view.errors()))
    for k, v in (props or {}).items():
        view.rootObject().setProperty(k, v)
    view.resize(1920, 1080)
    view.show()
    end = time.time() + 1.5
    while time.time() < end:
        app.processEvents()
        time.sleep(0.02)
    path = os.path.join("/tmp", os.path.basename(qml) + ".png")
    view.grabWindow().save(path)
    return Image.open(path).convert("RGB")


def main():
    QQuickWindow.setGraphicsApi(QSGRendererInterface.GraphicsApi.Software)
    app = QGuiApplication(sys.argv)
    name = load_name()
    slug = slug_of(name)
    ctx = {"sddm": Sddm(), "userModel": Users(), "sessionModel": Sessions(), "config": Config()}
    login = shot(app, os.path.join(OUT, "sddm", slug, "Main.qml"), ctx)
    splash = shot(app, os.path.join(OUT, "plasma", "look-and-feel", f"org.{slug}.desktop",
                                    "contents", "splash", "Splash.qml"), {}, {"stage": 4})

    # Boot menu with two mock entries
    grub = Image.open(os.path.join(OUT, "grub", slug, "background.png")).convert("RGB")
    for i, (line, col) in enumerate([(f"{name} (current)", P["H"]), (f"{name} (previous version)", P["L"])]):
        t = up(text(line, col), 3)
        grub.paste(t, (600, 480 + i * 40), t)

    sheet = Image.new("RGB", (1920, 1080), rgb(P["K"]))
    for i, im in enumerate([login, splash, grub]):
        sheet.paste(im.resize((960, 540), Image.NEAREST), ((i % 2) * 960, (i // 2) * 540))
    big = up(emblem(), 10)
    sheet.paste(big, (1200, 570), big)
    sheet.save(os.path.join(OUT, "preview-2.png"))
    print("Saved", os.path.join(OUT, "preview-2.png"))


if __name__ == "__main__":
    main()
