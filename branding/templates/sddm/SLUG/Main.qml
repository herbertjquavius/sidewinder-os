// $name login screen
import QtQuick
import QtQuick.Controls.Basic

Rectangle {
    id: root
    width: 1920
    height: 1080
    color: night

    property color hud: "#5cff7a"
    property color steel: "#8b97a3"
    property color night: "#0b0f14"
    property color ink: "#c9d1d9"

    FontLoader { id: pixel; source: "font.ttf" }

    // Last user, or the only user on first boot
    function firstUser() {
        if (userModel.lastUser !== "")
            return userModel.lastUser
        return userModel.count > 0 ? userModel.data(userModel.index(0, 0), Qt.UserRole + 1) : ""
    }

    function login() {
        sddm.login(user.text, pass.text, sessionModel.lastIndex)
    }

    Component.onCompleted: pass.forceActiveFocus()

    // Wallpaper behind everything
    Image {
        anchors.fill: parent
        source: config.background
        fillMode: Image.PreserveAspectCrop
        smooth: false
    }

    // Login panel
    Rectangle {
        anchors.centerIn: parent
        width: 440
        height: col.height + 64
        color: "#e60b0f14"
        border.color: root.hud
        border.width: 4

        Column {
            id: col
            anchors.centerIn: parent
            width: 360
            spacing: 18

            Image {
                anchors.horizontalCenter: parent.horizontalCenter
                source: "logo.png"
                smooth: false
            }

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: "PILOT LOGIN"
                font.family: pixel.name
                font.pixelSize: 24
                color: root.hud
            }

            TextField {
                id: user
                width: parent.width
                text: root.firstUser()
                placeholderText: "NAME"
                font.family: pixel.name
                font.pixelSize: 16
                color: root.ink
                placeholderTextColor: root.steel
                background: Rectangle { color: root.night; border.color: user.activeFocus ? root.hud : root.steel; border.width: 2 }
                onAccepted: pass.forceActiveFocus()
            }

            TextField {
                id: pass
                width: parent.width
                echoMode: TextInput.Password
                placeholderText: "PASSWORD"
                font.family: pixel.name
                font.pixelSize: 16
                color: root.ink
                placeholderTextColor: root.steel
                background: Rectangle { color: root.night; border.color: pass.activeFocus ? root.hud : root.steel; border.width: 2 }
                onAccepted: root.login()
            }

            Button {
                id: go
                width: parent.width
                text: "TAKE OFF"
                font.family: pixel.name
                font.pixelSize: 16
                onClicked: root.login()
                contentItem: Text { text: go.text; font: go.font; color: root.night; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                background: Rectangle { implicitHeight: 44; color: go.down ? "#3ccf5f" : root.hud }
            }

            Text {
                id: msg
                width: parent.width
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
                font.family: pixel.name
                font.pixelSize: 16
                color: "#ff5a36"
            }
        }
    }

    // Restart and power off
    Row {
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: 32
        spacing: 16

        Button {
            id: restart
            text: "RESTART"
            font.family: pixel.name
            font.pixelSize: 16
            onClicked: sddm.reboot()
            contentItem: Text { text: restart.text; font: restart.font; color: restart.hovered ? root.hud : root.steel; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
            background: Rectangle { implicitWidth: 160; implicitHeight: 44; color: "#cc0b0f14"; border.color: restart.hovered ? root.hud : root.steel; border.width: 2 }
        }

        Button {
            id: off
            text: "POWER OFF"
            font.family: pixel.name
            font.pixelSize: 16
            onClicked: sddm.powerOff()
            contentItem: Text { text: off.text; font: off.font; color: off.hovered ? root.hud : root.steel; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
            background: Rectangle { implicitWidth: 160; implicitHeight: 44; color: "#cc0b0f14"; border.color: off.hovered ? root.hud : root.steel; border.width: 2 }
        }
    }

    // Plain message when the password is wrong
    Connections {
        target: sddm
        function onLoginFailed() {
            msg.text = "WRONG PASSWORD. TRY AGAIN."
            pass.text = ""
            pass.forceActiveFocus()
        }
    }
}
