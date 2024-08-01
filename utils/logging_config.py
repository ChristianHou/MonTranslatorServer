import logging
import logging.handlers
import os

# 创建日志目录
log_dir = './logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 配置日志
LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE = os.path.join(log_dir, 'app.log')

logging.basicConfig(
    level=LOG_LEVEL,
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
