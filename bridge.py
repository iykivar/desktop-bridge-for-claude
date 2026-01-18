"""
Claude Desktop Bridge v0.7.0
============================
Plugin-based architecture - Modüler ve genişletilebilir.

Kullanım: python bridge.py
"""

import json
import time
import os
import sys
from datetime import datetime

# ============== AYARLAR ==============
BRIDGE_DIR = os.path.dirname(os.path.abspath(__file__))
COMMAND_FILE = os.path.join(BRIDGE_DIR, "command.json")
RESULT_FILE = os.path.join(BRIDGE_DIR, "result.json")

# ============== PLUGIN LOADER ==============
from plugins import get_all_handlers
from plugins.shared import screenshot_mgr, MAX_WIDTH
from plugins.tasks import run_task, list_tasks

HANDLERS = get_all_handlers()


# ============== KOMUT İŞLEYİCİ ==============
def process_command(cmd_data):
    """Komutu ilgili plugin'e yönlendir"""
    action = cmd_data.get("action", "")
    params = cmd_data.get("params", {})
    
    # Task sistemi (handlers referansı gerekiyor)
    if action == "run_task":
        try:
            return run_task(params, HANDLERS)
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    if action == "list_tasks":
        try:
            return list_tasks(params)
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    # Normal plugin handler'ları
    if action in HANDLERS:
        try:
            return HANDLERS[action](params)
        except Exception as e:
            return {"status": "error", "message": str(e)}
    else:
        return {"status": "error", "message": f"Unknown action: {action}"}


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
                    
                    # Debug bilgisi
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
    import pyautogui
    screen_w, screen_h = pyautogui.size()
    ratio = round(screen_w / MAX_WIDTH, 2)
    
    # Yüklenen action'ları listele
    action_list = sorted(HANDLERS.keys())
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║         Claude Desktop Bridge v0.7.0                         ║
║         Plugin-Based Architecture                            ║
╠══════════════════════════════════════════════════════════════╣
║  Platform: {sys.platform:<49} ║
║  Screen: {screen_w}x{screen_h} → Screenshot: {MAX_WIDTH}px (ratio: {ratio}x)      ║
╠══════════════════════════════════════════════════════════════╣
║  Loaded Actions ({len(action_list)}):                                         ║""")
    
    # Action'ları 3'lü gruplar halinde göster
    for i in range(0, len(action_list), 3):
        group = action_list[i:i+3]
        line = ", ".join(group)
        print(f"║    {line:<56} ║")
    
    print(f"""╠══════════════════════════════════════════════════════════════╣
║  Plugins: screenshot, mouse, keyboard, window,              ║
║           accessibility, system                              ║
╠══════════════════════════════════════════════════════════════╣
║  Durdurmak için: Ctrl+C                                      ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    write_result({"status": "ready", "message": "Bridge started", "version": "0.7.0"})
    
    print("  → Taking reference screenshot...")
    ref_result = screenshot_mgr.take_reference()
    print(f"    Reference: {ref_result['path']} ({ref_result['size_kb']} KB)")
    print(f"    Screen: {ref_result['screen_size'][0]}x{ref_result['screen_size'][1]}")
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
