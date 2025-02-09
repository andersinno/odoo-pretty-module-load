import logging
from contextlib import contextmanager
from typing import Iterator


@contextmanager
def override_logging_levels(levels: dict[str, int]) -> Iterator[None]:
    old_levels: dict[str, int] = {}
    for name, level in levels.items():
        logger = logging.getLogger(name)
        old_levels[name] = logger.level
        logger.setLevel(level)
    try:
        yield
    finally:
        for name, level in old_levels.items():
            logging.getLogger(name).setLevel(level)
