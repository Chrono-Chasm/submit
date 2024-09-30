import os
import yaml
file_path=os.path.dirname(__file__)
config_path=os.path.join(file_path,'../../config/default_config.yaml')
if 'CONFIG_PATH' in os.environ:
    config_path=os.environ['CONFIG_PATH']
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)