from loguru import logger

import sys
from pathlib import Path


LOG_FORMAT = ("<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level:<8}</level> | "
              "<white> THREAD: {thread:<15} </white> | "
              "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
              "<level>{message}</level>")


logger.configure(
    handlers=[
        dict(sink=sys.stderr, format=LOG_FORMAT, enqueue=True, level="DEBUG"),
        dict(
            sink=Path("logs", "twitter_{time:DD-MM-YYYY_HH}.log"),
            rotation="1 week",
            retention="2 week",
            compression="zip",
            level="DEBUG",
            enqueue=True,
            format=LOG_FORMAT),
    ],
)
