"""
utils.py
General-purpose utilities: hashing, rich console logger.
"""

from typing import Callable, Union

from cryptography.hazmat.primitives import hashes
from rich.console import Console
from rich.progress import Progress


def sha256sum(data: bytes) -> bytes:
    """Calculates SHA-256 hash of the given data."""
    digest = hashes.Hash(hashes.SHA256())
    digest.update(data)
    return digest.finalize()


def md5sum(data: bytes) -> bytes:
    """Calculates MD5 hash of the given data."""
    digest = hashes.Hash(hashes.MD5())
    digest.update(data)
    return digest.finalize()


def nocache(func) -> Callable:
    """Decorator to temporarily disable caching for GkmasDummyMedia and children."""

    from .media import GkmasDummyMedia

    def wrapper(*args, **kwargs):
        original = GkmasDummyMedia.ENABLE_CACHE
        GkmasDummyMedia.ENABLE_CACHE = False
        try:
            return func(*args, **kwargs)
        finally:
            GkmasDummyMedia.ENABLE_CACHE = original

    return wrapper


class Logger(Console):
    """
    A rich console logger with custom log levels.

    Methods:
        info(message: str): Logs an informational message in white text.
        success(message: str): Logs a success message in green text.
        warning(message: str): Logs a warning message in yellow text.
        error(message: str): Logs an error message in red text
            followed by traceback, and raises an error.
    """

    def __init__(self):
        super().__init__()

    def info(self, message: str):
        self.print(f"[bold white][Info][/bold white] {message}")

    def success(self, message: str):
        self.print(f"[bold green][Success][/bold green] {message}")

    def warning(self, message: str):
        self.print(f"[bold yellow][Warning][/bold yellow] {message}")

    def error(self, message: str):
        self.print(f"[bold red][Error][/bold red] {message}")
        raise


class ProgressReporter:
    """
    An interface for either printing a progress bar to the console,
    or passing progress updates to a GUI.

    Args:
        title (str): "Master" description for the task, usually a filename.
        progress (Progress, optional): Rich Progress instance for console output.
            Should only be instantiated in GkmasManifest.download()
            for a batch of tasks, to support multiple bar updates.
            If None, a disposable Progress instance is created.
        task_id (int, optional): Task ID for GUI progress updates.
            Again, should only be provided by GkmasManifest.download().
    """

    def __init__(
        self,
        title: str,
        progress: Union[Progress, None] = None,
        task_id: Union[int, None] = None,
    ):
        self.title = title
        if not progress:
            assert (
                task_id is None
            ), "task_id should only be provided with a Progress instance"
            self.progress = Progress()
            self.task_id = self.progress.add_task(title)
            self.is_standalone = True
        else:
            assert (
                task_id is not None
            ), "task_id should be provided with a Progress instance"
            self.progress = progress
            self.task_id = task_id
            self.is_standalone = False

    def start(self):
        """Starts the progress bar with the initial title."""
        if self.is_standalone:
            self.progress.start()
        self.progress.update(
            self.task_id,
            description=f"{self.title} - Starting",
            completed=False,
        )

    def update(
        self,
        stage: str,
        advance: Union[int, None] = None,
        total: Union[int, None] = None,
    ):
        """
        Updates the progress bar by the specified number of units.

        Args:
            stage (str): Description of the current stage
                (download, deobfuscate, convert, etc.)
            advance (int): Usually the number of bytes in a chunk.
            total (int): Usually the total file size in bytes.
        """

        self.progress.update(
            self.task_id,
            description=f"{self.title} - {stage}",
            advance=advance,
            total=total,
        )

    def stop(self, message: str = "Completed"):
        """Stops the progress bar and prints it to the console."""
        self.progress.update(
            self.task_id,
            description=f"{self.title} - {message}",
            completed=True,
        )
        if self.is_standalone:
            self.progress.stop()
        else:
            self.progress.refresh()
