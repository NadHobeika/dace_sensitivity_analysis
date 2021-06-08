import math
import numpy as np
import sys


def read_stl(filename):
    with open(filename) as f:
        lines = f.readlines()
        points = []
        for line in lines:
            split_line = line.split()
            if split_line[0] == 'vertex':
                x = float(split_line[1])
                y = float(split_line[2])
                z = float(split_line[3])
                points.append((x, y))
    return np.array(points)


def get_obb(points):
    """
    courtesy of stackoverflow: https://stackoverflow.com/questions/32892932/create-the-oriented-bounding-box-obb-with-python-and-numpy
    :param points:numpy array of points
    :return: corners of obb and center
    """
    ca = np.cov(points, y=None, rowvar=0, bias=1)
    v, vect = np.linalg.eig(ca)
    tvect = np.transpose(vect)

    # use the inverse of the eigenvectors as a rotation matrix and
    # rotate the points so they align with the x and y axes
    ar = np.dot(points, np.linalg.inv(tvect))

    # get the minimum and maximum x and y
    mina = np.min(ar, axis=0)
    maxa = np.max(ar, axis=0)
    diff = (maxa - mina) * 0.5

    # the center is just half way between the min and max xy
    center = mina + diff

    # get the 4 corners by subtracting and adding half the bounding boxes height and width to the center
    corners = np.array([center + [-diff[0], -diff[1]], center + [diff[0], -diff[1]], center + [diff[0], diff[1]],
                        center + [-diff[0], diff[1]], center + [-diff[0], -diff[1]]])

    # use the the eigenvectors as a rotation matrix and
    # rotate the corners and the centerback
    corners = np.dot(corners, tvect)
    center = np.dot(center, tvect)
    return corners, center


def translate_vectors(corners, off_set):
    base_line = np.array([corners[3], corners[0]])
    perp_base_line = corners[2:4]
    base_vector = base_line[1] - base_line[0]
    norm_base_vector = base_vector / np.linalg.norm(base_vector)
    translate_0 = norm_base_vector * off_set
    perp_base_vector = perp_base_line[1] - perp_base_line[0]
    norm_perp_base_vector = perp_base_vector / np.linalg.norm(perp_base_vector)
    translate_1 = norm_perp_base_vector * off_set
    return translate_0, translate_1


def offset_baseline(corners, off_set):
    base_line = np.array([corners[3], corners[0]])
    # extend the line to include the back point of the obb
    # if possible
    translate_0, translate_1 = translate_vectors(corners, off_set)
    pt_00 = base_line[0] - translate_0 + translate_1
    pt_01 = base_line[1] + translate_0 + translate_1
    return pt_00, pt_01


def get_intersection(a1, a2, b1, b2):
    """
    https://stackoverflow.com/questions/3252194/numpy-and-line-intersections
    Returns the point of intersection of the lines passing through a2,a1 and b2,b1.
    a1: [x, y] a point on the first line
    a2: [x, y] another point on the first line
    b1: [x, y] a point on the second line
    b2: [x, y] another point on the second line
    """
    s = np.vstack([a1, a2, b1, b2])  # s for stacked
    h = np.hstack((s, np.ones((4, 1))))  # h for homogeneous
    l1 = np.cross(h[0], h[1])  # get first line
    l2 = np.cross(h[2], h[3])  # get second line
    x, y, z = np.cross(l1, l2)  # point of intersection
    if z == 0:  # lines are parallel
        return float('inf'), float('inf')
    return x / z, y / z


def is_between(a, b, c, pt_index):
    v0 = b - a
    v1 = c - a
    crossproduct = np.cross(v0, v1)
    tol = 10**-8

    if abs(crossproduct) > tol:
        return False

    check_00 = v0 / np.linalg.norm(v0)
    check_01 = v1 / np.linalg.norm(v1)
    if pt_index == 0 and np.any(check_00 == check_01):
        return True

    dotproduct = np.dot(v0, v1)
    if dotproduct < 0:
        return False

    squaredlengthba = v0[0]**2 + v0[1]**2
    if dotproduct > squaredlengthba:
        return False

    return True


def cover_corners(base_line, corner_h, corner_v, wind_direction):
    new_baseline = []
    translate = np.array([-math.cos(math.radians(wind_direction)), -math.sin(math.radians(wind_direction))])
    horizontal = corner_h + translate
    vertical = corner_v + translate
    intersection_h = get_intersection(base_line[0], base_line[1], corner_h, horizontal)
    intersection_v = get_intersection(base_line[0], base_line[1], corner_v, vertical)
    if is_between(base_line[0], base_line[1], intersection_h, 0):
        new_baseline.append(base_line[0])
    else:
        new_baseline.append(intersection_h)
    if is_between(base_line[0], base_line[1], intersection_v, 1):
        new_baseline.append(base_line[1])
    else:
        new_baseline.append(intersection_v)
    return np.array(new_baseline)


def get_temp_angle(origin, pt0, pt1):
    v0 = pt0 - origin
    v1 = pt1 - origin

    cosine_angle = np.dot(v0, v1) / (np.linalg.norm(v0) * np.linalg.norm(v1))
    angle = np.arccos(cosine_angle)

    return 180 - np.degrees(angle)


def get_point_dune_foot(windangle, x, origin_point):
    cos_angle = math.cos(math.radians(windangle))
    x_total = x - origin_point[0]
    if cos_angle == 0:
        print('You have a 90 degree wind angle!')
    else:
        line_length = x_total / cos_angle
        add_y = line_length * math.sin(math.radians(windangle))
        return x, origin_point[1] + add_y


def get_point_dune_top(windangle, x, origin_point):
    cos_angle = math.cos(math.radians(windangle))
    x_total = x
    if cos_angle == 0:
        print('You have a 90 degree wind angle!')
    else:
        line_length = x_total / cos_angle
        add_y = line_length * math.sin(math.radians(windangle))
        return origin_point[0] + x, origin_point[1] + add_y


def get_final_baseline(base_line, divisions):
    tol = 10 ** -8
    dist = np.linalg.norm(base_line[0] - base_line[1])
    if (dist % divisions) <= tol:
        nbre_of_lines = dist / divisions
        return base_line, nbre_of_lines
    else:
        nbre_of_lines = math.ceil(dist / divisions)
        difference = (nbre_of_lines * divisions) - dist
        dummy_corners = np.array([[base_line[1][0], base_line[1][1]], [0, 0], [0, 0],
                                  [base_line[0][0], base_line[0][1]]])
        translate_0, translate_1 = translate_vectors(dummy_corners, difference / 2)
        pt_00 = base_line[0] - translate_0
        pt_01 = base_line[1] + translate_0
        return (pt_00, pt_01), nbre_of_lines


if __name__ == '__main__':
    wind_angle = float(sys.argv[1])
    x_bbox = float(sys.argv[2])
    d_dunes = float(sys.argv[3])

    configuration_file_stl = sys.argv[4]

    all_pts = read_stl(configuration_file_stl)
    pts = np.unique(all_pts, axis=0)
    obb_corners, obb_center = get_obb(pts)
    obb_corners = obb_corners[0:4]
    sorted_first_corners = obb_corners[np.argsort(obb_corners[:, 1])][0:2, :]
    start_pt = sorted_first_corners[np.where(sorted_first_corners[:, 0] == np.min(sorted_first_corners[:, 0]))]
    roll_int = np.where((obb_corners == start_pt).all(axis=1))
    if len(roll_int[0]) != 1:
        roll_int = -2 * roll_int[0][0]
    else:
        roll_int = -2 * roll_int[0]
    sorted_obb_corners = np.roll(obb_corners, roll_int)
    offset = 0.6
    baseline = offset_baseline(sorted_obb_corners, offset)
    total_to_dunes = x_bbox + d_dunes
    initial_pt_foot_dunes = get_point_dune_foot(wind_angle, total_to_dunes, baseline[0])
    temp_angle = get_temp_angle(baseline[0], baseline[1], initial_pt_foot_dunes)
    if temp_angle == 0:
        division_value = 0.6
    else:
        division_value = 0.6 / math.sin(math.radians(temp_angle))
    extend_baseline = cover_corners(baseline, sorted_obb_corners[2], sorted_obb_corners[1], wind_angle)
    final_baseline, number_of_lines = get_final_baseline(extend_baseline, division_value)
    pt_foot_dunes = get_point_dune_foot(wind_angle, total_to_dunes, final_baseline[0])
    dummy_corners = np.array([[final_baseline[1][0], final_baseline[1][1]], [0, 0], [0, 0],
                              [final_baseline[0][0], final_baseline[0][1]]])
    translate_0, translate_1 = translate_vectors(dummy_corners, division_value)
    mid_initial_pt = final_baseline[0] + (translate_0 / 2)
    mid_pt_foot_dunes = get_point_dune_foot(wind_angle, total_to_dunes, mid_initial_pt)

    p0 = np.array([mid_initial_pt[0], mid_initial_pt[1], 0.3])
    p1 = np.array([mid_pt_foot_dunes[0], mid_pt_foot_dunes[1], 0.3])
    p2 = np.array([mid_pt_foot_dunes[0], mid_pt_foot_dunes[1], 0.3])
    p3 = get_point_dune_top(wind_angle, 15, mid_pt_foot_dunes)
    p3 = np.array([p3[0], p3[1], 2.8])
    move_step = np.array([translate_0[0], translate_0[1], 0])

    # outerBox
    outer_box_max = np.array([p3[0]+1, p3[1]+1, 6])
    outer_box_min = np.array([final_baseline[0][0]-6, final_baseline[1][1]-6, 0])
    center_outer_box = (outer_box_max + outer_box_min)/2
    total_outer_box = outer_box_max - outer_box_min

    with open("boxesDict", "w") as f:
        f.write("outerBox\n")
        f.write("{\n")
        f.write("   type                box;\n")
        f.write("   cellSize            0.6;\n")
        f.write("   centre              ({0:.2f} {1:.2f} {2:.2f});\n".format(center_outer_box[0], center_outer_box[1],
                                                                             center_outer_box[2]))
        f.write("   lengthX             {0:.2f};\n".format(total_outer_box[0]))
        f.write("   lengthY             {0:.2f};\n".format(total_outer_box[1]))
        f.write("   lengthZ             {0:.2f};\n".format(total_outer_box[2]))
        f.write("}\n")

    # terrain
    
    move_step_v = np.array([0, translate_0[1], 0])
    with open("boxesDict", "a") as f:
        for i in range(int(number_of_lines)):
            pp0 = p0 + (move_step * i)
            pp1 = p1 + (move_step * i)
            pp2 = p2 + (move_step_v * i)
            pp3 = p3 + (move_step_v * i)
            f.write("lineTerrain{0}\n".format(i))
            f.write("{\n")
            f.write("   type                line;\n")
            f.write("   cellSize            0.15;\n")
            f.write("   p0                  ({0:.2f} {1:.2f} {2:.2f});\n".format(pp0[0], pp0[1], pp0[2]))
            f.write("   p1                  ({0:.2f} {1:.2f} {2:.2f});\n".format(pp1[0], pp1[1], pp1[2]))
            f.write("   refinementThickness 0.3;\n")
            f.write("}\n")

            f.write("slopeLineTerrain{0}\n".format(i))
            f.write("{\n")
            f.write("   type                line;\n")
            f.write("   cellSize            0.15;\n")
            f.write("   p0                  ({0:.2f} {1:.2f} {2:.2f});\n".format(pp2[0], pp2[1], pp2[2]))
            f.write("   p1                  ({0:.2f} {1:.2f} {2:.2f});\n".format(pp3[0], pp3[1], pp3[2]))
            f.write("   refinementThickness 0.3;\n")
            f.write("}\n")

    # houses
    houses = ([all_pts[488], all_pts[452]], [all_pts[380], all_pts[344]], [all_pts[278], all_pts[236]], [all_pts[164],
                                                                                                         all_pts[128]],
              [all_pts[56], all_pts[20]])
    h_p0 = []
    h_p1 = []
    for house in houses:
        h_00_p0 = house[0]
        h_00_p1 = house[1]
        dummy_corners_0 = np.array([[h_00_p0[0], h_00_p0[1]], [0, 0], [0, 0],
                                    [h_00_p1[0], h_00_p1[1]]])
        translate_0_0, translate_1_0 = translate_vectors(dummy_corners_0, 1.2)
        h_00_p0 = h_00_p0 - translate_0_0
        h_00_p1 = h_00_p1 + translate_0_0
        h_00_p0 = (h_00_p0[0], h_00_p0[1], 1.2)
        h_00_p1 = (h_00_p1[0], h_00_p1[1], 1.2)
        h_p0.append(h_00_p0)
        h_p1.append(h_00_p1)

    with open("boxesDict", "a") as f:
        for j in range(5):
            f.write("lineBldg{0}\n".format(j))
            f.write("{\n")
            f.write("   type                line;\n")
            f.write("   cellSize            0.15;\n")
            f.write("   p0                  ({0:.2f} {1:.2f} {2:.2f});\n".format(h_p0[j][0], h_p0[j][1], h_p0[j][2]))
            f.write("   p1                  ({0:.2f} {1:.2f} {2:.2f});\n".format(h_p1[j][0], h_p1[j][1], h_p1[j][2]))
            f.write("   refinementThickness 3;\n")
            f.write("}\n")

