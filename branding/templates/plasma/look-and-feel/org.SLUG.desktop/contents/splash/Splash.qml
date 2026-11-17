// $name desktop startup splash
import QtQuick

Rectangle {
    id: root
    color: "#0b0f14"

    // Set by Plasma as startup goes on, done at 6
    property int stage

    FontLoader { id: pixel; source: "images/font.ttf" }

    Image {
        id: logo
        anchors.centerIn: parent
        anchors.verticalCenterOffset: -60
        source: "images/logo.png"
        smooth: false
    }

    // Progress bar fills with each stage
    Rectangle {
        id: frame
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: logo.bottom
        anchors.topMargin: 40
        width: 320
        height: 16
        color: "transparent"
        border.color: "#5cff7a"
        border.width: 2

        Rectangle {
            x: 4
            y: 4
            height: 8
            width: (parent.width - 8) * Math.min(root.stage, 6) / 6
            color: "#5cff7a"
            Behavior on width { NumberAnimation { duration: 250 } }
        }
    }

    Text {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: frame.bottom
        anchors.topMargin: 10
        text: "ENGINE START"
        font.family: pixel.name
        font.pixelSize: 16
        color: "#8b97a3"
    }
}
