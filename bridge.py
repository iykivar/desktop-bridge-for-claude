"""
Claude Desktop Bridge v0.6.0
============================
Tek terminal, akıllı screenshot, tam kontrol.
Türkçe/Unicode desteği + Otomatik koordinat dönüşümü.

Kullanım: python bridge.py
"""

import json
import time
import os
import sys
import subprocess
from datetime import datetime

import pyautogui
from PIL import Image

# ============== AYARLAR ==============
BRIDGE_DIR = os.path.dirname(os.path.abspath(__file__))
COMMAND_FILE = os.path.join(BRIDGE_DIR, "command.json")
RESULT_FILE = os.path.join(BRIDGE_DIR, "result.json")
SCREENSHOT_DIR = os.path.join(BRIDGE_DIR, "screenshots")

# Screenshot ayarları
MAX_WIDTH = 1000
JPEG_QUALITY = 65

# PyAutoGUI güvenlik
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1


# ============== PENCERE YÖNETİMİ ==============
def get_window_position(app_name):
    """Uygulama penceresinin pozisyonunu al (cross-platform)"""
    try:
        if sys.platform == "darwin":
            script = f'''
            tell application "System Events"
                tell process "{app_name}"
                    set winPos to position of window 1
                    set winSize to size of window 1
                    set x to item 1 of winPos as integer
                    set y to item 2 of winPos as integer
                    set w to item 1 of winSize as integer
                    set h to item 2 of winSize as integer
                end tell
            end tell
            return (x as text) & "," & (y as text) & "," & (w as text) & "," & (h as text)
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
            
            user32 = ctypes.windll.user32
            # Pencereyi bul
            hwnd = user32.FindWindowW(None, None)
            
            # EnumWindows ile uygulama adına göre pencere bul
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
            
            if found_hwnd:
                rect = wintypes.RECT()
                user32.GetWindowRect(found_hwnd, ctypes.byref(rect))
                return {
                    "x": rect.left, "y": rect.top,
                    "width": rect.right - rect.left,
                    "height": rect.bottom - rect.top
                }
        
        return None
    except Exception as e:
        return {"error": str(e)}


def move_window(app_name, x, y):
    """Uygulama penceresini belirtilen konuma taşı (cross-platform)"""
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
            else:
                return {"status": "error", "message": result.stderr}
        
        elif sys.platform == "win32":
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
            
            if found_hwnd:
                # Pencere boyutunu koru, sadece pozisyonu değiştir
                rect = wintypes.RECT()
                user32.GetWindowRect(found_hwnd, ctypes.byref(rect))
                width = rect.right - rect.left
                height = rect.bottom - rect.top
                
                user32.MoveWindow(found_hwnd, x, y, width, height, True)
                return {"status": "success"}
            else:
                return {"status": "error", "message": f"Window not found: {app_name}"}
        
        else:
            return {"status": "error", "message": "Unsupported platform"}
    
    except Exception as e:
        return {"status": "error", "message": str(e)}


def resize_window(app_name, width, height):
    """Uygulama penceresinin boyutunu değiştir (cross-platform)"""
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
            else:
                return {"status": "error", "message": result.stderr}
        
        elif sys.platform == "win32":
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
            
            if found_hwnd:
                rect = wintypes.RECT()
                user32.GetWindowRect(found_hwnd, ctypes.byref(rect))
                x, y = rect.left, rect.top
                
                user32.MoveWindow(found_hwnd, x, y, width, height, True)
                return {"status": "success"}
            else:
                return {"status": "error", "message": f"Window not found: {app_name}"}
        
        else:
            return {"status": "error", "message": "Unsupported platform"}
    
    except Exception as e:
        return {"status": "error", "message": str(e)}


def list_windows():
    """Açık pencerelerin listesini al (cross-platform)"""
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
                        set winCount to count of windows of proc
                        if winCount > 0 then
                            set windowList to windowList & procName & "\n"
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


def get_ui_elements(app_name):
    """Uygulamanın UI elementlerini al (Accessibility API)"""
    elements = []
    try:
        if sys.platform == "darwin":
            # macOS: AppleScript ile UI elementlerini al
            script = f'''
            set output to ""
            tell application "System Events"
                tell process "{app_name}"
                    -- Butonlar
                    try
                        set btns to every button of splitter group 1 of window 1
                        repeat with btn in btns
                            set btnName to name of btn
                            set btnPos to position of btn
                            set btnSize to size of btn
                            set output to output & "button|" & btnName & "|" & (item 1 of btnPos) & "," & (item 2 of btnPos) & "|" & (item 1 of btnSize) & "," & (item 2 of btnSize) & "\n"
                        end repeat
                    end try
                    
                    -- Window butonları (minimize, close, vs.)
                    try
                        set winBtns to every button of window 1
                        repeat with btn in winBtns
                            set btnName to name of btn
                            set btnPos to position of btn
                            set btnSize to size of btn
                            set output to output & "button|" & btnName & "|" & (item 1 of btnPos) & "," & (item 2 of btnPos) & "|" & (item 1 of btnSize) & "," & (item 2 of btnSize) & "\n"
                        end repeat
                    end try
                    
                    -- Checkboxlar
                    try
                        set chks to every checkbox of splitter group 1 of window 1
                        repeat with chk in chks
                            set chkName to name of chk
                            set chkPos to position of chk
                            set chkSize to size of chk
                            set chkValue to value of chk
                            set output to output & "checkbox|" & chkName & "|" & (item 1 of chkPos) & "," & (item 2 of chkPos) & "|" & (item 1 of chkSize) & "," & (item 2 of chkSize) & "|" & chkValue & "\n"
                        end repeat
                    end try
                    
                    -- Text fieldlar
                    try
                        set txts to every text field of splitter group 1 of window 1
                        repeat with txt in txts
                            set txtName to name of txt
                            set txtPos to position of txt
                            set txtSize to size of txt
                            set txtValue to value of txt
                            set output to output & "textfield|" & txtName & "|" & (item 1 of txtPos) & "," & (item 2 of txtPos) & "|" & (item 1 of txtSize) & "," & (item 2 of txtSize) & "|" & txtValue & "\n"
                        end repeat
                    end try
                    
                    -- Menü butonları (dropdown)
                    try
                        set menus to every menu button of splitter group 1 of window 1
                        repeat with m in menus
                            set mName to name of m
                            set mPos to position of m
                            set mSize to size of m
                            set output to output & "menubutton|" & mName & "|" & (item 1 of mPos) & "," & (item 2 of mPos) & "|" & (item 1 of mSize) & "," & (item 2 of mSize) & "\n"
                        end repeat
                    end try
                end tell
            end tell
            return output
            '''
            result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0 and result.stdout.strip():
                for line in result.stdout.strip().split("\n"):
                    if line.strip():
                        parts = line.split("|")
                        if len(parts) >= 4:
                            elem_type = parts[0]
                            name = parts[1]
                            pos = parts[2].split(",")
                            size = parts[3].split(",")
                            
                            elem = {
                                "type": elem_type,
                                "name": name,
                                "position": {"x": int(pos[0]), "y": int(pos[1])},
                                "size": {"w": int(size[0]), "h": int(size[1])},
                                "center": {
                                    "x": int(pos[0]) + int(size[0]) // 2,
                                    "y": int(pos[1]) + int(size[1]) // 2
                                }
                            }
                            
                            # Checkbox için değer ekle
                            if len(parts) >= 5 and elem_type == "checkbox":
                                elem["checked"] = parts[4] == "1"
                            
                            # Textfield için değer ekle
                            if len(parts) >= 5 and elem_type == "textfield":
                                elem["value"] = parts[4]
                            
                            elements.append(elem)
        
        elif sys.platform == "win32":
            # Windows: pywinauto veya UIAutomation kullanabilir
            # Basit implementasyon
            return {"status": "error", "message": "Windows UI automation not yet implemented"}
        
        return elements
    
    except Exception as e:
        return {"error": str(e)}


def click_ui_element(app_name, element_name):
    """UI elementine isimle tıkla (Accessibility API)"""
    try:
        if sys.platform == "darwin":
            # Önce elementi bul
            elements = get_ui_elements(app_name)
            
            if isinstance(elements, dict) and "error" in elements:
                return elements
            
            # Element adını ara (kısmi eşleşme)
            target = None
            for elem in elements:
                if element_name.lower() in elem["name"].lower():
                    target = elem
                    break
            
            if not target:
                return {"status": "error", "message": f"Element not found: {element_name}"}
            
            # Merkeze tıkla
            x = target["center"]["x"]
            y = target["center"]["y"]
            
            pyautogui.click(x, y)
            
            return {
                "status": "success",
                "action": "click_element",
                "app": app_name,
                "element": target["name"],
                "type": target["type"],
                "clicked_at": {"x": x, "y": y}
            }
        
        elif sys.platform == "win32":
            return {"status": "error", "message": "Windows UI automation not yet implemented"}
        
        else:
            return {"status": "error", "message": "Unsupported platform"}
    
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ============== CLIPBOARD YÖNETİMİ ==============
def clipboard_copy(text):
    """Metni panoya kopyala (cross-platform)"""
    if sys.platform == "darwin":
        process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
        process.communicate(text.encode('utf-8'))
    elif sys.platform == "win32":
        process = subprocess.Popen(['clip'], stdin=subprocess.PIPE, shell=True)
        process.communicate(text.encode('utf-16-le'))
    else:
        try:
            process = subprocess.Popen(['xclip', '-selection', 'clipboard'], stdin=subprocess.PIPE)
            process.communicate(text.encode('utf-8'))
        except FileNotFoundError:
            process = subprocess.Popen(['xsel', '--clipboard', '--input'], stdin=subprocess.PIPE)
            process.communicate(text.encode('utf-8'))


def type_with_clipboard(text):
    """Clipboard kullanarak metin yaz (Unicode destekli)"""
    clipboard_copy(text)
    time.sleep(0.05)
    if sys.platform == "darwin":
        pyautogui.hotkey('command', 'v')
    else:
        pyautogui.hotkey('ctrl', 'v')
    time.sleep(0.05)


# ============== SCREENSHOT YÖNETİMİ ==============
class ScreenshotManager:
    """Akıllı screenshot yönetimi + koordinat dönüşümü"""
    
    def __init__(self):
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        self.reference_taken = False
        self.reference_path = os.path.join(SCREENSHOT_DIR, "reference.jpg")
        self.latest_path = os.path.join(SCREENSHOT_DIR, "latest.jpg")
        
        # Koordinat dönüşümü için
        self.scale_ratio = 1.0  # original_width / resized_width
        self.original_width = 0
        self.original_height = 0
        self.resized_width = 0
        self.resized_height = 0
        
    def _resize_and_save(self, img, filepath):
        """Resmi küçült ve JPEG olarak kaydet, oranı sakla"""
        original_w, original_h = img.width, img.height
        
        # pyautogui point cinsinden çalışır (Retina'da pixel/2)
        screen_w, screen_h = pyautogui.size()
        
        if img.width > MAX_WIDTH:
            # Ratio: pyautogui koordinatları / küçültülmüş screenshot
            # Bu Retina ekranlarda doğru çalışır
            self.scale_ratio = screen_w / MAX_WIDTH
            ratio = MAX_WIDTH / img.width
            new_height = int(img.height * ratio)
            img = img.resize((MAX_WIDTH, new_height), Image.LANCZOS)
        else:
            self.scale_ratio = 1.0
        
        # Boyutları sakla
        self.original_width = original_w
        self.original_height = original_h
        self.resized_width = img.width
        self.resized_height = img.height
        self.screen_width = screen_w
        self.screen_height = screen_h
        
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        
        img.save(filepath, "JPEG", quality=JPEG_QUALITY, optimize=True)
        
        return {
            "width": img.width,
            "height": img.height,
            "path": filepath,
            "size_kb": round(os.path.getsize(filepath) / 1024, 1),
            "scale_ratio": round(self.scale_ratio, 3),
            "screen_size": [screen_w, screen_h],
            "pixel_size": [original_w, original_h]
        }
    
    def convert_coords(self, x, y):
        """Screenshot koordinatlarını gerçek ekran koordinatlarına dönüştür"""
        real_x = int(x * self.scale_ratio)
        real_y = int(y * self.scale_ratio)
        return real_x, real_y
    
    def take_reference(self):
        """Tam ekran referans görüntüsü"""
        img = pyautogui.screenshot()
        result = self._resize_and_save(img, self.reference_path)
        self.reference_taken = True
        result["type"] = "reference"
        return result
    
    def take_full(self):
        """Tam ekran görüntüsü"""
        img = pyautogui.screenshot()
        result = self._resize_and_save(img, self.latest_path)
        result["type"] = "full"
        return result
    
    def take_region(self, x, y, w, h):
        """Belirli bölgenin görüntüsü"""
        img = pyautogui.screenshot(region=(x, y, w, h))
        filepath = os.path.join(SCREENSHOT_DIR, "region.jpg")
        result = self._resize_and_save(img, filepath)
        result["type"] = "region"
        result["region"] = {"x": x, "y": y, "w": w, "h": h}
        return result
    
    def take_active_window(self):
        """Aktif pencere görüntüsü"""
        try:
            if sys.platform == "darwin":
                script = '''
                tell application "System Events"
                    set frontApp to name of first application process whose frontmost is true
                    tell process frontApp
                        set winPos to position of window 1
                        set winSize to size of window 1
                        set x to item 1 of winPos as integer
                        set y to item 2 of winPos as integer
                        set w to item 1 of winSize as integer
                        set h to item 2 of winSize as integer
                    end tell
                end tell
                return (x as text) & "," & (y as text) & "," & (w as text) & "," & (h as text)
                '''
                result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
                if result.returncode == 0 and result.stdout.strip():
                    parts = result.stdout.strip().split(",")
                    if len(parts) == 4:
                        x, y, w, h = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
                        return self.take_region(x, y, w, h)
            
            elif sys.platform == "win32":
                import ctypes
                from ctypes import wintypes
                user32 = ctypes.windll.user32
                hwnd = user32.GetForegroundWindow()
                rect = wintypes.RECT()
                user32.GetWindowRect(hwnd, ctypes.byref(rect))
                x, y = rect.left, rect.top
                w, h = rect.right - rect.left, rect.bottom - rect.top
                return self.take_region(x, y, w, h)
            
            return self.take_full()
            
        except Exception as e:
            result = self.take_full()
            result["warning"] = f"Active window detection failed: {str(e)}"
            return result


screenshot_mgr = ScreenshotManager()


# ============== KOMUT İŞLEYİCİ ==============
def process_command(cmd_data):
    """Komutu işle"""
    action = cmd_data.get("action", "")
    params = cmd_data.get("params", {})
    
    # screenshot_coords parametresi - True ise koordinatları dönüştür
    use_screenshot_coords = params.get("screenshot_coords", False)
    
    try:
        # === SCREENSHOT ===
        if action == "screenshot":
            mode = params.get("mode", "full")
            
            if mode == "reference":
                return screenshot_mgr.take_reference()
            elif mode == "window":
                return screenshot_mgr.take_active_window()
            elif mode == "region":
                x = params.get("x", 0)
                y = params.get("y", 0)
                w = params.get("w", 800)
                h = params.get("h", 600)
                return screenshot_mgr.take_region(x, y, w, h)
            else:
                return screenshot_mgr.take_full()
        
        # === MOUSE ===
        elif action == "click":
            x, y = params.get("x", 0), params.get("y", 0)
            button = params.get("button", "left")
            clicks = params.get("clicks", 1)
            
            # Koordinat dönüşümü
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
        
        elif action == "move":
            x, y = params.get("x", 0), params.get("y", 0)
            duration = params.get("duration", 0.2)
            
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
        
        elif action == "scroll":
            amount = params.get("amount", -3)
            x, y = params.get("x"), params.get("y")
            
            if use_screenshot_coords and x is not None and y is not None:
                x, y = screenshot_mgr.convert_coords(x, y)
            
            pyautogui.scroll(amount, x=x, y=y)
            return {"status": "success", "action": "scroll", "amount": amount}
        
        elif action == "mouse":
            x, y = pyautogui.position()
            return {"status": "success", "x": x, "y": y}
        
        elif action == "drag":
            start_x = params.get("start_x", 0)
            start_y = params.get("start_y", 0)
            end_x = params.get("end_x", 0)
            end_y = params.get("end_y", 0)
            duration = params.get("duration", 0.5)
            button = params.get("button", "left")
            
            # Koordinat dönüşümü
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
        
        # === KLAVYE ===
        elif action == "type":
            text = params.get("text", "")
            type_with_clipboard(text)
            return {"status": "success", "action": "type", "length": len(text), "method": "clipboard"}
        
        elif action == "type_raw":
            text = params.get("text", "")
            interval = params.get("interval", 0.02)
            pyautogui.write(text, interval=interval)
            return {"status": "success", "action": "type_raw", "length": len(text), "method": "pyautogui"}
        
        elif action == "key":
            key = params.get("key", "")
            
            if '+' in key:
                keys = key.split('+')
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
                pyautogui.press(key)
            
            return {"status": "success", "action": "key", "key": key}
        
        # === KOMUT ÇALIŞTIRMA ===
        elif action == "run":
            command = params.get("command", "")
            cwd = params.get("cwd")
            timeout = params.get("timeout", 30)
            
            if cwd and not os.path.isdir(cwd):
                return {"status": "error", "message": f"Directory not found: {cwd}"}
            
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True,
                cwd=cwd, timeout=timeout
            )
            return {
                "status": "success",
                "command": command,
                "cwd": cwd or os.getcwd(),
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        
        # === PENCERE YÖNETİMİ ===
        elif action == "window_move":
            app = params.get("app", "")
            x = params.get("x", 0)
            y = params.get("y", 0)
            
            if not app:
                return {"status": "error", "message": "App name required"}
            
            # Önce mevcut pozisyonu al
            before = get_window_position(app)
            
            # Taşı
            result = move_window(app, x, y)
            
            # Sonra yeni pozisyonu al
            after = get_window_position(app)
            
            result["action"] = "window_move"
            result["app"] = app
            result["target"] = [x, y]
            result["before"] = before
            result["after"] = after
            result["verified"] = after is not None and after.get("x") == x and after.get("y") == y
            return result
        
        elif action == "window_resize":
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
        
        elif action == "window_position":
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
        
        elif action == "windows_list":
            windows = list_windows()
            return {
                "status": "success",
                "action": "windows_list",
                "windows": windows,
                "count": len(windows)
            }
        
        elif action == "get_ui_elements":
            # UI elementlerini listele (Accessibility API)
            app = params.get("app", "")
            if not app:
                return {"status": "error", "message": "App name required"}
            
            elements = get_ui_elements(app)
            
            if isinstance(elements, dict) and "error" in elements:
                return {"status": "error", "message": elements["error"]}
            
            return {
                "status": "success",
                "action": "get_ui_elements",
                "app": app,
                "elements": elements,
                "count": len(elements)
            }
        
        elif action == "click_element":
            # UI elementine isimle tıkla
            app = params.get("app", "")
            element = params.get("element", "")
            
            if not app or not element:
                return {"status": "error", "message": "app and element required"}
            
            result = click_ui_element(app, element)
            return result
        
        elif action == "scroll_app":
            # Belirli bir uygulamada scroll yap (screenshot gerektirmez!)
            app = params.get("app", "")
            amount = params.get("amount", -3)
            
            if not app:
                return {"status": "error", "message": "App name required"}
            
            try:
                if sys.platform == "darwin":
                    # Uygulamayı öne getir
                    script = f'tell application "{app}" to activate'
                    subprocess.run(["osascript", "-e", script], capture_output=True)
                    time.sleep(0.2)
                    pyautogui.scroll(amount)
                    return {"status": "success", "action": "scroll_app", "app": app, "amount": amount}
                
                elif sys.platform == "win32":
                    # Windows'ta pencereyi öne getir
                    import ctypes
                    user32 = ctypes.windll.user32
                    EnumWindows = user32.EnumWindows
                    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
                    GetWindowText = user32.GetWindowTextW
                    GetWindowTextLength = user32.GetWindowTextLengthW
                    SetForegroundWindow = user32.SetForegroundWindow
                    
                    found_hwnd = None
                    def foreach_window(hwnd, lParam):
                        nonlocal found_hwnd
                        length = GetWindowTextLength(hwnd)
                        if length > 0:
                            buff = ctypes.create_unicode_buffer(length + 1)
                            GetWindowText(hwnd, buff, length + 1)
                            if app.lower() in buff.value.lower():
                                found_hwnd = hwnd
                                return False
                        return True
                    
                    EnumWindows(EnumWindowsProc(foreach_window), 0)
                    
                    if found_hwnd:
                        SetForegroundWindow(found_hwnd)
                        time.sleep(0.2)
                        pyautogui.scroll(amount)
                        return {"status": "success", "action": "scroll_app", "app": app, "amount": amount}
                    else:
                        return {"status": "error", "message": f"Window not found: {app}"}
                
                else:
                    return {"status": "error", "message": "Unsupported platform"}
            
            except Exception as e:
                return {"status": "error", "message": str(e)}
        
        elif action == "terminal_run":
            # Terminal'de yeni pencere/tab açıp komut çalıştır (conda, venv, herşey çalışır!)
            command = params.get("command", "")
            cwd = params.get("cwd", "")
            new_window = params.get("new_window", False)
            
            if not command:
                return {"status": "error", "message": "command required"}
            
            try:
                if sys.platform == "darwin":
                    # macOS: osascript ile Terminal'de çalıştır
                    full_cmd = command
                    if cwd:
                        full_cmd = f'cd {cwd} && {command}'
                    
                    if new_window:
                        script = f'''tell application "Terminal"
                            do script "{full_cmd}"
                            activate
                        end tell'''
                    else:
                        script = f'tell application "Terminal" to do script "{full_cmd}"'
                    
                    result = subprocess.run(
                        ["osascript", "-e", script],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    return {
                        "status": "success" if result.returncode == 0 else "error",
                        "action": "terminal_run",
                        "command": command,
                        "cwd": cwd,
                        "stdout": result.stdout.strip(),
                        "stderr": result.stderr
                    }
                
                elif sys.platform == "win32":
                    # Windows: cmd veya PowerShell'de yeni pencere aç
                    full_cmd = command
                    if cwd:
                        full_cmd = f'cd /d {cwd} && {command}'
                    
                    # start komutu yeni pencere açar
                    result = subprocess.run(
                        f'start cmd /k "{full_cmd}"',
                        capture_output=True,
                        text=True,
                        shell=True,
                        timeout=10
                    )
                    
                    return {
                        "status": "success" if result.returncode == 0 else "error",
                        "action": "terminal_run",
                        "command": command,
                        "cwd": cwd
                    }
                
                else:
                    return {"status": "error", "message": "Unsupported platform"}
            
            except Exception as e:
                return {"status": "error", "message": str(e)}
        
        # === SİSTEM ===
        elif action == "screen":
            w, h = pyautogui.size()
            return {
                "status": "success", 
                "width": w, 
                "height": h, 
                "platform": sys.platform,
                "screenshot_width": MAX_WIDTH,
                "scale_ratio": round(w / MAX_WIDTH, 3)
            }
        
        elif action == "status":
            return {
                "status": "running",
                "name": "Claude Desktop Bridge",
                "version": "0.6.0",
                "platform": sys.platform,
                "reference_taken": screenshot_mgr.reference_taken,
                "scale_ratio": screenshot_mgr.scale_ratio
            }
        
        else:
            return {"status": "error", "message": f"Unknown action: {action}"}
    
    except subprocess.TimeoutExpired:
        return {"status": "error", "message": "Command timed out"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ============== DOSYA İZLEYİCİ ==============
def write_result(result):
    """Sonucu dosyaya yaz"""
    result["timestamp"] = datetime.now().isoformat()
    with open(RESULT_FILE, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)


def file_watcher():
    """command.json dosyasını izle"""
    last_processed_id = None
    
    while True:
        try:
            if os.path.exists(COMMAND_FILE):
                with open(COMMAND_FILE, 'r', encoding='utf-8') as f:
                    cmd_data = json.load(f)
                
                cmd_id = cmd_data.get("id", "")
                if cmd_id and cmd_id != last_processed_id:
                    action = cmd_data.get("action", "unknown")
                    print(f"  → Processing: {action} (id: {cmd_id})")
                    
                    result = process_command(cmd_data)
                    result["command_id"] = cmd_id
                    write_result(result)
                    
                    if "path" in result:
                        print(f"    Screenshot: {result['path']} ({result.get('size_kb', '?')} KB)")
                    if "real_coords" in result:
                        print(f"    Coords: {result.get('input_coords')} → {result.get('real_coords')}")
                    
                    last_processed_id = cmd_id
            
            time.sleep(0.2)
        
        except json.JSONDecodeError:
            time.sleep(0.3)
        except Exception as e:
            print(f"  ✗ Error: {e}")
            time.sleep(1)


# ============== ANA FONKSİYON ==============
def main():
    screen_w, screen_h = pyautogui.size()
    ratio = round(screen_w / MAX_WIDTH, 2)
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║         Claude Desktop Bridge v0.6.0                         ║
╠══════════════════════════════════════════════════════════════╣
║  Platform: {sys.platform:<49} ║
║  Screen: {screen_w}x{screen_h} → Screenshot: {MAX_WIDTH}px (ratio: {ratio}x)      ║
╠══════════════════════════════════════════════════════════════╣
║  NEW: Accessibility API - UI elementlerine isimle tıkla!    ║
║       get_ui_elements + click_element                       ║
║       Koordinat tahmini yok, %100 isabet!                    ║
╠══════════════════════════════════════════════════════════════╣
║  Actions:                                                    ║
║    screenshot  - mode: full/reference/region/window          ║
║    click       - x, y, button, clicks, screenshot_coords     ║
║    move        - x, y, duration, screenshot_coords           ║
║    drag        - start_x/y, end_x/y, screenshot_coords       ║
║    scroll      - amount, x, y                                ║
║    type        - text (Unicode destekli)                     ║
║    key         - key (cmd+c, ctrl+v, enter...)               ║
║    run         - command, cwd, timeout                       ║
║    window_move - app, x, y (Mouse olmadan pencere taşı!)     ║
║    window_resize - app, width, height                        ║
║    windows_list - Açık pencereleri listele                    ║
║    get_ui_elements - UI elementlerini listele (isim+koord)  ║
║    click_element - İsimle tıkla (koordinat gerekmez!)        ║
║    scroll_app  - app, amount (Screenshot gerektirmez!)       ║
║    terminal_run - command, cwd (Conda/venv/herşey çalışır!) ║
║    screen/status - Sistem bilgisi                            ║
╠══════════════════════════════════════════════════════════════╣
║  Durdurmak için: Ctrl+C                                      ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    write_result({"status": "ready", "message": "Bridge started"})
    
    print("  → Taking reference screenshot...")
    ref_result = screenshot_mgr.take_reference()
    print(f"    Reference: {ref_result['path']} ({ref_result['size_kb']} KB)")
    print(f"    Pixel size: {ref_result['pixel_size'][0]}x{ref_result['pixel_size'][1]}")
    print(f"    Screen size: {ref_result['screen_size'][0]}x{ref_result['screen_size'][1]}")
    print(f"    Resized: {ref_result['width']}x{ref_result['height']}")
    print()
    print("  Waiting for commands...")
    print()
    
    try:
        file_watcher()
    except KeyboardInterrupt:
        print("\n  Bridge stopped.")


if __name__ == '__main__':
    main()
