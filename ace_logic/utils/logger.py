import logging
import sys
from pathlib import Path


def setup_logger(name: str ):
    """
    Configures and returns a professional logger.
    (配置并返回一个专业的日志记录器)
    """
    logger = logging.getLogger(name)

    # If the logger already has handlers, don't add more (prevents duplicate logs)
    if not logger.handlers:
        logger.setLevel(logging.INFO)

        # 1. Create a format for logs (时间 - 等级 - 模块名 - 消息)
        # Detailed English logs help in international dev environments
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 2. Console Handler (输出到控制台)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # 3. File Handler (输出到文件，方便以后查 Bug)
        # 1. 获取当前文件 (logger.py) 的绝对路径
        current_file = Path(__file__).resolve()

        # 2. 向上找两级，定位到项目根目录 (ace_logic 的上一层)
        # logger.py -> utils -> ace_logic -> Root
        project_root = current_file.parent.parent.parent

        # 3. 在根目录下创建 logs
        log_dir = project_root / "logs"
        log_dir.mkdir(exist_ok=True)

        file_handler = logging.FileHandler(log_dir / "game.log", encoding='utf-8')

        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger