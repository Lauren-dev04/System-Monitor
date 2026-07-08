# Import psutil to get system and hardware information
import psutil
# Import os and glob to read system files for GPU info
import os
import glob
import time


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


def get_cpu_detailed_info():
    """Get detailed per-core CPU info: usage, frequency, temperature, VCore, cache sizes, uptime.
    All values are read from real sensors/sysfs. If a value isn't available on this
    hardware (e.g. VCore voltage), it's returned as None so the UI can show N/A
    instead of a fabricated number.
    """
    # --- Per-core usage (real, psutil) ---
    per_core_usage = psutil.cpu_percent(interval=0.3, percpu=True)
    overall_usage = sum(per_core_usage) / len(per_core_usage) if per_core_usage else 0

    # --- Per-core frequency (real, psutil; falls back to overall freq if percpu unsupported) ---
    per_core_freq = []
    try:
        freqs = psutil.cpu_freq(percpu=True)
        if freqs:
            per_core_freq = [f.current for f in freqs]
    except Exception:
        pass

    if not per_core_freq:
        try:
            f = psutil.cpu_freq()
            if f:
                per_core_freq = [f.current] * len(per_core_usage)
        except Exception:
            pass

    # --- Per-core temperature (real, coretemp/k10temp labels like "Core 0") ---
    per_core_temp = {}
    avg_temp = None
    try:
        temps = psutil.sensors_temperatures()
        if temps:
            source = temps.get('coretemp') or temps.get('k10temp')
            if source:
                core_temps = []
                for entry in source:
                    label = (entry.label or "").lower()
                    if 'core' in label:
                        try:
                            core_num = int(label.replace('core', '').strip())
                            per_core_temp[core_num] = entry.current
                            core_temps.append(entry.current)
                        except ValueError:
                            pass
                    elif 'package' in label or 'tctl' in label or 'tdie' in label:
                        avg_temp = entry.current
                if avg_temp is None:
                    if core_temps:
                        avg_temp = sum(core_temps) / len(core_temps)
                    else:
                        avg_temp = source[0].current
    except Exception:
        pass

    # --- VCore voltage (real, auto-detected from hwmon; None if not exposed by hardware) ---
    vcore = None
    try:
        for hwmon_path in glob.glob('/sys/class/hwmon/hwmon*'):
            for label_file in glob.glob(os.path.join(hwmon_path, 'in*_label')):
                try:
                    with open(label_file, 'r') as f:
                        label = f.read().strip().lower()
                except Exception:
                    continue
                if 'vcore' in label:
                    input_file = label_file.replace('_label', '_input')
                    if os.path.exists(input_file):
                        with open(input_file, 'r') as f:
                            # hwmon voltage values are in millivolts
                            vcore = int(f.read().strip()) / 1000.0
                    break
            if vcore is not None:
                break
    except Exception:
        pass

    # --- Cache sizes only (real, from sysfs; no hit rate since that needs perf/root) ---
    cache_sizes = {}
    try:
        cache_base = '/sys/devices/system/cpu/cpu0/cache'
        if os.path.isdir(cache_base):
            for index_dir in sorted(glob.glob(os.path.join(cache_base, 'index*'))):
                level_file = os.path.join(index_dir, 'level')
                type_file = os.path.join(index_dir, 'type')
                size_file = os.path.join(index_dir, 'size')
                if os.path.exists(level_file) and os.path.exists(size_file):
                    with open(level_file) as f:
                        level = f.read().strip()
                    cache_type = ""
                    if os.path.exists(type_file):
                        with open(type_file) as f:
                            cache_type = f.read().strip()
                    with open(size_file) as f:
                        size = f.read().strip()
                    key = f"L{level}"
                    if cache_type == "Data":
                        key += "d"
                    elif cache_type == "Instruction":
                        key += "i"
                    cache_sizes[key] = size
    except Exception:
        pass

    # --- Uptime (real, psutil) ---
    uptime_seconds = 0
    try:
        uptime_seconds = int(time.time() - psutil.boot_time())
    except Exception:
        pass

    return {
        'per_core_usage': per_core_usage,
        'overall_usage': overall_usage,
        'per_core_freq': per_core_freq,
        'per_core_temp': per_core_temp,
        'avg_temp': avg_temp,
        'vcore': vcore,
        'cache_sizes': cache_sizes,
        'uptime_seconds': uptime_seconds,
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


def get_ram_detailed_info():
    """Get detailed RAM info including swap."""
    ram_data = get_ram_info()

    # Add swap info
    try:
        swap = psutil.swap_memory()
        ram_data['swap_total_gb'] = round(swap.total / (1024 ** 3), 1)
        ram_data['swap_used_gb'] = round(swap.used / (1024 ** 3), 1)
        ram_data['swap_free_gb'] = round(swap.free / (1024 ** 3), 1)
        ram_data['swap_percent'] = swap.percent
    except Exception:
        ram_data['swap_total_gb'] = 0
        ram_data['swap_used_gb'] = 0
        ram_data['swap_free_gb'] = 0
        ram_data['swap_percent'] = 0

    return ram_data


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
            gpu_data['temp'] = pyrsmi.amdsmi_get_temp_metric(gpu, 1, 0)['current']  # Edge temp
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


def get_gpu_detailed_info():
    """Get detailed GPU info including usage, temperature, VRAM, and model."""
    # Reuse get_gpu_info() and add more details
    gpu_data = get_gpu_info()

    # Add GPU frequency if available
    gpu_freq = None
    try:
        # Try to read frequency from sysfs
        drm_path = "/sys/class/drm/card*/device"
        gpu_paths = glob.glob(drm_path)
        for path in gpu_paths:
            freq_file = os.path.join(path, "pp_dpm_sclk")
            if os.path.exists(freq_file):
                with open(freq_file, 'r') as f:
                    lines = f.readlines()
                    # The active line has an asterisk
                    for line in lines:
                        if '*' in line:
                            # Extract frequency (e.g., "0: 500Mhz *")
                            parts = line.split(':')
                            if len(parts) > 1:
                                freq_str = parts[1].strip().split('Mhz')[0].strip()
                                try:
                                    gpu_freq = int(freq_str)
                                except Exception:
                                    pass
                            break
                break
    except Exception:
        pass

    gpu_data['frequency_mhz'] = gpu_freq

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


def get_disk_detailed_info():
    """Get detailed disk info including I/O stats if available."""
    disks = get_all_disks_info()

    # Add I/O statistics for each disk
    try:
        disk_io = psutil.disk_io_counters(perdisk=True)
        for disk in disks:
            disk_name = disk['disk_name']
            if disk_name in disk_io:
                io = disk_io[disk_name]
                disk['read_mb'] = round(io.read_bytes / (1024 ** 2), 1)
                disk['write_mb'] = round(io.write_bytes / (1024 ** 2), 1)
            else:
                disk['read_mb'] = 0
                disk['write_mb'] = 0
    except Exception:
        for disk in disks:
            disk['read_mb'] = 0
            disk['write_mb'] = 0

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


# Cache of psutil.Process objects, kept alive between calls so cpu_percent()
# can report a real delta instead of always returning 0.0 on a fresh object.
_process_cache = {}


def get_detailed_processes(count=8):
    """Get top processes with CPU%, memory, thread count and status (real-time, non-blocking).
    Uses a persistent Process object cache instead of interval sleeps, so it's
    cheap enough to call every monitoring cycle.
    """
    global _process_cache
    current_pids = set()
    results = []

    for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'num_threads', 'status']):
        try:
            pid = proc.info['pid']
            current_pids.add(pid)

            if pid not in _process_cache:
                _process_cache[pid] = proc
                proc.cpu_percent(None)  # Prime the measurement, skip this cycle
                continue

            cached_proc = _process_cache[pid]
            cpu_pct = cached_proc.cpu_percent(None)
            info = proc.info

            if info['name']:
                results.append({
                    'name': info['name'],
                    'cpu_percent': round(cpu_pct, 1),
                    'memory_mb': round(info['memory_info'].rss / (1024 ** 2), 1) if info['memory_info'] else 0,
                    'threads': info['num_threads'],
                    'status': info['status']
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    # Clean up cache entries for processes that no longer exist
    dead_pids = set(_process_cache.keys()) - current_pids
    for pid in dead_pids:
        del _process_cache[pid]

    results.sort(key=lambda x: x['cpu_percent'], reverse=True)
    return results[:count]


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

    # Test detailed CPU info
    print("Testing detailed CPU info...")
    detail = get_cpu_detailed_info()
    print(f"Per-core usage: {detail['per_core_usage']}")
    print(f"Overall usage:  {detail['overall_usage']:.1f}%")
    print(f"Per-core freq:  {detail['per_core_freq']}")
    print(f"Per-core temp:  {detail['per_core_temp']}")
    print(f"Avg temp:       {detail['avg_temp']}")
    print(f"VCore:          {detail['vcore']}")
    print(f"Cache sizes:    {detail['cache_sizes']}")
    print(f"Uptime (s):     {detail['uptime_seconds']}")
    print("")  # Empty line separator

    # Test Fan info
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
    print("")  # Empty line separator

    # Test Detailed Processes (call twice, second call has real CPU% deltas)
    print("Testing Detailed Processes (CPU%)...")
    get_detailed_processes(8)
    import time as _t
    _t.sleep(1)
    detailed_procs = get_detailed_processes(8)
    for i, proc in enumerate(detailed_procs, 1):
        print(f"{i}. {proc['name']}: {proc['cpu_percent']}% CPU, {proc['memory_mb']} MB, "
              f"{proc['threads']} threads, {proc['status']}")
