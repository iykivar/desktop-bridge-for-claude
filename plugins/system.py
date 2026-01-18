"""
System Plugin - Komut çalıştırma, terminal, durum bilgisi
"""

import os
import sys
import subprocess

import pyautogui

from .shared import screenshot_mgr, MAX_WIDTH


def run_command(params):
    """Shell komutu çalıştır"""
    command = params.get("command", "")
    cwd = params.get("cwd")
    timeout = params.get("timeout", 30)
    background = params.get("background", False)  # GUI uygulamaları için
    
    if cwd and not os.path.isdir(cwd):
        return {"status": "error", "message": f"Directory not found: {cwd}"}
    
    try:
        if background:
            # Non-blocking - GUI uygulamaları için
            if sys.platform == "win32":
                proc = subprocess.Popen(
                    command, shell=True, cwd=cwd,
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            else:
                proc = subprocess.Popen(
                    command, shell=True, cwd=cwd,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
            return {
                "status": "success",
                "command": command,
                "cwd": cwd or os.getcwd(),
                "pid": proc.pid,
                "background": True
            }
        else:
            # Blocking - normal komutlar için
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
    except subprocess.TimeoutExpired:
        return {"status": "error", "message": "Command timed out"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def terminal_run(params):
    """Terminal'de yeni pencere açıp komut çalıştır (non-blocking)"""
    command = params.get("command", "")
    cwd = params.get("cwd", "")
    
    if not command:
        return {"status": "error", "message": "command required"}
    
    try:
        if sys.platform == "darwin":
            full_cmd = command
            if cwd:
                full_cmd = f'cd {cwd} && {command}'
            
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
            full_cmd = command
            if cwd:
                full_cmd = f'cd /d "{cwd}" && {command}'
            
            # CREATE_NEW_CONSOLE ile yeni pencerede aç, beklemeden devam et
            proc = subprocess.Popen(
                f'cmd /k "{full_cmd}"',
                shell=True,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            
            return {
                "status": "success",
                "action": "terminal_run",
                "command": command,
                "cwd": cwd,
                "pid": proc.pid,
                "note": "Non-blocking, yeni pencerede çalışıyor"
            }
        
        else:
            return {"status": "error", "message": "Unsupported platform"}
    
    except Exception as e:
        return {"status": "error", "message": str(e)}


def screen_info(params):
    """Ekran bilgisi"""
    w, h = pyautogui.size()
    return {
        "status": "success",
        "width": w,
        "height": h,
        "platform": sys.platform,
        "screenshot_width": MAX_WIDTH,
        "scale_ratio": round(w / MAX_WIDTH, 3)
    }


def status_info(params):
    """Bridge durumu"""
    return {
        "status": "running",
        "name": "Claude Desktop Bridge",
        "version": "0.7.0",
        "platform": sys.platform,
        "reference_taken": screenshot_mgr.reference_taken,
        "scale_ratio": screenshot_mgr.scale_ratio,
        "architecture": "plugin-based"
    }


# Dışa açılan action'lar
ACTIONS = {
    "run": run_command,
    "terminal_run": terminal_run,
    "screen": screen_info,
    "status": status_info,
}
