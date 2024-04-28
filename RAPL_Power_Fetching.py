import importlib
import subprocess

def install_module(module_name):
    subprocess.check_call(["pip3", "install", module_name])

# Check and install psutil
try:
    importlib.import_module("psutil")
except ImportError:
    print("psutil is not installed. Installing...")
    install_module("psutils")
    print("psutil has been installed.")


import datetime
import subprocess
import psutil
import os
import socket
import time

counts = 79200
# runner = "infinite"    
runner = "finite"

files = ["/sys/class/powercap/intel-rapl:0/energy_uj", "/sys/class/powercap/intel-rapl:1/energy_uj"]

def read_number_from_file(file_path):
    with open(file_path, 'r') as file:
        number = int(file.read().strip())
    return number

def get_node_name():
    return socket.gethostname()

os.makedirs("/scratch/raghuhv/Final_Model_March/logs", exist_ok=True)

current_node = get_node_name()

data_time = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")

log_file_path = "/scratch/raghuhv/Final_Model_March/logs/" + current_node + ".log"

# print("Node Name:", node_name, " Time: "+ data_time)

with open(log_file_path, "a") as log_file:
    while True:
        ##################### Power Fetch #####################
        
        start_number1 = read_number_from_file(files[0])
        start_number2 = read_number_from_file(files[1])

        start_time = time.time()

        # Wait for a second
        time.sleep(1)

        end_time = time.time()
        end_number1 = read_number_from_file(files[0])
        end_number2 = read_number_from_file(files[1])

        difference1 = (end_number1 - start_number1)/1000000
        difference2 = (end_number2 - start_number2)/1000000
        output = difference1 + difference2
        
        ########################################################
        
        start_time = time.time()
        total_bytes_read = psutil.disk_io_counters().read_bytes
        total_bytes_written = psutil.disk_io_counters().write_bytes
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        avg_temp = 0
        for i in psutil.sensors_temperatures()["coretemp"]:
            avg_temp = i.current
        avg_temp += len(psutil.sensors_temperatures()["coretemp"])
        ram_per = ((psutil.virtual_memory()[0]/1000000000) - (psutil.virtual_memory()[1] / 1000000000)) / (psutil.virtual_memory()[0] / 1000000000) * 100
        disk_per = psutil.disk_usage('/').used / psutil.disk_usage('/').total * 100

        end_time = time.time()
        read_speed = (total_bytes_read - psutil.disk_io_counters().read_bytes) / (end_time - start_time)
        write_speed = (total_bytes_written - psutil.disk_io_counters().write_bytes) / (end_time - start_time)
        
        log_file.write(timestamp + " | CPU Usage Percentage: " + str(psutil.cpu_percent()) + " % | CPU Clock Speed: " + str(psutil.cpu_freq().current) + " GHz | CPU Core Counts: " + str(psutil.cpu_count()) + " | CPU Temperature: " + str(avg_temp) + " C | RAM Usage Percentage: " + str(ram_per) + " % | Disk Usage: " + str(disk_per) + " | Disk Read Speed : " + str(read_speed) + " | Disk Write Speed : " + str(write_speed) + " | Power Watts: " + str(output) + "\n")
        
        if runner == "finite" and counts > 0:
            counts -= 1
        if counts <= 0:
            break

print("Completed")
