# Import Qt classes for threading and signals
from PySide6.QtCore import QThread, Signal

# Import hardware monitoring functions
from .monitor import (get_cpu_info, get_gpu_info, get_ram_info,
                      get_all_disks_info, get_top_processes, get_fan_info,
                      get_cpu_detailed_info, get_detailed_processes)


class MonitorThread(QThread):
    """Background thread for collecting hardware monitoring data without blocking the UI."""

    # Define signals to emit data to the main UI thread
    cpu_data = Signal(dict)
    gpu_data = Signal(dict)
    ram_data = Signal(dict)
    disks_data = Signal(list)
    fans_data = Signal(dict)
    processes_data = Signal(list)

    # New signals for the detailed CPU view
    cpu_detail_data = Signal(dict)
    processes_detail_data = Signal(list)

    def __init__(self):
        super().__init__()
        # Flag to control the thread loop
        self._running = True

    def run(self):
        """Main loop that runs in the background thread."""
        # Counter for processes update (update less frequently)
        process_counter = 0

        while self._running:
            # Collect and emit CPU data
            try:
                cpu_info = get_cpu_info()
                self.cpu_data.emit(cpu_info)
            except Exception as e:
                print(f"Error collecting CPU data: {e}")

            # Collect and emit detailed CPU data (per-core usage/temp/freq, vcore, cache)
            try:
                cpu_detail = get_cpu_detailed_info()
                self.cpu_detail_data.emit(cpu_detail)
            except Exception as e:
                print(f"Error collecting detailed CPU data: {e}")

            # Collect and emit GPU data
            try:
                gpu_info = get_gpu_info()
                self.gpu_data.emit(gpu_info)
            except Exception as e:
                print(f"Error collecting GPU data: {e}")

            # Collect and emit RAM data
            try:
                ram_info = get_ram_info()
                self.ram_data.emit(ram_info)
            except Exception as e:
                print(f"Error collecting RAM data: {e}")

            # Collect and emit disks data
            try:
                disks_info = get_all_disks_info()
                self.disks_data.emit(disks_info)
            except Exception as e:
                print(f"Error collecting disks data: {e}")

            # Collect and emit fans data
            try:
                fans_info = get_fan_info()
                self.fans_data.emit(fans_info)
            except Exception as e:
                print(f"Error collecting fans data: {e}")

            # Collect and emit detailed processes (CPU%, threads, status) every cycle
            # (cheap: no sleep, uses a persistent Process cache internally)
            try:
                processes_detail = get_detailed_processes(8)
                self.processes_detail_data.emit(processes_detail)
            except Exception as e:
                print(f"Error collecting detailed processes data: {e}")

            # Update simple top-5-by-memory processes every 5 seconds (less frequent)
            process_counter += 1
            if process_counter >= 5:
                try:
                    processes_info = get_top_processes(5)
                    self.processes_data.emit(processes_info)
                except Exception as e:
                    print(f"Error collecting processes data: {e}")
                process_counter = 0

            # Wait 1 second before next update
            self.msleep(1000)

    def stop(self):
        """Stop the thread loop gracefully."""
        self._running = False
