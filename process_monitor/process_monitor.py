"""
Process Monitor - Main entry point

This application provides a graphical interface for monitoring system and process resources.
Each major component is separated into its own module for better organization:
- data_collector.py: Background data collection for system and process metrics
- chart_manager.py: Chart rendering and updates
- process_monitor_gui.py: Main GUI application
"""

import tkinter as tk
from process_monitor_gui import ProcessMonitor


def main():
    """Main entry point for the Process Monitor application"""
    root = tk.Tk()
    app = ProcessMonitor(root)
    root.mainloop()


if __name__ == "__main__":
    main()