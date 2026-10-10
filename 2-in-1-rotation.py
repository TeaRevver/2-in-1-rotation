#!/usr/bin/env python3
# 2-in-1 rotation and device mode integration for Omarchy
# SPDX-FileCopyrightText: 2026 Trevor Fraser
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Gio, GLib

import subprocess
import os
import signal
from pathlib import Path

BUS_NAME = "org.surface.dtx"
OBJECT_PATH = "/org/surface/dtx"
INTERFACE = "org.surface.dtx"

bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)

MODE_FILE = Path(os.environ["XDG_RUNTIME_DIR"]) / "2-in-1-rotation-mode"


def publish_mode(mode):
    MODE_FILE.write_text(mode + "\n")

def hide_keyboard():
    subprocess.run(["pkill", "-USR1", "-x", "wvkbd-mobintl"], check=False)
    keyboard_state = Path(os.environ["XDG_RUNTIME_DIR"]) / "2-in-1-keyboard-visible"
    keyboard_state.unlink(missing_ok=True)

def get_mode():
    result = bus.call_sync(
        BUS_NAME,
        OBJECT_PATH,
        "org.freedesktop.DBus.Properties",
        "Get",
        GLib.Variant("(ss)", (INTERFACE, "DeviceMode")),
        GLib.VariantType.new("(v)"),
        Gio.DBusCallFlags.NONE,
        -1,
        None,
    )
    return result.unpack()[0]


def on_properties_changed(connection, sender, path, interface, signal, parameters):
    name, changed, invalidated = parameters.unpack()

    if name == INTERFACE and "DeviceMode" in changed:
        print(f"DTX mode: {changed['DeviceMode']}", flush=True)
        global current_mode
        current_mode = changed["DeviceMode"]
        publish_mode(current_mode)

        if current_mode == "laptop":
            hide_keyboard()

        if current_mode == "studio":
            set_keyboard_enabled(False)
        else:
            set_keyboard_enabled(True)

        update_rotation(get_orientation())

bus.signal_subscribe(
    BUS_NAME,
    "org.freedesktop.DBus.Properties",
    "PropertiesChanged",
    OBJECT_PATH,
    None,
    Gio.DBusSignalFlags.NONE,
    on_properties_changed,
)

SENSOR_BUS = "net.hadess.SensorProxy"
SENSOR_PATH = "/net/hadess/SensorProxy"
SENSOR_INTERFACE = "net.hadess.SensorProxy"


def on_sensor_changed(connection, sender, path, interface, signal, parameters):
    name, changed, invalidated = parameters.unpack()

    if name == SENSOR_INTERFACE and "AccelerometerOrientation" in changed:
        print(f"Orientation: {changed['AccelerometerOrientation']}", flush=True)
        update_rotation(changed["AccelerometerOrientation"])

bus.signal_subscribe(
    SENSOR_BUS,
    "org.freedesktop.DBus.Properties",
    "PropertiesChanged",
    SENSOR_PATH,
    None,
    Gio.DBusSignalFlags.NONE,
    on_sensor_changed,
)

def rotate(transform):
    command = (
        f'hl.monitor({{output="eDP-1", transform={transform}}}); '
        f'hl.device({{name="ipts-045e:0021-touchscreen", transform={transform}}}); '
        f'hl.device({{name="iptsd-virtual-touchscreen-045e:0021", transform={transform}}})'
    )
    subprocess.run(["hyprctl", "eval", command], check=True)

def set_keyboard_enabled(enabled):
    value = "true" if enabled else "false"

    devices = [
        "microsoft-surface-keyboard",
        "microsoft-surface-keyboard-touchpad",
    ]

    commands = [
        f'hl.device({{name="{device}", enabled={value}}})'
        for device in devices
    ]

    subprocess.run(
        ["hyprctl", "eval", "; ".join(commands)],
        check=True,
    )

ORIENTATIONS = {
    "normal": 0,
    "left-up": 1,
    "bottom-up": 2,
    "right-up": 3,
}

def get_orientation():
    result = bus.call_sync(
        SENSOR_BUS,
        SENSOR_PATH,
        "org.freedesktop.DBus.Properties",
        "Get",
        GLib.Variant("(ss)", (SENSOR_INTERFACE, "AccelerometerOrientation")),
        GLib.VariantType.new("(v)"),
        Gio.DBusCallFlags.NONE,
        -1,
        None,
    )
    return result.unpack()[0]

current_mode = "unknown"
current_transform = None

def update_rotation(orientation):
    global current_transform

    transform = 0 if current_mode == "laptop" else ORIENTATIONS.get(orientation)

    if transform is None or transform == current_transform:
        return

    rotate(transform)
    current_transform = transform
    print(f"Applied rotation: {transform}", flush=True)

loop = GLib.MainLoop()

def handle_sigterm(signum, frame):
    GLib.idle_add(loop.quit)

signal.signal(signal.SIGTERM, handle_sigterm)

accelerometer_claimed = False

try:
    bus.call_sync(
        SENSOR_BUS,
        SENSOR_PATH,
        SENSOR_INTERFACE,
        "ClaimAccelerometer",
        None,
        None,
        Gio.DBusCallFlags.NONE,
        -1,
        None,
    )

    accelerometer_claimed = True

    current_mode = get_mode()
    publish_mode(current_mode)

    if current_mode == "laptop":
        hide_keyboard()

    set_keyboard_enabled(current_mode != "studio")
    update_rotation(get_orientation())
    print(f"Initial DTX mode: {current_mode}", flush=True)
    loop.run()
except KeyboardInterrupt:
    print("\nStopped.")
finally:
    try:
        set_keyboard_enabled(True)
    except Exception as error:
        print(f"Failed to restore keyboard: {error}", flush=True)

    publish_mode("unknown")
    if accelerometer_claimed:
        bus.call_sync(
            SENSOR_BUS,
            SENSOR_PATH,
            SENSOR_INTERFACE,
            "ReleaseAccelerometer",
            None,
            None,
            Gio.DBusCallFlags.NONE,
            -1,
            None,
        )
