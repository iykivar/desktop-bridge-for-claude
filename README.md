# Claude Desktop Bridge v0.6.0 🌉

A bridge application that enables Claude to see the computer screen, execute commands, and interact with GUI applications.

## 🚀 Key Features

- ✅ **Accessibility API** - Click UI elements by name, no coordinate guessing!
- ✅ **Smart Screenshots** - JPEG, auto-resize (2-4 MB → 30-40 KB)
- ✅ **Coordinate Conversion** - Automatic calculation for Retina/HiDPI displays
- ✅ **Window Management** - Move/resize windows without mouse
- ✅ **Terminal Integration** - Conda/venv/everything works
- ✅ **Unicode Support** - Full international character support
- ✅ **Cross-platform** - macOS + Windows

## 📦 Installation

```bash
cd claude_desktop_bridge

# Virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# Dependencies
pip install -r requirements.txt
```

### macOS Permissions

System Preferences → Security & Privacy → Privacy:
- **Screen Recording** → Allow Terminal
- **Accessibility** → Allow Terminal

## 🎯 Usage

```bash
python bridge.py
```

Claude writes commands to `command.json`, Bridge processes them and writes results to `result.json`.

## 📋 All Commands

### 🖼️ Screenshot

```json
{"action": "screenshot", "params": {"mode": "full"}}
{"action": "screenshot", "params": {"mode": "window"}}
{"action": "screenshot", "params": {"mode": "region", "x": 0, "y": 0, "w": 800, "h": 600}}
```

### 🎯 Accessibility API (NEW!)

```json
// List UI elements - name, position, size
{"action": "get_ui_elements", "params": {"app": "python"}}

// Click by name - no coordinates needed!
{"action": "click_element", "params": {"app": "python", "element": "Start"}}
```

**Result:**
```json
{
  "elements": [
    {"type": "button", "name": "▶ Start", "center": {"x": 1895, "y": 296}},
    {"type": "button", "name": "⏹ Stop", "center": {"x": 2037, "y": 296}},
    {"type": "checkbox", "name": "Debug Mode", "checked": true}
  ]
}
```

### 🖱️ Mouse

```json
// Normal click
{"action": "click", "params": {"x": 500, "y": 300}}

// Click with screenshot coordinates (auto conversion)
{"action": "click", "params": {"x": 195, "y": 117, "screenshot_coords": true}}

// Double click
{"action": "click", "params": {"x": 500, "y": 300, "clicks": 2}}

// Drag
{"action": "drag", "params": {"start_x": 100, "start_y": 100, "end_x": 500, "end_y": 300}}

// Scroll
{"action": "scroll", "params": {"amount": -3}}
```

### ⌨️ Keyboard

```json
// Type text (Unicode supported)
{"action": "type", "params": {"text": "Hello World! 🎉"}}

// Key/shortcut
{"action": "key", "params": {"key": "enter"}}
{"action": "key", "params": {"key": "cmd+c"}}
```

### 🪟 Window Management

```json
// Move window (no mouse!)
{"action": "window_move", "params": {"app": "TextEdit", "x": 100, "y": 100}}

// Resize window
{"action": "window_resize", "params": {"app": "TextEdit", "width": 800, "height": 600}}

// List open windows
{"action": "windows_list", "params": {}}

// Scroll in app (no screenshot needed)
{"action": "scroll_app", "params": {"app": "Claude", "amount": -3}}
```

### 💻 Command Execution

```json
// Simple command
{"action": "run", "params": {"command": "ls -la", "cwd": "/path/to/dir"}}

// Run in Terminal (conda/venv works!)
{"action": "terminal_run", "params": {
    "command": "conda activate myenv && python main.py",
    "cwd": "/path/to/project"
}}
```

### ℹ️ System Info

```json
{"action": "screen", "params": {}}
{"action": "status", "params": {}}
```

## 📁 File Structure

```
claude_desktop_bridge/
├── bridge.py           # Main application
├── command.json        # Command file
├── result.json         # Result file
├── requirements.txt    # Dependencies
├── README.md           # This file
├── start.sh            # macOS/Linux launcher
├── start.bat           # Windows launcher
├── screenshots/        # Screenshot folder
│   ├── reference.jpg
│   ├── latest.jpg
│   └── region.jpg
└── venv/               # Virtual environment
```

## 🔄 Typical Workflow

```json
// 1. Launch GUI application
{"action": "terminal_run", "params": {"command": "conda activate myenv && python app.py", "cwd": "..."}}

// 2. Get UI elements (NO screenshot!)
{"action": "get_ui_elements", "params": {"app": "python"}}

// 3. Click button (NO coordinates!)
{"action": "click_element", "params": {"app": "python", "element": "Start"}}

// 4. (Optional) See result
{"action": "screenshot", "params": {"mode": "full"}}
```

## 🔒 Security

- Localhost only access
- FAILSAFE enabled (mouse to corner = stop)
- No external network access

## 📊 Version History

| Version | Features |
|---------|----------|
| v0.6.0 | Accessibility API, get_ui_elements, click_element |
| v0.5.0 | window_move, scroll_app, terminal_run |
| v0.4.0 | screenshot_coords, coordinate conversion |
| v0.3.0 | Unicode support, clipboard typing |
| v0.2.0 | Smart screenshots, JPEG optimization |
| v0.1.0 | Initial release |

## 📄 License

MIT
