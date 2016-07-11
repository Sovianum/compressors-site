import numpy as np


class IncompleteVelocityTriangle:
    def __init__(self, u_out_1=None, r_m_rel=None, c_u_rel=None, c_a_rel=None):
        self.u_out_1 = u_out_1
        self.r_m_rel = r_m_rel
        self.c_u_rel = c_u_rel
        self.c_a_rel = c_a_rel

    def __str__(self):
        result_str = ''
        result_str += 'alpha = %.2f   ' % np.rad2deg(self.alpha)
        result_str += 'c_u_rel = %.3f   ' % self.c_u_rel
        result_str += 'r_rel = %.3f   ' % self.r_m_rel
        result_str += 'c_a_rel = %.3f   ' % self.c_a_rel

        return result_str

    @property
    def u_m(self):
        return self.u_out_1 * self.r_m_rel

    @property
    def alpha(self):
        return np.arctan2(self.c_a_rel, self.c_u_rel)

    @property
    def c_u(self):
        return self.u_out_1 * self.c_u_rel

    @property
    def c_a(self):
        return self.u_out_1 * self.c_a_rel

    @property
    def c_total(self):
        return (self.c_u**2 + self.c_a**2)**0.5


class VelocityTriangle(IncompleteVelocityTriangle):
    def __str__(self):
        result_str = ''
        result_str += 'alpha = %.2f   ' % np.rad2deg(self.alpha)
        result_str += 'betta = %.2f   ' % np.rad2deg(self.betta)
        result_str += 'c_u_rel = %.3f   ' % self.c_u_rel
        result_str += 'w_u_rel = %.3f   ' % self.w_u_rel
        result_str += 'r_rel = %.3f   ' % self.r_m_rel
        result_str += 'c_a_rel = %.3f   ' % self.c_a_rel

        return result_str

    @property
    def betta(self):
        return np.arctan2(self.c_a_rel, self.r_m_rel - self.c_u_rel)

    @property
    def w_u_rel(self):
        return self.c_a_rel / np.tan(self.betta)

    @property
    def w_a_rel(self):
        return self.c_a_rel

    @property
    def w_u(self):
        return self.w_u_rel * self.u_out_1

    @property
    def w_a(self):
        return self.c_a

    @property
    def w_total(self):
        return (self.w_u**2 + self.w_a**2)**0.5
