import numpy as np
import sys
from stl import mesh


def read_stl(filename):
    with open(filename) as f:
        lines = f.readlines()
        x = []
        y = []
        z = []
        for line in lines:
            split_line = line.split()
            if split_line[0] == 'vertex':
                x.append(float(split_line[1]))
                y.append(float(split_line[2]))
                z.append(float(split_line[3]))
    return x, y, z


def bounding_box(x, y, z):
    """
    Calculate the bounding box edge lengths of an stl using the design coordinate system
    """
    return min(x), min(y), min(z), max(x), max(y), max(z)


def create_refinement_box(x_total, y_total, z_total):
    # Offset bounding box - Remember the configuration is moved to the origin!!!
    x_min_b = -3
    y_min_b = -3
    z_min_b = 0
    x_max_b = x_total + 15
    y_max_b = y_total + 15
    z_max_b = z_total + 3

    # Define the 8 vertices of the box
    vertices = np.array([
        [x_min_b, y_min_b, z_min_b],
        [x_max_b, y_min_b, z_min_b],
        [x_max_b, y_max_b, z_min_b],
        [x_min_b, y_max_b, z_min_b],
        [x_min_b, y_min_b, z_max_b],
        [x_max_b, y_min_b, z_max_b],
        [x_max_b, y_max_b, z_max_b],
        [x_min_b, y_max_b, z_max_b]])
    # Define the 12 triangles composing the box
    faces = np.array([
        [0, 3, 1],
        [1, 3, 2],
        [0, 4, 7],
        [0, 7, 3],
        [4, 5, 6],
        [4, 6, 7],
        [5, 1, 2],
        [5, 2, 6],
        [2, 3, 6],
        [3, 7, 6],
        [0, 1, 5],
        [0, 5, 4]])

    # Create the mesh
    box = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
    for i, f in enumerate(faces):
        for j in range(3):
            box.vectors[i][j] = vertices[f[j], :]

    # Write the mesh to file "refinement_box.stl"
    box.save('refinement_box.stl')


if __name__ == '__main__':
    file_stl = sys.argv[1]
    pts = read_stl(file_stl)
    bbox = bounding_box(pts[0], pts[1], pts[2])
    x_t = bbox[3] - bbox[0]
    y_t = bbox[4] - bbox[1]
    z_t = bbox[5] - bbox[2]
    print(-bbox[0])  # x_min
    print(-bbox[1])  # y_min
    print(x_t)  # x_total
    create_refinement_box(x_t, y_t, z_t)
