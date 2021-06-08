import numpy as np
import sys


def write_file(filename, pts):
    with open(filename, "w") as f:
        for point in pts:
            f.write("({0} {1} {2})\n".format(point[0], point[1], point[2]))


if __name__ == '__main__':
    x_total = float(sys.argv[1])
    d_dunes = float(sys.argv[2])
    move_x = x_total + d_dunes
    points = np.loadtxt(sys.argv[3])
    outfile = sys.argv[4]
    points[:, 0] += move_x
    write_file(outfile, points)
