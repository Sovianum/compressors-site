import numpy as np


def get_line_point(start_point, end_point, x_rel):
    start_point = np.array(start_point)
    end_point = np.array(end_point)

    line_vector = end_point - start_point

    return start_point + line_vector * x_rel


class LineBezierProfile:
    def __init__(self, inlet_angle, outlet_angle, line_frac):
        self.inlet_angle = inlet_angle
        self.outlet_angle = outlet_angle
        self.line_frac = line_frac
        self.inlet_point = np.array((0, 0))
        self.outlet_point = np.array((1, 0))
        self.curve_start_point = np.array((1, np.tan(inlet_angle))) * line_frac
        self._intersection_point = list()

    def __call__(self, x_rel):
        return self.get_profile_point(x_rel)[0]

    @property
    def intersection_point(self):
        if len(self._intersection_point) == 0:
            x = np.tan(self.outlet_angle) / (np.tan(self.inlet_angle) + np.tan(self.outlet_angle))
            y = np.tan(self.inlet_angle) * x

            self._intersection_point = np.array((x, y))

        return self._intersection_point

    def get_bezier_point(self, x_rel):
        point_1 = get_line_point(self.curve_start_point, self.intersection_point, x_rel)
        point_2 = get_line_point(self.intersection_point, self.outlet_point, x_rel)

        return get_line_point(point_1, point_2, x_rel)

    def get_profile_point(self, x_rel):
        if x_rel <= self.line_frac:
            return np.array((1, np.tan(self.inlet_angle))) * x_rel
        else:
            x_rel = (x_rel - self.line_frac) / (1 - self.line_frac)
            return self.get_bezier_point(x_rel)

    def get_profile(self, x_rel_arr):
        point_list = list()

        for x_rel in reversed(x_rel_arr):
            point_list.append(self.get_profile_point(x_rel))

        y_rel_arr = np.array([point[1] for point in point_list])

        return y_rel_arr






