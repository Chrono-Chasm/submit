import subprocess
from tqdm import tqdm
from auto_submit.utils.redisdb import redis_db
from auto_submit.utils.task import *


def get_gpu_info():
    result = subprocess.check_output(
        [
            "nvidia-smi",
            "--query-gpu=index,memory.total,memory.used,memory.free,utilization.gpu",
            "--format=csv,nounits,noheader",
        ]
    ).decode("utf-8")
    gpu_lines = result.strip().split("\n")

    gpu_info = {}
    for line in gpu_lines:
        gpu_id, total_memory, used_memory, free_memory, gpu_utilization = line.split(
            ","
        )
        gpu_info[int(gpu_id)] = {
            "total_memory": int(total_memory),
            "used_memory": int(used_memory),
            "free_memory": int(free_memory),
            "utilization": int(gpu_utilization),
        }

    return gpu_info


def get_available_gpus(task: Task, cuda_visible_devices):
    gpu_info = get_gpu_info()
    skip_gpus = get_skip_gpus()
    available_gpus = []
    for gpu_id, info in gpu_info.items():

        def test():
            if info["free_memory"] < task.min_gpu_memory:
                return False, f"{info['free_memory']}MiB < {task.min_gpu_memory}MiB"
            if gpu_id in skip_gpus:
                return False, "skipped"
            if task.available_gpu_ids is not None:
                if gpu_id not in task.available_gpu_ids:
                    return False, "not available"
            elif cuda_visible_devices is not None:
                if gpu_id not in cuda_visible_devices:
                    return False, "not visible"
            return True, "✅"

        res, msg = test()
        tqdm.write(f"{gpu_id}: {msg}", end=" ")
        if res:
            available_gpus.append(gpu_id)
    tqdm.write("")
    if len(available_gpus) >= task.min_gpus:
        return available_gpus[: task.min_gpus]


def get_skip_gpus():
    task_list = redis_db.flush_task()

    skip_gpus = list(
        set(
            gpu
            for task in task_list
            if task.state == RUNNING
            for gpu in task.occupied_gpu_ids
        )
    )
    return skip_gpus
