from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Tuple

import psutil
import time
from PyQt6 import QtCore


class _MetricsWorker(QtCore.QObject):
    """Worker object that collects metrics inside a dedicated QThread."""

    data_ready = QtCore.pyqtSignal(dict)

    def __init__(self) -> None:
        super().__init__()
        self._timer: Optional[QtCore.QTimer] = None
        self.selected_pid: Optional[int] = None
        self.processes: Dict[int, psutil.Process] = {}
        self.system_cpu = 0.0
        self.system_mem = 0.0
        self.process_cpu = 0.0
        self.process_mem = 0.0

        # Initialize CPU percent tracking (first call returns 0.0)
        psutil.cpu_percent(interval=None)

    @QtCore.pyqtSlot()
    def start(self) -> None:
        if self._timer is not None:
            return

        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._collect_metrics)
        self._timer.start()

    @QtCore.pyqtSlot()
    def stop(self) -> None:
        if self._timer is None:
            return

        self._timer.stop()
        self._timer.deleteLater()
        self._timer = None

    @QtCore.pyqtSlot(object)
    def set_selected_pid(self, pid: Optional[int]) -> None:
        self.selected_pid = pid if pid else None

    @QtCore.pyqtSlot(object)
    def update_process_cache(self, processes: Optional[Dict[int, psutil.Process]]) -> None:
        self.processes = processes or {}

    def _collect_metrics(self) -> None:
        self.system_cpu = psutil.cpu_percent(interval=None)
        self.system_mem = psutil.virtual_memory().percent

        if self.selected_pid and self.selected_pid in self.processes:
            try:
                proc = self.processes[self.selected_pid]
                if proc.is_running():
                    self.process_cpu = proc.cpu_percent(interval=None)
                    self.process_mem = proc.memory_percent()
                else:
                    self.process_cpu = 0.0
                    self.process_mem = 0.0
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                self.process_cpu = 0.0
                self.process_mem = 0.0
        else:
            self.process_cpu = 0.0
            self.process_mem = 0.0

        self.data_ready.emit(
            {
                "system_cpu": self.system_cpu,
                "system_mem": self.system_mem,
                "process_cpu": self.process_cpu,
                "process_mem": self.process_mem,
                "timestamp": time.time(),
            }
        )


class DataCollector(QtCore.QObject):
    """Coordinates background data collection using Qt threads/signals."""

    data_ready = QtCore.pyqtSignal(dict)
    _selected_pid_changed = QtCore.pyqtSignal(object)
    _process_cache_changed = QtCore.pyqtSignal(object)
    _stop_requested = QtCore.pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self._thread = QtCore.QThread(self)
        self._worker = _MetricsWorker()
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.start)
        self._thread.finished.connect(self._worker.deleteLater)
        self._worker.data_ready.connect(self.data_ready)

        self._selected_pid_changed.connect(self._worker.set_selected_pid)
        self._process_cache_changed.connect(self._worker.update_process_cache)
        self._stop_requested.connect(self._worker.stop)

        self.process_cache: Dict[int, psutil.Process] = {}
        self.selected_pid: Optional[int] = None

    def start(self) -> None:
        if self._thread.isRunning():
            return
        self._thread.start()

    def stop(self) -> None:
        if not self._thread.isRunning():
            return

        self._stop_requested.emit()
        self._thread.quit()
        self._thread.wait(1000)

    def set_selected_pid(self, pid: Optional[int]) -> None:
        self.selected_pid = pid if pid else None
        self._selected_pid_changed.emit(self.selected_pid)

    def update_process_cache(self, processes: Dict[int, psutil.Process]) -> None:
        self.process_cache = processes
        self._process_cache_changed.emit(self.process_cache)

    def get_process(self, pid: int) -> Optional[psutil.Process]:
        return self.process_cache.get(pid)

    @staticmethod
    def collect_process_list() -> Tuple[List[dict], Dict[int, psutil.Process]]:
        """Collect process information returning both list and process objects."""
        process_list: List[dict] = []
        process_objects: Dict[int, psutil.Process] = {}

        # Pre-call cpu_percent to prepare for the next interval
        for proc in _safe_process_iter(["pid"]):
            try:
                proc.cpu_percent(interval=None)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Small delay to let CPU measurements accumulate
        time.sleep(0.1)

        for proc in _safe_process_iter(
            ["pid", "name", "cpu_percent", "memory_percent", "num_threads", "status"]
        ):
            try:
                info = proc.info
                pid = info["pid"]
                process_list.append(
                    {
                        "pid": pid,
                        "name": info["name"],
                        "cpu": info["cpu_percent"],
                        "memory": info["memory_percent"],
                        "threads": info["num_threads"],
                        "status": info["status"],
                    }
                )
                process_objects[pid] = proc
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        return process_list, process_objects


def _safe_process_iter(attrs: Iterable[str]) -> Iterable[psutil.Process]:
    """Yield processes while gracefully ignoring access-related exceptions."""

    for proc in psutil.process_iter(attrs):
        try:
            yield proc
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
