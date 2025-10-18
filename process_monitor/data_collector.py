import psutil
import time
import threading
from queue import Queue


class DataCollector:
    """Handles background data collection for system and process metrics"""

    def __init__(self):
        self.running = False
        self.thread = None
        self.data_queue = Queue()
        self.processes = {}
        self.selected_pid = None

        # System metrics
        self.system_cpu = 0.0
        self.system_mem = 0.0

        # Process metrics for selected process
        self.process_cpu = 0.0
        self.process_mem = 0.0

        # Initialize CPU percent tracking (first call returns 0.0)
        psutil.cpu_percent(interval=None)

    def start(self):
        """Start the data collection thread"""
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._collect_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop the data collection thread"""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)

    def set_selected_pid(self, pid):
        """Set the process ID to track"""
        self.selected_pid = pid

    def _collect_loop(self):
        """Main collection loop running in background thread"""
        last_update = time.time()

        while self.running:
            current_time = time.time()
            elapsed = current_time - last_update

            if elapsed >= 1.0:
                last_update = current_time

                # Collect system metrics (non-blocking calls)
                self.system_cpu = psutil.cpu_percent(interval=None)
                self.system_mem = psutil.virtual_memory().percent

                # Collect selected process metrics
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

                # Queue data for UI update
                self.data_queue.put({
                    'system_cpu': self.system_cpu,
                    'system_mem': self.system_mem,
                    'process_cpu': self.process_cpu,
                    'process_mem': self.process_mem,
                    'timestamp': current_time
                })

            time.sleep(0.1)

    def collect_process_list(self):
        """Collect process list (called from background thread)"""
        process_list = []
        new_processes = {}

        # Pre-call cpu_percent to prepare for next interval
        for proc in psutil.process_iter(['pid']):
            try:
                proc.cpu_percent(interval=None)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # Small delay to let CPU measurements accumulate
        time.sleep(0.1)

        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'num_threads', 'status']):
            try:
                process_info = proc.info
                pid = process_info['pid']

                process_list.append({
                    'pid': pid,
                    'name': process_info['name'],
                    'cpu': process_info['cpu_percent'],
                    'memory': process_info['memory_percent'],
                    'threads': process_info['num_threads'],
                    'status': process_info['status']
                })

                new_processes[pid] = proc
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        self.processes = new_processes
        return process_list
