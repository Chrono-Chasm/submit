from dataclasses import dataclass, asdict, field
from typing import List, Optional
import uuid
import subprocess
import psutil
from tqdm import tqdm
import os

NOT_SUBMITTED = "NOT_SUBMITTED"
SUBMITTING = "SUBMITTING"
RUNNING = "RUNNING"
FINISHED = "FINISHED"


@dataclass
class Task:
    cmd: List[str]
    min_gpus: int = 0
    min_gpu_memory: int = 0
    priority: int = 0
    available_gpu_ids: Optional[List[int]] = None
    stderr_log_path: Optional[str] = None
    stdout_log_path: Optional[str] = None

    full_cmd: Optional[str] = None
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    state: str = NOT_SUBMITTED
    pid: Optional[int] = None
    occupied_gpu_ids: List[int] = field(default_factory=list)

    def submitting(self):
        assert self.state == NOT_SUBMITTED
        self.state = SUBMITTING

    def running(self, gpus, stdout_log_path, stderr_log_path):
        assert self.state == SUBMITTING
        _ = self
        try:
            if self.stdout_log_path is None:
                self.stdout_log_path = stdout_log_path
            if self.stderr_log_path is None:
                self.stderr_log_path = stderr_log_path
            os.makedirs(
                os.path.dirname(os.path.abspath(self.stdout_log_path)), exist_ok=True
            )
            os.makedirs(
                os.path.dirname(os.path.abspath(self.stderr_log_path)), exist_ok=True
            )
        except Exception as e:
            self = _
            raise e
        self.state = RUNNING
        cmd=self.cmd
        if self.min_gpus != 0:
            CUDA_DEVICES = f"export CUDA_VISIBLE_DEVICES={','.join(map(str, gpus))}"
            cmd = [CUDA_DEVICES] + cmd
        cmd = " && ".join(cmd)
        full_cmd = f"nohup bash -c '{cmd}' 1>\"{self.stdout_log_path}\" 2>\"{self.stderr_log_path}\" &  echo $!"
        self.pid = int(subprocess.getoutput(full_cmd))
        self.occupied_gpu_ids = gpus
        self.full_cmd = full_cmd

        tqdm.write(f"Submitting task {self.cmd} on GPU {gpus}")
        tqdm.write(full_cmd)
        tqdm.write(str(self.pid))

    def flush(self):
        try:
            process = psutil.Process(self.pid)
            # if not process.is_running():
            #     del pid_to_gpu_map[pid]
        except psutil.NoSuchProcess:
            self.state = FINISHED
            self.occupied_gpu_ids = []
            self.pid = None
        return self
