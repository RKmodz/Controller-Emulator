import os
import json
import time
import threading
try:
    import keyboard
    import mouse
    import vgamepad as vg
except ImportError:
    print("Please install dependencies: pip install vgamepad keyboard mouse pywin32")
    exit(1)

# Full Xbox 360 button mapping
BUTTON_MAP = {
    "UP": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
    "DOWN": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
    "LEFT": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
    "RIGHT": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
    "A": vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
    "B": vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
    "X": vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
    "Y": vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
    "START": vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
    "BACK": vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
    "LS": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
    "RS": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
    "LB": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
    "RB": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
}

# Global state
active = True
gamepad = None
config = {}
pressed_keys = set()
left_joystick_state = {'x': 0.0, 'y': 0.0}

def load_config():
    global config
    try:
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"Error: config.json not found ({config_path}).")
        exit(1)

def apply_joystick_state():
    """Apply the computed state to the left joystick"""
    if gamepad:
        gamepad.left_joystick_float(x_value_float=left_joystick_state['x'], y_value_float=left_joystick_state['y'])

def on_key_event(e):
    global active, left_joystick_state
    
    if e.name is None:
        return
        
    key_name = e.name.lower()
    
    # Toggle emulation on/off (F12 by default)
    if key_name == config.get("toggle_key", "f12").lower() and e.event_type == keyboard.KEY_DOWN:
        active = not active
        print(f"XIM Emulator: {'ENABLED' if active else 'DISABLED'}")
        
        if not active:
            # Release everything
            gamepad.reset()
            gamepad.update()
        return

    if not active:
        return

    # Left joystick handling (WASD / ZQSD)
    js_conf = config.get("joystick_left", {})
    is_js_key = False
    
    if key_name in js_conf.values():
        is_js_key = True
        if e.event_type == keyboard.KEY_DOWN:
            if key_name == js_conf.get("up"): left_joystick_state['y'] = 1.0
            elif key_name == js_conf.get("down"): left_joystick_state['y'] = -1.0
            elif key_name == js_conf.get("left"): left_joystick_state['x'] = -1.0
            elif key_name == js_conf.get("right"): left_joystick_state['x'] = 1.0
        elif e.event_type == keyboard.KEY_UP:
            if key_name == js_conf.get("up") and left_joystick_state['y'] > 0: left_joystick_state['y'] = 0.0
            elif key_name == js_conf.get("down") and left_joystick_state['y'] < 0: left_joystick_state['y'] = 0.0
            elif key_name == js_conf.get("left") and left_joystick_state['x'] < 0: left_joystick_state['x'] = 0.0
            elif key_name == js_conf.get("right") and left_joystick_state['x'] > 0: left_joystick_state['x'] = 0.0
            
        apply_joystick_state()

    # Standard button handling
    mappings = config.get("mappings", {})
    if key_name in mappings and not is_js_key:
        target_btn_str = mappings[key_name]
        invert = config.get("invert_bumpers", False)
        
        # Bumper/trigger inversion
        if invert:
            if target_btn_str == "LB": target_btn_str = "LT"
            elif target_btn_str == "RB": target_btn_str = "RT"
            elif target_btn_str == "LT": target_btn_str = "LB"
            elif target_btn_str == "RT": target_btn_str = "RB"
            
        if target_btn_str in ["LT", "RT"]:
            # Simulate a trigger from a keyboard key
            val = 1.0 if e.event_type == keyboard.KEY_DOWN else 0.0
            if e.event_type == keyboard.KEY_DOWN:
                if target_btn_str == "LT": gamepad.left_trigger_float(value_float=val)
                elif target_btn_str == "RT": gamepad.right_trigger_float(value_float=val)
                pressed_keys.add(key_name)
            elif e.event_type == keyboard.KEY_UP:
                if target_btn_str == "LT": gamepad.left_trigger_float(value_float=val)
                elif target_btn_str == "RT": gamepad.right_trigger_float(value_float=val)
                if key_name in pressed_keys:
                    pressed_keys.remove(key_name)
                
        elif target_btn_str in BUTTON_MAP:
            btn = BUTTON_MAP[target_btn_str]
            
            if e.event_type == keyboard.KEY_DOWN:
                gamepad.press_button(button=btn)
                pressed_keys.add(key_name)
                
            elif e.event_type == keyboard.KEY_UP:
                gamepad.release_button(button=btn)
                if key_name in pressed_keys:
                    pressed_keys.remove(key_name)

def mouse_loop():
    """Handles the right joystick (aiming) via mouse with smooth input"""
    global active
    import ctypes
    import math
    import time
    user32 = ctypes.windll.user32
    winmm = ctypes.windll.winmm
    winmm.timeBeginPeriod(1)  # Force timer resolution to 1ms
    
    screen_width = user32.GetSystemMetrics(0)
    screen_height = user32.GetSystemMetrics(1)
    center_x = screen_width // 2
    center_y = screen_height // 2
    
    class POINT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
        
    pt = POINT()
    user32.SetCursorPos(center_x, center_y)
    last_x = center_x
    last_y = center_y
    
    smoothed_jx = 0.0
    smoothed_jy = 0.0
    
    while True:
        if not active:
            time.sleep(0.1)
            user32.GetCursorPos(ctypes.byref(pt))
            last_x = pt.x
            last_y = pt.y
            continue
            
        try:
            user32.GetCursorPos(ctypes.byref(pt))
            dx = pt.x - last_x
            dy = pt.y - last_y
            
            # Lazy centering: only reset the cursor if it drifts too far from center.
            # Calling SetCursorPos every millisecond destroys Windows fluidity and causes discomfort.
            if abs(pt.x - center_x) > 400 or abs(pt.y - center_y) > 400:
                user32.SetCursorPos(center_x, center_y)
                last_x = center_x
                last_y = center_y
            else:
                last_x = pt.x
                last_y = pt.y
            
            sens_x = config.get("mouse_settings", {}).get("sensitivity_x", 15.0)
            sens_y = config.get("mouse_settings", {}).get("sensitivity_y", 15.0)
            
            # Convert mouse delta to joystick value (divided by 100 for the 1000Hz loop)
            jx = (dx * sens_x) / 100.0 
            jy = -(dy * sens_y) / 100.0 
            
            # Light smoothing for a natural feel without added latency (0.1 or 0.2)
            smoothing = config.get("mouse_settings", {}).get("smoothing", 0.1)
            smoothed_jx = smoothed_jx * smoothing + jx * (1.0 - smoothing)
            smoothed_jy = smoothed_jy * smoothing + jy * (1.0 - smoothing)
            
            # Ballistic curve
            curve = config.get("mouse_settings", {}).get("curve", 1.0)
            if curve != 1.0:
                smoothed_jx = math.copysign(abs(smoothed_jx) ** curve, smoothed_jx)
                smoothed_jy = math.copysign(abs(smoothed_jy) ** curve, smoothed_jy)
            
            # Circular anti-deadzone (1:1 mapping)
            magnitude = math.sqrt(smoothed_jx**2 + smoothed_jy**2)
            dz = config.get("mouse_settings", {}).get("anti_deadzone", 0.15)
            
            if magnitude > 0.001:
                new_magnitude = dz + magnitude * (1.0 - dz)
                new_magnitude = min(new_magnitude, 1.0)
                ratio = new_magnitude / magnitude
                final_jx = smoothed_jx * ratio
                final_jy = smoothed_jy * ratio
            else:
                final_jx = 0.0
                final_jy = 0.0
            
            final_jx = max(-1.0, min(1.0, final_jx))
            final_jy = max(-1.0, min(1.0, final_jy))
            
            # Handle LB/LT and RB/RT inversion
            invert = config.get("invert_bumpers", False)
            click_right = user32.GetAsyncKeyState(0x02) & 0x8000
            click_left = user32.GetAsyncKeyState(0x01) & 0x8000
            
            if invert:
                # Mouse clicks control LB and RB buttons
                if click_right: gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER)
                else: gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER)
                
                if click_left: gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER)
                else: gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER)
            else:
                # Mouse clicks control LT and RT triggers
                gamepad.left_trigger_float(value_float=1.0 if click_right else 0.0)
                gamepad.right_trigger_float(value_float=1.0 if click_left else 0.0)
            
            # Update right joystick if there is mouse movement
            if abs(final_jx) > 0.01 or abs(final_jy) > 0.01:
                gamepad.right_joystick_float(x_value_float=final_jx, y_value_float=final_jy)
            else:
                gamepad.right_joystick_float(x_value_float=0.0, y_value_float=0.0)
                
            gamepad.update()
                
            # Stable 200Hz loop to avoid Windows jitter
            time.sleep(0.005)
            
        except Exception as e:
            print(f"Mouse error: {e}")
            time.sleep(1)

def main():
    global gamepad
    print("Initializing virtual controller (ViGEmBus)...")
    try:
        gamepad = vg.VX360Gamepad()
    except Exception as e:
        print(f"Error initializing gamepad: {e}")
        print("Did you install the ViGEmBus driver?")
        exit(1)

    load_config()
    print("Configuration loaded successfully.")
    
    # Global keyboard hook
    keyboard.hook(on_key_event)
    
    # Start mouse thread for smooth aiming and click handling
    mouse_thread = threading.Thread(target=mouse_loop, daemon=True)
    mouse_thread.start()
    
    print("\n[+] XIM Emulator active and fully running!")
    print(f"[+] Toggle key (enable/disable): {config.get('toggle_key', 'F12').upper()}")
    print("[!] ZQSD / WASD = Movement (Left Joystick)")
    print("[!] Mouse = Aim (Right Joystick) + Clicks = LT/RT Triggers")
    print("[!] Make sure to run this script as Administrator.")
    print("Press CTRL+C to quit.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        gamepad.reset()
        gamepad.update()

if __name__ == "__main__":
    main()
