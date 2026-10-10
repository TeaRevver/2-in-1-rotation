# 2-in-1 Rotation for Omarchy

**Development status:** Preparing v1.0.0. The renamed integration has been installed and successfully tested on a Microsoft Surface Book 2. Installation from a fresh Git checkout has not yet been validated.

2-in-1 Rotation for Omarchy brings automatic display rotation and convertible-device integration to [Omarchy](https://github.com/omacom/omarchy), a Linux desktop built around Hyprland. It aims to provide a reusable foundation for 2-in-1, detachable and convertible computers. **The first implementation is developed and tested on a Microsoft Surface Book 2; other devices are not yet supported or tested.**

On the Surface Book 2, the project rotates the internal display and touchscreen together, responds to changes in the way the device is assembled, manages the physical keyboard and trackpad, and adds an on-screen keyboard button to the Omarchy bar.

## Quick Start: Surface Book 2 (first supported device)

**Installation status:** These steps reflect the successfully tested installation on the development machine. A fresh-checkout installation has not yet been independently tested. The GitHub repository URL must be supplied after publication.

**Before starting:** Omarchy and a working [Linux Surface](https://github.com/linux-surface/linux-surface) kernel/touchscreen setup are assumed. The commands below use Arch Linux's `pacman` and the AUR helper `yay`. Packages from the Arch User Repository (AUR) are community-maintained, not officially vetted by Arch or Omarchy; review package sources and build instructions before installing them.

1. Install the application dependencies and enable the Surface device-mode service:

   ```bash
   sudo pacman -S --needed python python-gobject iio-sensor-proxy quickshell
   yay -S surface-dtx-daemon wvkbd
   sudo systemctl enable --now surface-dtx-daemon.service
   ```

2. Once the GitHub repository is published, clone it to the **exact path** expected by the user service:

   ```bash
   mkdir -p ~/Projects
   git clone <REPOSITORY-URL> ~/Projects/2-in-1-rotation
   ```

   The `~/Projects` directory is a convenient convention on Omarchy systems, but the commands create it if absent; it is not a requirement of Omarchy. Replace `<REPOSITORY-URL>` with the published repository's GitHub clone URL. This placeholder is intentional; the project has not been published yet. If you use another directory, edit `ExecStart` in the service file before enabling it.

3. Copy the integration files into your user configuration and ensure the scripts are executable:

   ```bash
   mkdir -p ~/.local/bin ~/.config/omarchy/bar/modules ~/.config/systemd/user
   cp ~/Projects/2-in-1-rotation/scripts/toggle-2-in-1-keyboard ~/.local/bin/toggle-2-in-1-keyboard
   cp ~/Projects/2-in-1-rotation/quickshell/2-in-1-keyboard.qml ~/.config/omarchy/bar/modules/2-in-1-keyboard.qml
   cp ~/Projects/2-in-1-rotation/systemd/2-in-1-rotation.service ~/.config/systemd/user/2-in-1-rotation.service
   chmod +x ~/Projects/2-in-1-rotation/2-in-1-rotation.py ~/.local/bin/toggle-2-in-1-keyboard
   ```

4. Edit your existing `~/.config/omarchy/shell.json` and add this entry to the desired bar layout (tested in `right`):

   ```json
   { "id": "2-in-1-keyboard", "type": "qml" }
   ```

   **Add the entry to the existing array; do not replace the entire `shell.json` file.** Keep its JSON syntax valid, including commas between entries.

5. Enable the rotation service and restart the Omarchy shell:

   ```bash
   systemctl --user daemon-reload
   systemctl --user enable --now 2-in-1-rotation.service
   omarchy-restart-shell
   ```

   Use `omarchy-restart-shell`, **not** `omarchy-refresh-shell`: refreshing can reset changes to `shell.json`.

6. Check that the service is running:

   ```bash
   systemctl --user status 2-in-1-rotation.service --no-pager -l
   ```

The Surface DTX user service (`surface-dtx-userd.service`) was enabled on the test machine, but has **not** been established as a strict requirement for this script. See [Dependencies and upstream projects](#dependencies-and-upstream-projects) and [Troubleshooting](#troubleshooting-and-known-limitations) if the setup does not work.

## Device modes and terminology

The following names describe how the **Surface Book 2** is configured. Other manufacturers may use different terms or detection methods.

- **Laptop mode:** The display faces the keyboard and trackpad on the attached **keyboard base**, as on a conventional laptop. Automatic rotation is locked upright.
- **Tablet mode:** The display is detached from the keyboard base. Rotation follows the accelerometer; the on-screen keyboard button is available.
- **Studio mode:** The display is reattached facing away from the keyboard and can be folded back for touch-based use. Rotation follows the accelerometer, and the physical keyboard and trackpad are disabled.
- **Tent mode (proposed enhancement):** The device rests in an inverted V shape. This is a physical arrangement, **not a separate Surface DTX mode** in v1. A future enhancement may recognise it when studio mode and the `bottom-up` orientation occur together.

Surface DTX (the Surface device-mode interface) supplies `laptop`, `tablet` and `studio` states. The term *keyboard base* refers to the detachable lower assembly, which contains more than just a keyboard. Surface DTX sometimes calls the detachable screen assembly the *clipboard*. This README uses *display* or *screen* for that assembly, and *keyboard base* for the lower assembly, to avoid confusion with the text clipboard.

## Why this project exists

This project was inspired by VisorDTE's Omarchy discussion, [Feature: native 2-in-1 screen auto-rotation (tablet mode) support — #9427](https://github.com/omacom/omarchy/discussions/9427).

The goal is to make convertible-device integration more practical on Omarchy, beginning with a tested implementation and documentation that others can improve. Surface Book 2 support is the starting point, **not a claim of compatibility with all 2-in-1 hardware**.

## Features in Version 1

- Detects Surface DTX device modes through the system D-Bus messaging interface.
- Reads accelerometer orientation from `iio-sensor-proxy`.
- Rotates the built-in display and both detected IPTS touchscreen devices together through Hyprland's `hyprctl eval` interface.
- Keeps the display upright in laptop mode, regardless of accelerometer changes.
- Disables the physical keyboard and trackpad in studio mode; re-enables them in laptop and tablet modes.
- Writes the current device mode to `$XDG_RUNTIME_DIR/2-in-1-rotation-mode` for the Omarchy bar to read.
- Shows an on-screen keyboard button in tablet and studio modes; hides it in laptop mode.
- Hides a visible on-screen keyboard when returning to laptop mode.
- Runs as a systemd user service and performs cleanup on shutdown.

`$XDG_RUNTIME_DIR` is a standard environment variable pointing to a temporary runtime directory belonging to the signed-in user. This project stores small state files there; they are not permanent configuration files.

The on-screen keyboard in v1 is **`wvkbd-mobintl`**, provided by the `wvkbd` package. Using a different virtual keyboard would require changes to the keyboard-toggle script.

## Expected behaviour

| Device mode | Display rotation | Physical keyboard and trackpad | On-screen keyboard button |
| :--- | :--- | :--- | :--- |
| Laptop | Fixed upright | Enabled | Hidden; visible keyboard dismissed |
| Tablet | Follows accelerometer | Enabled by the current script | Shown |
| Studio | Follows accelerometer | Disabled | Shown |

The `scripts/toggle-2-in-1-keyboard` helper starts `wvkbd-mobintl` hidden if it is not running, then shows or hides it when the bar button is pressed. It uses standard Unix user signals (`SIGUSR1` and `SIGUSR2`) to control visibility and stores its visibility marker at `$XDG_RUNTIME_DIR/2-in-1-keyboard-visible`.

## Tested

The following versions were observed on the **Microsoft Surface Book 2 test machine on 9 October 2026**. They are **tested versions, not established minimum requirements**.

| Component                      | Tested version              | Purpose / note |
| :----------------------------- | :-------------------------- | :------------- |
| Omarchy                        | `4.0.4-1`                   | Desktop environment |
| Hyprland                       | `0.56.2` (`0.56.2-2` pkg)   | Compositor and rotation commands |
| Linux Surface kernel           | `6.19.8-arch1-3-surface`    | Surface-specific kernel |
| `linux-surface`                | `6.19.8.arch1-3`            | Kernel package |
| `linux-surface-headers`        | `6.19.8.arch1-3`            | Installed; not a script runtime dependency |
| `surface-dtx-daemon`           | `0.3.11-1`                  | Device-mode service |
| `surface-dtx-daemon-debug`     | `0.3.11-1`                  | Optional debug symbols |
| `iptsd`                        | `3.1.0-1`                   | Surface touch hardware support |
| `surface-ipts-firmware`        | `20200929-1`                | Touch firmware |
| `libwacom`                     | `2.19.1-1`                  | Installed tablet/stylus support |
| `python`                       | `3.14.7-1`                  | Python runtime |
| `python-gobject`               | `3.56.3-1`                  | Python access to GLib/Gio and D-Bus |
| `iio-sensor-proxy`             | `3.9-1`                     | Accelerometer orientation service |
| `wvkbd`                        | `0.20-1`                    | On-screen keyboard (`wvkbd-mobintl`) |
| `quickshell`                   | `0.3.1-1`                   | Omarchy bar integration |

## Dependencies and upstream projects

The rotation service requires Python 3, PyGObject (Gio/GLib bindings), the Surface DTX system service, `iio-sensor-proxy` and a compatible Hyprland installation. The Omarchy bar button additionally requires Quickshell and `wvkbd-mobintl`.

- **[Linux Surface](https://github.com/linux-surface/linux-surface):** Surface-specific kernel and hardware setup. Follow the upstream instructions for your device and distribution.
- **[Surface DTX daemon](https://github.com/linux-surface/surface-dtx-daemon):** Device-mode detection; installed from the Arch User Repository (AUR) as `surface-dtx-daemon` using `yay` on the test machine. Its package build specifies `dbus` and `gcc-libs` as runtime dependencies, and `rust` and `cargo` for building.
- **[wvkbd](https://git.sr.ht/~proycon/wvkbd):** On-screen keyboard; installed from the AUR using `yay`. Its package build lists `wayland`, `pango`, `cairo` and `glibc` as runtime dependencies, with `fontconfig`, `libxkbcommon` and `scdoc` needed for building.
- **`iio-sensor-proxy`:** Available as an Arch package; exposes accelerometer orientation.
- **`python-gobject`:** Available as an Arch package; provides the Python bindings used to access D-Bus.

The following DTX services were enabled on the tested system:

```bash
sudo systemctl enable --now surface-dtx-daemon.service
systemctl --user enable --now surface-dtx-userd.service
```

The Python program subscribes to the **system** DTX service. The separate user DTX service has not been demonstrated to be mandatory. Sensor proxy activation requirements may vary by system.

## Repository layout

```text
2-in-1-rotation/
├── .gitignore
├── README.md
├── LICENSE                 # to be added before publication
├── 2-in-1-rotation.py
├── scripts/
│   └── toggle-2-in-1-keyboard
├── quickshell/
│   └── 2-in-1-keyboard.qml
└── systemd/
    └── 2-in-1-rotation.service
```

This is the current project layout, excluding local working drafts. The renamed Python program, QML module, helper script and systemd service have been tested together. A fresh-checkout installation still needs validation. A `LICENSE` file containing the complete GPLv3 text is required before publication.

The systemd unit starts `%h/Projects/2-in-1-rotation/2-in-1-rotation.py`, where `%h` means the user's home directory. **This path must match the actual checkout location** or the service will fail to start.

## Device-specific configuration

The current implementation has hard-coded device names from the test Surface Book 2:

- **Built-in display:** `eDP-1`
- **Touchscreen devices:** `ipts-045e:0021-touchscreen` and `iptsd-virtual-touchscreen-045e:0021`
- **Physical keyboard:** `microsoft-surface-keyboard`
- **Physical trackpad:** `microsoft-surface-keyboard-touchpad`
- **Surface DTX D-Bus service:** `org.surface.dtx`
- **Accelerometer D-Bus service:** `net.hadess.SensorProxy`

These values are not guaranteed to match other devices, or even a different configuration of the same model. To adapt v1, inspect the device identifiers exposed by Hyprland and edit `2-in-1-rotation.py` accordingly. A user-facing hardware configuration mechanism is planned for a later version.

## Troubleshooting and known limitations

**Check service status and recent logs:**

```bash
systemctl --user status 2-in-1-rotation.service --no-pager -l
journalctl --user -u 2-in-1-rotation.service -n 40 --no-pager
systemctl status iio-sensor-proxy.service
monitor-sensor
```

- **Intermittent accelerometer timeout:** During testing, the D-Bus `ClaimAccelerometer` request occasionally timed out after approximately 25 seconds while `iio-sensor-proxy` remained active. The user service restarted the process and a later attempt succeeded. The cause has not been identified; this is an unresolved v1 limitation.
- **Display rotates but touch input does not match:** Confirm the actual Hyprland display and touchscreen device identifiers. On the tested Surface Book 2, both `ipts-045e:0021-touchscreen` and `iptsd-virtual-touchscreen-045e:0021` must receive the same transform as the display.
- **On-screen keyboard button missing:** Confirm the mode file exists, the Quickshell module was copied to the correct location and its entry was merged into `shell.json`.
- **Service fails immediately:** Check `ExecStart` in the installed systemd user service and confirm the script exists and is executable at that path.
- **Persistent “Clipboard can be detached” notification:** On the tested system (`surface-dtx-daemon` 0.3.11-1, Linux Surface kernel `6.19.8-arch1-3-surface`), a notification may remain after detaching and reattaching the screen. This is tracked upstream in [Surface DTX issue #23](https://github.com/linux-surface/surface-dtx-daemon/issues/23) and is not caused by this rotation script. The version that introduced the behaviour has not been established. This project accepts this issue and does not attempt a workaround in v1.
- **Shutdown behaviour:** A SIGTERM shutdown was tested to exit successfully. The script restores the physical keyboard, writes `unknown` to the mode file and attempts to release its accelerometer claim. More robust independent error handling during cleanup remains a possible improvement.

## Roadmap

- Test installation from a clean checkout and publish v1.0.0.
- Improve recovery and diagnostics for intermittent accelerometer D-Bus timeouts.
- Make monitor, touchscreen and physical-input identifiers configurable.
- Expand testing and support to additional Omarchy-compatible 2-in-1 and convertible hardware.
- **Proposed v2 tent-mode enhancement:** When Surface DTX reports `studio` and the accelerometer reports `bottom-up`, temporarily suppress hardware power and volume button actions. In this arrangement, those buttons can be pressed accidentally by the surface the device rests on, especially if it is soft or uneven. Restore normal button behaviour immediately when either condition changes. **Not implemented in v1.**
- Consider a system-wide installation option after the user-service installation is complete and validated.

## Author and acknowledgements

**Created by:** Trevor Fraser  
**Development assistance:** OpenAI ChatGPT (GPT-6)  
**First tested device:** Microsoft Surface Book 2

Trevor defined the requirements, supplied the hardware and test environment, made implementation decisions and validated the behaviour. ChatGPT assisted with implementation, integration, troubleshooting and documentation.

The project was inspired by [VisorDTE's Omarchy feature discussion #9427](https://github.com/omacom/omarchy/discussions/9427). It builds on the work of the [Linux Surface](https://github.com/linux-surface/linux-surface), [Surface DTX daemon](https://github.com/linux-surface/surface-dtx-daemon), Hyprland, Omarchy and other upstream communities.

Once published, the GitHub repository will be the preferred place for questions, bug reports, contributions and feature requests. A repository/profile link will be added when its public URL is known; no personal email address is required.

## Licence

The intended licence is the **GNU General Public License version 3 or later (`GPL-3.0-or-later`)**. The complete licence text will be provided in `LICENSE`, with source-file notices, before v1.0.0 is published.
