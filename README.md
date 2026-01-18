# Desktop Bridge for Claude 🌉

> Give Claude the ability to see and control your computer

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

**⚠️ Disclaimer:** This is a community project, not affiliated with or endorsed by Anthropic.

---

## What is this?

Claude is incredibly capable but can't interact with your computer directly. This bridge changes that.

Write a command in `command.json` → Bridge executes it → Result appears in `result.json`

**Claude can now:**
- 📸 Take screenshots and see your screen
- 🖱️ Click, type, scroll, drag
- 🪟 Manage windows
- 🌐 Automate browsers with Selenium
- 💻 Run terminal commands
- 🎯 Click UI elements by name (Accessibility API)

---

## Quick Start

```bash
# Clone
git clone https://github.com/iykivar/claude_desktop_bridge.git
cd claude_desktop_bridge

# Setup
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install
pip install -r requirements.txt

# Run
python bridge.py
```

---

## Architecture

```
┌─────────────┐     command.json      ┌─────────────┐
│   Claude    │ ──────────────────▶   │   Bridge    │
│  (claude.ai │                       │  (Python)   │
│  or Desktop)│ ◀──────────────────   │             │
└─────────────┘     result.json       └─────────────┘
                                            │
                    ┌───────────────────────┼───────────────────────┐
                    ▼                       ▼                       ▼
              ┌──────────┐           ┌──────────┐            ┌──────────┐
              │screenshot│           │  mouse   │            │   web    │
              │ keyboard │           │  window  │            │ (Selenium)│
              │  system  │           │accessibility│          │          │
              └──────────┘           └──────────┘            └──────────┘
```

**Plugin-based design** - Easy to extend, each plugin handles specific actions.

---

## Plugins & Actions

### 📸 Screenshot
```json
{"action": "screenshot", "params": {"mode": "full"}}
{"action": "screenshot", "params": {"mode": "window"}}
{"action": "screenshot", "params": {"mode": "region", "x": 0, "y": 0, "w": 800, "h": 600}}
```
- Auto-resizes to 1000px width
- JPEG compression (65% quality)
- Typical size: 40-80 KB

### 🖱️ Mouse
```json
{"action": "click", "params": {"x": 500, "y": 300}}
{"action": "click", "params": {"x": 500, "y": 300, "clicks": 2}}
{"action": "drag", "params": {"start_x": 100, "start_y": 100, "end_x": 500, "end_y": 300}}
{"action": "scroll", "params": {"amount": -3}}
```

### ⌨️ Keyboard
```json
{"action": "type", "params": {"text": "Hello World! Türkçe 🎉"}}
{"action": "key", "params": {"key": "enter"}}
{"action": "key", "params": {"key": "ctrl+c"}}
```
- Full Unicode support via clipboard

### 🪟 Window Management
```json
{"action": "windows_list", "params": {}}
{"action": "window_move", "params": {"app": "Notepad", "x": 100, "y": 100}}
{"action": "window_resize", "params": {"app": "Notepad", "width": 800, "height": 600}}
```

### 🎯 Accessibility API
```json
{"action": "get_ui_elements", "params": {"app": "Notepad"}}
{"action": "click_element", "params": {"app": "Notepad", "element": "Save"}}
```
- Click buttons by name, no coordinates needed!
- Works with native applications

### 💻 System / Terminal
```json
{"action": "run", "params": {"command": "dir", "cwd": "C:/Projects"}}
{"action": "terminal_run", "params": {"command": "npm start", "cwd": "C:/Projects/app"}}
{"action": "status", "params": {}}
```

### 🌐 Web / Selenium
```json
{"action": "web_open", "params": {"url": "https://example.com"}}
{"action": "web_click", "params": {"selector": "#login-btn", "by": "css"}}
{"action": "web_type", "params": {"selector": "input[name='email']", "text": "test@example.com"}}
{"action": "web_screenshot", "params": {"filename": "page.jpg"}}
{"action": "web_source", "params": {}}
{"action": "web_execute", "params": {"script": "return document.title"}}
{"action": "web_close", "params": {}}
```
- Full browser automation
- JS-rendered content support
- Screenshots auto-compressed like native

### 📋 Task System
```json
{"action": "list_tasks", "params": {}}
{"action": "run_task", "params": {"task": "my_workflow"}}
```
Save multi-step workflows as JSON in `tasks/` folder.

---

## Example: Web Scraping

```json
// 1. Open site
{"action": "web_open", "params": {"url": "https://books.example.com"}}

// 2. Wait for content
{"action": "web_wait", "params": {"selector": ".book-card", "timeout": 10}}

// 3. Extract data with JavaScript
{"action": "web_execute", "params": {
  "script": "return JSON.stringify([...document.querySelectorAll('.book-card')].map(el => ({title: el.querySelector('h3').innerText, price: el.querySelector('.price').innerText})))"
}}

// 4. Screenshot for reference
{"action": "web_screenshot", "params": {"filename": "books.jpg"}}

// 5. Close browser
{"action": "web_close", "params": {}}
```

---

## Platform Support

| Feature | Windows | macOS |
|---------|---------|-------|
| Screenshot | ✅ | ✅ |
| Mouse/Keyboard | ✅ | ✅ |
| Window Management | ✅ | ✅ |
| Accessibility API | ✅ | ✅ |
| Selenium/Web | ✅ | ✅ |
| Terminal | ✅ | ✅ |

### macOS Permissions
System Preferences → Security & Privacy → Privacy:
- **Screen Recording** → Allow Terminal
- **Accessibility** → Allow Terminal

---

## File Structure

```
claude_desktop_bridge/
├── bridge.py           # Main dispatcher
├── plugins/            # Action handlers
│   ├── screenshot.py
│   ├── mouse.py
│   ├── keyboard.py
│   ├── window.py
│   ├── accessibility.py
│   ├── system.py
│   └── web.py          # Selenium
├── tasks/              # Saved workflows
├── screenshots/        # Output images
├── command.json        # Input (Claude writes)
├── result.json         # Output (Bridge writes)
└── requirements.txt
```

---

## Security

- 🏠 **Localhost only** - No network exposure
- 🛑 **Failsafe** - Move mouse to corner to stop
- 👁️ **Transparent** - All actions logged to console
- 🔒 **Your control** - Claude can only do what you allow

---

## Version History

| Version | Highlights |
|---------|------------|
| **0.7.0** | Plugin architecture, Selenium web automation, Task system |
| 0.6.0 | Accessibility API, click by element name |
| 0.5.0 | Window management, terminal integration |
| 0.4.0 | Coordinate conversion for HiDPI displays |
| 0.3.0 | Unicode support |
| 0.2.0 | Smart screenshot compression |
| 0.1.0 | Initial release |

---

## Contributing

PRs welcome! Ideas for new plugins:
- Audio control
- Clipboard management  
- File system operations
- OCR integration

---

## License

MIT License - Use freely, attribution appreciated.

---

**Made with 🤝 by a human and Claude working together**
