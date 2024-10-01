import json
from typing import List
from auto_submit.utils.task import *
import redis
from tqdm import tqdm

TASK_KEY = f"tasks"


class RedisDB:
    def __init__(self, host, port, db):
        self.r = redis.Redis(host=host, port=port, db=db)
        try:
            self.r.ping()
        except redis.ConnectionError:
            raise ConnectionError(
                (
                    "RedisDB is not connected.\n"
                    "You need to start the Redis server first:\n"
                    "redis-server --port PORT"
                )
            )
        if self.r.get(TASK_KEY) is None:
            self.r.set(TASK_KEY, json.dumps([]))
        tqdm.write("RedisDB is connected.")

    def add_tasks(self, tasks: List[Task], force=False) -> None:
        assert self.r is not None, "redis is not connected."
        task_list = self.flush_task(save=False)
        max_priority = max(
            [t.priority for t in task_list if t.state in [SUBMITTING, RUNNING]],
            default=0,
        )
        if not force:
            assert min(t.priority for t in tasks) >= max_priority, (
                "priority must be larger than the max priority of the task list, "
                "you can set 'force' to True to force add tasks"
            )
        else:
            tqdm.write(
                f"'force' is set to True, priority will be increased by {max_priority}"
            )
            for task in tasks:
                task.priority += max_priority
        task_list += tasks
        self.set_task_list(task_list)
        tqdm.write(f"add {len(tasks)} tasks to redisdb.")

    def get_task_list(self) -> List[Task]:
        assert self.r is not None, "redis is not connected."
        tasks = self.r.get(TASK_KEY)
        return [Task(**task) for task in json.loads(tasks)]

    def get_task(self) -> Optional[Task]:
        task_list = self.flush_task()
        task = min(
            [task for task in task_list if task.state == NOT_SUBMITTED],
            key=lambda x: x.priority,
            default=None,
        )
        return task

    def set_task_list(self, tasks) -> None:
        assert self.r is not None, "redis is not connected."
        self.r.set(TASK_KEY, json.dumps([asdict(task) for task in tasks]))

    def set_task(self, task) -> None:
        task_list = self.flush_task(save=False)
        task_list = [t if t.task_id != task.task_id else task for t in task_list]
        self.set_task_list(task_list)

    def flush_task(self, save=True):
        task_list = self.get_task_list()
        task_list = [t.flush() for t in task_list]
        if save:
            self.set_task_list(task_list)
        return task_list


from auto_submit.utils.config import config

redis_db = RedisDB(
    host=config["redis"]["host"],
    port=config["redis"]["port"],
    db=config["redis"]["tasks_db"],
)
