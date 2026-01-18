"""
Accessibility / UI Automation Plugin
"""

import sys
import subprocess
import pyautogui

# Windows pywinauto (sadece Windows'ta)
PYWINAUTO_AVAILABLE = False
if sys.platform == "win32":
    try:
        from pywinauto import Application
        PYWINAUTO_AVAILABLE = True
    except ImportError:
        pass


def get_ui_elements(app_name):
    """UI elementlerini al"""
    elements = []
    
    try:
        if sys.platform == "darwin":
            # macOS: AppleScript
            script = f'''
            set output to ""
            tell application "System Events"
                tell process "{app_name}"
                    try
                        set btns to every button of window 1
                        repeat with btn in btns
                            set btnName to name of btn
                            set btnPos to position of btn
                            set btnSize to size of btn
                            set output to output & "button|" & btnName & "|" & (item 1 of btnPos) & "," & (item 2 of btnPos) & "|" & (item 1 of btnSize) & "," & (item 2 of btnSize) & "\\n"
                        end repeat
                    end try
                    try
                        set chks to every checkbox of window 1
                        repeat with chk in chks
                            set chkName to name of chk
                            set chkPos to position of chk
                            set chkSize to size of chk
                            set chkValue to value of chk
                            set output to output & "checkbox|" & chkName & "|" & (item 1 of chkPos) & "," & (item 2 of chkPos) & "|" & (item 1 of chkSize) & "," & (item 2 of chkSize) & "|" & chkValue & "\\n"
                        end repeat
                    end try
                    try
                        set txts to every text field of window 1
                        repeat with txt in txts
                            set txtName to name of txt
                            set txtPos to position of txt
                            set txtSize to size of txt
                            set txtValue to value of txt
                            set output to output & "textfield|" & txtName & "|" & (item 1 of txtPos) & "," & (item 2 of txtPos) & "|" & (item 1 of txtSize) & "," & (item 2 of txtSize) & "|" & txtValue & "\\n"
                        end repeat
                    end try
                    try
                        set menus to every menu button of window 1
                        repeat with m in menus
                            set mName to name of m
                            set mPos to position of m
                            set mSize to size of m
                            set output to output & "menubutton|" & mName & "|" & (item 1 of mPos) & "," & (item 2 of mPos) & "|" & (item 1 of mSize) & "," & (item 2 of mSize) & "\\n"
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
                            
                            if len(parts) >= 5:
                                if elem_type == "checkbox":
                                    elem["checked"] = parts[4] == "1"
                                elif elem_type == "textfield":
                                    elem["value"] = parts[4]
                            
                            elements.append(elem)
        
        elif sys.platform == "win32":
            if not PYWINAUTO_AVAILABLE:
                return {"status": "error", "message": "pywinauto not installed"}
            
            try:
                app = Application(backend="uia").connect(title_re=f".*{app_name}.*", timeout=5)
                window = app.top_window()
                
                type_map = {
                    "Button": "button",
                    "CheckBox": "checkbox",
                    "Edit": "textfield",
                    "ComboBox": "menubutton",
                    "MenuItem": "menuitem",
                    "RadioButton": "radiobutton"
                }
                
                for ctrl in window.descendants():
                    try:
                        ctrl_type = ctrl.element_info.control_type
                        name = ctrl.element_info.name or ""
                        rect = ctrl.element_info.rectangle
                        
                        if ctrl_type in type_map and name:
                            elem = {
                                "type": type_map[ctrl_type],
                                "name": name,
                                "position": {"x": rect.left, "y": rect.top},
                                "size": {"w": rect.width(), "h": rect.height()},
                                "center": {
                                    "x": rect.left + rect.width() // 2,
                                    "y": rect.top + rect.height() // 2
                                }
                            }
                            
                            if ctrl_type == "CheckBox":
                                try:
                                    elem["checked"] = ctrl.get_toggle_state() == 1
                                except:
                                    elem["checked"] = False
                            
                            if ctrl_type == "Edit":
                                try:
                                    elem["value"] = ctrl.get_value() or ""
                                except:
                                    elem["value"] = ""
                            
                            elements.append(elem)
                    except:
                        continue
                        
            except Exception as e:
                return {"error": f"Could not connect to window: {str(e)}"}
        
        return elements
    
    except Exception as e:
        return {"error": str(e)}


def click_ui_element(app_name, element_name):
    """UI elementine isimle tıkla"""
    try:
        elements = get_ui_elements(app_name)
        
        if isinstance(elements, dict) and ("error" in elements or "status" in elements):
            return elements
        
        # Element adını ara (kısmi eşleşme)
        target = None
        for elem in elements:
            if element_name.lower() in elem["name"].lower():
                target = elem
                break
        
        if not target:
            return {"status": "error", "message": f"Element not found: {element_name}"}
        
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
    
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ============== ACTION HANDLERS ==============

def get_ui_elements_action(params):
    """UI elementleri action"""
    app = params.get("app", "")
    if not app:
        return {"status": "error", "message": "App name required"}
    
    elements = get_ui_elements(app)
    
    if isinstance(elements, dict) and ("error" in elements or "status" in elements):
        return {"status": "error", "message": elements.get("error") or elements.get("message")}
    
    return {
        "status": "success",
        "action": "get_ui_elements",
        "app": app,
        "elements": elements,
        "count": len(elements)
    }


def click_element_action(params):
    """Element tıkla action"""
    app = params.get("app", "")
    element = params.get("element", "")
    
    if not app or not element:
        return {"status": "error", "message": "app and element required"}
    
    return click_ui_element(app, element)


# Dışa açılan action'lar
ACTIONS = {
    "get_ui_elements": get_ui_elements_action,
    "click_element": click_element_action,
}
