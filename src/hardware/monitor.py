# Import psutil to get system and hardware information
import psutil
# Import os and glob to read system files for GPU info
import os
import glob


def get_cpu_info():
    """Get CPU usage percentage and temperature."""

    # Get CPU usage (interval=0.5 means it takes 0.5 seconds to calculate)
    cpu_usage = psutil.cpu_percent(interval=0.5)

    # Initialize temperature as None
    cpu_temp = None

    try:
        # Try to get temperature sensors data
        temps = psutil.sensors_temperatures()

        if temps:
            # Check for Intel 'coretemp' or AMD 'k10temp'
            if 'coretemp' in temps:
                cpu_temp = temps['coretemp'][0].current
            elif 'k10temp' in temps:
                cpu_temp = temps['k10temp'][0].current
            else:
                # Fallback: get the first available sensor
                for key in temps:
                    cpu_temp = temps[key][0].current
                    break

    except AttributeError:
        # sensors_temperatures() is not available on this OS
        pass

    # Return data as a dictionary
    return {
        'usage': cpu_usage,
        'temp': cpu_temp
    }


def get_ram_info():
    """Get RAM usage percentage and memory in GB."""

    # Get virtual memory stats
    mem = psutil.virtual_memory()

    # Convert bytes to gigabytes (1 GB = 1024^3 bytes)
    bytes_to_gb = 1024 ** 3
    total_gb = round(mem.total / bytes_to_gb, 1)
    used_gb = round(mem.used / bytes_to_gb, 1)
    free_gb = round(mem.available / bytes_to_gb, 1)

    # Return data as a dictionary
    return {
        'percent': mem.percent,
        'total_gb': total_gb,
        'used_gb': used_gb,
        'free_gb': free_gb
    }


def get_gpu_info():
    """Get GPU usage, temperature and VRAM with fallback methods."""

    # Default values in case everything fails
    gpu_data = {
        'usage': 0,
        'temp': None,
        'vram_used_mb': 0,
        'vram_total_mb': 0
    }

    # --- METHOD 1: Try pyrsmi (AMD GPU) ---
    try:
        import pyrsmi
        # Initialize the library
        pyrsmi.amdsmi_init()

        # Get the first GPU (usually the only one in desktop PCs)
        processors = pyrsmi.amdsmi_get_processor_handles()
        if processors:
            gpu = processors[0]

            # Get metrics
            gpu_data['usage'] = pyrsmi.amdsmi_get_gpu_activity(gpu)['gfx_activity']
            gpu_data['temp'] = pyrsmi.amdsmi_get_temp_metric(gpu, 1, 0)['current'] # Edge temp

        # Shutdown the library to free resources
        pyrsmi.amdsmi_shut_down()
        return gpu_data

    except Exception:
        # pyrsmi failed or is not installed, try Method 2
        pass

    # --- METHOD 2: Native Linux files (/sys/class/drm/) ---
    try:
        # Find all GPU devices in the system
        drm_path = "/sys/class/drm/card*/device"
        gpu_paths = glob.glob(drm_path)

        for path in gpu_paths:
            # 1. Get GPU Usage
            usage_file = os.path.join(path, "gpu_busy_percent")
            if os.path.exists(usage_file):
                with open(usage_file, 'r') as f:
                    gpu_data['usage'] = int(f.read().strip())

            # 2. Get Temperature
            hwmon_path = os.path.join(path, "hwmon/hwmon*/temp1_input")
            temp_files = glob.glob(hwmon_path)
            if temp_files:
                with open(temp_files[0], 'r') as f:
                    # Temperature is in millidegrees, convert to Celsius
                    gpu_data['temp'] = int(f.read().strip()) / 1000.0

            # 3. Get VRAM
            vram_used_file = os.path.join(path, "mem_info_vram_used")
            vram_total_file = os.path.join(path, "mem_info_vram_total")

            if os.path.exists(vram_used_file) and os.path.exists(vram_total_file):
                with open(vram_used_file, 'r') as f:
                    gpu_data['vram_used_mb'] = round(int(f.read().strip()) / (1024**2), 1)
                with open(vram_total_file, 'r') as f:
                    gpu_data['vram_total_mb'] = round(int(f.read().strip()) / (1024**2), 1)

            # Break after the first valid GPU found
            break

    except Exception:
        # Native method failed, return default values
        pass

    return gpu_data


def get_disk_info():
    """Get disk usage percentage and space in GB for the root partition."""

    # Get disk usage stats for the root partition '/'
    disk = psutil.disk_usage('/')

    # Convert bytes to gigabytes (1 GB = 1024^3 bytes)
    bytes_to_gb = 1024 ** 3
    total_gb = round(disk.total / bytes_to_gb, 1)
    used_gb = round(disk.used / bytes_to_gb, 1)
    free_gb = round(disk.free / bytes_to_gb, 1)

    # Return data as a dictionary
    return {
        'percent': disk.percent,
        'total_gb': total_gb,
        'used_gb': used_gb,
        'free_gb': free_gb
    }


# --- TEST BLOCK ---
# This code runs only if you execute this file directly
if __name__ == "__main__":
    # Test CPU info
    print("Testing CPU info...")
    cpu = get_cpu_info()
    print(f"CPU Usage: {cpu['usage']}%")
    print(f"CPU Temp:  {cpu['temp']}°C")

    print("")  # Empty line separator

    # Test RAM info
    print("Testing RAM info...")
    ram = get_ram_info()
    print(f"RAM Usage: {ram['percent']}%")
    print(f"RAM Total: {ram['total_gb']} GB")
    print(f"RAM Used:  {ram['used_gb']} GB")
    print(f"RAM Free:  {ram['free_gb']} GB")

    print("")  # Empty line separator

    # Test GPU info
    print("Testing GPU info...")
    gpu = get_gpu_info()
    print(f"GPU Usage:     {gpu['usage']}%")
    print(f"GPU Temp:      {gpu['temp']}°C")
    print(f"GPU VRAM Used: {gpu['vram_used_mb']} MB")
    print(f"GPU VRAM Total:{gpu['vram_total_mb']} MB")

    print("")  # Empty line separator

    # Test Disk info
    print("Testing Disk info...")
    disk = get_disk_info()
    print(f"Disk Usage:  {disk['percent']}%")
    print(f"Disk Total:  {disk['total_gb']} GB")
    print(f"Disk Used:   {disk['used_gb']} GB")
    print(f"Disk Free:   {disk['free_gb']} GB")
