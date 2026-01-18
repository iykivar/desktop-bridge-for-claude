"""
Window Management Plugin
"""

import sys
import subprocess
import time
import pyautogui


def _find_window_hwnd(app_name):
    """Windows'ta pencere handle'ı bul"""
    import ctypes
    from ctypes import wintypes
    
    user32 = ctypes.windll.user32
    EnumWindows = user32.EnumWindows
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
    GetWindowText = user32.GetWindowTextW
    GetWindowTextLength = user32.GetWindowTextLengthW
    
    found_hwnd = None
    
    def foreach_window(hwnd, lParam):
        nonlocal found_hwnd
        length = GetWindowTextLength(hwnd)
        if length > 0:
            buff = ctypes.create_unicode_buffer(length + 1)
            GetWindowText(hwnd, buff, length + 1)
            if app_name.lower() in buff.value.lower():
                found_hwnd = hwnd
                return False
        return True
    
    EnumWindows(EnumWindowsProc(foreach_window), 0)
    return found_hwnd


def get_window_position(app_name):
    """Pencere pozisyonunu al"""
    try:
        if sys.platform == "darwin":
            script = f'''
            tell application "System Events"
                tell process "{app_name}"
                    set winPos to position of window 1
                    set winSize to size of window 1
                end tell
            end tell
            return (item 1 of winPos as text) & "," & (item 2 of winPos as text) & "," & (item 1 of winSize as text) & "," & (item 2 of winSize as text)
            '''
            result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                parts = result.stdout.strip().split(",")
                if len(parts) == 4:
                    return {
                        "x": int(parts[0]), "y": int(parts[1]),
                        "width": int(parts[2]), "height": int(parts[3])
                    }
        
        elif sys.platform == "win32":
            import ctypes
            from ctypes import wintypes
            
            hwnd = _find_window_hwnd(app_name)
            if hwnd:
                rect = wintypes.RECT()
                ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
                return {
                    "x": rect.left, "y": rect.top,
                    "width": rect.right - rect.left,
                    "height": rect.bottom - rect.top
                }
        
        return None
    except Exception as e:
        return {"error": str(e)}


def move_window(app_name, x, y):
    """Pencereyi taşı"""
    try:
        if sys.platform == "darwin":
            script = f'''
            tell application "System Events"
                tell process "{app_name}"
                    set position of window 1 to {{{x}, {y}}}
                end tell
            end tell
            '''
            result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
            if result.returncode == 0:
                return {"status": "success"}
            return {"status": "error", "message": result.stderr}
        
        elif sys.platform == "win32":
            import ctypes
            from ctypes import wintypes
            
            hwnd = _find_window_hwnd(app_name)
            if hwnd:
                rect = wintypes.RECT()
                ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
                width = rect.right - rect.left
                height = rect.bottom - rect.top
                ctypes.windll.user32.MoveWindow(hwnd, x, y, width, height, True)
                return {"status": "success"}
            return {"status": "error", "message": f"Window not found: {app_name}"}
        
        return {"status": "error", "message": "Unsupported platform"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def resize_window(app_name, width, height):
    """Pencere boyutunu değiştir"""
    try:
        if sys.platform == "darwin":
            script = f'''
            tell application "System Events"
                tell process "{app_name}"
                    set size of window 1 to {{{width}, {height}}}
                end tell
            end tell
            '''
            result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
            if result.returncode == 0:
                return {"status": "success"}
            return {"status": "error", "message": result.stderr}
        
        elif sys.platform == "win32":
            import ctypes
            from ctypes import wintypes
            
            hwnd = _find_window_hwnd(app_name)
            if hwnd:
                rect = wintypes.RECT()
                ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
                x, y = rect.left, rect.top
                ctypes.windll.user32.MoveWindow(hwnd, x, y, width, height, True)
                return {"status": "success"}
            return {"status": "error", "message": f"Window not found: {app_name}"}
        
        return {"status": "error", "message": "Unsupported platform"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def list_windows():
    """Açık pencereleri listele"""
    windows = []
    try:
        if sys.platform == "darwin":
            script = '''
            set windowList to ""
            tell application "System Events"
                set allProcesses to (every process whose visible is true)
                repeat with proc in allProcesses
                    set procName to name of proc
                    try
                        if (count of windows of proc) > 0 then
                            set windowList to windowList & procName & "\\n"
                        end if
                    end try
                end repeat
            end tell
            return windowList
            '''
            result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
            if result.returncode == 0:
                windows = [w.strip() for w in result.stdout.strip().split("\n") if w.strip()]
        
        elif sys.platform == "win32":
            import ctypes
            
            user32 = ctypes.windll.user32
            EnumWindows = user32.EnumWindows
            EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
            GetWindowText = user32.GetWindowTextW
            GetWindowTextLength = user32.GetWindowTextLengthW
            IsWindowVisible = user32.IsWindowVisible
            
            def foreach_window(hwnd, lParam):
                if IsWindowVisible(hwnd):
                    length = GetWindowTextLength(hwnd)
                    if length > 0:
                        buff = ctypes.create_unicode_buffer(length + 1)
                        GetWindowText(hwnd, buff, length + 1)
                        if buff.value:
                            windows.append(buff.value)
                return True
            
            EnumWindows(EnumWindowsProc(foreach_window), 0)
    
    except Exception as e:
        return {"error": str(e)}
    
    return windows


# ============== ACTION HANDLERS ==============

def window_move_action(params):
    """Pencere taşı action"""
    app = params.get("app", "")
    x = params.get("x", 0)
    y = params.get("y", 0)
    
    if not app:
        return {"status": "error", "message": "App name required"}
    
    before = get_window_position(app)
    result = move_window(app, x, y)
    after = get_window_position(app)
    
    result["action"] = "window_move"
    result["app"] = app
    result["target"] = [x, y]
    result["before"] = before
    result["after"] = after
    result["verified"] = after is not None and after.get("x") == x and after.get("y") == y
    return result


def window_resize_action(params):
    """Pencere boyutlandır action"""
    app = params.get("app", "")
    width = params.get("width", 800)
    height = params.get("height", 600)
    
    if not app:
        return {"status": "error", "message": "App name required"}
    
    result = resize_window(app, width, height)
    result["action"] = "window_resize"
    result["app"] = app
    result["size"] = [width, height]
    return result


def window_position_action(params):
    """Pencere pozisyonu action"""
    app = params.get("app", "")
    if not app:
        return {"status": "error", "message": "App name required"}
    
    pos = get_window_position(app)
    return {
        "status": "success" if pos else "error",
        "action": "window_position",
        "app": app,
        "position": pos
    }


def windows_list_action(params):
    """Pencere listesi action"""
    windows = list_windows()
    return {
        "status": "success",
        "action": "windows_list",
        "windows": windows,
        "count": len(windows)
    }


def scroll_app_action(params):
    """Uygulamada scroll yap"""
    app = params.get("app", "")
    amount = params.get("amount", -3)
    
    if not app:
        return {"status": "error", "message": "App name required"}
    
    try:
        if sys.platform == "darwin":
            script = f'tell application "{app}" to activate'
            subprocess.run(["osascript", "-e", script], capture_output=True)
            time.sleep(0.2)
            pyautogui.scroll(amount)
            return {"status": "success", "action": "scroll_app", "app": app, "amount": amount}
        
        elif sys.platform == "win32":
            import ctypes
            hwnd = _find_window_hwnd(app)
            if hwnd:
                ctypes.windll.user32.SetForegroundWindow(hwnd)
                time.sleep(0.2)
                pyautogui.scroll(amount)
                return {"status": "success", "action": "scroll_app", "app": app, "amount": amount}
            return {"status": "error", "message": f"Window not found: {app}"}
        
        return {"status": "error", "message": "Unsupported platform"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# Dışa açılan action'lar
ACTIONS = {
    "window_move": window_move_action,
    "window_resize": window_resize_action,
    "window_position": window_position_action,
    "windows_list": windows_list_action,
    "scroll_app": scroll_app_action,
}
