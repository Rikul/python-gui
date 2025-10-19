# Process Monitor

A real-time system process monitor with CPU and memory usage graphs built with Python and Qt 6.

## Requirements
- Python 3.8+
- PyQt6

To install required packages:

```bash
pip install -r requirements.txt
```

## Running the application

```bash
python process_monitor.py
```

## Usage
1. The process list automatically updates every 5 seconds
2. Click on any process to view detailed information in the right panel
3. Use the search box to filter processes by name
4. Sort processes by clicking the "Sort by" dropdown or column headers
5. Click "End Process" to terminate the selected process
6. Monitor system-wide CPU and memory usage in real-time graphs

## Note
Some operations (like viewing process paths or terminating processes) may require elevated privileges on certain systems.
