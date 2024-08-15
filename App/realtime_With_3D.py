import customtkinter as ctk
from tkinter import ttk
import tkinter as tk
import trimesh
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
import random
import threading
import time
import cv2
from PIL import Image, ImageTk
import asyncio
from data_store import DataStore
from web_socket_client import WebSocketClient



class Realtime_ChartWindow:
    def __init__(self, root):
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

        #asyncio.run(websocket_client())

        # Create charts
        self.create_ypr_chart(self.yaw_frame)
        self.create_accel_chart(self.pitch_frame)
        self.create_gyro_chart(self.roll_frame)

        # Create car orientation plot
        self.create_car_orientation_plot(self.orientation_frame)

        self.websocket_client = WebSocketClient(uri="wss://begvn.home:9090/realtime/data", cert_path=r'C:\Users\HOB6HC\Code_Source\FOTA_Station_Up1-main\App\ca.crt')
        
        # Start WebSocket client in a separate thread
        self.websocket_thread = threading.Thread(target=self.websocket_client.start)
        self.websocket_thread.daemon = True
        self.websocket_thread.start()

        # Start data update threads
        self.update_data_thread = threading.Thread(target=self.run_event_loop_in_thread, daemon=True)
        self.update_car_orientation_thread = threading.Thread(target=self.update_car_orientation_continuously, daemon=True)
        self.update_data_thread.start()
        self.update_car_orientation_thread.start()

        # Start webcam feed
        self.create_webcam_feed(self.camera_frame)

        # Bind keyboard events
        self.data_window.bind("<KeyPress>", self.on_key_press)

    def on_key_press(self, event):
        # if event.keysym == "w":
        #     self.pitch = min(self.pitch + 5, 90)  # Limit pitch to 90 degrees
        # elif event.keysym == "s":
        #     self.pitch = max(self.pitch - 5, -90)  # Limit pitch to -90 degrees
        # elif event.keysym == "a":
        #     self.yaw = max(self.yaw - 5, -180)  # Wrap around the yaw
        # elif event.keysym == "d":
        #     self.yaw = min(self.yaw + 5, 180)  # Wrap around the yaw
        pass

    def create_layout(self):
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
        self.orientation_fig = plt.figure(figsize=(6, 3))
        self.orientation_ax = self.orientation_fig.add_subplot(111, projection='3d')

        # Load the car model
        self.car_scene = trimesh.load(r'C:\Users\HOB6HC\Code_Source\FOTA_Station_Up1-main\model\Porsche.obj')

        # Check if the scene contains geometries
        if isinstance(self.car_scene, trimesh.Scene):
            if len(self.car_scene.geometry) == 0:
                raise ValueError("The scene does not contain any geometries.")
            self.car_model = list(self.car_scene.geometry.values())[0]
        else:
            self.car_model = self.car_scene

        # Get the vertices and faces of the car model
        self.car_vertices = self.car_model.vertices
        self.car_faces = self.car_model.faces

        # Resize the car model to fit in the plot
        self.car_vertices -= self.car_vertices.mean(axis=0)
        scale_factor = 300 / np.max(self.car_vertices.ptp(axis=0))  # Scale to 300 units
        self.car_vertices *= scale_factor

        # Rotate the car model so its initial forward direction (Z-axis) points to the negative Y-axis
        # To do this, we need to rotate around the X-axis by 90 degrees and then reverse the direction by rotating 180 degrees around the Z-axis
        angle_x = np.radians(90)  # Rotate 90 degrees around the X-axis
        angle_z = np.radians(180)  # Rotate 180 degrees around the Z-axis

        rotation_matrix_x = np.array([
            [1, 0, 0],
            [0, np.cos(angle_x), -np.sin(angle_x)],
            [0, np.sin(angle_x), np.cos(angle_x)]
        ])

        rotation_matrix_z = np.array([
            [np.cos(angle_z), -np.sin(angle_z), 0],
            [np.sin(angle_z), np.cos(angle_z), 0],
            [0, 0, 1]
        ])

        # Combined rotation matrix
        combined_rotation_matrix = rotation_matrix_z @ rotation_matrix_x

        self.car_vertices = self.car_vertices @ combined_rotation_matrix.T

        # Create the Poly3DCollection object
        self.car_poly3d = Poly3DCollection(self.car_vertices[self.car_faces], alpha=.25, linewidths=1, edgecolors='none')
        self.orientation_ax.add_collection3d(self.car_poly3d)

        self.orientation_ax.set_xlabel('Yaw')
        self.orientation_ax.set_ylabel('Roll')
        self.orientation_ax.set_zlabel('Pitch')

        self.orientation_ax.set_xlim([-180, 180])
        self.orientation_ax.set_ylim([-180, 180])
        self.orientation_ax.set_zlim([-90, 90])

        self.orientation_canvas = FigureCanvasTkAgg(self.orientation_fig, master=frame)
        self.orientation_canvas.get_tk_widget().pack(side=tk.LEFT, fill=ctk.BOTH, expand=True)

        # Initialize battery status text
        self.battery_text = self.orientation_ax.text(
            180, 90, 360,  # Replace these with the actual coordinates where you want the text to appear
            f"Battery: {self.battery_status:.2f}%",
            color='black', fontsize=8, horizontalalignment='right', verticalalignment='top'
        )

        self.update_car_orientation()

    def update_battery_status(self):
        # Update the battery status
        self.battery_status = max(self.battery_status - random.uniform(0.1, 0.5), 0)  # Simulate battery drain and ensure it doesn't go below 0

        # Remove the old text
        for text in self.orientation_ax.texts:
            text.remove()

        # Format the battery status to show only two decimal places
        formatted_battery_status = f"Battery: {self.battery_status:.2f}%"

        # Add the new text
        self.battery_text = self.orientation_ax.text(
            180, 90, 360,  # Position it at the top-right corner
            f"Battery: {formatted_battery_status}%",
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

        # Combined rotation matrix
        rotation_matrix = yaw_matrix @ pitch_matrix @ roll_matrix

        # Apply rotation to car vertices
        rotated_vertices = self.car_vertices @ rotation_matrix.T
        self.car_poly3d.set_verts(rotated_vertices[self.car_faces])

        # Redraw the plot
        self.orientation_canvas.draw()

    def update_car_orientation_continuously(self):
        while True:
            self.update_car_orientation()
            self.update_battery_status()
            #time.sleep(0.1)

    def create_webcam_feed(self, frame):
        self.cap = cv2.VideoCapture(0)
        self.video_label = ctk.CTkLabel(frame)
        self.video_label.pack()

        self.update_video_feed()

    def update_video_feed(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)

        self.video_label.after(10, self.update_video_feed)

    def create_ypr_chart(self, frame):
        fig, ax = plt.subplots(3, 1, figsize=(5, 8))

        self.yaw_line, = ax[0].plot([], [], label="Yaw")
        self.pitch_line, = ax[1].plot([], [], label="Pitch")
        self.roll_line, = ax[2].plot([], [], label="Roll")

        ax[0].set_ylim(-180, 180)
        ax[1].set_ylim(-90, 90)
        ax[2].set_ylim(-180, 180)

        for a in ax:
            a.set_xlim(0, 50)
            a.legend()
            a.grid(True)

        self.ypr_fig = fig
        self.ypr_ax = ax

        self.ypr_canvas = FigureCanvasTkAgg(self.ypr_fig, master=frame)
        self.ypr_canvas.get_tk_widget().pack(side=tk.LEFT, fill=ctk.BOTH, expand=True)

    def create_accel_chart(self, frame):
        fig, ax = plt.subplots(3, 1, figsize=(5, 8))

        self.accel_x_line, = ax[0].plot([], [], label="Accel X")
        self.accel_y_line, = ax[1].plot([], [], label="Accel Y")
        self.accel_z_line, = ax[2].plot([], [], label="Accel Z")

        ax[0].set_ylim(-1000, 1000)
        ax[1].set_ylim(-1000, 1000)
        ax[2].set_ylim(-1000, 1000)

        for a in ax:
            a.set_xlim(0, 50)
            a.legend()
            a.grid(True)

        self.accel_fig = fig
        self.accel_ax = ax

        self.accel_canvas = FigureCanvasTkAgg(self.accel_fig, master=frame)
        self.accel_canvas.get_tk_widget().pack(side=tk.LEFT, fill=ctk.BOTH, expand=True)

    def create_gyro_chart(self, frame):
        fig, ax = plt.subplots(3, 1, figsize=(5, 8))

        self.gyro_x_line, = ax[0].plot([], [], label="Gyro X")
        self.gyro_y_line, = ax[1].plot([], [], label="Gyro Y")
        self.gyro_z_line, = ax[2].plot([], [], label="Gyro Z")

        ax[0].set_ylim(-500, 500)
        ax[1].set_ylim(-500, 500)
        ax[2].set_ylim(-500, 500)

        for a in ax:
            a.set_xlim(0, 50)
            a.legend()
            a.grid(True)

        self.gyro_fig = fig
        self.gyro_ax = ax

        self.gyro_canvas = FigureCanvasTkAgg(self.gyro_fig, master=frame)
        self.gyro_canvas.get_tk_widget().pack(side=tk.LEFT, fill=ctk.BOTH, expand=True)

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

            #time.sleep(1)  # Adjust the sleep interval as needed

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

    def __del__(self):
        self.cap.release()

if __name__ == "__main__":
    root = ctk.CTk()
    app = Realtime_ChartWindow(root)
    root.mainloop()
