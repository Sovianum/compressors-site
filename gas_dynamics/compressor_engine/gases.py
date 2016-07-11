# -*- coding: utf-8 -*-

import numpy as np
from scipy.optimize import curve_fit


def mix(gas_list, fraction_list):
    assert len(gas_list) == len(fraction_list)

    class Mixture(GasPhysicalModel):
            def __init__(self):
                self.gas_list = [gas() for gas in gas_list]
                self.fraction_list = fraction_list

            def mixture_parameter(self, component_parameter_func_name, *args):
                function_list = [getattr(gas, component_parameter_func_name) for gas in self.gas_list]
                partial_parameter_list = [function(*args) * fraction
                                          for function, fraction in zip(function_list, self.fraction_list)]
                return sum(partial_parameter_list)

            def rho(self, T, p):
                return self.mixture_parameter('rho', T, p)

            def lambda_T(self, T):
                return self.mixture_parameter('lambda_T', T)

            def mu(self, T):
                return self.mixture_parameter('mu', T)

            def nu(self, T, p):
                return self.mixture_parameter('nu', T, p)

            def C_p(self, T):
                return self.mixture_parameter('C_p', T)

            def Pr(self, T):
                return self.mixture_parameter('Pr', T)

    return Mixture


class GasPhysicalModel:
    '''
    Abstract class - model of a general-case gas. Includes methods
    returning physical parameters of the gas given environmental conditions
    '''
    def rho(self, T, p):
        '''функция возвращает значение плотности газа при заданной
        температуре и давлении
        return p/(self.R*T)

        При этом используются следующие параметры газа:
        self.R - значение газовой постоянной данного газа
        '''
        return p/(self.R*T)

    def lambda_T(self, T):
        ''' функция возвращает значение теплопроводности газа при заданной
        температуре
        return self.lambda_0*(T/self.T_0)**self.n_cond

        При этом используются следующие параметры газа:
        self.lambda_0 - значение теплопроводности данного газа при стандартной температуре
        self.T_0 - значение стандартной температуры для данного газа
        self.n_cond - значение показателя степени в степенной зависимости
                        теплопроводности данного газа от температуры
        '''
        return self.lambda_0*(T/self.T_0)**self.n_cond

    def mu(self, T):
        ''' функция возвращает значение вязкости газа при заданной
        температуре
        return self.mu_0*(T/self.T_0)**self.m_visk

        При этом используются следующие параметры газа:
        self.mu_0 - значение вязкости данного газа при стандартной температуре
        self.T_0 - значение стандартной температуры для данного газа
        self.m_visk - значение показателя степени в степенной зависимости
                        вязкости данного газа от температуры
        '''
        return self.mu_0*(T/self.T_0)**self.m_visk

    def nu(self, T, p):
        return self.mu(T) / self.rho(T, p)

    def C_p(self, T):
        ''' функция возвращает значение теплоемкости газа при заданной
        температуре
        return self.C_p0

        При этом используются следующие параметры газа:
        self.C_p0 - значение теплоемкости данного газа при стандартной
                    температуре
        '''
        return self.C_p0

    def Pr(self, T):
        ''' функция возвращает числ Прандтля газа при заданной
        температуре
        return self.C_p(T)*self.mu(T)/self.lambda_T(T)
        '''
        return self.C_p(T)*self.mu(T)/self.lambda_T(T)

    def k(self, T):
            return self.C_p(T) / (self.C_p(T) - self.R)


class Mixture(GasPhysicalModel):
        def __init__(self, gas_list, fraction_list):
            self.gas_list = [gas() for gas in gas_list]
            self.fraction_list = fraction_list

        def mixture_parameter(self, component_parameter_func_name, *args):
            function_list = [getattr(gas, component_parameter_func_name) for gas in self.gas_list]
            partial_parameter_list = [function(*args) * fraction for function, fraction in zip(function_list, self.fraction_list)]
            return sum(partial_parameter_list)

        def rho(self, T, p):
            return self.mixture_parameter('rho', T, p)

        def lambda_T(self, T):
            return self.mixture_parameter('lambda_T', T)

        def mu(self, T):
            return self.mixture_parameter('mu', T)

        def nu(self, T, p):
            return self.mixture_parameter('nu', T, p)

        def C_p(self, T):
            return self.mixture_parameter('C_p', T)

        def Pr(self, T):
            return self.mixture_parameter('Pr', T)


class Air(GasPhysicalModel):
    def __init__(self):
        self.R = 287
        self.T_0 = 273.
        self.lambda_0 = 244.2e-4
        self.mu_0 = 17.6e-6
        self.C_p0 = 1006.
        self.n_cond = 0.82
        self.m_visk = 0.68


class Nitrogen(GasPhysicalModel):
    def __init__(self):
        self.R = 297
        self.T_0 = 273
        self.lambda_0 = 241.9e-4
        self.mu_0 = 16.67e-6
        self.C_p0 = 1040
        self.n_cond = 0.8
        self.m_visk = 0.68


class CO2(GasPhysicalModel):
    def __init__(self):
        self.R = 189
        self.T_0 = 273
        self.lambda_0 = 147e-4
        self.mu_0 = 13.65e-6
        self.C_p0 = 849
        self.n_cond = 1.23
        self.m_visk = 0.82


class H20Vapour(GasPhysicalModel):
    def __init__(self):
        self.T_0 = 293
        self.C_p0 = 2010
        self.R = 465
        self.T_array = self.get_T_array()
        self.lambda_array = self.get_lambda_array()
        self.mu_array = self.get_mu_array()
        self.Pr_array = self.get_Pr_array()
        self.mu_0, self.m_visk = self.get_visk_parameters()
        self.lambda_0, self.n_cond = self.get_cond_parameters()

    def get_T_array(self):
        result = np.arange(120, 500, 10)
        result += 273
        return result

    def get_lambda_array(self):
        lambda_array = []
        lambda_array.append(26)
        lambda_array.append(26.9)
        lambda_array.append(27.7)
        lambda_array.append(28.6)
        lambda_array.append(29.5)
        lambda_array.append(30.4)
        lambda_array.append(31.3)
        lambda_array.append(32.2)
        lambda_array.append(33.1)
        lambda_array.append(34.1)
        lambda_array.append(35.1)
        lambda_array.append(36.1)
        lambda_array.append(37.1)
        lambda_array.append(38.1)
        lambda_array.append(39.1)
        lambda_array.append(40.1)
        lambda_array.append(41.2)
        lambda_array.append(42.3)
        lambda_array.append(44.4)
        lambda_array.append(45.5)
        lambda_array.append(46.7)
        lambda_array.append(47.8)
        lambda_array.append(49.0)
        lambda_array.append(50.1)
        lambda_array.append(51.3)
        lambda_array.append(52.5)
        lambda_array.append(53.6)
        lambda_array.append(54.8)
        lambda_array.append(56)
        lambda_array.append(57.3)
        lambda_array.append(58.5)
        lambda_array.append(59.7)
        lambda_array.append(61)
        lambda_array.append(62.2)
        lambda_array.append(63.5)
        lambda_array.append(64.8)
        lambda_array.append(66)
        lambda_array.append(67.3)

        lambda_array = [lambda_value / 1000 for lambda_value in lambda_array]

        return lambda_array

    def get_mu_array(self):
        mu_array = []
        mu_array.append(129)
        mu_array.append(133)
        mu_array.append(137)
        mu_array.append(141)
        mu_array.append(146)
        mu_array.append(150)
        mu_array.append(154)
        mu_array.append(158)
        mu_array.append(162)
        mu_array.append(166)
        mu_array.append(170)
        mu_array.append(174)
        mu_array.append(178)
        mu_array.append(182)
        mu_array.append(186)
        mu_array.append(190)
        mu_array.append(194)
        mu_array.append(198)
        mu_array.append(202)
        mu_array.append(207)
        mu_array.append(211)
        mu_array.append(215)
        mu_array.append(219)
        mu_array.append(223)
        mu_array.append(227)
        mu_array.append(231)
        mu_array.append(235)
        mu_array.append(239)
        mu_array.append(243)
        mu_array.append(247)
        mu_array.append(251)
        mu_array.append(255)
        mu_array.append(260)
        mu_array.append(264)
        mu_array.append(268)
        mu_array.append(272)
        mu_array.append(276)
        mu_array.append(280)

        mu_array = [mu / 1e7 for mu in mu_array]
        return mu_array

    def get_Pr_array(self):
        return [mu * self.C_p0 / lambda_T for mu, lambda_T in zip(self.mu_array, self.lambda_array)]

    def get_visk_parameters(self):
        return curve_fit(lambda T, mu_0, m: mu_0 * (T / self.T_0)**m, self.T_array, self.mu_array)[0]

    def get_cond_parameters(self):
        return curve_fit(lambda T, lambda_0, n: lambda_0 * (T / self.T_0)**n, self.T_array, self.lambda_array)[0]


class CH4Smoke(Mixture):
    def __init__(self):
        super(CH4Smoke, self).__init__([Nitrogen, CO2, H20Vapour], [0.711, 0.159, 1 - (0.711 + 0.159)])
