# <del>自动提交任务</del> 抢GPU😋
本项目可以自动提交任务，提升实验设备的利用率，抢占显卡快人一步，反向促进实验室其乐融融的氛围

本项目可能有一堆bug，但是作者被抓去当帕鲁了😭，就先不继续调了

本项目支持：
 - 为不同任务设定不同GPU
 - 按照优先级顺序执行任务
 - 动态添加新的任务
---

### 安装

```bash
# 创建一个新的conda环境，命名为<your_env_name>，并安装Python 3.<your_python_version>
conda create -n <your_env_name> python=3.<your_python_version>
# 激活conda环境
conda activate <your_env_name>
# 安装redis
conda install redis
# 安装当前目录下的项目
pip install .
```

**注意**：请将`<your_env_name>`替换为您希望的环境名称，`<your_python_version>`替换为您需要的Python版本号。

### 配置文件

默认配置文件位于`./config/default_config.yaml`。
若启动服务或任务提交时未指定配置文件路径，将使用默认配置文件。

```yaml
redis:
  host: localhost       # Redis主机地址
  port: 9876            # Redis端口号
  tasks_db: 0           # 用于存储任务的Redis数据库编号
  lock_db: 1            # 用于锁机制的Redis数据库编号
  # （同时最多运行一个auto_commit.launch任务，因此需要一个表来维护进程状态）

cuda_visible_devices: null  # 例如 "0,1,2,3"，指定可见的GPU设备编号
# 若任务未对GPU的使用设定具体限制，则会依据cuda_visible_devices来界定可使用的GPU范围
WAIT_TIME: 3               # 等待时间（秒）
```

### 启动服务

1. **启动Redis服务**：
   ```bash
   redis-server --port <your_redis_port>
   ```
   请将`<your_redis_port>`替换为您希望的Redis端口号。

2. **启动项目服务**：
   打开一个新的Shell窗口，并运行以下命令：
   ```bash
   # 可以使用CONFIG_PATH环境变量指定配置文件路径
   CONFIG_PATH=<your_yaml_config_path> python -m auto_submit.launch
   ```
   请将`<your_yaml_config_path>`替换为您的配置文件路径。此命令将启动一个后台进程，用于提交Redis数据库中的任务。

### 任务配置

任务可以配置在任意位置的YAML文件中，格式如下：

```yaml
# 可以配置多个任务，每个任务是一个字典
- cmd:
  - export PATH=/PATH/TO/anaconda3/bin:$PATH # 没这句可能会导致找不到activate
  - source activate submit   # 激活conda环境"submit"
  - whereis python
  - echo $CUDA_VISIBLE_DEVICES
  - sleep 10
  - echo 1
  # 最好不要用引号，可能有转义问题。如需引号，可将命令写入bash脚本并调用。
  min_gpus: 1                # 任务所需GPU数量，可选，默认为0
  min_gpu_memory: 1000       # 任务所需GPU内存（MB），可选，默认为0
  priority: 0                # 任务优先级，越小越优先，默认为0
  # 新任务必须比正在被提交和运行的任务优先级低。可强制提交以提高优先级。
  available_gpu_ids: [2]     # 任务可使用的GPU ID列表，可选
  stderr_log_path: stderr.log # 任务标准错误输出文件路径，可选，默认为./log/{datetime}_{task_id}.stderr
  stdout_log_path: stdout.log # 任务标准输出文件路径，可选，默认为./log/{datetime}_{task_id}.stdout
  # task_id自动生成，可在数据库中查找。
```

### 任务提交

```bash
# 可以使用CONFIG_PATH环境变量指定配置文件路径，也可使用默认配置文件
CONFIG_PATH=<your_yaml_config_path> python -m auto_submit.shell
# 按提示操作即可。
```

**注意**：请将`<your_yaml_config_path>`替换为您的任务配置文件路径。

---
