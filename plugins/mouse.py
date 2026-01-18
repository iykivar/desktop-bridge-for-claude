"""
Mouse Plugin
"""

import time
import pyautogui
from .shared import screenshot_mgr


def click(params):
    """Mouse tıklama"""
    x, y = params.get("x", 0), params.get("y", 0)
    button = params.get("button", "left")
    clicks = params.get("clicks", 1)
    use_screenshot_coords = params.get("screenshot_coords", False)
    
    if use_screenshot_coords:
        real_x, real_y = screenshot_mgr.convert_coords(x, y)
    else:
        real_x, real_y = x, y
    
    pyautogui.click(x=real_x, y=real_y, button=button, clicks=clicks)
    
    return {
        "status": "success",
        "action": "click",
        "input_coords": [x, y],
        "real_coords": [real_x, real_y],
        "screenshot_coords": use_screenshot_coords,
        "scale_ratio": screenshot_mgr.scale_ratio
    }


def move(params):
    """Mouse taşı"""
    x, y = params.get("x", 0), params.get("y", 0)
    duration = params.get("duration", 0.2)
    use_screenshot_coords = params.get("screenshot_coords", False)
    
    if use_screenshot_coords:
        real_x, real_y = screenshot_mgr.convert_coords(x, y)
    else:
        real_x, real_y = x, y
    
    pyautogui.moveTo(real_x, real_y, duration=duration)
    
    return {
        "status": "success",
        "action": "move",
        "input_coords": [x, y],
        "real_coords": [real_x, real_y],
        "screenshot_coords": use_screenshot_coords
    }


def scroll(params):
    """Mouse scroll"""
    amount = params.get("amount", -3)
    x, y = params.get("x"), params.get("y")
    use_screenshot_coords = params.get("screenshot_coords", False)
    
    if use_screenshot_coords and x is not None and y is not None:
        x, y = screenshot_mgr.convert_coords(x, y)
    
    pyautogui.scroll(amount, x=x, y=y)
    return {"status": "success", "action": "scroll", "amount": amount}


def mouse_position(params):
    """Mouse pozisyonunu al"""
    x, y = pyautogui.position()
    return {"status": "success", "x": x, "y": y}


def drag(params):
    """Sürükle bırak"""
    start_x = params.get("start_x", 0)
    start_y = params.get("start_y", 0)
    end_x = params.get("end_x", 0)
    end_y = params.get("end_y", 0)
    duration = params.get("duration", 0.5)
    button = params.get("button", "left")
    use_screenshot_coords = params.get("screenshot_coords", False)
    
    if use_screenshot_coords:
        real_start_x, real_start_y = screenshot_mgr.convert_coords(start_x, start_y)
        real_end_x, real_end_y = screenshot_mgr.convert_coords(end_x, end_y)
    else:
        real_start_x, real_start_y = start_x, start_y
        real_end_x, real_end_y = end_x, end_y
    
    pyautogui.moveTo(real_start_x, real_start_y, duration=0.2)
    time.sleep(0.1)
    pyautogui.drag(real_end_x - real_start_x, real_end_y - real_start_y, duration=duration, button=button)
    
    return {
        "status": "success",
        "action": "drag",
        "input_from": [start_x, start_y],
        "input_to": [end_x, end_y],
        "real_from": [real_start_x, real_start_y],
        "real_to": [real_end_x, real_end_y],
        "screenshot_coords": use_screenshot_coords
    }


# Dışa açılan action'lar
ACTIONS = {
    "click": click,
    "move": move,
    "scroll": scroll,
    "mouse": mouse_position,
    "drag": drag,
}
