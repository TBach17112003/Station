import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import pandas as pd
from datetime import datetime, timedelta
import time
import threading

class AllData_Chart_Window:
    def __init__(self, root, cloud_COM):
        self.root = root
        self.allDateTypes = ['', 'Orientation', 'Accelerator', 'Gyroscope', 'Gesture', 'Battery']
        self.queryDataType = "Orientation"
        self.queryDate = None
        self.Datatree = None
        self.all_data_window = ctk.CTkToplevel(root)
        self.all_data_window.title("View All Data")
        self.all_data_window.geometry("800x600")
        self.all_data_window.configure(bg="#2C2F33")

        # Create a frame for the selection
        self.selection_frame = ctk.CTkFrame(self.all_data_window, fg_color="#2C2F33")
        self.selection_frame.pack(fill=ctk.X, pady=10)

        self.data_label = ctk.CTkLabel(self.selection_frame, text="Select Data type:", text_color="white", font=("MS Sans Serif", 14))
        self.data_label.pack(side=ctk.LEFT, padx=10)

        self.data_combo = ctk.CTkComboBox(self.selection_frame, values=self.allDateTypes, command=self.save_queryData)
        self.data_combo.pack(side=ctk.LEFT, padx=10)

        # Create a label and combo box for date selection
        self.date_label = ctk.CTkLabel(self.selection_frame, text="Select Date:", text_color="white", font=("MS Sans Serif", 14))
        self.date_label.pack(side=ctk.LEFT, padx=10)

        self.date_comboBox = ctk.CTkComboBox(self.selection_frame, values=self.get_recent_dates(), command=self.save_queryDate)
        self.date_comboBox.pack(side=ctk.LEFT, padx=10)

        self.querySubmitBtn = ctk.CTkButton(master=self.selection_frame, text="Query", command=self.start_query_thread)
        self.querySubmitBtn.pack(side="left", expand=True, fill="x")

        # Create a frame for displaying data
        self.data_frame = ctk.CTkFrame(self.all_data_window, fg_color="#2C2F33")
        self.data_frame.pack(expand=True, fill=ctk.BOTH, pady=10)

        # Placeholder label before data is loaded
        self.DataFrame_Text = ctk.CTkLabel(master=self.data_frame, text="Loading data...", font=("Roboto Medium", -16))
        self.DataFrame_Text.pack(pady=20, padx=20)

        # Pagination controls
        self.pagination_frame = ctk.CTkFrame(self.all_data_window, fg_color="#2C2F33")
        self.pagination_frame.pack(fill=ctk.X, pady=10)

        # Configure grid layout
        self.pagination_frame.grid_columnconfigure(0, weight=1)
        self.pagination_frame.grid_columnconfigure(2, weight=1)
        self.pagination_frame.grid_rowconfigure(0, weight=1)

        self.prev_button = ctk.CTkButton(self.pagination_frame, text="Previous", command=self.show_previous_page, state=tk.DISABLED)
        self.prev_button.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.page_label = ctk.CTkLabel(self.pagination_frame, text="Page 1", text_color="white")
        self.page_label.grid(row=0, column=1, padx=5, pady=5)

        self.next_button = ctk.CTkButton(self.pagination_frame, text="Next", command=self.show_next_page, state=tk.DISABLED)
        self.next_button.grid(row=0, column=2, padx=5, pady=5, sticky="e")

        self.Cloud_COM = cloud_COM

        # Export data button
        self.export_button = ctk.CTkButton(self.all_data_window, text="Export Data", command=self.start_export_thread, fg_color="#1DB954", text_color="white", font=("MS Sans Serif", 12, "bold"))
        self.export_button.pack(pady=10)

        # Time measurement variables
        self.start_time = None
        self.end_time = None

        # Pagination state
        self.data_dict = []
        self.current_page = 0
        self.rows_per_page = 100

    def save_queryDate(self, choice):
        self.queryDate = choice

    def save_queryData(self, choice):
        self.queryDataType = choice

    def get_recent_dates(self):
        # Generate the last 7 days of dates
        today = datetime.today()
        dates = [today - timedelta(days=i) for i in range(7)]
        return [''] + [date.strftime('%Y-%m-%d') for date in dates]

    def start_query_thread(self):
        # Record the start time
        self.start_time = time.time()

        # Reset pagination state
        self.current_page = 0
        self.update_page_info()

        # Disable UI elements while querying data
        self.disable_controls()

        query_thread = threading.Thread(target=self.queryData, daemon=True)
        query_thread.start()

    def queryData(self):
        try:
            if self.queryDate:
                queryStatus, Data = self.Cloud_COM.RequestData_ByDate(self.queryDataType.lower(), self.queryDate)
                if queryStatus == 200:
                    if Data == "[]":
                        self.update_no_data()
                    else:
                        self.data_dict = json.loads(Data)
                        self.createTreeview()
                        self.load_page_data()
                elif queryStatus == 400:
                    self.update_error_message(json.loads(Data)['error'])
                elif queryStatus == 404:
                    self.update_error_message('Invalid API')
                else:
                    self.update_error_message("Other problem")
            else:
                self.update_error_message("Please select a valid date.")
        except Exception as e:
            print(f"Error during querying: {e}")
        finally:
            # Re-enable the controls and show a message when the data is loaded
            self.enable_controls()
            self.show_query_complete_message()

    def update_no_data(self):
        if self.Datatree:
            self.Datatree.destroy()
            self.Datatree = None
        self.DataFrame_Text.configure(text="No data available")
        self.DataFrame_Text.pack(pady=20, padx=20)
        # Disable pagination controls
        self.prev_button.configure(state=tk.DISABLED)
        self.next_button.configure(state=tk.DISABLED)

    def update_error_message(self, message):
        self.DataFrame_Text.configure(text=message)
        self.DataFrame_Text.pack(pady=20, padx=20)

    def createTreeview(self):
        # Remove placeholder text
        self.DataFrame_Text.pack_forget()

        if self.Datatree:
            self.Datatree.destroy()

        columnsList = ['deviceId']
        for key in self.data_dict[0][self.queryDataType].keys():
            columnsList.append(key)
        columnsList.append('recordTime')

        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Times New Roman", 12))
        style.configure("Treeview", font=("Times New Roman", 12))
        style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])

        self.Datatree = ttk.Treeview(self.data_frame, columns=columnsList, show="headings", height=20, style="Treeview")

        for col in columnsList:
            self.Datatree.heading(col, text=col, anchor=tk.CENTER)
            self.Datatree.column(col, anchor=tk.CENTER)

        self.Datatree.pack(expand=True, fill=tk.BOTH)

        # Load initial page data
        self.update_page_info()

    def load_page_data(self):
        if not self.Datatree:
            return

        # Clear existing data
        self.Datatree.delete(*self.Datatree.get_children())

        start_index = self.current_page * self.rows_per_page
        end_index = start_index + self.rows_per_page
        page_data = self.data_dict[start_index:end_index]

        for entry in page_data:
            DataList = [entry.get('deviceId', 'N/A')]
            for key in entry[self.queryDataType].values():
                DataList.append(key)
            DataList.append(entry.get("recordTime", "N/A"))
            self.Datatree.insert("", tk.END, values=DataList)

        # Update page controls
        self.update_page_info()

    def update_page_info(self):
        total_pages = (len(self.data_dict) + self.rows_per_page - 1) // self.rows_per_page
        self.page_label.configure(text=f"Page {self.current_page + 1} of {total_pages}")

        # Enable/Disable buttons based on current page
        self.prev_button.configure(state=tk.NORMAL if self.current_page > 0 else tk.DISABLED)
        self.next_button.configure(state=tk.NORMAL if self.current_page < total_pages - 1 else tk.DISABLED)

    def show_previous_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.load_page_data()

    def show_next_page(self):
        total_pages = (len(self.data_dict) + self.rows_per_page - 1) // self.rows_per_page
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.load_page_data()

    def disable_controls(self):
        # Disable all interactive controls
        self.querySubmitBtn.configure(state=tk.DISABLED)
        self.export_button.configure(state=tk.DISABLED)
        self.data_combo.configure(state=tk.DISABLED)
        self.date_comboBox.configure(state=tk.DISABLED)

    def enable_controls(self):
        # Re-enable all interactive controls
        self.querySubmitBtn.configure(state=tk.NORMAL)
        self.export_button.configure(state=tk.NORMAL)
        self.data_combo.configure(state=tk.NORMAL)
        self.date_comboBox.configure(state=tk.NORMAL)

    def show_query_complete_message(self):
        # Show message box to notify the user that data loading is complete
        self.root.after(0, lambda: messagebox.showinfo("Query Complete", "Data loading complete. You can now interact with the window again."))

    def start_export_thread(self):
        export_thread = threading.Thread(target=self.export_data_to_csv, daemon=True)
        export_thread.start()

    def export_data_to_csv(self):
        if not self.Datatree:
            self.root.after(0, lambda: messagebox.showinfo("Info", "No data available to export."))
            return

        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialfile=f"data_{self.queryDataType}_{self.queryDate}.csv",
                title="Save as"
            )

            if not file_path:
                return

            columns = self.Datatree['columns']
            data = [self.Datatree.item(row_id)['values'] for row_id in self.Datatree.get_children()]

            if not data:
                self.root.after(0, lambda: messagebox.showinfo("Info", "No data available to export."))
                return

            df = pd.DataFrame(data, columns=columns)
            df.to_csv(file_path, index=False)
            self.root.after(1, lambda: messagebox.showinfo("Success", f"Data successfully exported to {file_path}"))

        except Exception as e:
            print(f"Error during export: {e}")
            self.root.after(1, lambda: messagebox.showerror("Error", f"Failed to export data: {e}"))
