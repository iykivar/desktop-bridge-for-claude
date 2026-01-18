"""
Screenshot Plugin
"""

from .shared import screenshot_mgr


def screenshot(params):
    """Screenshot al"""
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


# Dışa açılan action'lar
ACTIONS = {
    "screenshot": screenshot,
}
