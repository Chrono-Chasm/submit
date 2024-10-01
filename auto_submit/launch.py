import os
import time
from auto_submit.utils.task import *
from auto_submit.utils.redisdb import redis_db
from auto_submit.utils.gpu import get_available_gpus
from auto_submit.utils.config import config
from auto_submit.utils.lock import Lock

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WAIT_TIME = config["WAIT_TIME"]


def try_submit(task: Task, cuda_visible_devices):

    task.submitting()
    redis_db.set_task(task)
    gpus = get_available_gpus(task, cuda_visible_devices)
    while gpus is None:
        time.sleep(WAIT_TIME)
        gpus = get_available_gpus(task, cuda_visible_devices)
    datetime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    task.running(
        gpus,
        os.path.join(SCRIPT_DIR, os.pardir, "log", f"{datetime} {task.task_id}.stdout"),
        os.path.join(SCRIPT_DIR, os.pardir, "log", f"{datetime} {task.task_id}.stderr"),
    )
    redis_db.set_task(task)


def submit_tasks(cuda_visible_devices):
    while True:
        task = redis_db.get_task()
        if task is None:
            tqdm.write("No tasks to submit")
            time.sleep(WAIT_TIME)
            continue
        try_submit(task, cuda_visible_devices)


if __name__ == "__main__":
    lock = Lock(
        "launch",
        config["redis"]["host"],
        config["redis"]["port"],
        config["redis"]["lock_db"],
    )
    if lock.conflict:
        tqdm.write("Another auto_submit.launch is running")
        exit(0)
    submit_tasks(config["cuda_visible_devices"])
