"""
Keyboard Plugin
"""

import sys
import pyautogui
from .shared import type_with_clipboard


def type_text(params):
    """Metin yaz (clipboard ile, Unicode destekli)"""
    text = params.get("text", "")
    type_with_clipboard(text)
    return {"status": "success", "action": "type", "length": len(text), "method": "clipboard"}


def type_raw(params):
    """Metin yaz (pyautogui ile, sadece ASCII)"""
    text = params.get("text", "")
    interval = params.get("interval", 0.02)
    pyautogui.write(text, interval=interval)
    return {"status": "success", "action": "type_raw", "length": len(text), "method": "pyautogui"}


def key(params):
    """Tuş bas"""
    key_name = params.get("key", "")
    
    if '+' in key_name:
        keys = key_name.split('+')
        normalized_keys = []
        for k in keys:
            k_lower = k.lower().strip()
            if k_lower in ('cmd', 'command'):
                normalized_keys.append('command' if sys.platform == 'darwin' else 'ctrl')
            elif k_lower == 'ctrl':
                normalized_keys.append('ctrl')
            elif k_lower == 'alt':
                normalized_keys.append('alt')
            elif k_lower == 'shift':
                normalized_keys.append('shift')
            else:
                normalized_keys.append(k_lower)
        pyautogui.hotkey(*normalized_keys)
    else:
        pyautogui.press(key_name)
    
    return {"status": "success", "action": "key", "key": key_name}


# Dışa açılan action'lar
ACTIONS = {
    "type": type_text,
    "type_raw": type_raw,
    "key": key,
}
