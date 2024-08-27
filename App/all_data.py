import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
import ssl
import urllib3
import json
from utils.Cloud_COM.Cloud_COM import Cloud_COM

class AllData_Chart_Window:
    def __init__(self, root, cloud_COM: Cloud_COM):
        self.root = root
        self.all_data_window = ctk.CTkToplevel(root)
        self.all_data_window.title("View All Data")
        self.all_data_window.geometry("800x600")
        self.all_data_window.configure(bg="#2C2F33")
        

        # Create a frame for the selection
        self.selection_frame = ctk.CTkFrame(self.all_data_window, fg_color="#2C2F33")
        self.selection_frame.pack(fill=ctk.X, pady=10)

        # Create a label and combo box for date selection
        self.date_label = ctk.CTkLabel(self.selection_frame, text="Select Date:", text_color="white", font=("MS Sans Serif", 14))
        self.date_label.pack(side=ctk.LEFT, padx=10)

        self.date_combo = ttk.Combobox(self.selection_frame, values=self.get_recent_dates())
        self.date_combo.pack(side=ctk.LEFT, padx=10)
        self.date_combo.bind("<<ComboboxSelected>>", self.load_data)

        # Create a frame for displaying data
        self.data_frame = ctk.CTkFrame(self.all_data_window, fg_color="#2C2F33")
        self.data_frame.pack(expand=True, fill=ctk.BOTH, pady=10)

        self.tree = ttk.Treeview(self.data_frame, columns=("Time", "Yaw", "Pitch", "Roll", "Accel", "Gyro", "Temp", "Battery"), show="headings", height=20)
        self.tree.heading("Time", text="Time")
        self.tree.heading("Yaw", text="Yaw")
        self.tree.heading("Pitch", text="Pitch")
        self.tree.heading("Roll", text="Roll")
        self.tree.heading("Accel", text="Accel")
        self.tree.heading("Gyro", text="Gyro")
        self.tree.heading("Temp", text="Temp")
        self.tree.heading("Battery", text="Battery")
        self.tree.pack(expand=True, fill=ctk.BOTH)

        self.Cloud_COM = cloud_COM

        # Close button
        self.close_button = ctk.CTkButton(self.all_data_window, text="Close", command=self.close_window, fg_color="#1DB954", text_color="white", font=("MS Sans Serif", 12, "bold"))
        self.close_button.pack(pady=10)

    def get_recent_dates(self):
        # Replace this with actual date retrieval logic or hardcoded dates for now
        return ["2024-08-14", "2024-08-15", "2024-08-16"]

    def load_data(self, event):
        selected_date = self.date_combo.get()
        if selected_date:
            # Request data for each type
            status_orientation, data_orientation = self.Cloud_COM.RequestData_ByDate("orientation", selected_date)
            status_accelerator, data_accelerator = self.Cloud_COM.RequestData_ByDate("accelerator", selected_date)
            status_gyroscope, data_gyroscope = self.Cloud_COM.RequestData_ByDate("gyroscope", selected_date)
            
            if status_orientation == 200 and status_accelerator == 200 and status_gyroscope == 200:
                # Combine data for display
                combined_data = self.combine_data(data_orientation, data_accelerator, data_gyroscope)
                self.display_data(combined_data)
            else:
                messagebox.showerror("Error", "Failed to retrieve data.")


    def combine_data(self, data_orientation, data_accelerator, data_gyroscope):
        try:
            # Load JSON data
            orientation_data = json.loads(data_orientation)
            accelerator_data = json.loads(data_accelerator)
            gyroscope_data = json.loads(data_gyroscope)
            
            # Create a dictionary to store combined data
            combined_data = []

            # Assuming all data lists are the same length and sorted by time
            for i in range(len(orientation_data)):
                combined_entry = {
                    "time": orientation_data[i].get("time", "N/A"),
                    "yaw": orientation_data[i].get("yaw", "N/A"),
                    "pitch": orientation_data[i].get("pitch", "N/A"),
                    "roll": orientation_data[i].get("roll", "N/A"),
                    "accel_x": accelerator_data[i].get("x", "N/A"),
                    "accel_y": accelerator_data[i].get("y", "N/A"),
                    "accel_z": accelerator_data[i].get("z", "N/A"),
                    "gyro_x": gyroscope_data[i].get("x", "N/A"),
                    "gyro_y": gyroscope_data[i].get("y", "N/A"),
                    "gyro_z": gyroscope_data[i].get("z", "N/A"),
                }
                combined_data.append(combined_entry)
            
            # Convert combined data to JSON for display
            return json.dumps(combined_data)
        except (json.JSONDecodeError, IndexError) as e:
            messagebox.showerror("Error", f"Failed to combine data: {e}")
            return "[]"
        
    def display_data(self, data):
        try:
            # Parse the JSON data
            data_list = json.loads(data)
            
            # Clear existing data from the Treeview
            self.tree.delete(*self.tree.get_children())

            for entry in data_list:
                # Extract data from each entry, handling missing keys
                time = entry.get("time", "N/A")
                yaw = entry.get("yaw", "N/A")
                pitch = entry.get("pitch", "N/A")
                roll = entry.get("roll", "N/A")
                accel_x = entry.get("accel_x", "N/A")
                accel_y = entry.get("accel_y", "N/A")
                accel_z = entry.get("accel_z", "N/A")
                gyro_x = entry.get("gyro_x", "N/A")
                gyro_y = entry.get("gyro_y", "N/A")
                gyro_z = entry.get("gyro_z", "N/A")
                
                # Insert data into the Treeview
                self.tree.insert("", tk.END, values=(
                    time, yaw, pitch, roll,
                    accel_x, accel_y, accel_z,
                    gyro_x, gyro_y, gyro_z
                ))
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Failed to decode data.")


    def close_window(self):
        self.all_data_window.destroy()
