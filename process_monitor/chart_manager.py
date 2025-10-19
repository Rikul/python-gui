from collections import deque


class ChartManager:
    """Manages chart rendering and updates"""

    def __init__(self, canvas_cpu, canvas_mem, canvas_process, ax_cpu, ax_mem, ax_process):
        self.canvas_cpu = canvas_cpu
        self.canvas_mem = canvas_mem
        self.canvas_process = canvas_process
        self.ax_cpu = ax_cpu
        self.ax_mem = ax_mem
        self.ax_process = ax_process

        self.time_data = deque(maxlen=60)
        self.cpu_data = deque(maxlen=60)
        self.mem_data = deque(maxlen=60)
        self.process_cpu_data = deque(maxlen=60)
        self.process_mem_data = deque(maxlen=60)

        # Initialize with zeros
        for i in range(60):
            self.time_data.append(-60 + i)
            self.cpu_data.append(0)
            self.mem_data.append(0)
            self.process_cpu_data.append(0)
            self.process_mem_data.append(0)

    def add_data_point(self, system_cpu, system_mem, process_cpu, process_mem):
        """Add new data point to chart data"""
        self.time_data.append(self.time_data[-1] + 1)
        self.cpu_data.append(system_cpu)
        self.mem_data.append(system_mem)
        self.process_cpu_data.append(process_cpu)
        self.process_mem_data.append(process_mem)

    def reset_process_data(self):
        """Reset process-specific chart data"""
        self.process_cpu_data.clear()
        self.process_mem_data.clear()
        for i in range(60):
            self.process_cpu_data.append(0)
            self.process_mem_data.append(0)

    def update_charts(self, selected_pid=None):
        """Update all charts with current data"""
        # Update CPU chart
        self.ax_cpu.clear()
        self.ax_cpu.set_title("CPU Usage")
        self.ax_cpu.set_ylim(0, 100)
        self.ax_cpu.set_xlabel("Time (s)")
        self.ax_cpu.set_ylabel("Usage (%)")
        self.ax_cpu.grid(True)
        self.ax_cpu.plot(list(self.time_data), list(self.cpu_data), 'b-')
        self.canvas_cpu.draw_idle()

        # Update Memory chart
        self.ax_mem.clear()
        self.ax_mem.set_title("Memory Usage")
        self.ax_mem.set_ylim(0, 100)
        self.ax_mem.set_xlabel("Time (s)")
        self.ax_mem.set_ylabel("Usage (%)")
        self.ax_mem.grid(True)
        self.ax_mem.plot(list(self.time_data), list(self.mem_data), 'r-')
        self.canvas_mem.draw_idle()

        # Update process chart
        self.ax_process.clear()
        if selected_pid is not None:
            self.ax_process.set_title(f"Process {selected_pid} Resource Usage")
            max_val = max(
                max(self.process_cpu_data, default=0),
                max(self.process_mem_data, default=0)
            )
            self.ax_process.set_ylim(0, max(max_val + 10, 10))
            self.ax_process.set_xlabel("Time (s)")
            self.ax_process.set_ylabel("Usage (%)")
            self.ax_process.grid(True)
            self.ax_process.plot(list(self.time_data), list(self.process_cpu_data), 'b-', label='CPU')
            self.ax_process.plot(list(self.time_data), list(self.process_mem_data), 'r-', label='Memory')
            self.ax_process.legend()
        else:
            self.ax_process.set_title("Select a process to view resource usage")
            self.ax_process.set_ylim(0, 10)
            self.ax_process.set_xlabel("Time (s)")
            self.ax_process.set_ylabel("Usage (%)")
            self.ax_process.grid(True)
        self.canvas_process.draw_idle()
