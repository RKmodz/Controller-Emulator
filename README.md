# Controller-Emulator

A lightweight keyboard and mouse to Xbox 360 controller emulator for Windows, powered by ViGEmBus.

## Description

Controller-Emulator lets you play controller-only games with a keyboard and mouse by creating a virtual Xbox 360 gamepad. Mouse movement maps to the right joystick for aiming, WASD/ZQSD maps to the left joystick for movement, and every other button is fully remappable via `config.json`.

Features:
- Smooth, high-frequency mouse-to-right-joystick conversion (200Hz loop)
- Configurable sensitivity, smoothing, ballistic curve, and circular anti-deadzone
- Full Xbox 360 button remapping (A, B, X, Y, LB, RB, LT, RT, Start, Back, D-Pad, LS, RS)
- Optional LB/RB ↔ LT/RT inversion
- Toggle emulation on/off with a hotkey (default: F5)

## Requirements

- Windows 10/11
- [ViGEmBus driver](https://github.com/nefarius/ViGEmBus/releases)
- Python 3.8+

pip install vgamepad keyboard mouse pywin32

## Usage

Run as Administrator:

python main.py

## Configuration

Edit `config.json` to customize bindings and mouse feel:

| Setting | Description |
|---|---|
| `toggle_key` | Key to enable/disable emulation |
| `invert_bumpers` | Swap LB↔LT and RB↔RT (and mouse clicks) |
| `joystick_left` | Keys for left stick movement |
| `sensitivity_x/y` | Mouse sensitivity per axis |
| `anti_deadzone` | Circular anti-deadzone offset (0.0–1.0) |
| `smoothing` | Mouse smoothing factor (0.0 = none) |
| `curve` | Ballistic curve exponent (1.0 = linear) |
| `mappings` | Keyboard key → Xbox button bindings |

## License

MIT
