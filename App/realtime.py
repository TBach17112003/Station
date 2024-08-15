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

        self.arrow = None  # Add this line to initialize the arrow attribute

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

        # Create charts
        self.create_ypr_chart(self.yaw_frame)
        self.create_accel_chart(self.pitch_frame)
        self.create_gyro_chart(self.roll_frame)

        # Create car orientation plot
        self.create_car_orientation_plot(self.orientation_frame)

        # Start data update thread
        self.update_data_thread = threading.Thread(target=self.update_data, daemon=True)
        self.update_data_thread.start()

        # Start webcam feed
        self.create_webcam_feed(self.camera_frame)

        # Bind keyboard events
        self.data_window.bind("<KeyPress>", self.on_key_press)

    def on_key_press(self, event):
        if event.keysym == "w":
            self.pitch = min(self.pitch + 5, 90)  # Limit pitch to 90 degrees
        elif event.keysym == "s":
            self.pitch = max(self.pitch - 5, -90)  # Limit pitch to -90 degrees
        elif event.keysym == "a":
            self.yaw = max(self.yaw - 5, -180)  # Wrap around the yaw
        elif event.keysym == "d":
            self.yaw = min(self.yaw + 5, 180)  # Wrap around the yaw

        

    def create_layout(self):
        self.camera_frame = ctk.CTkFrame(self.data_window, width=800, height=300)
        self.camera_frame.grid(row=0, column=0, columnspan = 2, sticky="nsew")

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


    
    # def create_car_orientation_plot(self, frame):
    
    #     self.orientation_fig = plt.figure(figsize=(6, 3))
    #     self.orientation_ax = self.orientation_fig.add_subplot(111, projection='3d')

    #     # Load the car model
    #     self.car_scene = trimesh.load(r'C:\Users\HOB6HC\Code_Source\FOTA_Station_Up1-main\model\Porsche.obj')

    #     # Check if the scene contains geometries
    #     if isinstance(self.car_scene, trimesh.Scene):
    #         if len(self.car_scene.geometry) == 0:
    #             raise ValueError("The scene does not contain any geometries.")
    #         self.car_model = list(self.car_scene.geometry.values())[0]
    #     else:
    #         self.car_model = self.car_scene

    #     # Get the vertices and faces of the car model
    #     self.car_vertices = self.car_model.vertices
    #     self.car_faces = self.car_model.faces

    #     # Resize the car model to fit in the plot
    #     self.car_vertices -= self.car_vertices.mean(axis=0)
    #     scale_factor = 300 / np.max(self.car_vertices.ptp(axis=0))  # Scale to 300 units
    #     self.car_vertices *= scale_factor

    #     # Rotate the car model so its initial forward direction (Z-axis) points to the negative Y-axis
    #     # To do this, we need to rotate around the X-axis by 90 degrees and then reverse the direction by rotating 180 degrees around the Z-axis
    #     angle_x = np.radians(90)  # Rotate 90 degrees around the X-axis
    #     angle_z = np.radians(180) # Rotate 180 degrees around the Z-axis

    #     rotation_matrix_x = np.array([
    #         [1, 0, 0],
    #         [0, np.cos(angle_x), -np.sin(angle_x)],
    #         [0, np.sin(angle_x), np.cos(angle_x)]
    #     ])

    #     rotation_matrix_z = np.array([
    #         [np.cos(angle_z), -np.sin(angle_z), 0],
    #         [np.sin(angle_z), np.cos(angle_z), 0],
    #         [0, 0, 1]
    #     ])

    #     # Combined rotation matrix
    #     combined_rotation_matrix = rotation_matrix_z @ rotation_matrix_x

    #     self.car_vertices = self.car_vertices @ combined_rotation_matrix.T

    #     # Create the Poly3DCollection object
    #     self.car_poly3d = Poly3DCollection(self.car_vertices[self.car_faces], alpha=.25, linewidths=1, edgecolors='none')
    #     self.orientation_ax.add_collection3d(self.car_poly3d)

    #     self.orientation_ax.set_xlabel('Yaw')
    #     self.orientation_ax.set_ylabel('Roll')
    #     self.orientation_ax.set_zlabel('Pitch')

    #     self.orientation_ax.set_xlim([-180, 180])
    #     self.orientation_ax.set_ylim([-180, 180])
    #     self.orientation_ax.set_zlim([-90, 90])

    #     self.orientation_canvas = FigureCanvasTkAgg(self.orientation_fig, master=frame)
    #     self.orientation_canvas.get_tk_widget().pack(side=tk.LEFT, fill=ctk.BOTH, expand=True)

    #     # Initialize battery status text
    #     self.battery_text = self.orientation_ax.text(
    #         180, 90, 360,  # Replace these with the actual coordinates where you want the text to appear
    #         f"Battery: {self.battery_status:.2f}%",
    #         color='black', fontsize=8, horizontalalignment='right', verticalalignment='top'
    #     )

    #     self.update_car_orientation()

    def create_car_orientation_plot(self, frame):
        self.orientation_fig = plt.figure(figsize=(6, 3))
        self.orientation_ax = self.orientation_fig.add_subplot(111, projection='3d')

        # Define block vertices and faces
        self.block_vertices = np.array([
            [-1, -1, -1],
            [1, -1, -1],
            [1, 1, -1],
            [-1, 1, -1],
            [-1, -1, 1],
            [1, -1, 1],
            [1, 1, 1],
            [-1, 1, 1]
        ])
        self.block_faces = np.array([
            [0, 1, 2, 3],
            [4, 5, 6, 7],
            [0, 1, 5, 4],
            [2, 3, 7, 6],
            [0, 3, 7, 4],
            [1, 2, 6, 5]
        ])

        # Scale and center the block
        self.block_vertices *= 45  # Scale the block size

        # Create block faces
        self.block_faces_3d = [[self.block_vertices[vertice] for vertice in face] for face in self.block_faces]
        self.block_poly3d = Poly3DCollection(self.block_faces_3d, alpha=.25, linewidths=1, edgecolors='k')
        self.orientation_ax.add_collection3d(self.block_poly3d)

        # Draw arrows for yaw, pitch, roll
        #self.draw_arrow([0, 0, 0], [0, -50, 0], 'r', 'Forward')   # X-axis arrow
        

        self.orientation_ax.set_xlabel('Yaw')
        self.orientation_ax.set_ylabel('Pitch')
        self.orientation_ax.set_zlabel('Roll')

        self.orientation_ax.set_xlim([-180, 180])
        self.orientation_ax.set_ylim([-180, 180])
        self.orientation_ax.set_zlim([-180, 180])

        self.orientation_canvas = FigureCanvasTkAgg(self.orientation_fig, master=frame)
        self.orientation_canvas.get_tk_widget().pack(side=tk.LEFT, fill=ctk.BOTH, expand=True)

        # Initialize battery status text
        self.battery_text = self.orientation_ax.text(
            180, 180, 180,  # Position text at the top-right corner
            f"Battery: {self.battery_status:.2f}%",
            color='black', fontsize=8, horizontalalignment='right', verticalalignment='top'
        )

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
            [0, np.cos(np.radians(-self.pitch)), -np.sin(np.radians(-self.pitch))],
            [0, np.sin(np.radians(-self.pitch)), np.cos(np.radians(-self.pitch))]
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

        self.draw_arrow([0, 0, 0], [0, -1, 0], 'r', 'Forward', rotation_matrix)
 

        # Redraw the canvas to reflect changes
        self.orientation_canvas.draw()


    def create_ypr_chart(self, frame):
        self.ypr_fig, (self.ax0, self.ax1, self.ax2) = plt.subplots(3, 1, figsize=(4, 6), dpi=100)
        self.ypr_canvas = FigureCanvasTkAgg(self.ypr_fig, master=frame)
        self.ypr_canvas.get_tk_widget().pack(side=tk.LEFT, fill=ctk.BOTH, expand=True)

        self.ax0.set_title("Yaw_Pitch_Roll")

    def create_accel_chart(self, frame):
        self.accel_fig, (self.ax_accel_x, self.ax_accel_y, self.ax_accel_z) = plt.subplots(3, 1, figsize=(4, 6), dpi=100)
        self.accel_canvas = FigureCanvasTkAgg(self.accel_fig, master=frame)
        self.accel_canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=ctk.BOTH, expand=True)

        self.ax_accel_x.set_title("Accelerometer")

    def create_gyro_chart(self, frame):
        self.gyro_fig, (self.ax_gyro_x, self.ax_gyro_y, self.ax_gyro_z) = plt.subplots(3, 1, figsize=(4, 6), dpi=100)
        self.gyro_canvas = FigureCanvasTkAgg(self.gyro_fig, master=frame)
        self.gyro_canvas.get_tk_widget().pack(side=tk.RIGHT, fill=ctk.BOTH, expand=True)

        self.ax_gyro_x.set_title("Gyroscope")

    def create_webcam_feed(self, frame):
        self.cap = cv2.VideoCapture(0)
        self.webcam_label = ctk.CTkLabel(frame)
        self.webcam_label.pack(fill=ctk.BOTH, expand=True)
        self.update_webcam_feed()

    def update_webcam_feed(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (800, 300))
            img = Image.fromarray(frame)
            imgtk = ImageTk.PhotoImage(image=img)
            self.webcam_label.imgtk = imgtk
            self.webcam_label.configure(image=imgtk)
        self.webcam_label.after(10, self.update_webcam_feed)


    def update_data(self):
        while True:
            self.update_charts()
            self.update_car_orientation()
            self.update_battery_status()
            #time.sleep(0.01)  # Adjusted sleep for smoother updates

    def update_charts(self):
        # Update Yaw, Pitch, Roll
        self.yaw_history.append(self.yaw)
        self.pitch_history.append(self.pitch)
        self.roll_history.append(self.roll)

        if len(self.yaw_history) > 50:
            self.yaw_history.pop(0)
        if len(self.pitch_history) > 50:
            self.pitch_history.pop(0)
        if len(self.roll_history) > 50:
            self.roll_history.pop(0)

        self.ax0.clear()
        self.ax0.plot(self.yaw_history, '-r', label="Yaw")
        self.ax0.legend()
        self.ax0.set_title("Yaw_Pitch_Roll")

        self.ax1.clear()
        self.ax1.plot(self.pitch_history, '-g', label="Pitch")
        self.ax1.legend()

        self.ax2.clear()
        self.ax2.plot(self.roll_history, '-b', label="Roll")
        self.ax2.legend()

        self.ypr_canvas.draw()

        # Update Accelerometer
        self.accel_x_history.append(self.accel_x)
        self.accel_y_history.append(self.accel_y)
        self.accel_z_history.append(self.accel_z)

        if len(self.accel_x_history) > 50:
            self.accel_x_history.pop(0)
        if len(self.accel_y_history) > 50:
            self.accel_y_history.pop(0)
        if len(self.accel_z_history) > 50:
            self.accel_z_history.pop(0)

        self.ax_accel_x.clear()
        self.ax_accel_x.plot(self.accel_x_history, 'r-', label="Accel X")
        self.ax_accel_x.legend()
        self.ax_accel_x.set_title("Accelerometer")

        self.ax_accel_y.clear()
        self.ax_accel_y.plot(self.accel_y_history, 'g-', label="Accel Y")
        self.ax_accel_y.legend()

        self.ax_accel_z.clear()
        self.ax_accel_z.plot(self.accel_z_history, 'b-', label="Accel Z")
        self.ax_accel_z.legend()

        self.accel_canvas.draw()

        # Update Gyroscope
        self.gyro_x_history.append(self.gyro_x)
        self.gyro_y_history.append(self.gyro_y)
        self.gyro_z_history.append(self.gyro_z)

        if len(self.gyro_x_history) > 50:
            self.gyro_x_history.pop(0)
        if len(self.gyro_y_history) > 50:
            self.gyro_y_history.pop(0)
        if len(self.gyro_z_history) > 50:
            self.gyro_z_history.pop(0)

        self.ax_gyro_x.clear()
        self.ax_gyro_x.plot(self.gyro_x_history, 'r-', label="Gyro X")
        self.ax_gyro_x.legend()
        self.ax_gyro_x.set_title("Gyroscope")

        self.ax_gyro_y.clear()
        self.ax_gyro_y.plot(self.gyro_y_history, 'g-', label="Gyro Y")
        self.ax_gyro_y.legend()

        self.ax_gyro_z.clear()
        self.ax_gyro_z.plot(self.gyro_z_history, 'b-', label="Gyro Z")
        self.ax_gyro_z.legend()

        self.gyro_canvas.draw()

        # Simulate accelerometer and gyroscope data changes
        self.accel_x = random.uniform(-1, 1)
        self.accel_y = random.uniform(-1, 1)
        self.accel_z = random.uniform(-1, 1)
        self.gyro_x = random.uniform(-1, 1)
        self.gyro_y = random.uniform(-1, 1)
        self.gyro_z = random.uniform(-1, 1) 

if __name__ == "__main__":
    root = ctk.CTk()
    app = Realtime_ChartWindow(root)
    root.mainloop()


