import numpy as np
import heapq
import random
import math
from math import factorial
from scipy.special import gamma as gamma_func

class MMCSystem:
    """
    Многоканальная СМО с отказами (очереди нет).
    Состояния: 0..n — число занятых каналов.
    Поддерживаемые законы: 'exponential' (показательный), 'weibull' (Вейбула), 'gamma' (Гамма).
    """
    def __init__(self, n_channels, lambda_rate, mu_rate, T_max=10_000.0,
                 arrival_dist='exponential', arrival_params=None,
                 service_dist='exponential', service_params=None):
        self.n = n_channels
        self.lambda_rate = lambda_rate
        self.mu_rate = mu_rate
        self.T_max = T_max
        self.arrival_dist = arrival_dist
        self.service_dist = service_dist
        self.arrival_params = arrival_params or {}
        self.service_params = service_params or {}

        # Предвычисление параметров для Вейбулла (масштаб b подбирается так, чтобы среднее было 1/lambda или 1/mu)
        self._arr_a, self._arr_b = None, None
        if arrival_dist == 'weibull':
            a = self.arrival_params.get('a', 2.0)
            self._arr_a = a
            self._arr_b = (1.0 / lambda_rate) / gamma_func(1.0 + 1.0 / a)
            
        self._srv_a, self._srv_b = None, None
        if service_dist == 'weibull':
            a = self.service_params.get('a', 2.0)
            self._srv_a = a
            self._srv_b = (1.0 / mu_rate) / gamma_func(1.0 + 1.0 / a)

        # Статистика
        self.state_times = np.zeros(n_channels + 1)
        self.total_arrivals = 0
        self.served = 0
        self.refusals = 0

    def _gen_exp(self, rate):
        return -math.log(1.0 - random.random()) / rate

    def _gen_weibull_arr(self):
        return self._arr_b * (-math.log(1.0 - random.random())) ** (1.0 / self._arr_a)

    def _gen_weibull_srv(self):
        return self._srv_b * (-math.log(1.0 - random.random())) ** (1.0 / self._srv_a)

    def _gen_gamma(self, rate, eta):
        return sum(-math.log(1.0 - random.random()) for _ in range(eta)) / (eta * rate)

    def gen_interarrival(self):
        if self.arrival_dist == 'exponential': return self._gen_exp(self.lambda_rate)
        if self.arrival_dist == 'weibull': return self._gen_weibull_arr()
        if self.arrival_dist == 'gamma': return self._gen_gamma(self.lambda_rate, self.arrival_params.get('eta', 3))
        raise ValueError(self.arrival_dist)

    def gen_service(self):
        if self.service_dist == 'exponential': return self._gen_exp(self.mu_rate)
        if self.service_dist == 'weibull': return self._gen_weibull_srv()
        if self.service_dist == 'gamma': return self._gen_gamma(self.mu_rate, self.service_params.get('eta', 3))
        raise ValueError(self.service_dist)

    def simulate(self):
        events = []
        heapq.heappush(events, (self.gen_interarrival(), 1, 1, -1))
        channel_free = [0.0] * self.n
        busy = 0
        last_change = 0.0

        while events:
            event_time, _, kind, channel = heapq.heappop(events)
            if event_time > self.T_max:
                break

            self.state_times[busy] += event_time - last_change
            last_change = event_time

            if kind == 1:  # arrival
                self.total_arrivals += 1
                free_ch = -1
                for i in range(self.n):
                    if channel_free[i] <= event_time:
                        free_ch = i
                        break
                
                if free_ch >= 0:
                    s = self.gen_service()
                    channel_free[free_ch] = event_time + s
                    self.served += 1
                    busy += 1
                    heapq.heappush(events, (channel_free[free_ch], 0, 0, free_ch))
                else:
                    self.refusals += 1
                
                heapq.heappush(events, (event_time + self.gen_interarrival(), 1, 1, -1))
            else:  # service
                busy -= 1

        self.state_times[busy] += self.T_max - last_change

    def get_stats(self):
        total = float(np.sum(self.state_times))
        P = self.state_times / total
        p_refusal = self.refusals / self.total_arrivals if self.total_arrivals > 0 else 0.0
        return {
            'P': P, 'p_refusal': p_refusal, 'q': 1.0 - p_refusal, 
            'A': self.lambda_rate * (1.0 - p_refusal),
            'k_bar': sum(i * P[i] for i in range(self.n + 1)),
            'total': self.total_arrivals, 'served': self.served, 'refusals': self.refusals
        }

def analytical_mmn0(n, lambda_rate, mu_rate):
    rho = lambda_rate / mu_rate
    denom = sum(rho ** k / factorial(k) for k in range(n + 1))
    P = np.array([rho ** k / factorial(k) / denom for k in range(n + 1)])
    return {
        'rho': rho, 'P': P, 'p_refusal': P[n], 'q': 1.0 - P[n],
        'A': lambda_rate * (1.0 - P[n]), 'k_bar': sum(k * P[k] for k in range(n + 1))
    }

if __name__ == '__main__':
    random.seed(42)
    np.random.seed(42)

    LAMBDA = 42.0
    MU = 13.0
    N = 3
    T_MAX = 50_000.0

    print("Моделирование многоканальной СМО методом Монте-Карло")
    print("Параметры системы:")
    print(f"  λ = {LAMBDA} звонков/час")
    print(f"  μ = {MU} звонков/час")
    print(f"  n = {N} линии")
    print(f"  T = {T_MAX} часов моделирования")
    print("  Очередь не предусмотрена (при занятости всех линий - отказ)")

    # 1. Показательное распределение
    print("\n1. Закон распределения: Показательный (экспоненциальный)")
    sys1 = MMCSystem(N, LAMBDA, MU, T_MAX)
    sys1.simulate()
    st1 = sys1.get_stats()
    ana = analytical_mmn0(N, LAMBDA, MU)

    print("\nРезультаты моделирования:")
    print(f"Общее число поступивших заявок: {st1['total']}")
    print(f"Обслужено заявок: {st1['served']}")
    print(f"Отказов: {st1['refusals']}")
    print(f"Вероятность простоя системы (p0): {st1['P'][0]:.4f}")
    print(f"Среднее число занятых линий (k_cp): {st1['k_bar']:.4f}")
    print(f"Вероятность отказа (p_отк): {st1['p_refusal']:.4f}")
    print(f"Относительная пропускная способность (q): {st1['q']:.4f}")
    print(f"Абсолютная пропускная способность (A): {st1['A']:.4f} зв./час")

    print("\nАналитическое решение (M/M/3/0):")
    print(f"Коэффициент загрузки ρ = λ/μ = {ana['rho']:.4f}")
    print(f"Вероятность простоя (p0): {ana['P'][0]:.4f}")
    print(f"Среднее число занятых линий (k_cp): {ana['k_bar']:.4f}")
    print(f"Вероятность отказа (p_отк): {ana['p_refusal']:.4f}")
    print(f"Относительная пропускная способность (q): {ana['q']:.4f}")
    print(f"Абсолютная пропускная способность (A): {ana['A']:.4f} зв./час")

    print("\nСравнение результатов (погрешность):")
    print(f"  p0: {abs(st1['P'][0] - ana['P'][0]):.5f}")
    print(f"  P_отк: {abs(st1['p_refusal'] - ana['p_refusal']):.5f}")
    print(f"  k_cp: {abs(st1['k_bar'] - ana['k_bar']):.5f}")
    print(f"  q: {abs(st1['q'] - ana['q']):.5f}")
    print(f"  A: {abs(st1['A'] - ana['A']):.4f}")

    # 2. Закон Вейбула
    print("\n2. Закон распределения: Вейбула (a=2) для поступления, Показательный для обслуживания")
    sys_w = MMCSystem(N, LAMBDA, MU, T_MAX, arrival_dist='weibull', arrival_params={'a': 2.0})
    sys_w.simulate()
    st_w = sys_w.get_stats()
    print(f"Результаты моделирования:")
    print(f"  Вероятность простоя (p0): {st_w['P'][0]:.4f}")
    print(f"  Вероятность отказа (p_отк): {st_w['p_refusal']:.4f}")
    print(f"  Среднее число занятых линий (k_cp): {st_w['k_bar']:.4f}")
    print(f"  Абсолютная пропускная способность (A): {st_w['A']:.4f} зв./час")

    # 3. Гамма-распределение
    print("\n3. Закон распределения: Гамма (η=3) для поступления, Показательный для обслуживания")
    sys_g = MMCSystem(N, LAMBDA, MU, T_MAX, arrival_dist='gamma', arrival_params={'eta': 3})
    sys_g.simulate()
    st_g = sys_g.get_stats()
    print(f"Результаты моделирования:")
    print(f"  Вероятность простоя (p0): {st_g['P'][0]:.4f}")
    print(f"  Вероятность отказа (p_отк): {st_g['p_refusal']:.4f}")
    print(f"  Среднее число занятых линий (k_cp): {st_g['k_bar']:.4f}")
    print(f"  Абсолютная пропускная способность (A): {st_g['A']:.4f} зв./час")