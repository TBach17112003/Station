
import customtkinter as ctk
import re
from tkinter import messagebox, filedialog, ttk
import sys
import os
import shutil
import subprocess
import tkinter as tk
import realtime_With_3D
import realtime_With_3D_CamWS
import all_data
from utils.Cloud_COM.Cloud_COM import Cloud_COM

# Define your directories and other variables here
UPLOAD_DIR = "software_files"
BOOT_DIR = os.path.join(UPLOAD_DIR, "FOTA_Master_Boot")
APP_DIR = os.path.join(UPLOAD_DIR, "FOTA_Master_App")
CLIENT_DIR = os.path.join(UPLOAD_DIR, "FOTA_Client")

# Create upload directories if they don't exist
for directory in [BOOT_DIR, APP_DIR, CLIENT_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

class HomeWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("FOTA-CBDS_Station")
        self.root.geometry("600x480")

        self.bg_color = "#000000"
        self.root.configure(bg=self.bg_color)

        self.header_frame = ctk.CTkFrame(root, height=80, fg_color=self.bg_color)
        self.header_frame.pack(fill=ctk.X)

        self.header_label = ctk.CTkLabel(self.header_frame, text="Home", text_color="white", font=("MS Sans Serif", 24, "bold"), bg_color=self.bg_color)
        self.header_label.pack(pady=20)

        self.content_frame = ctk.CTkFrame(root, fg_color=self.bg_color)
        self.content_frame.pack(expand=True, fill=ctk.BOTH)

        self.welcome_label = ctk.CTkLabel(self.content_frame, text="Welcome to CBDS-FOTA SW Station!", bg_color=self.bg_color, text_color="white", font=("MS Sans Serif", 18))
        self.welcome_label.pack(pady=30)

        self.upload_file_button = ctk.CTkButton(self.content_frame, text="Upload File", command=self.choose_file_type_for_upload, fg_color="#1DB954", text_color="white", font=("MS Sans Serif", 12, "bold"))
        self.upload_file_button.pack(pady=10)

        self.create_file_button = ctk.CTkButton(self.content_frame, text="Create New File", command=self.choose_file_type_for_creation, fg_color="#1DB954", text_color="white", font=("MS Sans Serif", 12, "bold"))
        self.create_file_button.pack(pady=10)

        self.view_files_button = ctk.CTkButton(self.content_frame, text="View Software", command=self.view_files, fg_color="#1DB954", text_color="white", font=("MS Sans Serif", 12, "bold"))
        self.view_files_button.pack(pady=10)

        self.view_data_button = ctk.CTkButton(self.content_frame, text="View Real-time Data", command=self.open_chart_window, fg_color="#1DB954", text_color="white", font=("MS Sans Serif", 12, "bold"))
        self.view_data_button.pack(pady=10)

        #New button to view all data
        self.view_all_data_button = ctk.CTkButton(self.content_frame, text="View All Data", command=self.open_all_data_window, fg_color="#1DB954", text_color="white", font=("MS Sans Serif", 12, "bold"))
        self.view_all_data_button.pack(pady=10)

        self.Cloud_COM = Cloud_COM()
        success, error_message = self.Cloud_COM.startConnect()
        # print(self.Cloud_COM.getSW_Ver('FOTA_Master_Boot'))
        if not success:
            messagebox.showerror("Error", f"Server connection failed: {error_message}")
            exit()

        self.chart_window = None
        self.all_data_window = None

    def choose_file_type_for_upload(self):
        self.file_type_window = ctk.CTkToplevel(self.root)
        self.file_type_window.title("Choose File Type")
        self.file_type_window.geometry("300x200")
        self.file_type_window.attributes("-topmost", True)

        self.boot_button = ctk.CTkButton(self.file_type_window, text="FOTA Master_Boot", command=lambda: self.ask_for_version("FOTA_Master_Boot"), fg_color="#1DB954", text_color="white", font=("MS Sans Serif", 12, "bold"))
        self.boot_button.pack(pady=10)

        self.app_button = ctk.CTkButton(self.file_type_window, text="FOTA Master_App", command=lambda: self.ask_for_version("FOTA_Master_App"), fg_color="#1DB954", text_color="white", font=("MS Sans Serif", 12, "bold"))
        self.app_button.pack(pady=10)

        self.client_button = ctk.CTkButton(self.file_type_window, text="FOTA Client", command=lambda: self.ask_for_version("FOTA_Client"), fg_color="#1DB954", text_color="white", font=("MS Sans Serif", 12, "bold"))
        self.client_button.pack(pady=10)

    def upload_file(self, file_type):
        if self.Cloud_COM.isSendingInProgress():
            messagebox.showinfo("Info", "Cannot upload a new file while a previous send is in progress.")
            return

        self.file_type_window.destroy()
        file_path = filedialog.askopenfilename(filetypes=[("Python Files", "*.py"), ("Binary Files", "*.bin")])

        if file_path:
            self.save_file(file_path, file_type)

    def choose_file_type_for_creation(self):
        self.file_type_window = ctk.CTkToplevel(self.root)
        self.file_type_window.title("Choose File Type")
        self.file_type_window.geometry("300x200")
        self.file_type_window.attributes("-topmost", True)

        self.boot_button = ctk.CTkButton(self.file_type_window, text="FOTA Master_Boot", command=lambda: self.ask_for_version("FOTA_Master_Boot"), fg_color="#1DB954", text_color="white", font=("MS Sans Serif", 12, "bold"))
        self.boot_button.pack(pady=10)

        self.app_button = ctk.CTkButton(self.file_type_window, text="FOTA Master_App", command=lambda: self.ask_for_version("FOTA_Master_App"), fg_color="#1DB954", text_color="white", font=("MS Sans Serif", 12, "bold"))
        self.app_button.pack(pady=10)

        self.client_button = ctk.CTkButton(self.file_type_window, text="FOTA Client", command=lambda: self.ask_for_version("FOTA_Client"), fg_color="#1DB954", text_color="white", font=("MS Sans Serif", 12, "bold"))
        self.client_button.pack(pady=10)

    def ask_for_version(self, file_type):
        self.file_type_window.destroy()
        
        # Get the current version as a string
        version_str = self.get_current_version(file_type)
        
        try:
            # Convert the version string to a float
            current_version = float(version_str)
        except ValueError:
            print(f"Invalid version format: {version_str}")
            return
        
        major_version = int(current_version)  # Extract major version as an integer
        minor_version = int(round((current_version - major_version) * 10))  # Extract minor version as an integer

        self.version_choice_window = ctk.CTkToplevel(self.root)
        self.version_choice_window.title("Choose Version")
        self.version_choice_window.geometry("300x150")
        self.version_choice_window.attributes("-topmost", True)

        big_update_version = major_version + 1

        # Calculate the next minor version correctly
        if minor_version < 9:
            small_update_version = f"{major_version}.{minor_version + 1}"
        else:
            # If minor_version is 9, roll over to the next major version
            small_update_version = f"{major_version + 1}.0"

        # Display buttons for big and small updates
        next_button = ctk.CTkButton(
            self.version_choice_window,
            text=f"Big Update Version: ({big_update_version}.0)",
            command=lambda: self.select_version(file_type, big_update_version, 0),
            fg_color="#1DB954",
            text_color="white",
            font=("MS Sans Serif", 12, "bold")
        )
        next_button.pack(pady=10)

        minor_version_int, minor_version_fraction = map(int, small_update_version.split('.'))
        small_update_button = ctk.CTkButton(
            self.version_choice_window,
            text=f"Small Update Version: ({small_update_version})",
            command=lambda: self.select_version(file_type, minor_version_int, minor_version_fraction),
            fg_color="#1DB954",
            text_color="white",
            font=("MS Sans Serif", 12, "bold")
        )
        small_update_button.pack(pady=10)


    def select_version(self, file_type, major_version, minor_version):
        self.version_choice_window.destroy()
        file_path = filedialog.askopenfilename(filetypes=[("Python Files", "*.py")])
        if file_path:
            self.save_file(file_path, file_type, major_version, minor_version)

    def get_current_version(self, file_type):
        # Attempt to get the version from Cloud_COM using the SWType (file_type)
        cloud_version = self.Cloud_COM.getSW_Ver(file_type)
        
        # Check if a valid version was retrieved
        if cloud_version is not None:
            try:
                # Extract the major and minor versions
                major_version = int(cloud_version['Major'])
                minor_version = int(cloud_version['Minor'])
                
                # Return the version formatted as a string
                return f"{major_version}.{minor_version}"
            except (KeyError, ValueError) as e:
                # Handle any errors in the version data
                print(f"Error processing version from Cloud_COM: {cloud_version}, error: {e}")
        
        # If no version found or there was an error, default to 0.0
        print(f"No valid version found in Cloud_COM for {file_type}. Defaulting to 0.0.")
        return "0.0"


    def get_dest_dir(self, file_type):
        if file_type == "FOTA_Master_Boot":
            return BOOT_DIR
        elif file_type == "FOTA_Master_App":
            return APP_DIR
        elif file_type == "FOTA_Client":
            return CLIENT_DIR

    def create_file(self, file_type):
        self.file_type_window.destroy()
        file_path = filedialog.asksaveasfilename(defaultextension=".py", filetypes=[("Python Files", "*.py")])
        if file_path:
            with open(file_path, "w") as file:
                file.write("# New Python file")
            self.ask_for_version(file_type, file_path)

    def save_file(self, file_path, file_type, major_version, minor_version):
        dest_dir = self.get_dest_dir(file_type)
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)

        new_filename_py = f"n_{file_type}_v{major_version}.{minor_version}.py"
        dest_path = os.path.join(dest_dir, new_filename_py)
        shutil.copy(file_path, dest_path)
        self.Cloud_COM.SendSW(dest_path, self.show_message)

    def show_message(self, filename, Status):
        if Status:
            messagebox.showinfo("Success", f"File {filename} has been uploaded successfully")
        else:
            messagebox.showinfo("Failed", f"File {filename} upload failed")

    def view_files(self):
        files_window = ctk.CTkToplevel(self.root)
        files_window.title("View Software")
        files_window.geometry("600x400")
        files_window.attributes("-topmost", True)
        files_window.config(bg="#2C2F33")

        # Create a notebook widget for tabs
        notebook = ttk.Notebook(files_window)
        notebook.pack(expand=True, fill=ctk.BOTH)

        # Define folder names and their corresponding tabs
        folders = {
            "FOTA Master_Boot": BOOT_DIR,
            "FOTA Master_App": APP_DIR,
            "FOTA Client": CLIENT_DIR
        }

        for tab_name, dir_name in folders.items():
            tab = ttk.Frame(notebook)
            notebook.add(tab, text=tab_name)

            tree = ttk.Treeview(tab, columns=("File Name", "Path"), show="headings", height=10)
            tree.heading("File Name", text="File Name")
            tree.heading("Path", text="Path")
            tree.pack(expand=True, fill=ctk.BOTH, padx=10, pady=10)

            for filename in os.listdir(dir_name):
                if filename.endswith(".py"):  # List only Python files
                    filepath = os.path.join(dir_name, filename)
                    tree.insert("", ctk.END, values=(filename, filepath))

            tree.bind("<Double-1>", self.open_in_idle)

        close_button = ctk.CTkButton(files_window, text="Close", command=files_window.destroy, fg_color="#1DB954", text_color="white", font=("MS Sans Serif", 12, "bold"))
        close_button.pack(pady=10)

    def open_in_idle(self, event):
        selected_item = event.widget.selection()[0]
        file_path = event.widget.item(selected_item)['values'][1]
        subprocess.Popen([sys.executable, '-m', 'idlelib', file_path])

    def open_chart_window(self):
        if self.chart_window is None or not self.chart_window.data_window.winfo_exists():
            self.chart_window = realtime_With_3D_CamWS.Realtime_ChartWindow(self.root,cloudCOM=self.Cloud_COM)
            # Bind the destroy event for the chart window
            self.chart_window.data_window.protocol("WM_DELETE_WINDOW", self.on_chart_window_close)

    def on_chart_window_close(self):
        if self.chart_window:
            self.chart_window.data_window.destroy()
        self.chart_window.stop()
        self.chart_window = None

    def open_all_data_window(self):
        # Correct reference to the window existence check
        if self.all_data_window is None or not self.all_data_window.all_data_window.winfo_exists():
            self.all_data_window = all_data.AllData_Chart_Window(self.root, cloud_COM=self.Cloud_COM)
            # Optionally bind the window close event
            self.all_data_window.all_data_window.protocol("WM_DELETE_WINDOW", self.on_all_data_window_close)

    def on_all_data_window_close(self):
        if self.all_data_window and self.all_data_window.all_data_window.winfo_exists():
            self.all_data_window.all_data_window.destroy()
            # del self.all_data_window
        self.all_data_window = None
        #self.root.destroy()

    def on_close(self):
        #Ensure the chart window is destroyed when the main window is closed
        if self.chart_window and self.chart_window.data_window.winfo_exists():
            self.chart_window.data_window.destroy()
        if self.all_data_window and self.all_data_window.all_data_window.winfo_exists():
            self.all_data_window.all_data_window.destroy()
        self.root.destroy()
        pass
