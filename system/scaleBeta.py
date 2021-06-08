import math
import sys


def read_stl(filename):
    with open(filename) as f:
        lines = f.readlines()
        points = []
        for line in lines:
            split_line = line.split()
            if split_line[0] == 'vertex':
                points.append((float(split_line[1]), float(split_line[2]), float(split_line[3])))
    s = set(points)
    points = list(s)
    points.sort()
    return points


def get_angle(origin, pt1, pt2):
    angle = math.degrees(math.atan2(pt2[1] - origin[1], pt2[0] - origin[0])
                         - math.atan2(pt1[1] - origin[1], pt1[0] - origin[0]))
    return angle


def get_y_unit_vector(point):
    return point[0], (point[1] + 1), point[2]


def get_neg_x_unit_vector(point):
    return point[0]-1, point[1], point[2]


def length(pt0, pt1):
    x = pt1[0] - pt0[0]
    y = pt1[1] - pt0[1]
    return math.sqrt(x**2 + y**2)


def get_rotating_angle(stl_0, stl_4, alpha, space, beta):
    if alpha <= 70:
        end_pt_reference = stl_4[0]
        orig_pt = stl_0[5]
        end_pt_straighten = stl_4[5]
    else:
        end_pt_reference = stl_4[5]
        orig_pt = stl_0[12]
        end_pt_straighten = stl_4[12]
    # straighten configuration
    y_unit = get_y_unit_vector(orig_pt)
    straighten_angle = get_angle(orig_pt, y_unit, end_pt_straighten)
    # get x_total when straightened and left space for rotation
    new_angle = alpha - straighten_angle
    x_total = 7 * math.cos(math.radians(new_angle)) + 3 * math.cos(math.radians(90 - new_angle))
    left_space = space - x_total
    # get reference to inclination of configuration
    neg_x_unit = get_neg_x_unit_vector(orig_pt)
    initial_angle = get_angle(orig_pt, end_pt_reference, neg_x_unit)
    straight_reference_angle = initial_angle + straighten_angle
    reference_length = length(orig_pt, end_pt_reference)
    print(reference_length)
    max_x = left_space + reference_length * math.cos(math.radians(straight_reference_angle))
    max_angle = straight_reference_angle - math.degrees(math.acos(max_x / reference_length))
    rotating_angle = (max_angle / 90) * beta
    return straighten_angle, rotating_angle


if __name__ == '__main__':
    pts_0 = read_stl(sys.argv[1])
    pts_4 = read_stl(sys.argv[2])
    alpha = float(sys.argv[3])
    beta = float(sys.argv[4])
    distance_dunes = float(sys.argv[5])
    plateau = 30
    available_space = plateau - distance_dunes
    transformation = get_rotating_angle(pts_0, pts_4, alpha, available_space, beta)
    print(-transformation[0])
    print(transformation[1])
