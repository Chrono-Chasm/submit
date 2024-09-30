import yaml
import os
import sys
import datetime
from auto_submit.utils.lock import Lock
from auto_submit.utils.config import config
from auto_submit.utils.redisdb import redis_db
from auto_submit.utils.task import Task, NOT_SUBMITTED, SUBMITTING, RUNNING, FINISHED


def submit(yaml_path, force=False):
    redis_db.flush_task()
    with open(yaml_path, "r") as f:
        tasks = [Task(**task) for task in yaml.safe_load(f)]
        redis_db.add_tasks(tasks, force=force)


def ls(states=None):
    redis_db.flush_task()
    tasks = redis_db.get_task_list()
    for task in tasks:
        if states is None or task.state in states:
            print(task)


def clear():
    redis_db.flush_task()
    redis_db.set_task_list([])


if __name__ == "__main__":
    lock = Lock(
        "launch",
        config["redis"]["host"],
        config["redis"]["port"],
        config["redis"]["lock_db"],
    )
    if not lock.exist:
        choice = input("launch is not running, do you want to start it? ([y]/n)")
        if choice.lower() == "y" or choice == "":
            log_path = input("log path: [./launch.log]")
            if log_path == "":
                log_path = "./launch.log"
            with open(log_path, "w") as f:
                f.write(f"{str(datetime.datetime.now())}\n")
            os.system(
                f"nohup {sys.executable} -m auto_submit.launch > {log_path} 2>&1 &"
            )
    while True:
        print("0: submit")
        print("1: ls")
        print("2: clear")
        print("3: exit")
        choice = input("choice: ")
        if choice == "0":
            submit(input("yaml path: "))
        elif choice == "1":
            ls()
        elif choice == "2":
            clear()
        elif choice == "3":
            break
