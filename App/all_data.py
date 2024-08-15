import tkinter as tk
from tkinter import ttk
import pymongo
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime
import matplotlib.dates as mdates

class AllData_ChartWindow(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.grid(row=0, column=0, sticky='nsew')
        
        # Create and configure the notebook (tabbed interface)
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=0, column=0, sticky='nsew')
        
        # Create tabs for each data type
        self.yaw_tab = ttk.Frame(self.notebook)
        self.pitch_tab = ttk.Frame(self.notebook)
        self.roll_tab = ttk.Frame(self.notebook)
        self.accelerometer_tab = ttk.Frame(self.notebook)
        self.gyroscope_tab = ttk.Frame(self.notebook)
        self.battery_tab = ttk.Frame(self.notebook)
        self.tree_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.yaw_tab, text='Yaw')
        self.notebook.add(self.pitch_tab, text='Pitch')
        self.notebook.add(self.roll_tab, text='Roll')
        self.notebook.add(self.accelerometer_tab, text='Accelerometer')
        self.notebook.add(self.gyroscope_tab, text='Gyroscope')
        self.notebook.add(self.battery_tab, text='Battery')
        self.notebook.add(self.tree_tab, text='Temperature & Gesture')
        
        # Add a placeholder for matplotlib figures
        self.yaw_figure, self.yaw_ax = plt.subplots()
        self.pitch_figure, self.pitch_ax = plt.subplots()
        self.roll_figure, self.roll_ax = plt.subplots()
        self.accelerometer_figure, self.accelerometer_ax = plt.subplots()
        self.gyroscope_figure, self.gyroscope_ax = plt.subplots()
        self.battery_figure, self.battery_ax = plt.subplots()
        
        # Create canvas for each figure
        self.yaw_canvas = FigureCanvasTkAgg(self.yaw_figure, self.yaw_tab)
        self.pitch_canvas = FigureCanvasTkAgg(self.pitch_figure, self.pitch_tab)
        self.roll_canvas = FigureCanvasTkAgg(self.roll_figure, self.roll_tab)
        self.accelerometer_canvas = FigureCanvasTkAgg(self.accelerometer_figure, self.accelerometer_tab)
        self.gyroscope_canvas = FigureCanvasTkAgg(self.gyroscope_figure, self.gyroscope_tab)
        self.battery_canvas = FigureCanvasTkAgg(self.battery_figure, self.battery_tab)
        
        self.yaw_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.pitch_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.roll_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.accelerometer_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.gyroscope_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.battery_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Create tree view for temperature and gesture
        self.tree = ttk.Treeview(self.tree_tab, columns=("Type", "Value"), show='headings')
        self.tree.heading("Type", text="Type")
        self.tree.heading("Value", text="Value")
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Fetch and plot data
        self.plot_data()

    def plot_data(self):
        # Connect to MongoDB
        client = pymongo.MongoClient("mongodb://localhost:27017/")
        db = client['your_database_name']  # Replace with your actual database name
        collection = db['your_collection_name']  # Replace with your actual collection name
        
        # Fetch data from MongoDB
        data = list(collection.find())
        
        # Initialize data containers
        yaw_data = []
        pitch_data = []
        roll_data = []
        accelerometer_data = []
        gyroscope_data = []
        battery_data = []
        temperature_data = []
        gesture_data = []
        
        for document in data:
            timestamp = datetime.fromisoformat(document['timestamp'])  # Adjust according to your timestamp format
            
            # Populate data lists
            if 'yaw' in document:
                yaw_data.append((timestamp, document['yaw']))
            if 'pitch' in document:
                pitch_data.append((timestamp, document['pitch']))
            if 'roll' in document:
                roll_data.append((timestamp, document['roll']))
            if 'accelerometer' in document:
                accelerometer_data.append((timestamp, document['accelerometer']))
            if 'gyroscope' in document:
                gyroscope_data.append((timestamp, document['gyroscope']))
            if 'battery' in document:
                battery_data.append((timestamp, document['battery']))
            if 'temperature' in document:
                temperature_data.append((document['temperature_type'], document['temperature_value']))
            if 'gesture' in document:
                gesture_data.append((document['gesture_type'], document['gesture_value']))
        
        # Plot each data type
        self.plot_chart(self.yaw_ax, yaw_data, "Yaw Data", "Time", "Yaw")
        self.plot_chart(self.pitch_ax, pitch_data, "Pitch Data", "Time", "Pitch")
        self.plot_chart(self.roll_ax, roll_data, "Roll Data", "Time", "Roll")
        self.plot_chart(self.accelerometer_ax, accelerometer_data, "Accelerometer Data", "Time", "Accelerometer")
        self.plot_chart(self.gyroscope_ax, gyroscope_data, "Gyroscope Data", "Time", "Gyroscope")
        self.plot_chart(self.battery_ax, battery_data, "Battery Data", "Time", "Battery")
        
        # Update tree view for temperature and gesture
        self.tree.delete(*self.tree.get_children())
        for temp_type, temp_value in temperature_data:
            self.tree.insert("", tk.END, values=(f"Temperature: {temp_type}", temp_value))
        for gesture_type, gesture_value in gesture_data:
            self.tree.insert("", tk.END, values=(f"Gesture: {gesture_type}", gesture_value))

        # Refresh the plots
        self.yaw_canvas.draw()
        self.pitch_canvas.draw()
        self.roll_canvas.draw()
        self.accelerometer_canvas.draw()
        self.gyroscope_canvas.draw()
        self.battery_canvas.draw()

    def plot_chart(self, ax, data, title, xlabel, ylabel):
        # Clear previous plot
        ax.clear()
        
        if not data:
            return
        
        # Unpack data
        timestamps, values = zip(*data)
        
        # Plot data
        ax.plot(timestamps, values, marker='o', linestyle='-')
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M:%S'))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
        ax.tick_params(axis='x', rotation=45)