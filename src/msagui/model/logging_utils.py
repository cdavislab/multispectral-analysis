import glob
import json
import logging
from logging.handlers import RotatingFileHandler
import os
import platform
import sys
import tempfile
import threading
from datetime import datetime, timezone
from zipfile import ZIP_DEFLATED, ZipFile

APP_NAME = "msaGUI"
LOG_FILE_NAME = "msa_app.log"

_current_log_file: str | None = None
_logging_configured = False


def resolve_app_data_dir() -> str:
    home = os.path.expanduser("~")
    system = platform.system()

    if system == "Windows":
        base_dir = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA") or home
        app_dir = os.path.join(base_dir, APP_NAME)
    elif system == "Darwin":
        app_dir = os.path.join(home, "Library", "Application Support", APP_NAME)
    else:
        base_dir = os.environ.get("XDG_DATA_HOME") or os.path.join(home, ".local", "share")
        app_dir = os.path.join(base_dir, APP_NAME)

    try:
        os.makedirs(app_dir, exist_ok=True)
        return app_dir
    except OSError:
        return tempfile.gettempdir()


def resolve_log_dir() -> str:
    app_dir = resolve_app_data_dir()
    log_dir = os.path.join(app_dir, "logs")
    try:
        os.makedirs(log_dir, exist_ok=True)
        return log_dir
    except OSError:
        return tempfile.gettempdir()


def get_log_file_path() -> str:
    global _current_log_file
    if _current_log_file is None:
        _current_log_file = os.path.join(resolve_log_dir(), LOG_FILE_NAME)
    return _current_log_file


def _install_exception_logging() -> None:
    previous_excepthook = sys.excepthook

    def _handle_uncaught_exception(
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_traceback,
    ) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            previous_excepthook(exc_type, exc_value, exc_traceback)
            return
        logging.getLogger("msagui.crash").critical(
            "Unhandled exception",
            exc_info=(exc_type, exc_value, exc_traceback),
        )
        previous_excepthook(exc_type, exc_value, exc_traceback)

    sys.excepthook = _handle_uncaught_exception

    if hasattr(threading, "excepthook"):
        previous_threading_hook = threading.excepthook

        def _handle_thread_exception(args: threading.ExceptHookArgs) -> None:
            if args.exc_value is not None:
                logging.getLogger("msagui.crash").critical(
                    "Unhandled thread exception",
                    exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
                )
            else:
                logging.getLogger("msagui.crash").critical(
                    "Unhandled thread exception with no exception value"
                )
            previous_threading_hook(args)

        threading.excepthook = _handle_thread_exception


def configure_logging(
    *,
    level: int = logging.INFO,
    max_bytes: int = 5 * 1024 * 1024,
    backup_count: int = 5,
    enable_console: bool = True,
) -> str:
    global _logging_configured
    root = logging.getLogger()

    if _logging_configured:
        return get_log_file_path()

    log_file = get_log_file_path()

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    root.handlers.clear()
    root.setLevel(level)
    root.addHandler(file_handler)

    if enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root.addHandler(console_handler)

    logging.captureWarnings(True)
    _install_exception_logging()

    _logging_configured = True

    logging.getLogger(__name__).info("Logging initialized at %s", log_file)
    return log_file


def list_log_files() -> list[str]:
    log_file = get_log_file_path()
    candidates = [log_file]
    candidates.extend(glob.glob(f"{log_file}.*"))

    files = [path for path in candidates if os.path.isfile(path)]
    files.sort()
    return files


def build_log_bundle_metadata() -> dict:
    return {
        "app_name": APP_NAME,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "platform": platform.platform(),
        "python_version": sys.version,
        "executable": sys.executable,
        "is_frozen": bool(getattr(sys, "frozen", False)),
        "log_file": get_log_file_path(),
        "log_files": list_log_files(),
    }


def export_logs_bundle(destination_zip: str) -> str:
    if not destination_zip.lower().endswith(".zip"):
        destination_zip = f"{destination_zip}.zip"

    log_files = list_log_files()
    metadata = build_log_bundle_metadata()

    with ZipFile(destination_zip, mode="w", compression=ZIP_DEFLATED) as archive:
        for path in log_files:
            archive.write(path, arcname=os.path.join("logs", os.path.basename(path)))
        archive.writestr("metadata.json", json.dumps(metadata, indent=2))

    return destination_zip
