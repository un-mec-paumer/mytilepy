from threading import Lock
import time
import json


_progress = {}
_lock = Lock()

def get_progress(task_id):
    with _lock:
        current_progress = _progress.get(task_id)
        # print("Initial progress fetch:", current_progress)
        # print("Current progress dict:", _progress)

    if current_progress is None:
        yield json.dumps({"status": "unknown", "progress": 0, "message": "No such task_id"})
    else:
        try:
            while True:
                with _lock:
                    current_progress = _progress.get(task_id)
                if current_progress is not None:
                    yield json.dumps(current_progress)
                else:
                    yield json.dumps({"status": "completed", "progress": 1, "message": "Task completed"})
                    break
                time.sleep(0.1)
        except GeneratorExit:
            print(f"Stopped monitoring progress for task_id: {task_id}")


def report(task_id, progress=None, message=None, status=None, result=None):
    with _lock:
        
        data = _progress.get(task_id)

        if data is None:
            data = {"progress": 0, "message": "", "status": "in_progress", "result": None}

        if progress is not None:
            data["progress"] = progress
        if message is not None:
            data["message"] = message
        if status is not None:
            data["status"] = status
        if result is not None:
            data["result"] = result

        if status == "completed":
            print(f"Task {task_id} completed. Cleaning up progress data.")
            _progress.pop(task_id, None)
        else:
            _progress[task_id] = data
        print(f"Reported progress for {task_id}: {_progress} \n")

# # -------- For Debug -------- 

# def consume_progress(task_id):
#     for update in get_progress(task_id):
#         # print("PROGRESS:", update, end="")
#         yield update

# report("test", progress=0.0, message="Starting", status="in_progress")

# # Lancer la surveillance dans un thread
# Thread(target=consume_progress, args=("test",), daemon=True).start()

# report("test", progress=0.5, message="Halfway", status="in_progress")
# time.sleep(1)
# report("test", progress=0.75, message="Almost", status="in_progress")
# time.sleep(2)
# report("test", progress=0.9, message="Ninety", status="in_progress")
# time.sleep(1)
# report("test", progress=1.0, message="Done", status="completed", result={"data": [1, 2, 3]})
