import tkinter as tk
from tkinter import ttk
import psutil
import time
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
from matplotlib.figure import Figure
import numpy as np
from collections import deque

class ProcessMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("Process Monitor")
        self.root.geometry("1000x600")
        self.root.minsize(800, 500)
        
        self.style = ttk.Style()
        self.style.theme_use("clam")         
        self.style.configure("Treeview", background="#f0f0f0", foreground="black")
        self.style.map('Treeview', background=[('selected', '#0078d7')])
        
        self.main_frame = ttk.Frame(self.root, padding=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        self.top_frame = ttk.Frame(self.main_frame)
        self.top_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.refresh_btn = ttk.Button(self.top_frame, text="Refresh", command=self.update_process_list)
        self.refresh_btn.pack(side=tk.LEFT, padx=5)
        
        self.end_btn = ttk.Button(self.top_frame, text="End Process", command=self.end_selected_process)
        self.end_btn.pack(side=tk.LEFT, padx=5)
        
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.filter_processes)
        self.search_label = ttk.Label(self.top_frame, text="Search:")
        self.search_label.pack(side=tk.LEFT, padx=(20, 5))
        self.search_entry = ttk.Entry(self.top_frame, textvariable=self.search_var, width=20)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        
        self.sort_label = ttk.Label(self.top_frame, text="Sort by:")
        self.sort_label.pack(side=tk.LEFT, padx=(20, 5))
        self.sort_var = tk.StringVar(value="CPU")
        sort_options = ["PID", "Name", "CPU", "Memory"]
        self.sort_combo = ttk.Combobox(self.top_frame, textvariable=self.sort_var, values=sort_options, width=10, state="readonly")
        self.sort_combo.pack(side=tk.LEFT, padx=5)
        self.sort_combo.bind("<<ComboboxSelected>>", lambda e: self.update_process_list())
        
        self.paned_window = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)
        
        self.process_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.process_frame, weight=1)
        
        self.tree_columns = ("PID", "Name", "CPU %", "Memory %", "Threads", "Status")
        self.process_tree = ttk.Treeview(self.process_frame, columns=self.tree_columns, show="headings")
        
        for col in self.tree_columns:
            self.process_tree.heading(col, text=col, command=lambda _col=col: self.sort_column(_col))
            if col == "Name":
                self.process_tree.column(col, width=200, minwidth=150)
            else:
                self.process_tree.column(col, width=80, minwidth=80, anchor=tk.CENTER)
        
        self.vsb = ttk.Scrollbar(self.process_frame, orient="vertical", command=self.process_tree.yview)
        self.hsb = ttk.Scrollbar(self.process_frame, orient="horizontal", command=self.process_tree.xview)
        self.process_tree.configure(yscrollcommand=self.vsb.set, xscrollcommand=self.hsb.set)
        
        self.process_tree.grid(column=0, row=0, sticky='nsew')
        self.vsb.grid(column=1, row=0, sticky='ns')
        self.hsb.grid(column=0, row=1, sticky='ew')
        
        self.process_frame.columnconfigure(0, weight=1)
        self.process_frame.rowconfigure(0, weight=1)
        
        self.charts_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.charts_frame, weight=1)
        
        self.charts_frame.columnconfigure(0, weight=1)
        self.charts_frame.rowconfigure(0, weight=1)
        self.charts_frame.rowconfigure(1, weight=1)
        
        self.system_stats_frame = ttk.LabelFrame(self.charts_frame, text="System Resources")
        self.system_stats_frame.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')
        
        self.fig_cpu = Figure(figsize=(5, 2), dpi=100)
        self.ax_cpu = self.fig_cpu.add_subplot(111)
        self.ax_cpu.set_title("CPU Usage")
        self.ax_cpu.set_ylim(0, 100)
        self.ax_cpu.set_xlabel("Time (s)")
        self.ax_cpu.set_ylabel("Usage (%)")
        self.ax_cpu.grid(True)
        
        self.fig_mem = Figure(figsize=(5, 2), dpi=100)
        self.ax_mem = self.fig_mem.add_subplot(111)
        self.ax_mem.set_title("Memory Usage")
        self.ax_mem.set_ylim(0, 100)
        self.ax_mem.set_xlabel("Time (s)")
        self.ax_mem.set_ylabel("Usage (%)")
        self.ax_mem.grid(True)
        
        self.system_stats_frame.columnconfigure(0, weight=1)
        self.system_stats_frame.rowconfigure(0, weight=1)
        self.system_stats_frame.rowconfigure(1, weight=1)
        
        self.canvas_cpu = FigureCanvasTkAgg(self.fig_cpu, master=self.system_stats_frame)
        self.canvas_cpu.get_tk_widget().grid(row=0, column=0, padx=5, pady=5, sticky='nsew')
        
        self.canvas_mem = FigureCanvasTkAgg(self.fig_mem, master=self.system_stats_frame)
        self.canvas_mem.get_tk_widget().grid(row=1, column=0, padx=5, pady=5, sticky='nsew')
        
        self.process_detail_frame = ttk.LabelFrame(self.charts_frame, text="Process Details")
        self.process_detail_frame.grid(row=1, column=0, padx=5, pady=5, sticky='nsew')
        
        self.detail_labels = {}
        details = ["PID", "Name", "CPU %", "Memory %", "Threads", "Created", "Path"]
        
        for i, detail in enumerate(details):
            label = ttk.Label(self.process_detail_frame, text=f"{detail}:")
            label.grid(row=i, column=0, sticky=tk.W, padx=5, pady=2)
            value = ttk.Label(self.process_detail_frame, text="-")
            value.grid(row=i, column=1, sticky=tk.W, padx=5, pady=2)
            self.detail_labels[detail] = value
        
        self.process_chart_frame = ttk.Frame(self.process_detail_frame)
        self.process_chart_frame.grid(row=len(details), column=0, columnspan=2, sticky='nsew', padx=5, pady=5)
        self.process_detail_frame.rowconfigure(len(details), weight=1)
        
        self.fig_process = Figure(figsize=(5, 2), dpi=100)
        self.ax_process = self.fig_process.add_subplot(111)
        self.ax_process.set_title("Process Resource Usage")
        self.ax_process.set_xlabel("Time (s)")
        self.ax_process.set_ylabel("Usage (%)")
        self.ax_process.grid(True)
        
        self.canvas_process = FigureCanvasTkAgg(self.fig_process, master=self.process_chart_frame)
        self.canvas_process.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.time_data = deque(maxlen=60)  
        self.cpu_data = deque(maxlen=60)
        self.mem_data = deque(maxlen=60)
        self.selected_process_cpu_data = deque(maxlen=60)
        self.selected_process_mem_data = deque(maxlen=60)
        
        # Initialize chart data
        for i in range(60):
            self.time_data.append(-60 + i)
            self.cpu_data.append(0)
            self.mem_data.append(0)
            self.selected_process_cpu_data.append(0)
            self.selected_process_mem_data.append(0)
        
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(self.main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=(5, 0))
        
        self.processes = {}
        self.selected_pid = None
        self.update_count = 0
        self.running = True
        
        self.process_tree.bind("<<TreeviewSelect>>", self.on_process_select)
        
        self.update_process_list()
        
        self.update_thread = threading.Thread(target=self.update_loop)
        self.update_thread.daemon = True
        self.update_thread.start()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def update_process_list(self):
        """Update the list of processes"""
        try:
            process_list = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'num_threads', 'status']):
                try:

                    process_info = proc.info
                    pid = process_info['pid']
                    name = process_info['name']
                    cpu = process_info['cpu_percent']
                    mem = process_info['memory_percent']
                    threads = process_info['num_threads']
                    status = process_info['status']
                    
                    process_list.append({
                        'pid': pid,
                        'name': name,
                        'cpu': cpu,
                        'memory': mem,
                        'threads': threads,
                        'status': status
                    })
                    
                    self.processes[pid] = proc
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            sort_key = self.sort_var.get().lower()
            if sort_key == "cpu":
                process_list.sort(key=lambda x: x['cpu'], reverse=True)
            elif sort_key == "memory":
                process_list.sort(key=lambda x: x['memory'], reverse=True)
            elif sort_key == "pid":
                process_list.sort(key=lambda x: x['pid'])
            else:  # Name
                process_list.sort(key=lambda x: x['name'].lower())
            
            for item in self.process_tree.get_children():
                self.process_tree.delete(item)
            
            search_text = self.search_var.get().lower()
            for proc in process_list:
                if search_text and search_text not in proc['name'].lower():
                    continue
                    
                self.process_tree.insert("", "end", values=(
                    proc['pid'],
                    proc['name'],
                    f"{proc['cpu']:.1f}",
                    f"{proc['memory']:.1f}",
                    proc['threads'],
                    proc['status']
                ))
            
            self.status_var.set(f"Processes: {len(process_list)} | System CPU: {psutil.cpu_percent()}% | Memory: {psutil.virtual_memory().percent}%")
            
        except Exception as e:
            self.status_var.set(f"Error updating process list: {str(e)}")
    
    def update_loop(self):
        """Update data in a background thread"""
        last_time = time.time()
        
        while self.running:
            current_time = time.time()
            elapsed = current_time - last_time
            
            if elapsed >= 1.0:
                last_time = current_time
                
                self.time_data.append(self.time_data[-1] + 1)                
                self.cpu_data.append(psutil.cpu_percent())
                self.mem_data.append(psutil.virtual_memory().percent)
                
                if self.selected_pid in self.processes:
                    try:
                        proc = self.processes[self.selected_pid]
                        if proc.is_running():
                            self.selected_process_cpu_data.append(proc.cpu_percent())
                            self.selected_process_mem_data.append(proc.memory_percent())
                        else:
                            self.selected_process_cpu_data.append(0)
                            self.selected_process_mem_data.append(0)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        self.selected_process_cpu_data.append(0)
                        self.selected_process_mem_data.append(0)
                else:
                    self.selected_process_cpu_data.append(0)
                    self.selected_process_mem_data.append(0)
                
                self.root.after(0, self.update_ui)
                
                self.update_count += 1
                if self.update_count >= 5:
                    self.update_count = 0
                    self.root.after(0, self.update_process_list)
            
            time.sleep(0.1)
    
    def update_ui(self):
        """Update UI elements with current data"""
        try:
            self.ax_cpu.clear()
            self.ax_cpu.set_title("CPU Usage")
            self.ax_cpu.set_ylim(0, 100)
            self.ax_cpu.set_xlabel("Time (s)")
            self.ax_cpu.set_ylabel("Usage (%)")
            self.ax_cpu.grid(True)
            self.ax_cpu.plot(list(self.time_data), list(self.cpu_data), 'b-')
            self.canvas_cpu.draw()
            
            self.ax_mem.clear()
            self.ax_mem.set_title("Memory Usage")
            self.ax_mem.set_ylim(0, 100)
            self.ax_mem.set_xlabel("Time (s)")
            self.ax_mem.set_ylabel("Usage (%)")
            self.ax_mem.grid(True)
            self.ax_mem.plot(list(self.time_data), list(self.mem_data), 'r-')
            self.canvas_mem.draw()
            
            if self.selected_pid is not None:
                self.ax_process.clear()
                self.ax_process.set_title(f"Process {self.selected_pid} Resource Usage")
                self.ax_process.set_ylim(0, max(max(self.selected_process_cpu_data), max(self.selected_process_mem_data)) + 10)
                self.ax_process.set_xlabel("Time (s)")
                self.ax_process.set_ylabel("Usage (%)")
                self.ax_process.grid(True)
                self.ax_process.plot(list(self.time_data), list(self.selected_process_cpu_data), 'b-', label='CPU')
                self.ax_process.plot(list(self.time_data), list(self.selected_process_mem_data), 'r-', label='Memory')
                self.ax_process.legend()
                self.canvas_process.draw()
            
            mem = psutil.virtual_memory()
            self.status_var.set(
                f"CPU: {psutil.cpu_percent()}% | Memory: {mem.percent}% ({self.format_bytes(mem.used)}/{self.format_bytes(mem.total)}) | "
                f"Disk: {psutil.disk_usage('/').percent}%"
            )
        except Exception as e:
            self.status_var.set(f"Error updating UI: {str(e)}")
    
    def on_process_select(self, event):
        """Handle selection of a process in the tree view"""
        selected_items = self.process_tree.selection()
        if not selected_items:
            return
        
        item = selected_items[0]
        values = self.process_tree.item(item, "values")
        pid = int(values[0])
        self.selected_pid = pid
        
        self.selected_process_cpu_data = deque(maxlen=60)
        self.selected_process_mem_data = deque(maxlen=60)
        
        for i in range(60):
            self.selected_process_cpu_data.append(0)
            self.selected_process_mem_data.append(0)
        
        try:
            if pid in self.processes:
                proc = self.processes[pid]
                if proc.is_running():
                    self.detail_labels["PID"].config(text=str(pid))
                    self.detail_labels["Name"].config(text=proc.name())
                    self.detail_labels["CPU %"].config(text=f"{proc.cpu_percent():.1f}%")
                    self.detail_labels["Memory %"].config(text=f"{proc.memory_percent():.1f}%")
                    self.detail_labels["Threads"].config(text=str(proc.num_threads()))
                    
                    try:
                        create_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(proc.create_time()))
                        self.detail_labels["Created"].config(text=create_time)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        self.detail_labels["Created"].config(text="N/A")
                    
                    try:
                        self.detail_labels["Path"].config(text=proc.exe())
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        self.detail_labels["Path"].config(text="N/A")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            for key in self.detail_labels:
                self.detail_labels[key].config(text="N/A")
    
    def end_selected_process(self):
        """End the selected process"""
        if self.selected_pid is None:
            return
        
        try:
            proc = psutil.Process(self.selected_pid)
            proc.terminate()
            self.status_var.set(f"Process {self.selected_pid} terminated")
            
            # Update the process list
            self.update_process_list()
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            self.status_var.set(f"Error terminating process: {str(e)}")
    
    def filter_processes(self, *args):
        """Filter processes based on search text"""
        self.update_process_list()
    
    def sort_column(self, col):
        """Sort treeview by column"""
        if col == "PID":
            self.sort_var.set("PID")
        elif col == "Name":
            self.sort_var.set("Name")
        elif col == "CPU %":
            self.sort_var.set("CPU")
        elif col == "Memory %":
            self.sort_var.set("Memory")
        
        self.update_process_list()
    
    def format_bytes(self, bytes_num):
        """Format bytes to human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_num < 1024.0:
                return f"{bytes_num:.1f} {unit}"
            bytes_num /= 1024.0
        return f"{bytes_num:.1f} PB"
    
    def on_close(self):
        """Clean up resources when closing the window"""
        self.running = False
        if self.update_thread.is_alive():
            self.update_thread.join(1.0)  
        self.root.destroy()

def main():
    root = tk.Tk()
    app = ProcessMonitor(root)
    root.mainloop()

if __name__ == "__main__":
    main()