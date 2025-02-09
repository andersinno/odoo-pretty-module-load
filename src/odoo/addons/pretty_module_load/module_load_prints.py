import logging
import os
import threading
from contextlib import contextmanager
from typing import Iterator

import odoo.tools

from .log_utils import override_logging_levels

FORCE_ASCII = os.getenv("PML_FORCE_ASCII", "").lower() in {"1", "true"}
USE_UNICODE = not FORCE_ASCII
LOAD_ICON = "🔨" if USE_UNICODE else "="
TIME_ICON = "⏱️" if USE_UNICODE else "@"
MODULE_ICONS = "⭐➕" if USE_UNICODE else "* "
PROGRESS_CHARS = "█▉▊▋▌▍▎▏▏" if USE_UNICODE else "#:::... |"
PROGRESS_FULL_CHAR = PROGRESS_CHARS[0]
PROGRESS_EDGE_CHAR = PROGRESS_CHARS[-1]


@contextmanager
def override_logging_for_module_loading(
    verbosity: int = 1,
    has_logfile: bool = False,
    db_name: str | None = None,
) -> Iterator[None]:
    base_level = logging.WARNING
    if verbosity >= 5:
        base_level = logging.INFO
    elif verbosity >= 6:
        base_level = logging.DEBUG
    log_levels: dict[str, int] = {
        "odoo": base_level,
        "werkzeug": base_level,
        "odoo.modules.loading": min(base_level, logging.INFO),
    }
    if has_logfile:
        log_levels = {}
    with override_logging_levels(log_levels):
        module_loading_logger = logging.getLogger("odoo.modules.loading")
        module_loading_filter = ModuleLoadingProgressLogFilter(
            verbosity=verbosity,
            db_name=db_name,
        )
        if has_logfile:
            module_loading_filter.verbosity = 4
        module_loading_logger.addFilter(module_loading_filter)
        try:
            yield
        finally:
            module_loading_logger.removeFilter(module_loading_filter)


class ModuleLoadingProgressLogFilter(logging.Filter):
    """
    Filter Odoo module loading log messages and convert them to prints.
    """

    def __init__(self, *, verbosity: int = 1, db_name: str | None = None):
        super().__init__()
        self._wanted_modules: set[str] | None = None
        self.verbosity = verbosity
        self.multiline = True if verbosity >= 2 else False
        self.db_name = db_name

    def filter(self, record):
        if self._wanted_modules is None:
            mods = {**odoo.tools.config["init"], **odoo.tools.config["update"]}
            if mods:
                # Initialize _wanted_modules as soon as modules are set
                # in Odoo's config.
                self._wanted_modules = {mod for (mod, v) in mods.items() if v}
        if record.levelno >= logging.WARNING:
            return True  # Passthrough
        elif self.verbosity <= 0:
            return False  # Filter all INFO messages
        elif record.msg == "Loading module %s (%d/%d)":
            # Convert "Loading module" messages to prints
            (name, index, count) = record.args
            db_name = self.db_name
            if not db_name:
                db_name = getattr(threading.current_thread(), "dbname", "?db?")
            progress_bar = make_progress_bar(index, count, bar_length=50)
            is_wanted_module = name in (self._wanted_modules or [])
            module_icon = MODULE_ICONS[0 if is_wanted_module else 1]
            prefix = "\r" if not self.multiline else ""
            line = (
                f"{LOAD_ICON} {progress_bar} "
                f"[{db_name}] Loading module {index:4} / {count:4} "
                f"{module_icon} {name:45}"
            )
            end = "\n" if index == count or self.multiline else ""
            print(prefix + line, end=end)
        elif record.msg.startswith("%s modules loaded in %.2fs"):
            # Print "N modules loaded in Xs" messages with a special icon
            print(f"{TIME_ICON} {record.msg % record.args}")
        return self.verbosity >= 4  # filter INFO messages if level <= 3


def make_progress_bar(n: int, total: int, *, bar_length: int):
    full_bars = int((bar_length * n) / total)
    remainder = int(8 * ((bar_length * n) % total) / total)
    remainder_chr = PROGRESS_CHARS[8 - remainder] if remainder else ""
    bar_chars = PROGRESS_FULL_CHAR * full_bars + remainder_chr
    return f"{bar_chars:{bar_length}}{PROGRESS_EDGE_CHAR}"
