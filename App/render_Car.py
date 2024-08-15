import trimesh
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Load the 3D model from the .obj file
file_path = "C:\\Users\\HOB6HC\\Code_Source\\FOTA_Station_Up1-main\\model\\Porsche.obj"
mesh = trimesh.load(file_path)

# Create a 3D plot
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# Plot the vertices
ax.plot_trisurf(mesh.vertices[:, 0], mesh.vertices[:, 1], mesh.vertices[:, 2], triangles=mesh.faces, cmap='viridis', edgecolor='k')

# Set plot title and labels
ax.set_title('3D Model Visualization')
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')

# Show the plot
plt.show()
