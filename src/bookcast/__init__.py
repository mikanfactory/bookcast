import logging.config
from pathlib import Path

import yaml

config_path = Path(__file__).parent / "logging.yml"
with config_path.open() as f:
    config = yaml.safe_load(f)

logging.config.dictConfig(config)
