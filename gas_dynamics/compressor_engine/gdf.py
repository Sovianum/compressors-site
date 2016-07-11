def epsilon(lambda_, k):
    return (1 - (k - 1) / (k + 1) * lambda_**2)**(1 / (k -1))


def pi(lambda_, k):
    return (1 - (k - 1) / (k + 1) * lambda_**2)**(k / (k -1))


def tau(lambda_, k):
    return 1 - lambda_**2 * (k - 1) / (k + 1)


def q(lambda_, k, R):
    '''
    :param lambda_:
    :param k:
    :return: функция возвращет не газодинамическую функцию расхода, а ее произведение на коэффициент m
    '''
    coef = (2 * k / ((k + 1) * R))**0.5
    return coef * lambda_ * (1 - (k - 1) / (k + 1) * lambda_**2)**(1 / (k - 1))


def a_crit(k, R, T_stag):
    '''
    :param k: показатель адиабаты рабочего тела
    :param R: газовая постоянная рабочего тела
    :param T_stag: температура торможения рабочего тела
    :return: критическая скорость
    '''
    return (2 * k / (k + 1) * R * T_stag)**0.5


def mach(lambda_, k):
    enum = 2 / (k + 1) * lambda_**2
    denum = 1 - (k - 1) / (k + 1) * lambda_**2

    return (enum / denum)**0.5


def lambda_(mach, k):
    enum = (k + 1) / 2 * mach**2
    denum = 1 + 2 * mach**2

    return (enum / denum)**0.5