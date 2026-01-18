"""
Shared state ve yardımcı fonksiyonlar
"""

import os
import sys
import subprocess
import time

import pyautogui
from PIL import Image

# ============== AYARLAR ==============
BRIDGE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCREENSHOT_DIR = os.path.join(BRIDGE_DIR, "screenshots")
MAX_WIDTH = 1000
JPEG_QUALITY = 65

# PyAutoGUI güvenlik
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

# ============== SCREENSHOT MANAGER ==============
class ScreenshotManager:
    """Akıllı screenshot yönetimi + koordinat dönüşümü"""
    
    def __init__(self):
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        self.reference_taken = False
        self.reference_path = os.path.join(SCREENSHOT_DIR, "reference.jpg")
        self.latest_path = os.path.join(SCREENSHOT_DIR, "latest.jpg")
        
        # Koordinat dönüşümü için
        self.scale_ratio = 1.0
        self.original_width = 0
        self.original_height = 0
        self.resized_width = 0
        self.resized_height = 0
        self.screen_width = 0
        self.screen_height = 0
        
    def _resize_and_save(self, img, filepath):
        """Resmi küçült ve JPEG olarak kaydet"""
        original_w, original_h = img.width, img.height
        screen_w, screen_h = pyautogui.size()
        
        if img.width > MAX_WIDTH:
            self.scale_ratio = screen_w / MAX_WIDTH
            ratio = MAX_WIDTH / img.width
            new_height = int(img.height * ratio)
            img = img.resize((MAX_WIDTH, new_height), Image.LANCZOS)
        else:
            self.scale_ratio = 1.0
        
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
        return int(x * self.scale_ratio), int(y * self.scale_ratio)
    
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
                    end tell
                end tell
                return (item 1 of winPos as text) & "," & (item 2 of winPos as text) & "," & (item 1 of winSize as text) & "," & (item 2 of winSize as text)
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


# Global screenshot manager instance
screenshot_mgr = ScreenshotManager()


# ============== CLIPBOARD ==============
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
