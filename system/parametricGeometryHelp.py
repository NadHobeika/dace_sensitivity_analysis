import math
import sys


def gauss_function(alpha):
    """ get the gaussian relationship for initial translation """
    height_peak = 0.3
    euler_number = 2.71828
    center_of_peak = 70
    std_deviation = 10
    temp = ((alpha - center_of_peak) ** 2) / (2 * std_deviation ** 2)
    return 1 - (height_peak * (euler_number ** (- temp)))


def get_initial_translation_factor(alpha, factor):
    angle_factor = alpha * factor
    dist_between_houses = 6
    return math.sin(math.radians(angle_factor)) * dist_between_houses / math.cos(math.radians(angle_factor))


if __name__ == '__main__':
    input_alpha = float(sys.argv[1])
    factor_00 = gauss_function(input_alpha)
    factor_01 = get_initial_translation_factor(input_alpha, factor_00)
    x_translation = math.cos(math.radians(input_alpha)) * factor_01
    y_translation = math.sin(math.radians(input_alpha)) * factor_01
    print(x_translation)
    print(y_translation)
    print(2 * x_translation)
    print(2 * y_translation)
    print(3 * x_translation)
    print(3 * y_translation)
    print(4 * x_translation)
    print(4 * y_translation)
