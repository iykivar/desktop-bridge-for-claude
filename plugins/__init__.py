"""
Claude Desktop Bridge - Plugin System
======================================
Her plugin ACTIONS dict'i export eder.
"""

from . import screenshot
from . import mouse
from . import keyboard
from . import window
from . import accessibility
from . import system
from . import web

def get_all_handlers():
    """Tüm plugin'lerden handler'ları topla"""
    handlers = {}
    
    for module in [screenshot, mouse, keyboard, window, accessibility, system, web]:
        if hasattr(module, 'ACTIONS'):
            handlers.update(module.ACTIONS)
    
    return handlers
