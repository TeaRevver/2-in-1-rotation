#!/usr/bin/env python3
# Surface Book 2 rotation and device mode integration for Omarchy

from gi.repository import Gio, GLib

import subprocess

BUS_NAME = "org.surface.dtx"
OBJECT_PATH = "/org/surface/dtx"
INTERFACE = "org.surface.dtx"

bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)


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

def rotate(transform):
    command = (
        f'hl.monitor({{output="eDP-1", transform={transform}}}); '
        f'hl.device({{name="ipts-045e:0021-touchscreen", transform={transform}}})'
    )
    subprocess.run(["hyprctl", "eval", command], check=True)

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

current_mode = get_mode()
current_transform = None


def update_rotation(orientation):
    global current_transform

    transform = 0 if current_mode == "laptop" else ORIENTATIONS.get(orientation)

    if transform is None or transform == current_transform:
        return

    rotate(transform)
    current_transform = transform
    print(f"Applied rotation: {transform}", flush=True)

print(f"Initial DTX mode: {get_mode()}", flush=True)

try:
    GLib.MainLoop().run()
except KeyboardInterrupt:
    print("\nStopped.")
finally:
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
