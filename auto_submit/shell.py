import time
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

    while True:
        print("-------------")
        print("0: exit")
        print("1: submit")
        print("2: ls")
        print("3: clear")
        if not lock.exist:
            print("4: Start the launch process")
        else:
            print("4: Stop the launch process")
        choice = input("choice: ")
        if choice == "1":
            path = input("yaml path([./config/tasks.yaml]): ")
            if path == "":
                path = "./config/tasks.yaml"
            try:
                submit(path)
            except AssertionError as e:
                choise = input(f"{e}, do you want to force submit? ([y]/n)")
                if choise.lower() == "y" or choise == "":
                    submit(path, force=True)
                elif choise.lower() == "n":
                    print("abandon")

        elif choice == "2":
            choise = input(
                (
                    "Which tasks do you want to print? "
                    "0: NOT_SUBMITTED, 1: SUBMITTING, 2: RUNNING, 3: FINISHED\n"
                    "default: 0,1,2,3\n"
                )
            )
            if choise == "":
                choise = "0,1,2,3"
            ls(
                [
                    {0: NOT_SUBMITTED, 1: SUBMITTING, 2: RUNNING, 3: FINISHED}[int(i)]
                    for i in choise.split(",")
                ]
            )
        elif choice == "3":
            if lock.exist:
                print("please stop the launch process first")
            else:
                clear()
                print("clear all tasks")
        elif choice == "4":
            if not lock.exist:
                log_path = input("log path: [./log/launch.log]")
                if log_path == "":
                    log_path = "./log/launch.log"
                abs_path = os.path.abspath(log_path)
                par_dir = os.path.dirname(abs_path)
                if not os.path.exists(par_dir):
                    os.makedirs(par_dir)
                with open(log_path, "w") as f:
                    f.write(f"{str(datetime.datetime.now())}\n")
                os.system(
                    f"nohup {sys.executable} -m auto_submit.launch > {log_path} 2>&1 &"
                )
                for i in range(10):
                    time.sleep(0.1)
                    if lock.exist:
                        break
                if not lock.exist:
                    print("launch failed")
            else:
                lock_pid = int(lock.lock_pid)
                os.system(f"kill {lock_pid}")
                task_list = redis_db.get_task_list()
                for task in task_list:
                    if task.state == SUBMITTING:
                        task.state = NOT_SUBMITTED
                redis_db.set_task_list(task_list)
                for i in range(10):
                    time.sleep(0.1)
                    if not lock.exist:
                        break
                if lock.exist:
                    print("kill failed")
        elif choice == "0":
            break
