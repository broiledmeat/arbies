from __future__ import annotations
import os
from enum import Enum
import random
import re
import threading
import time
import natsort
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from typing import Optional, Callable, Tuple, List, Set, Dict

__all__ = ('OnChangedCallback', 'add_on_changed', 'get_dir_iterator')

OnChangedCallback = Callable[[str], None]
_DirectoryIteratorKey = Tuple[str, 'DirectoryIterationMethod', bool, Optional[str]]

_on_changed_callbacks: Dict[str, 'OnModifyObserver'] = {}
_directory_iterators: Dict[_DirectoryIteratorKey, 'DirectoryIterator'] = {}


class OnModifyObserver:
    def __init__(self, path: str, recursive: bool = False):
        self.callbacks: Set[OnChangedCallback] = set()

        self._filename: Optional[str] = None
        if os.path.isfile(path):
            self._filename = path
            path = os.path.dirname(path)
            recursive = False

        self._throttled_callback = self._ThrottledCallback(self.trigger)
        self._handler = self._EventHandler(self)
        self._observer: Observer = Observer()
        self._observer.schedule(self._handler, path, recursive=recursive)
        self._observer.start()

    def trigger(self):
        for callback in self.callbacks:
            callback()

    def is_throttling(self) -> bool:
        return self._throttled_callback.is_throttling()

    def close(self):
        if self._observer.is_alive():
            self._observer.stop()
            self._observer.join()

    class _ThrottledCallback:
        def __init__(self, callback: Callable[[], None], delay: float = 2.0):
            self.callback = callback
            self.delay = delay
            self._timer: Optional[threading.Timer] = None

        def trigger(self):
            if self._timer is not None and self._timer.is_alive():
                self._timer.cancel()
            self._timer = threading.Timer(self.delay, self.callback)
            self._timer.start()

        def is_throttling(self) -> bool:
            return self._timer is not None and self._timer.is_alive()

    class _EventHandler(FileSystemEventHandler):
        def __init__(self, parent: OnModifyObserver):
            self.parent = parent

        def on_modified(self, event):
            if self.parent._filename is None or event.src_path == self.parent._filename:
                self.parent._throttled_callback.trigger()


class DirectoryIterationMethod(Enum):
    FileSystem = 0
    Sorted = 1
    Random = 2


class DirectoryIterator:
    def __init__(self,
                 path: str,
                 method: DirectoryIterationMethod = DirectoryIterationMethod.Sorted,
                 recursive: bool = False,
                 filter: Optional[str] = None):
        self.path: str = path
        self.method: DirectoryIterationMethod = method
        self.recursive: bool = recursive
        self.filter: Optional[re.Match] = re.compile(filter, re.IGNORECASE) if filter is not None else None

        self._index = 0
        self._paths: List[str] = []

        self._refresh_paths()

        self._observer = OnModifyObserver(self.path, self.recursive)
        self._observer.callbacks.add(self._refresh_paths)

    def __iter__(self) -> DirectoryIterator:
        return self

    def __next__(self) -> str:
        while self._observer.is_throttling():
            time.sleep(0.1)

        if len(self._paths) == 0:
            return ''

        value: str = self._paths[self._index]

        self._index += 1

        if self._index >= len(self._paths):
            self._index = 0

        return value

    def close(self):
        self._observer.close()

    def _refresh_paths(self):
        self._index = 0

        if not os.path.isdir(self.path):
            self._paths = []
            return

        if self.recursive:
            self._paths = os.listdir(self.path)
        else:
            self._paths.clear()
            for root, dirs, files in os.walk(self.path):
                for name in dirs + files:
                    self._paths.append(os.path.join(root, name))

        if self.filter is not None:
            self._paths = list(filter(lambda path: self.filter.match(path) is not None, self._paths))

        if self.method == DirectoryIterationMethod.Sorted:
            self._paths = natsort.natsorted(self._paths)
        elif self.method == DirectoryIterationMethod.Random:
            random.shuffle(self._paths)

    class _EventHandler(FileSystemEventHandler):
        def __init__(self, parent: DirectoryIterator):
            self.parent = parent

        def on_modified(self, event):
            self.parent._throttled_callback.trigger()


def add_on_changed(path: str, callback: OnChangedCallback):
    if path not in _on_changed_callbacks:
        _on_changed_callbacks[path] = OnModifyObserver(path)

    _on_changed_callbacks[path].callbacks.add(callback)


def get_dir_iterator(path: str,
                     method: DirectoryIterationMethod = DirectoryIterationMethod.FileSystem,
                     recursive: bool = False,
                     filter: Optional[re.Match] = None
                     ) -> DirectoryIterator:
    key: _DirectoryIteratorKey = path, method, recursive, filter

    if key not in _directory_iterators:
        _directory_iterators[key] = DirectoryIterator(path, method=method, recursive=recursive, filter=filter)

    return _directory_iterators[key]
