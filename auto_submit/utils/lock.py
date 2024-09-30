import redis
import os
import psutil


class Lock:
    def __init__(self, name, host, port, db):
        self.redis = redis.Redis(host=host, port=port, db=db)
        try:
            self.redis.ping()
        except redis.ConnectionError:
            raise ConnectionError(
                (
                    "RedisDB is not connected.\n"
                    "You need to start the Redis server first:\n"
                    "redis-server --port <PORT>"
                )
            )
        self.name = name
        self.pid = os.getpid()

    # 当前进程与目标进程只能存在一个
    @property
    def conflict(self):
        pid = self.redis.get(self.name)
        if pid is not None and pid != self.pid:
            if psutil.pid_exists(int(pid)):
                return True
        self.redis.set(self.name, self.pid)
        return False

    # 判断目标进程是否存在
    @property
    def exist(self):
        pid = self.redis.get(self.name)
        return pid is not None and psutil.pid_exists(int(pid))
