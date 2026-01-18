"""
Task Plugin - JSON tabanlı workflow çalıştırıcı
"""

import os
import json
import time

BRIDGE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TASKS_DIR = os.path.join(BRIDGE_DIR, "tasks")


def load_task(task_name):
    """Task dosyasını yükle"""
    # .json uzantısı yoksa ekle
    if not task_name.endswith('.json'):
        task_name = f"{task_name}.json"
    
    task_path = os.path.join(TASKS_DIR, task_name)
    
    if not os.path.exists(task_path):
        return None, f"Task not found: {task_path}"
    
    try:
        with open(task_path, 'r', encoding='utf-8') as f:
            return json.load(f), None
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON: {str(e)}"
    except Exception as e:
        return None, str(e)


def run_task(params, handlers):
    """Task çalıştır"""
    task_name = params.get("task", "")
    
    if not task_name:
        return {"status": "error", "message": "task name required"}
    
    # Task'ı yükle
    task_data, error = load_task(task_name)
    if error:
        return {"status": "error", "message": error}
    
    task_title = task_data.get("name", task_name)
    steps = task_data.get("steps", [])
    
    if not steps:
        return {"status": "error", "message": "Task has no steps"}
    
    results = []
    
    for i, step in enumerate(steps):
        action = step.get("action", "")
        step_params = step.get("params", {})
        step_name = step.get("name", f"Step {i+1}")
        wait_after = step.get("wait_after", 0)  # Adımdan sonra bekle (saniye)
        
        if not action:
            results.append({
                "step": i + 1,
                "name": step_name,
                "status": "skipped",
                "reason": "No action specified"
            })
            continue
        
        # Özel action: wait
        if action == "wait":
            seconds = step_params.get("seconds", 1)
            time.sleep(seconds)
            results.append({
                "step": i + 1,
                "name": step_name,
                "action": "wait",
                "status": "success",
                "seconds": seconds
            })
            continue
        
        # Handler'ı bul ve çalıştır
        if action in handlers:
            try:
                result = handlers[action](step_params)
                results.append({
                    "step": i + 1,
                    "name": step_name,
                    "action": action,
                    "status": result.get("status", "success"),
                    "result": result
                })
            except Exception as e:
                results.append({
                    "step": i + 1,
                    "name": step_name,
                    "action": action,
                    "status": "error",
                    "message": str(e)
                })
        else:
            results.append({
                "step": i + 1,
                "name": step_name,
                "action": action,
                "status": "error",
                "message": f"Unknown action: {action}"
            })
        
        # Adımdan sonra bekle
        if wait_after > 0:
            time.sleep(wait_after)
    
    # Özet
    success_count = sum(1 for r in results if r.get("status") == "success")
    error_count = sum(1 for r in results if r.get("status") == "error")
    
    return {
        "status": "success" if error_count == 0 else "partial",
        "action": "run_task",
        "task": task_title,
        "total_steps": len(steps),
        "success": success_count,
        "errors": error_count,
        "results": results
    }


def list_tasks(params):
    """Mevcut task'ları listele"""
    if not os.path.exists(TASKS_DIR):
        return {"status": "success", "tasks": [], "count": 0}
    
    tasks = []
    for filename in os.listdir(TASKS_DIR):
        if filename.endswith('.json'):
            task_path = os.path.join(TASKS_DIR, filename)
            try:
                with open(task_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    tasks.append({
                        "file": filename,
                        "name": data.get("name", filename),
                        "description": data.get("description", ""),
                        "steps": len(data.get("steps", []))
                    })
            except:
                tasks.append({
                    "file": filename,
                    "name": filename,
                    "description": "Error loading task",
                    "steps": 0
                })
    
    return {
        "status": "success",
        "action": "list_tasks",
        "tasks": tasks,
        "count": len(tasks)
    }


# NOT: ACTIONS burada tanımlanmıyor çünkü handlers referansı gerekiyor
# Bridge'de özel olarak handle edilecek
