import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import speedtest
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import datetime
import os
import json

class SpeedTestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Internet Speed Test")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        self.root.configure(bg="#f0f0f0")
        
        # Set app icon
        # self.root.iconbitmap("speedtest_icon.ico")  # Uncomment and add icon if available
        
        # History data
        self.history = []
        self.history_file = "speedtest_history.json"
        self.load_history()
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create header
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(header_frame, text="Internet Speed Test", 
                  font=("Segoe UI", 24, "bold")).pack(side=tk.LEFT)
        
        # Create tabs
        self.tab_control = ttk.Notebook(self.main_frame)
        
        # Tab 1: Speed Test
        self.test_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.test_tab, text="Speed Test")
        
        # Tab 2: History
        self.history_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.history_tab, text="History")
        
        # Tab 3: Settings
        self.settings_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.settings_tab, text="Settings")
        
        self.tab_control.pack(fill=tk.BOTH, expand=True)
        
        # Set up speed test tab
        self.setup_test_tab()
        
        # Set up history tab
        self.setup_history_tab()
        
        # Set up settings tab
        self.setup_settings_tab()
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Test in progress flag
        self.test_running = False
        
        # Apply theme
        self.apply_theme()
    
    def setup_test_tab(self):
        # Speed displays
        display_frame = ttk.Frame(self.test_tab)
        display_frame.pack(fill=tk.X, pady=20)
        
        # Download speed
        download_frame = ttk.LabelFrame(display_frame, text="Download Speed", padding=10)
        download_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=5)
        
        self.download_var = tk.StringVar(value="0.00")
        ttk.Label(download_frame, textvariable=self.download_var, 
                  font=("Segoe UI", 32)).pack(pady=10)
        ttk.Label(download_frame, text="Mbps", 
                  font=("Segoe UI", 12)).pack()
        
        # Upload speed
        upload_frame = ttk.LabelFrame(display_frame, text="Upload Speed", padding=10)
        upload_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=5)
        
        self.upload_var = tk.StringVar(value="0.00")
        ttk.Label(upload_frame, textvariable=self.upload_var, 
                  font=("Segoe UI", 32)).pack(pady=10)
        ttk.Label(upload_frame, text="Mbps", 
                  font=("Segoe UI", 12)).pack()
        
        # Ping
        ping_frame = ttk.LabelFrame(display_frame, text="Ping", padding=10)
        ping_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=5)
        
        self.ping_var = tk.StringVar(value="0")
        ttk.Label(ping_frame, textvariable=self.ping_var, 
                  font=("Segoe UI", 32)).pack(pady=10)
        ttk.Label(ping_frame, text="ms", 
                  font=("Segoe UI", 12)).pack()
        
        # Progress bar
        progress_frame = ttk.Frame(self.test_tab)
        progress_frame.pack(fill=tk.X, pady=10)
        
        self.progress = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, 
                                         length=100, mode='determinate')
        self.progress.pack(fill=tk.X, padx=20)
        
        # Status label
        self.test_status_var = tk.StringVar(value="Click 'Start Test' to begin")
        test_status = ttk.Label(progress_frame, textvariable=self.test_status_var)
        test_status.pack(pady=5)
        
        # Start button
        button_frame = ttk.Frame(self.test_tab)
        button_frame.pack(pady=20)
        
        self.start_button = ttk.Button(button_frame, text="Start Test", 
                                       command=self.start_test, width=20)
        self.start_button.pack(pady=10)
        
        # Results frame for graph
        self.results_frame = ttk.Frame(self.test_tab)
        self.results_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Server info
        info_frame = ttk.Frame(self.test_tab)
        info_frame.pack(fill=tk.X, pady=10, padx=20)
        
        self.server_info_var = tk.StringVar(value="Server: Not tested yet")
        server_label = ttk.Label(info_frame, textvariable=self.server_info_var, 
                                font=("Segoe UI", 9))
        server_label.pack(side=tk.LEFT)
        
        self.time_info_var = tk.StringVar(value="Time: Not tested yet")
        time_label = ttk.Label(info_frame, textvariable=self.time_info_var, 
                              font=("Segoe UI", 9))
        time_label.pack(side=tk.RIGHT)
    
    def setup_history_tab(self):
        # Controls
        controls_frame = ttk.Frame(self.history_tab)
        controls_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(controls_frame, text="Clear History", 
                  command=self.clear_history).pack(side=tk.RIGHT, padx=10)
        
        ttk.Button(controls_frame, text="Export CSV", 
                  command=self.export_history).pack(side=tk.RIGHT, padx=10)
        
        # History table
        table_frame = ttk.Frame(self.history_tab)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ('date', 'time', 'download', 'upload', 'ping', 'server')
        self.history_table = ttk.Treeview(table_frame, columns=columns, show='headings')
        
        # Define headings
        self.history_table.heading('date', text='Date')
        self.history_table.heading('time', text='Time')
        self.history_table.heading('download', text='Download (Mbps)')
        self.history_table.heading('upload', text='Upload (Mbps)')
        self.history_table.heading('ping', text='Ping (ms)')
        self.history_table.heading('server', text='Server')
        
        # Define columns
        self.history_table.column('date', width=100)
        self.history_table.column('time', width=100)
        self.history_table.column('download', width=120)
        self.history_table.column('upload', width=120)
        self.history_table.column('ping', width=100)
        self.history_table.column('server', width=200)
        
        # Add a scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.history_table.yview)
        self.history_table.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Populate table with history data
        self.update_history_table()
        
        # Graph frame
        graph_frame = ttk.LabelFrame(self.history_tab, text="History Graph")
        graph_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create the plot
        self.update_history_graph(graph_frame)
    
    def setup_settings_tab(self):
        settings_frame = ttk.Frame(self.settings_tab, padding=20)
        settings_frame.pack(fill=tk.BOTH, expand=True)
        
        # Theme selection
        theme_frame = ttk.LabelFrame(settings_frame, text="Theme", padding=10)
        theme_frame.pack(fill=tk.X, pady=10)
        
        self.theme_var = tk.StringVar(value="light")
        ttk.Radiobutton(theme_frame, text="Light", variable=self.theme_var, 
                       value="light", command=self.apply_theme).pack(anchor=tk.W, pady=5)
        ttk.Radiobutton(theme_frame, text="Dark", variable=self.theme_var, 
                       value="dark", command=self.apply_theme).pack(anchor=tk.W, pady=5)
        
        # Server selection
        server_frame = ttk.LabelFrame(settings_frame, text="Test Server", padding=10)
        server_frame.pack(fill=tk.X, pady=10)
        
        self.server_auto_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(server_frame, text="Auto-select best server", 
                       variable=self.server_auto_var).pack(anchor=tk.W, pady=5)
        
        # About section
        about_frame = ttk.LabelFrame(settings_frame, text="About", padding=10)
        about_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(about_frame, text="Speed Test App v1.0", 
                 font=("Segoe UI", 12, "bold")).pack(anchor=tk.W, pady=5)
        ttk.Label(about_frame, text="A simple internet speed test application").pack(anchor=tk.W)
        ttk.Label(about_frame, text="© 2025").pack(anchor=tk.W, pady=5)
    
    def start_test(self):
        if self.test_running:
            return
        
        self.test_running = True
        self.start_button.configure(state=tk.DISABLED)
        self.status_var.set("Testing in progress...")
        self.test_status_var.set("Initializing speed test...")
        self.progress['value'] = 0
        
        # Reset values
        self.download_var.set("0.00")
        self.upload_var.set("0.00")
        self.ping_var.set("0")
        
        # Create and start test thread
        test_thread = threading.Thread(target=self.run_speed_test)
        test_thread.daemon = True
        test_thread.start()
    
    def run_speed_test(self):
        try:
            self.update_status("Finding best server...", 10)
            st = speedtest.Speedtest()
            
            if self.server_auto_var.get():
                st.get_best_server()
            else:
                st.get_closest_servers()
                st.get_best_server()
            
            server_name = f"{st.results.server['sponsor']} ({st.results.server['name']})"
            self.server_info_var.set(f"Server: {server_name}")
            
            # Test ping
            self.update_status("Testing ping...", 20)
            ping = st.results.ping
            self.ping_var.set(f"{ping:.1f}")
            
            # Test download
            self.update_status("Testing download speed...", 40)
            download = st.download() / 1_000_000  # Convert to Mbps
            self.download_var.set(f"{download:.2f}")
            
            # Test upload
            self.update_status("Testing upload speed...", 80)
            upload = st.upload() / 1_000_000  # Convert to Mbps
            self.upload_var.set(f"{upload:.2f}")
            
            # Complete
            self.update_status("Test completed!", 100)
            
            # Record timestamp
            now = datetime.datetime.now()
            timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
            self.time_info_var.set(f"Time: {timestamp}")
            
            # Save to history
            history_entry = {
                "timestamp": timestamp,
                "date": now.strftime("%Y-%m-%d"),
                "time": now.strftime("%H:%M:%S"),
                "download": round(download, 2),
                "upload": round(upload, 2),
                "ping": round(ping, 1),
                "server": server_name
            }
            
            self.history.append(history_entry)
            self.save_history()
            self.update_history_table()
            
            # Update graph if on history tab
            if self.tab_control.index(self.tab_control.select()) == 1:
                self.update_history_graph(None)
            
            # Plot this test result
            self.plot_test_result(download, upload, ping)
            
        except Exception as e:
            self.test_status_var.set(f"Error: {str(e)}")
            messagebox.showerror("Error", f"An error occurred during the speed test: {str(e)}")
        
        finally:
            self.test_running = False
            self.status_var.set("Ready")
            self.start_button.configure(state=tk.NORMAL)
    
    def update_status(self, message, progress_value):
        self.test_status_var.set(message)
        self.progress['value'] = progress_value
        self.root.update_idletasks()
    
    def plot_test_result(self, download, upload, ping):
        # Clear previous results
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        
        # Create figure and axis
        fig, ax = plt.subplots(figsize=(7, 3))
        
        # Data
        metrics = ['Download', 'Upload', 'Ping (ms/10)']
        values = [download, upload, ping/10]  # Scale ping to fit better
        colors = ['#3498db', '#2ecc71', '#e74c3c']
        
        # Plot
        bars = ax.bar(metrics, values, color=colors, width=0.6)
        
        # Add data labels
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height:.1f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom')
        
        ax.set_ylabel('Mbps (Ping in ms/10)')
        ax.set_title('Speed Test Results')
        
        # Create canvas
        canvas = FigureCanvasTkAgg(fig, master=self.results_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def update_history_table(self):
        # Clear existing items
        for item in self.history_table.get_children():
            self.history_table.delete(item)
        
        # Add history items
        for entry in reversed(self.history):
            self.history_table.insert('', tk.END, values=(
                entry['date'],
                entry['time'],
                entry['download'],
                entry['upload'],
                entry['ping'],
                entry['server']
            ))
    
    def update_history_graph(self, frame):
        # If no frame provided (updating existing), get the existing frame
        if frame is None:
            frames = [f for f in self.history_tab.winfo_children() if isinstance(f, ttk.LabelFrame)]
            if frames:
                frame = frames[0]
                for widget in frame.winfo_children():
                    widget.destroy()
            else:
                return
        else:
            for widget in frame.winfo_children():
                widget.destroy()
        
        # Create figure for history
        fig, ax = plt.subplots(figsize=(7, 3))
        
        # Prepare data - last 10 entries for readability
        history_data = self.history[-10:] if len(self.history) > 10 else self.history
        
        if not history_data:
            ttk.Label(frame, text="No history data available").pack(pady=30)
            return
        
        dates = [entry['timestamp'] for entry in history_data]
        downloads = [entry['download'] for entry in history_data]
        uploads = [entry['upload'] for entry in history_data]
        
        # Format x-axis labels to be more readable
        if len(dates) > 5:
            date_labels = [d.split()[1] if i % 2 == 0 else '' for i, d in enumerate(dates)]
        else:
            date_labels = [d.split()[1] for d in dates]
        
        # Plot
        ax.plot(range(len(dates)), downloads, 'o-', color='#3498db', label='Download')
        ax.plot(range(len(dates)), uploads, 'o-', color='#2ecc71', label='Upload')
        
        ax.set_xticks(range(len(dates)))
        ax.set_xticklabels(date_labels, rotation=45)
        
        ax.set_ylabel('Mbps')
        ax.set_title('Speed History')
        ax.legend()
        
        fig.tight_layout()
        
        # Create canvas
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def clear_history(self):
        if messagebox.askyesno("Clear History", "Are you sure you want to clear all history?"):
            self.history = []
            self.save_history()
            self.update_history_table()
            self.update_history_graph(None)
    
    def export_history(self):
        if not self.history:
            messagebox.showinfo("Export", "No history data to export.")
            return
        
        try:
            filename = f"speedtest_history_{datetime.datetime.now().strftime('%Y%m%d')}.csv"
            with open(filename, 'w') as f:
                # Header
                f.write("Date,Time,Download (Mbps),Upload (Mbps),Ping (ms),Server\n")
                
                # Data
                for entry in self.history:
                    f.write(f"{entry['date']},{entry['time']},{entry['download']},{entry['upload']},{entry['ping']},\"{entry['server']}\"\n")
            
            messagebox.showinfo("Export", f"Data exported to {filename} successfully!")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export data: {str(e)}")
    
    def load_history(self):
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    self.history = json.load(f)
        except Exception as e:
            print(f"Error loading history: {e}")
            self.history = []
    
    def save_history(self):
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f)
        except Exception as e:
            print(f"Error saving history: {e}")
    
    def apply_theme(self):
        theme = self.theme_var.get()
        
        if theme == "dark":
            self.root.configure(bg="#2c3e50")
            style = ttk.Style()
            
            # Configure dark theme elements - just basic example
            style.configure("TFrame", background="#2c3e50")
            style.configure("TLabel", background="#2c3e50", foreground="#ecf0f1")
            style.configure("TLabelframe", background="#2c3e50", foreground="#ecf0f1")
            style.configure("TLabelframe.Label", background="#2c3e50", foreground="#ecf0f1")
            
            # This is just a basic example - a complete dark theme would need more styling
        else:
            # Reset to default light theme
            self.root.configure(bg="#f0f0f0")
            style = ttk.Style()
            style.theme_use('default')

def main():
    root = tk.Tk()
    app = SpeedTestApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()