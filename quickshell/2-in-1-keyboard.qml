// SPDX-FileCopyrightText: 2026 Trevor Fraser
// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import Quickshell
import Quickshell.Io

Item {
    id: root

    property var bar
    property string moduleName
    property var settings
    property string surfaceMode: ""

    implicitWidth: root.surfaceMode === "tablet" || root.surfaceMode === "studio" ? 65 : 0
    implicitHeight: bar ? bar.barSize : 26

    FileView {
        id: modeFile
        path: Quickshell.env("XDG_RUNTIME_DIR") + "/2-in-1-rotation-mode"
        watchChanges: true
        onFileChanged: reload()
        onLoaded: root.surfaceMode = text().trim()
        onLoadFailed: console.log("Surface mode file load failed")
    }

    Text {
        id: modeText
        anchors.centerIn: parent
        text: "⌨"
        color: bar ? bar.foreground : "white"
        font.pixelSize: 22
    }
    MouseArea {
        anchors.fill: parent
        onClicked: bar.run("~/.local/bin/toggle-2-in-1-keyboard")
    }
}
