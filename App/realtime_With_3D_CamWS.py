# main_application.py
import customtkinter as ctk
from tkinter import ttk
import tkinter as tk
import trimesh
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
import threading
import time
import random
import cv2
from PIL import Image, ImageTk
from get_Img_new import WebSocketCameraClient
from data_store import DataStore
from web_socket_client import WebSocketClient
import asyncio
from utils.Cloud_COM.Cloud_COM import Cloud_COM

class Realtime_ChartWindow:
    def __init__(self, root,cloudCOM: Cloud_COM):
        self.root = root
        self.data_window = ctk.CTkToplevel(self.root)
        self.data_window.title("View Real-time Data")
        self.data_window.geometry("1200x900")

        self.create_layout()

        # Initialize yaw, pitch, roll, accelerometer, and gyroscope
        self.yaw = 0
        self.pitch = 0
        self.roll = 0
        self.accel_x = 0
        self.accel_y = 0
        self.accel_z = 0
        self.gyro_x = 0
        self.gyro_y = 0
        self.gyro_z = 0
        self.battery_status = 100
        self.temperature_status = 0

        self.arrow = None

        # Track the latest 50 changes
        self.yaw_history = []
        self.pitch_history = []
        self.roll_history = []
        self.accel_x_history = []
        self.accel_y_history = []
        self.accel_z_history = []
        self.gyro_x_history = []
        self.gyro_y_history = []
        self.gyro_z_history = []
        
        self.Cloud_COM = cloudCOM
        # Create charts
        self.create_ypr_chart(self.yaw_frame)
        self.create_accel_chart(self.pitch_frame)
        self.create_gyro_chart(self.roll_frame)

        # Create car orientation plot
        self.create_car_orientation_plot(self.orientation_frame)

        self.websocket_client = WebSocketClient(uri="wss://begvn.home:9090/realtime/data", cert_path=r'C:\Users\HOB6HC\Code_Source\FOTA_Station\App\ca.crt')
        
        # Start WebSocket client in a separate thread
        self.websocket_thread = threading.Thread(target=self.websocket_client.start)
        self.websocket_thread.daemon = True
        self.websocket_thread.start()

        # Start data update threads
        self.update_data_thread = threading.Thread(target=self.run_event_loop_in_thread, daemon=True)
        self.update_car_orientation_thread = threading.Thread(target=self.update_car_orientation_continuously, daemon=True)
        self.update_data_thread.start()
        self.update_car_orientation_thread.start()

        # Initialize WebSocket client
        self.websocket_client_video = WebSocketCameraClient("wss://begvn.home:9090/realtime/streaming", capath=r'C:\Users\HOB6HC\Code_Source\FOTA_Station\App\ca.crt')
        self.websocket_thread = threading.Thread(target=self.run_websocket_client, daemon=True)
        self.websocket_thread.start()

        # Start webcam feed
        self.create_webcam_feed(self.camera_frame)
        self.Cloud_COM.MQTT_Connect()
        # Bind keyboard events
        self.data_window.bind("<KeyPress>", self.on_key_press)

    def stop(self):
        self.websocket_client.stop()
        self.websocket_client_video.stop()
        print("Stop ws")

    def run_websocket_client(self):
        asyncio.run(self.websocket_client_video.start())

    def on_key_press(self, event):
        print('event')
        if event.keysym == "w":
            status =self.Cloud_COM.MQTT_SendControl("w")
            print(status)
        if event.keysym == "a":
            status =self.Cloud_COM.MQTT_SendControl("a")
            print(status)
        if event.keysym == "s":
            status =self.Cloud_COM.MQTT_SendControl("s")
            print(status)
        if event.keysym == "d":
            status =self.Cloud_COM.MQTT_SendControl("d")
            print(status)
        if event.keysym == "q":
            status =self.Cloud_COM.MQTT_SendControl("q")
            print(status)
        if event.keysym == "c":
            status =self.Cloud_COM.MQTT_SendControl("c")
            print(status)
        # elif event.keysym == "s":
        #     self.pitch = max(self.pitch - 5, -90)  # Limit pitch to -90 degrees
        # elif event.keysym == "a":
        #     self.yaw = max(self.yaw - 5, -180)  # Wrap around the yaw
        # elif event.keysym == "d":
        #     self.yaw = min(self.yaw + 5, 180)  # Wrap around the yaw
        pass
    def create_layout(self):
        #separate frame for charts, car orientation, camera
        self.camera_frame = ctk.CTkFrame(self.data_window, width=800, height=300)
        self.camera_frame.grid(row=0, column=0, columnspan=2, sticky="nsew")

        self.orientation_frame = ctk.CTkFrame(self.data_window, width=400, height=300)
        self.orientation_frame.grid(row=0, column=2, sticky="nsew")

        self.yaw_frame = ctk.CTkFrame(self.data_window, width=400, height=600)
        self.yaw_frame.grid(row=1, column=0, sticky="nsew")

        self.pitch_frame = ctk.CTkFrame(self.data_window, width=400, height=600)
        self.pitch_frame.grid(row=1, column=1, sticky="nsew")

        self.roll_frame = ctk.CTkFrame(self.data_window, width=400, height=600)
        self.roll_frame.grid(row=1, column=2, sticky="nsew")

        self.data_window.grid_rowconfigure(0, weight=1)
        self.data_window.grid_rowconfigure(1, weight=1)
        self.data_window.grid_columnconfigure(0, weight=1)
        self.data_window.grid_columnconfigure(1, weight=1)
        self.data_window.grid_columnconfigure(2, weight=1)

    def create_car_orientation_plot(self, frame):
        # Initialize the figure for the 3D plot, setting the size to 6x3 inches
        self.orientation_fig = plt.figure(figsize=(6, 3))
        # Create a 3D subplot within the figure
        self.orientation_ax = self.orientation_fig.add_subplot(111, projection='3d')

        # Define the vertices of the block (representing the car), with coordinates in 3D space
        self.block_vertices = np.array([
            [-1, -1, -1],  # Bottom-left-back corner
            [1, -1, -1],   # Bottom-right-back corner
            [1, 1, -1],    # Top-right-back corner
            [-1, 1, -1],   # Top-left-back corner
            [-1, -1, 1],   # Bottom-left-front corner
            [1, -1, 1],    # Bottom-right-front corner
            [1, 1, 1],     # Top-right-front corner
            [-1, 1, 1]     # Top-left-front corner
        ])
        
        # Define the faces of the block by specifying which vertices make up each face
        self.block_faces = np.array([
            [0, 1, 2, 3],  # Back face
            [4, 5, 6, 7],  # Front face
            [0, 1, 5, 4],  # Bottom face
            [2, 3, 7, 6],  # Top face
            [0, 3, 7, 4],  # Left face
            [1, 2, 6, 5]   # Right face
        ])

        # Scale the block to a larger size for better visibility
        self.block_vertices *= 100  # Multiply coordinates by 100 to enlarge the block

        # Create 3D polygons for the block faces using the vertex coordinates
        self.block_faces_3d = [[self.block_vertices[vertice] for vertice in face] for face in self.block_faces]
        # Create a Poly3DCollection object to render the block with transparency and edge outlines
        self.block_poly3d = Poly3DCollection(self.block_faces_3d, alpha=.25, linewidths=1, edgecolors='k')
        # Add the block to the 3D axis for rendering
        self.orientation_ax.add_collection3d(self.block_poly3d)

        # (Optional) Draw arrows to indicate the car's forward direction, yaw, pitch, and roll axes.
        # Currently commented out.
        # self.draw_arrow([0, 0, 0], [0, -50, 0], 'r', 'Forward')   # X-axis arrow

        # Label the axes to represent yaw, pitch, and roll
        self.orientation_ax.set_xlabel('Yaw')
        self.orientation_ax.set_ylabel('Pitch')
        self.orientation_ax.set_zlabel('Roll')

        # Set the axis limits to define the range of rotation values for yaw, pitch, and roll
        self.orientation_ax.set_xlim([-180, 180])
        self.orientation_ax.set_ylim([-180, 180])
        self.orientation_ax.set_zlim([-180, 180])

        # Embed the 3D plot into the provided frame (Tkinter widget) using a canvas
        self.orientation_canvas = FigureCanvasTkAgg(self.orientation_fig, master=frame)
        self.orientation_canvas.get_tk_widget().pack(side=tk.LEFT, fill=ctk.BOTH, expand=True)

        # Initialize text display for battery status in the 3D plot
        self.battery_text = self.orientation_ax.text(
            180, 0, 360,  # Place text at a corner of the 3D plot
            f"Battery: {self.battery_status:.2f}%",  # Display the battery status percentage
            color='black', fontsize=8, horizontalalignment='right', verticalalignment='top'
        )

        # Initialize text display for temperature status in the 3D plot
        self.temp_text = self.orientation_ax.text(
            180, 0, 320,  # Place text slightly below the battery status
            f"Temperature: {self.temperature_status:.2f}%",  # Display the temperature status
            color='black', fontsize=8, horizontalalignment='right', verticalalignment='top'
        )

        # Call the method to update the car's orientation based on real-time sensor data
        self.update_car_orientation()
        
    def draw_arrow(self, start, direction, color, label, rotation_matrix):
        # Remove the previous arrow if it exists
        if self.arrow is not None:
            self.arrow.remove()
        
        # Calculate the length of the block's diagonal
        block_diagonal_length = np.sqrt((self.block_vertices**2).sum(axis=1).max())
        
        # Scale the direction vector to be 1.5 times the block's diagonal length
        scaled_direction = np.array(direction) * 1.5 * block_diagonal_length / np.linalg.norm(direction)
        
        # Apply the rotation matrix to the direction vector
        rotated_direction = scaled_direction @ rotation_matrix.T
        
        # Draw the new arrow
        self.arrow = self.orientation_ax.quiver(*start, *rotated_direction, color=color, length=np.linalg.norm(rotated_direction), normalize=True)
        
        # Calculate the midpoint for labeling
        mid_point = np.array(start) + rotated_direction / 2
        self.orientation_ax.text(mid_point[0], mid_point[1], mid_point[2], label, color=color, fontsize=10)

    def update_battery_status(self):
        # Update the battery status
        dataStore = DataStore()
        self.battery_status = dataStore.battery_status
        self.temperature_status = dataStore.battery_temp

        # Remove the old text
        for text in self.orientation_ax.texts:
            text.remove()

        # Format the battery status to show only two decimal places
        formatted_battery_status = f"{self.battery_status:.2f}%"
        formatted_temp_status = f"{self.temperature_status:.2f}%"

        # Add the new text
        self.battery_text = self.orientation_ax.text(
            180, 90, 360,  # Position it at the top-right corner
            f"Battery: {formatted_battery_status}%",
            color='black', fontsize=8, horizontalalignment='right', verticalalignment='top'
        )

        # Add the new text
        self.battery_text = self.orientation_ax.text(
            180, 90, 320,  # Position it at the top-right corner
            f"Temperature: {formatted_temp_status}%",
            color='black', fontsize=8, horizontalalignment='right', verticalalignment='top'
        )

        self.orientation_canvas.draw()

    def update_car_orientation(self):
        # Rotation matrices for yaw, pitch, roll
        roll_matrix = np.array([
            [np.cos(np.radians(self.roll)), 0, np.sin(np.radians(self.roll))],
            [0, 1, 0],
            [-np.sin(np.radians(self.roll)), 0, np.cos(np.radians(self.roll))]
        ])
        
        pitch_matrix = np.array([
            [1, 0, 0],
            [0, np.cos(np.radians(self.pitch)), -np.sin(np.radians(self.pitch))],
            [0, np.sin(np.radians(self.pitch)), np.cos(np.radians(self.pitch))]
        ])
        
        yaw_matrix = np.array([
            [np.cos(np.radians(self.yaw)), -np.sin(np.radians(self.yaw)), 0],
            [np.sin(np.radians(self.yaw)), np.cos(np.radians(self.yaw)), 0],
            [0, 0, 1]
        ])

        # Combine the rotation matrices
        rotation_matrix = yaw_matrix @ pitch_matrix @ roll_matrix

        # Apply the rotations to the block's vertices
        rotated_vertices = self.block_vertices @ rotation_matrix.T

        # Update the block faces with rotated vertices
        rotated_faces_3d = [[rotated_vertices[vertice] for vertice in face] for face in self.block_faces]
        self.block_poly3d.set_verts(rotated_faces_3d)

        self.draw_arrow([0, 0, 0], [0, -1, 0], 'r', '', rotation_matrix)
 

        # Redraw the canvas to reflect changes
        self.orientation_canvas.draw()

    def update_car_orientation_continuously(self):
        while True:
            self.update_car_orientation()
            self.update_battery_status()
            #time.sleep(0.1)

    def create_ypr_chart(self, frame):
        # Create a new figure and a set of subplots with 3 rows and 1 column
        fig, ax = plt.subplots(3, 1, figsize=(5, 8))

        # Initialize lines for Yaw, Pitch, and Roll data, starting with empty data
        self.yaw_line, = ax[0].plot([], [], label="Yaw")
        self.pitch_line, = ax[1].plot([], [], label="Pitch")
        self.roll_line, = ax[2].plot([], [], label="Roll")

        # Set the y-axis limits for each subplot
        ax[0].set_ylim(-180, 180)  # Yaw range
        ax[1].set_ylim(-90, 90)    # Pitch range
        ax[2].set_ylim(-180, 180)  # Roll range

        # Configure each subplot
        for a in ax:
            a.set_xlim(0, 50)  # Set x-axis limits (time or index range)
            a.legend()         # Add legend to identify the lines
            a.grid(True)       # Add grid lines for better readability

        # Store figure and axes for later use
        self.ypr_fig = fig
        self.ypr_ax = ax

        # Embed the figure into a Tkinter frame
        self.ypr_canvas = FigureCanvasTkAgg(self.ypr_fig, master=frame)
        self.ypr_canvas.get_tk_widget().pack(side=tk.LEFT, fill=ctk.BOTH, expand=True)

    def create_accel_chart(self, frame):
        # Create a new figure and a set of subplots with 3 rows and 1 column
        fig, ax = plt.subplots(3, 1, figsize=(5, 8))

        # Initialize lines for Acceleration X, Y, and Z data, starting with empty data
        self.accel_x_line, = ax[0].plot([], [], label="Accel X")
        self.accel_y_line, = ax[1].plot([], [], label="Accel Y")
        self.accel_z_line, = ax[2].plot([], [], label="Accel Z")

        # Set the y-axis limits for each subplot
        ax[0].set_ylim(-1000, 1000)  # Acceleration X range
        ax[1].set_ylim(-1000, 1000)  # Acceleration Y range
        ax[2].set_ylim(-1000, 1000)  # Acceleration Z range

        # Configure each subplot
        for a in ax:
            a.set_xlim(0, 50)  # Set x-axis limits (time or index range)
            a.legend()         # Add legend to identify the lines
            a.grid(True)       # Add grid lines for better readability

        # Store figure and axes for later use
        self.accel_fig = fig
        self.accel_ax = ax

        # Embed the figure into a Tkinter frame
        self.accel_canvas = FigureCanvasTkAgg(self.accel_fig, master=frame)
        self.accel_canvas.get_tk_widget().pack(side=tk.LEFT, fill=ctk.BOTH, expand=True)

    def create_gyro_chart(self, frame):
        # Create a new figure and a set of subplots with 3 rows and 1 column
        fig, ax = plt.subplots(3, 1, figsize=(5, 8))

        # Initialize lines for Gyroscope X, Y, and Z data, starting with empty data
        self.gyro_x_line, = ax[0].plot([], [], label="Gyro X")
        self.gyro_y_line, = ax[1].plot([], [], label="Gyro Y")
        self.gyro_z_line, = ax[2].plot([], [], label="Gyro Z")

        # Set the y-axis limits for each subplot
        ax[0].set_ylim(-500, 500)  # Gyroscope X range
        ax[1].set_ylim(-500, 500)  # Gyroscope Y range
        ax[2].set_ylim(-500, 500)  # Gyroscope Z range

        # Configure each subplot
        for a in ax:
            a.set_xlim(0, 50)  # Set x-axis limits (time or index range)
            a.legend()         # Add legend to identify the lines
            a.grid(True)       # Add grid lines for better readability

        # Store figure and axes for later use
        self.gyro_fig = fig
        self.gyro_ax = ax

        # Embed the figure into a Tkinter frame
        self.gyro_canvas = FigureCanvasTkAgg(self.gyro_fig, master=frame)
        self.gyro_canvas.get_tk_widget().pack(side=tk.LEFT, fill=ctk.BOTH, expand=True)

    def create_webcam_feed(self, frame):
        self.webcam_label = ctk.CTkLabel(frame)
        self.webcam_label.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.update_webcam_feed()

    def update_webcam_feed(self):
        frame = self.websocket_client_video.get_frame()
        if frame is not None:
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(image)
            image = ImageTk.PhotoImage(image)
            self.webcam_label.configure(image=image)
            self.webcam_label.image = image

        self.root.after(10, self.update_webcam_feed)  # Update every 100 ms

    async def update_data(self):
        
        while True:
            data_store = DataStore()
            
            # Use values from DataStore
            self.yaw = data_store.yaw
            self.pitch = data_store.pitch
            self.roll = data_store.roll
            self.accel_x = data_store.accel_x
            self.accel_y = data_store.accel_y
            self.accel_z = data_store.accel_z
            self.gyro_x = data_store.gyro_x
            self.gyro_y = data_store.gyro_y
            self.gyro_z = data_store.gyro_z

            # Append to history
            self.yaw_history.append(self.yaw)
            self.pitch_history.append(self.pitch)
            self.roll_history.append(self.roll)
            self.accel_x_history.append(self.accel_x)
            self.accel_y_history.append(self.accel_y)
            self.accel_z_history.append(self.accel_z)
            self.gyro_x_history.append(self.gyro_x)
            self.gyro_y_history.append(self.gyro_y)
            self.gyro_z_history.append(self.gyro_z)

            # Maintain only the latest 50 records
            if len(self.yaw_history) > 50:
                self.yaw_history.pop(0)
            if len(self.pitch_history) > 50:
                self.pitch_history.pop(0)
            if len(self.roll_history) > 50:
                self.roll_history.pop(0)
            if len(self.accel_x_history) > 50:
                self.accel_x_history.pop(0)
            if len(self.accel_y_history) > 50:
                self.accel_y_history.pop(0)
            if len(self.accel_z_history) > 50:
                self.accel_z_history.pop(0)
            if len(self.gyro_x_history) > 50:
                self.gyro_x_history.pop(0)
            if len(self.gyro_y_history) > 50:
                self.gyro_y_history.pop(0)
            if len(self.gyro_z_history) > 50:
                self.gyro_z_history.pop(0)

            # Update charts
            self.update_ypr_chart()
            self.update_accel_chart()
            self.update_gyro_chart()

            # time.sleep(1)  # Adjust the sleep interval as needed
    def run_event_loop_in_thread(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.update_data())

    def update_ypr_chart(self):
        self.yaw_history.append(self.yaw)
        self.pitch_history.append(self.pitch)
        self.roll_history.append(self.roll)

        if len(self.yaw_history) > 50:
            self.yaw_history.pop(0)
            self.pitch_history.pop(0)
            self.roll_history.pop(0)

        self.yaw_line.set_data(range(len(self.yaw_history)), self.yaw_history)
        self.pitch_line.set_data(range(len(self.pitch_history)), self.pitch_history)
        self.roll_line.set_data(range(len(self.roll_history)), self.roll_history)

        for ax in self.ypr_ax:
            ax.set_xlim(0, len(self.yaw_history))

        self.ypr_canvas.draw()

    def update_accel_chart(self):
        self.accel_x_history.append(self.accel_x)
        self.accel_y_history.append(self.accel_y)
        self.accel_z_history.append(self.accel_z)

        if len(self.accel_x_history) > 50:
            self.accel_x_history.pop(0)
            self.accel_y_history.pop(0)
            self.accel_z_history.pop(0)

        self.accel_x_line.set_data(range(len(self.accel_x_history)), self.accel_x_history)
        self.accel_y_line.set_data(range(len(self.accel_y_history)), self.accel_y_history)
        self.accel_z_line.set_data(range(len(self.accel_z_history)), self.accel_z_history)

        for ax in self.accel_ax:
            ax.set_xlim(0, len(self.accel_x_history))

        self.accel_canvas.draw()

    def update_gyro_chart(self):
        self.gyro_x_history.append(self.gyro_x)
        self.gyro_y_history.append(self.gyro_y)
        self.gyro_z_history.append(self.gyro_z)

        if len(self.gyro_x_history) > 50:
            self.gyro_x_history.pop(0)
            self.gyro_y_history.pop(0)
            self.gyro_z_history.pop(0)

        self.gyro_x_line.set_data(range(len(self.gyro_x_history)), self.gyro_x_history)
        self.gyro_y_line.set_data(range(len(self.gyro_y_history)), self.gyro_y_history)
        self.gyro_z_line.set_data(range(len(self.gyro_z_history)), self.gyro_z_history)

        for ax in self.gyro_ax:
            ax.set_xlim(0, len(self.gyro_x_history))

        self.gyro_canvas.draw()
    

if __name__ == "__main__":
    root = ctk.CTk()
    app = Realtime_ChartWindow(root)
    root.mainloop()
