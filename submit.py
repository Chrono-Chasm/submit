import os
import sys
import yaml
import time
import psutil
import subprocess
from tqdm import tqdm
from typing import List
from dataclasses import dataclass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WAIT_TIME = 10


@dataclass
class GPU_task:
    cmd: List[str]  # 执行命令
    GPU: int = 1  # 需要多少个GPU
    mem: int = 0  # 需要多少MiB内存
    util: int = 100  # 需要百分之多少GPU利用率


def get_task_list():
    with open(os.path.join(SCRIPT_DIR, "tasks.yaml"), "r") as f:
        tasks = yaml.safe_load(f)
    tasks = [GPU_task(**task) for task in tasks]
    return tasks


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


def get_available_gpus(task, pid_to_gpu_map, cuda_visible_devices):
    gpu_info = get_gpu_info()
    available_gpus = []
    pid_list = list(pid_to_gpu_map.keys())
    for pid in pid_list:
        try:
            process = psutil.Process(pid)
            # if not process.is_running():
            #     del pid_to_gpu_map[pid]
        except psutil.NoSuchProcess:
            del pid_to_gpu_map[pid]
    skip_gpus = {gpu for gpus in pid_to_gpu_map.values() for gpu in gpus}
    for gpu_id, info in gpu_info.items():
        if info["free_memory"] < task.mem:
            tqdm.write(
                f"GPU {gpu_id} free_memory is {info['free_memory']} , which is less than {task.mem}"
            )
            continue
        if info["utilization"] > 100 - task.util:
            tqdm.write(
                f"GPU {gpu_id} utilization is {info['utilization']} , which is more than {100 - task.util}"
            )
            continue
        if gpu_id in skip_gpus:
            tqdm.write(f"GPU {gpu_id} is skipped")
            continue
        if cuda_visible_devices is not None and gpu_id not in cuda_visible_devices:
            tqdm.write(f"GPU {gpu_id} is not in cuda_visible_devices")
            continue
        available_gpus.append(gpu_id)
    if len(available_gpus) >= task.GPU:
        return available_gpus[: task.GPU]


def submit_tasks(tasks, cuda_visible_devices):
    pid_to_gpu_map = dict()
    for task in tqdm(tasks):
        gpus = get_available_gpus(task, pid_to_gpu_map, cuda_visible_devices)
        while gpus is None:
            time.sleep(WAIT_TIME)
            gpus = get_available_gpus(task, pid_to_gpu_map, cuda_visible_devices)
        print(f"Submitting task {task.cmd} on GPU {gpus}")
        CUDA_DEVICES = f"export CUDA_VISIBLE_DEVICES={','.join(map(str, gpus))}"
        task.cmd = [CUDA_DEVICES] + task.cmd
        cmd = ";".join(task.cmd)
        log_path = f"{SCRIPT_DIR}/log/{str(gpus[0])}.log"
        full_cmd = f"nohup bash -c '{cmd}' >>{log_path} 2>&1  &  echo $!"
        print(full_cmd)
        with open(log_path, "a") as f:
            f.write(full_cmd + "\n")
        pid = int(subprocess.getoutput(full_cmd))
        print(pid)
        pid_to_gpu_map[pid] = gpus


if __name__ == "__main__":
    cuda_visible_devices = (
        map(int, sys.argv[1].split(",")) if len(sys.argv) > 1 else None
    )
    tasks = get_task_list()
    submit_tasks(tasks, cuda_visible_devices)
