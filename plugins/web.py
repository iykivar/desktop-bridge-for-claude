"""
Web/Selenium Plugin - Browser automation ve web parsing
"""

import os
import sys
import time

# Selenium imports
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import (
        TimeoutException, 
        NoSuchElementException,
        WebDriverException
    )
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

from .shared import BRIDGE_DIR, SCREENSHOT_DIR, MAX_WIDTH, JPEG_QUALITY


# ============== SESSION YÖNETİMİ ==============
class WebSession:
    """Selenium browser session yönetimi"""
    
    def __init__(self):
        self.driver = None
        self.is_open = False
    
    def open(self, url=None, headless=False):
        """Browser başlat"""
        if not SELENIUM_AVAILABLE:
            return {"status": "error", "message": "Selenium not installed. Run: pip install selenium webdriver-manager"}
        
        if self.is_open:
            # Zaten açık, sadece URL'ye git
            if url:
                self.driver.get(url)
            return {"status": "success", "message": "Session already open", "url": self.driver.current_url}
        
        try:
            options = Options()
            
            if headless:
                options.add_argument("--headless=new")
            
            # Genel ayarlar
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--start-maximized")
            
            # Türkçe dil desteği
            options.add_argument("--lang=tr")
            
            # WebDriver başlat
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.implicitly_wait(5)
            self.is_open = True
            
            if url:
                self.driver.get(url)
                return {"status": "success", "message": "Browser opened", "url": url}
            
            return {"status": "success", "message": "Browser opened"}
        
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def close(self):
        """Browser kapat"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
            self.is_open = False
            return {"status": "success", "message": "Browser closed"}
        return {"status": "success", "message": "No browser to close"}
    
    def ensure_open(self):
        """Session açık değilse hata döndür"""
        if not self.is_open or not self.driver:
            return {"status": "error", "message": "No browser session. Use web_open first."}
        return None


# Global session instance
session = WebSession()


# ============== BY SELECTOR MAPPING ==============
BY_MAP = {
    "id": By.ID,
    "class": By.CLASS_NAME,
    "css": By.CSS_SELECTOR,
    "xpath": By.XPATH,
    "text": By.LINK_TEXT,
    "partial_text": By.PARTIAL_LINK_TEXT,
    "tag": By.TAG_NAME,
    "name": By.NAME,
}


def get_by(by_str):
    """String'den By enum'a çevir"""
    return BY_MAP.get(by_str.lower(), By.CSS_SELECTOR)


# ============== ACTION HANDLERS ==============

def web_open(params):
    """Browser aç ve URL'ye git"""
    url = params.get("url", "")
    headless = params.get("headless", False)
    return session.open(url, headless)


def web_close(params):
    """Browser kapat"""
    return session.close()


def web_goto(params):
    """URL'ye git"""
    error = session.ensure_open()
    if error:
        return error
    
    url = params.get("url", "")
    if not url:
        return {"status": "error", "message": "url required"}
    
    try:
        session.driver.get(url)
        return {"status": "success", "action": "web_goto", "url": url, "title": session.driver.title}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def web_find(params):
    """Element bul, bilgilerini döndür"""
    error = session.ensure_open()
    if error:
        return error
    
    selector = params.get("selector", "")
    by = params.get("by", "css")
    
    if not selector:
        return {"status": "error", "message": "selector required"}
    
    try:
        element = session.driver.find_element(get_by(by), selector)
        rect = element.rect
        
        return {
            "status": "success",
            "action": "web_find",
            "found": True,
            "selector": selector,
            "by": by,
            "tag": element.tag_name,
            "text": element.text[:200] if element.text else "",
            "visible": element.is_displayed(),
            "enabled": element.is_enabled(),
            "location": {"x": rect["x"], "y": rect["y"]},
            "size": {"width": rect["width"], "height": rect["height"]}
        }
    except NoSuchElementException:
        return {"status": "success", "action": "web_find", "found": False, "selector": selector, "by": by}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def web_click(params):
    """Elemente tıkla"""
    error = session.ensure_open()
    if error:
        return error
    
    selector = params.get("selector", "")
    by = params.get("by", "css")
    
    if not selector:
        return {"status": "error", "message": "selector required"}
    
    try:
        element = session.driver.find_element(get_by(by), selector)
        element.click()
        return {
            "status": "success",
            "action": "web_click",
            "selector": selector,
            "by": by,
            "tag": element.tag_name
        }
    except NoSuchElementException:
        return {"status": "error", "message": f"Element not found: {selector}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def web_type(params):
    """Elemente metin yaz"""
    error = session.ensure_open()
    if error:
        return error
    
    selector = params.get("selector", "")
    text = params.get("text", "")
    by = params.get("by", "css")
    clear = params.get("clear", True)  # Önce temizle
    
    if not selector:
        return {"status": "error", "message": "selector required"}
    
    try:
        element = session.driver.find_element(get_by(by), selector)
        if clear:
            element.clear()
        element.send_keys(text)
        return {
            "status": "success",
            "action": "web_type",
            "selector": selector,
            "by": by,
            "length": len(text)
        }
    except NoSuchElementException:
        return {"status": "error", "message": f"Element not found: {selector}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def web_text(params):
    """Element text içeriğini oku"""
    error = session.ensure_open()
    if error:
        return error
    
    selector = params.get("selector", "")
    by = params.get("by", "css")
    
    if not selector:
        return {"status": "error", "message": "selector required"}
    
    try:
        element = session.driver.find_element(get_by(by), selector)
        return {
            "status": "success",
            "action": "web_text",
            "selector": selector,
            "by": by,
            "text": element.text,
            "tag": element.tag_name
        }
    except NoSuchElementException:
        return {"status": "error", "message": f"Element not found: {selector}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def web_exists(params):
    """Element var mı kontrol et"""
    error = session.ensure_open()
    if error:
        return error
    
    selector = params.get("selector", "")
    by = params.get("by", "css")
    timeout = params.get("timeout", 0)
    
    if not selector:
        return {"status": "error", "message": "selector required"}
    
    try:
        if timeout > 0:
            # Belirli süre bekle
            WebDriverWait(session.driver, timeout).until(
                EC.presence_of_element_located((get_by(by), selector))
            )
            return {"status": "success", "action": "web_exists", "exists": True, "selector": selector}
        else:
            # Anında kontrol
            elements = session.driver.find_elements(get_by(by), selector)
            return {"status": "success", "action": "web_exists", "exists": len(elements) > 0, "selector": selector, "count": len(elements)}
    except TimeoutException:
        return {"status": "success", "action": "web_exists", "exists": False, "selector": selector, "timeout": True}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def web_wait(params):
    """Element görünene kadar bekle"""
    error = session.ensure_open()
    if error:
        return error
    
    selector = params.get("selector", "")
    by = params.get("by", "css")
    timeout = params.get("timeout", 10)
    visible = params.get("visible", True)  # Görünür olmasını bekle
    
    if not selector:
        return {"status": "error", "message": "selector required"}
    
    try:
        if visible:
            condition = EC.visibility_of_element_located((get_by(by), selector))
        else:
            condition = EC.presence_of_element_located((get_by(by), selector))
        
        element = WebDriverWait(session.driver, timeout).until(condition)
        
        return {
            "status": "success",
            "action": "web_wait",
            "selector": selector,
            "by": by,
            "found": True,
            "tag": element.tag_name
        }
    except TimeoutException:
        return {"status": "error", "message": f"Timeout waiting for: {selector}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def web_screenshot(params):
    """Sayfa screenshot'ı al (küçültülmüş JPEG)"""
    error = session.ensure_open()
    if error:
        return error
    
    filename = params.get("filename", "web_screenshot.jpg")
    # Uzantıyı .jpg yap
    if filename.endswith('.png'):
        filename = filename[:-4] + '.jpg'
    fullpath = os.path.join(SCREENSHOT_DIR, filename)
    
    try:
        # Önce temp PNG al
        temp_path = os.path.join(SCREENSHOT_DIR, "_temp_web.png")
        session.driver.save_screenshot(temp_path)
        
        # PIL ile aç, küçült, JPEG kaydet
        from PIL import Image
        img = Image.open(temp_path)
        original_w, original_h = img.width, img.height
        
        # Küçült
        if img.width > MAX_WIDTH:
            ratio = MAX_WIDTH / img.width
            new_height = int(img.height * ratio)
            img = img.resize((MAX_WIDTH, new_height), Image.LANCZOS)
        
        # RGBA -> RGB
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        
        # JPEG kaydet
        img.save(fullpath, "JPEG", quality=JPEG_QUALITY, optimize=True)
        
        # Temp sil
        try:
            os.remove(temp_path)
        except:
            pass
        
        size_kb = round(os.path.getsize(fullpath) / 1024, 1)
        return {
            "status": "success",
            "action": "web_screenshot",
            "path": fullpath,
            "size_kb": size_kb,
            "original_size": [original_w, original_h],
            "resized_size": [img.width, img.height],
            "url": session.driver.current_url
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def web_source(params):
    """Sayfa HTML kaynağını al"""
    error = session.ensure_open()
    if error:
        return error
    
    try:
        html = session.driver.page_source
        return {
            "status": "success",
            "action": "web_source",
            "url": session.driver.current_url,
            "title": session.driver.title,
            "length": len(html),
            "html": html[:50000] if len(html) > 50000 else html  # Max 50KB
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def web_elements(params):
    """Çoklu element bul"""
    error = session.ensure_open()
    if error:
        return error
    
    selector = params.get("selector", "")
    by = params.get("by", "css")
    limit = params.get("limit", 50)  # Max element sayısı
    
    if not selector:
        return {"status": "error", "message": "selector required"}
    
    try:
        elements = session.driver.find_elements(get_by(by), selector)[:limit]
        
        results = []
        for i, el in enumerate(elements):
            try:
                results.append({
                    "index": i,
                    "tag": el.tag_name,
                    "text": el.text[:100] if el.text else "",
                    "visible": el.is_displayed(),
                    "location": {"x": el.rect["x"], "y": el.rect["y"]}
                })
            except:
                continue
        
        return {
            "status": "success",
            "action": "web_elements",
            "selector": selector,
            "by": by,
            "count": len(results),
            "elements": results
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def web_execute(params):
    """JavaScript çalıştır"""
    error = session.ensure_open()
    if error:
        return error
    
    script = params.get("script", "")
    
    if not script:
        return {"status": "error", "message": "script required"}
    
    try:
        result = session.driver.execute_script(script)
        return {
            "status": "success",
            "action": "web_execute",
            "result": str(result) if result else None
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def web_info(params):
    """Mevcut sayfa bilgisi"""
    error = session.ensure_open()
    if error:
        return error
    
    try:
        return {
            "status": "success",
            "action": "web_info",
            "url": session.driver.current_url,
            "title": session.driver.title,
            "session_open": session.is_open
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def web_scroll(params):
    """Sayfada scroll yap"""
    error = session.ensure_open()
    if error:
        return error
    
    direction = params.get("direction", "down")  # down, up, top, bottom
    amount = params.get("amount", 500)  # pixel
    selector = params.get("selector", "")  # Elemente scroll
    by = params.get("by", "css")
    
    try:
        if selector:
            # Elemente scroll
            element = session.driver.find_element(get_by(by), selector)
            session.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
            return {"status": "success", "action": "web_scroll", "to_element": selector}
        else:
            # Yön bazlı scroll
            if direction == "down":
                session.driver.execute_script(f"window.scrollBy(0, {amount});")
            elif direction == "up":
                session.driver.execute_script(f"window.scrollBy(0, -{amount});")
            elif direction == "top":
                session.driver.execute_script("window.scrollTo(0, 0);")
            elif direction == "bottom":
                session.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            return {"status": "success", "action": "web_scroll", "direction": direction, "amount": amount}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ============== EXPORTS ==============
ACTIONS = {
    "web_open": web_open,
    "web_close": web_close,
    "web_goto": web_goto,
    "web_find": web_find,
    "web_click": web_click,
    "web_type": web_type,
    "web_text": web_text,
    "web_exists": web_exists,
    "web_wait": web_wait,
    "web_screenshot": web_screenshot,
    "web_source": web_source,
    "web_elements": web_elements,
    "web_execute": web_execute,
    "web_info": web_info,
    "web_scroll": web_scroll,
}
