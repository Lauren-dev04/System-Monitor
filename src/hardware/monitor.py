# Import psutil to get system and hardware information
import psutil
# Import os and glob to read system files for GPU info
import os
import glob


def get_cpu_info():
    """Get CPU usage percentage, temperature, and model name."""

    # Get CPU usage (interval=0.5 means it takes 0.5 seconds to calculate)
    cpu_usage = psutil.cpu_percent(interval=0.5)

    # Initialize temperature as None
    cpu_temp = None

    # Get CPU model name from /proc/cpuinfo
    cpu_model = "Unknown CPU"
    try:
        with open('/proc/cpuinfo', 'r') as f:
            for line in f:
                if 'model name' in line:
                    cpu_model = line.split(':')[1].strip()
                    break
    except Exception:
        pass

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
        'temp': cpu_temp,
        'model': cpu_model
    }


def get_ram_info():
    """Get RAM usage percentage, memory in GB, and type."""

    # Get virtual memory stats
    mem = psutil.virtual_memory()

    # Convert bytes to gigabytes (1 GB = 1024^3 bytes)
    bytes_to_gb = 1024 ** 3
    total_gb = round(mem.total / bytes_to_gb, 1)
    used_gb = round(mem.used / bytes_to_gb, 1)
    free_gb = round(mem.available / bytes_to_gb, 1)

    # Try to get RAM type from system
    ram_type = "DDR"
    try:
        import subprocess
        result = subprocess.run(['dmidecode', '-t', 'memory'], capture_output=True, text=True, timeout=2)
        if 'DDR4' in result.stdout:
            ram_type = "DDR4"
        elif 'DDR5' in result.stdout:
            ram_type = "DDR5"
    except Exception:
        pass

    ram_model = f"{total_gb}GB {ram_type}"

    # Return data as a dictionary
    return {
        'percent': mem.percent,
        'total_gb': total_gb,
        'used_gb': used_gb,
        'free_gb': free_gb,
        'model': ram_model
    }


def get_gpu_info():
    """Get GPU usage, temperature, VRAM, and model name with fallback methods."""

    # Default values in case everything fails
    gpu_data = {
        'usage': 0,
        'temp': None,
        'vram_used_mb': 0,
        'vram_total_mb': 0,
        'model': 'Unknown GPU'
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
            gpu_data['model'] = pyrsmi.amdsmi_get_gpu_vendor_name(gpu)

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

            # 4. Get GPU Model Name
            vendor_file = os.path.join(path, "vendor")
            device_file = os.path.join(path, "device")
            if os.path.exists(vendor_file) and os.path.exists(device_file):
                with open(vendor_file, 'r') as f:
                    vendor = f.read().strip()
                with open(device_file, 'r') as f:
                    device = f.read().strip()
                # Try to get a human-readable name from lspci
                try:
                    import subprocess
                    result = subprocess.run(['lspci', '-nn'], capture_output=True, text=True, timeout=2)
                    for line in result.stdout.split('\n'):
                        if vendor[2:] in line and device[2:] in line:
                            # Extract the model name (after the vendor)
                            parts = line.split(': ', 1)
                            if len(parts) > 1:
                                gpu_data['model'] = parts[1].strip()
                                break
                except Exception:
                    gpu_data['model'] = f"GPU {vendor}:{device}"

            # Break after the first valid GPU found
            break

    except Exception:
        # Native method failed, return default values
        pass

    return gpu_data


def get_all_disks_info():
    """Get information about all physical disks in the system."""

    disks_dict = {}  # Dictionary to group partitions by physical disk
    bytes_to_gb = 1024 ** 3

    # Get all disk partitions
    partitions = psutil.disk_partitions()

    for partition in partitions:
        # Skip virtual filesystems
        if partition.fstype not in ['ext4', 'xfs', 'btrfs', 'ntfs', 'fat32', 'vfat']:
            continue

        try:
            # Extract physical disk name (e.g., /dev/sda1 -> sda, /dev/nvme0n1p2 -> nvme0n1)
            device = partition.device.split('/')[-1]

            # Remove partition numbers to get the base disk name
            # For /dev/sda1 -> sda, /dev/nvme0n1p2 -> nvme0n1
            disk_name = device.rstrip('0123456789')
            if not disk_name:
                disk_name = device

            # Get disk usage for this partition
            usage = psutil.disk_usage(partition.mountpoint)

            # Initialize disk entry if not exists
            if disk_name not in disks_dict:
                # Try to get disk model name
                disk_model = "Unknown Disk"
                try:
                    model_file = f"/sys/block/{disk_name}/device/model"
                    if os.path.exists(model_file):
                        with open(model_file, 'r') as f:
                            disk_model = f.read().strip()
                except Exception:
                    pass

                disks_dict[disk_name] = {
                    'model': disk_model,
                    'total_bytes': 0,
                    'used_bytes': 0,
                    'free_bytes': 0,
                    'mountpoints': []
                }

            # Accumulate space from all partitions of this disk
            disks_dict[disk_name]['total_bytes'] += usage.total
            disks_dict[disk_name]['used_bytes'] += usage.used
            disks_dict[disk_name]['free_bytes'] += usage.free
            disks_dict[disk_name]['mountpoints'].append(partition.mountpoint)

        except (PermissionError, OSError):
            continue

    # Convert to list format
    disks = []
    for disk_name, data in disks_dict.items():
        total_gb = round(data['total_bytes'] / bytes_to_gb, 1)
        used_gb = round(data['used_bytes'] / bytes_to_gb, 1)
        free_gb = round(data['free_bytes'] / bytes_to_gb, 1)
        percent = round((data['used_bytes'] / data['total_bytes']) * 100, 1) if data['total_bytes'] > 0 else 0

        disks.append({
            'disk_name': disk_name,
            'model': f"{total_gb}GB {data['model']}",
            'mountpoints': ', '.join(data['mountpoints']),
            'total_gb': total_gb,
            'used_gb': used_gb,
            'free_gb': free_gb,
            'percent': percent
        })

    return disks


def get_top_processes(count=5):
    """Get the top N processes by memory usage."""

    processes = []

    try:
        # Iterate over all running processes
        for proc in psutil.process_iter(['name', 'memory_info']):
            try:
                # Get process info
                name = proc.info['name']
                memory_info = proc.info['memory_info']

                if name and memory_info:
                    # Convert bytes to MB
                    memory_mb = round(memory_info.rss / (1024 ** 2), 1)

                    processes.append({
                        'name': name,
                        'memory_mb': memory_mb
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                # Skip processes that disappeared or we can't access
                continue

        # Sort by memory usage (descending) and take top N
        processes.sort(key=lambda x: x['memory_mb'], reverse=True)
        return processes[:count]

    except Exception:
        return []

def get_fan_info():
    """Get fan speeds in RPM from system sensors."""

    fan_data = {
        'cpu_fan_rpm': None,
        'gpu_fan_rpm': None,
        'system_fan_rpm': None
    }

    try:
        fans = psutil.sensors_fans()

        if fans:
            # GPU fan (AMD)
            if 'amdgpu' in fans:
                for entry in fans['amdgpu']:
                    fan_data['gpu_fan_rpm'] = entry.current

            # Collect all motherboard fans
            mobo_fans = []

            # Check nct6796 (your motherboard chip)
            if 'nct6796' in fans:
                for entry in fans['nct6796']:
                    if entry.current > 0:  # Only add if fan is spinning
                        mobo_fans.append(entry.current)

            # Check coretemp as fallback
            if 'coretemp' in fans:
                for entry in fans['coretemp']:
                    if entry.current > 0:
                        mobo_fans.append(entry.current)

            # Assign fans: highest RPM is usually CPU fan
            mobo_fans.sort(reverse=True)
            if len(mobo_fans) > 0:
                fan_data['cpu_fan_rpm'] = mobo_fans[0]
            if len(mobo_fans) > 1:
                fan_data['system_fan_rpm'] = mobo_fans[1]

    except Exception as e:
        print(f"Error reading fan sensors: {e}")

    return fan_data

# --- TEST BLOCK ---
# This code runs only if you execute this file directly
if __name__ == "__main__":
    # Test CPU info
    print("Testing CPU info...")
    cpu = get_cpu_info()
    print(f"CPU Model: {cpu['model']}")
    print(f"CPU Usage: {cpu['usage']}%")
    print(f"CPU Temp:  {cpu['temp']}°C")

    print("")  # Empty line separator

    #test Fan info
    print("Testing Fan info...")
    fans = get_fan_info()
    print(f"CPU Fan:  {fans['cpu_fan_rpm']} RPM" if fans['cpu_fan_rpm'] else "CPU Fan: N/A")
    print(f"GPU Fan:  {fans['gpu_fan_rpm']} RPM" if fans['gpu_fan_rpm'] else "GPU Fan: N/A")
    print(f"System Fan: {fans['system_fan_rpm']} RPM" if fans['system_fan_rpm'] else "System Fan: N/A")

    # Test RAM info
    print("Testing RAM info...")
    ram = get_ram_info()
    print(f"RAM Model: {ram['model']}")
    print(f"RAM Usage: {ram['percent']}%")
    print(f"RAM Total: {ram['total_gb']} GB")
    print(f"RAM Used:  {ram['used_gb']} GB")
    print(f"RAM Free:  {ram['free_gb']} GB")

    print("")  # Empty line separator

    # Test GPU info
    print("Testing GPU info...")
    gpu = get_gpu_info()
    print(f"GPU Model: {gpu['model']}")
    print(f"GPU Usage:     {gpu['usage']}%")
    print(f"GPU Temp:      {gpu['temp']}°C")
    print(f"GPU VRAM Used: {gpu['vram_used_mb']} MB")
    print(f"GPU VRAM Total:{gpu['vram_total_mb']} MB")

    print("")  # Empty line separator

    # Test All Disks info
    print("Testing All Disks info...")
    disks = get_all_disks_info()
    for i, disk in enumerate(disks, 1):
        print(f"Disk {i}: {disk['model']}")
        print(f"  Mount: {disk['mountpoints']}")
        print(f"  Usage: {disk['percent']}%")
        print(f"  Total: {disk['total_gb']} GB | Used: {disk['used_gb']} GB | Free: {disk['free_gb']} GB")
        print("")

    # Test Top Processes
    print("Testing Top 5 Processes by RAM...")
    top_procs = get_top_processes(5)
    for i, proc in enumerate(top_procs, 1):
        print(f"{i}. {proc['name']}: {proc['memory_mb']} MB")
