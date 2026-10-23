import numpy as np  
import heapq 
import random  
import math  
from math import factorial  
from scipy.special import gamma as gamma_func  

class MMCSystem:  # Объявление класса, описывающего многоканальную СМО с отказами
    """
    Многоканальная СМО с отказами (очереди нет).
    Состояния: 0..n — число занятых каналов.
    Поддерживаемые законы: 'exponential' (показательный), 'weibull' (Вейбула), 'gamma' (Гамма).
    """
    
    def __init__(self, n_channels, lambda_rate, mu_rate, T_max=10_000.0,
                 arrival_dist='exponential', arrival_params=None,
                 service_dist='exponential', service_params=None):
        self.n = n_channels  # Сохраняем число каналов
        self.lambda_rate = lambda_rate  # Сохраняем интенсивность входящего потока заявок
        self.mu_rate = mu_rate  # Сохраняем интенсивность обслуживания одной линии
        self.T_max = T_max  # Сохраняем общее время, сколько будем моделировать систему
        self.arrival_dist = arrival_dist  # Сохраняем тип закона для входящего потока
        self.service_dist = service_dist  # Сохраняем тип закона для обслуживания
        self.arrival_params = arrival_params or {}  # Сохраняем доп. параметры для закона поступления (например, 'a' или 'eta')
        self.service_params = service_params or {}  # Сохраняем доп. параметры для закона обслуживания

        # Предвычисление параметров для Вейбулла (масштаб b подбирается так, чтобы среднее было 1/lambda или 1/mu)
        self._arr_a, self._arr_b = None, None  # Инициализируем переменные для параметров Вейбулла (входящий поток)
        if arrival_dist == 'weibull':  # Если выбран закон Вейбулла для поступления
            a = self.arrival_params.get('a', 2.0)  # Берем параметр формы 'a' (по умолчанию 2.0)
            self._arr_a = a  # Запоминаем параметр формы
            self._arr_b = (1.0 / lambda_rate) / gamma_func(1.0 + 1.0 / a)  # Вычисляем масштаб b так, чтобы мат. ожидание совпало с 1/lambda
            
        self._srv_a, self._srv_b = None, None  # Инициализируем переменные для параметров Вейбулла (обслуживание)
        if service_dist == 'weibull':  # Если выбран закон Вейбулла для обслуживания
            a = self.service_params.get('a', 2.0)  # Берем параметр формы 'a'
            self._srv_a = a  # Запоминаем параметр формы
            self._srv_b = (1.0 / mu_rate) / gamma_func(1.0 + 1.0 / a)  # Вычисляем масштаб b так, чтобы среднее было 1/mu

        # Статистика для сбора результатов
        self.state_times = np.zeros(n_channels + 1)  # Массив для накопления времени пребывания в каждом состоянии (от 0 до n)
        self.total_arrivals = 0  # Счетчик всех пришедших заявок
        self.served = 0  # Счетчик успешно обслуженных заявок
        self.refusals = 0  # Счетчик заявок, получивших отказ

    def _gen_exp(self, rate):  # Вспомогательный метод для генерации случайного числа по показательному закону
        return -math.log(1.0 - random.random()) / rate  # Формула обратного преобразования: -1/lambda * ln(R)

    def _gen_weibull_arr(self):  # Метод генерации времени поступления по закону Вейбулла
        return self._arr_b * (-math.log(1.0 - random.random())) ** (1.0 / self._arr_a)  # Формула обратного преобразования для Вейбулла

    def _gen_weibull_srv(self):  # Метод генерации времени обслуживания по закону Вейбулла
        return self._srv_b * (-math.log(1.0 - random.random())) ** (1.0 / self._srv_a)  # Аналогичная формула для обслуживания

    def _gen_gamma(self, rate, eta):  # Метод генерации по гамма-распределению (с целым параметром формы eta)
        return sum(-math.log(1.0 - random.random()) for _ in range(eta)) / (eta * rate)  # Суммируем eta экспоненциальных величин и делим на eta*rate

    def gen_interarrival(self):  # Метод, который выбирает нужный генератор для интервала прибытия
        if self.arrival_dist == 'exponential': return self._gen_exp(self.lambda_rate)  # Если выбран показательный закон
        if self.arrival_dist == 'weibull': return self._gen_weibull_arr()  # Если выбран закон Вейбулла
        if self.arrival_dist == 'gamma': return self._gen_gamma(self.lambda_rate, self.arrival_params.get('eta', 3))  # Если выбрана гамма
        raise ValueError(self.arrival_dist)  # Если передали неизвестный закон, выдаем ошибку

    def gen_service(self):  # Метод, который выбирает нужный генератор для времени обслуживания
        if self.service_dist == 'exponential': return self._gen_exp(self.mu_rate)  # Если выбран показательный закон
        if self.service_dist == 'weibull': return self._gen_weibull_srv()  # Если выбран закон Вейбулла
        if self.service_dist == 'gamma': return self._gen_gamma(self.mu_rate, self.service_params.get('eta', 3))  # Если выбрана гамма
        raise ValueError(self.service_dist)  # Если передали неизвестный закон, выдаем ошибку

    def simulate(self):  # Главный метод, запускающий процесс дискретно-событийного моделирования
        events = []  # Создаем пустой список, который будет играть роль приоритетной очереди событий
        heapq.heappush(events, (self.gen_interarrival(), 1, 1, -1))  # Планируем самое первое событие "прибытие"
        channel_free = [0.0] * self.n  # Массив, хранящий время, когда каждый канал станет свободным (изначально все 0.0)
        busy = 0  # Счетчик текущего количества занятых каналов (изначально система пуста)
        last_change = 0.0  # Переменная для хранения времени предыдущего события

        while events:  # Основной цикл: работает, пока в очереди есть события
            event_time, _, kind, channel = heapq.heappop(events)  # Достаем ближайшее по времени событие из очереди
            if event_time > self.T_max:  # Если время события вышло за пределы моделирования
                break  # Прерываем цикл моделирования

            self.state_times[busy] += event_time - last_change  # Накапливаем время, которое система провела в текущем состоянии
            last_change = event_time  # Обновляем время последнего изменения состояния

            if kind == 1:  # Если тип события равен 1, значит это "прибытие" заявки
                self.total_arrivals += 1  # Увеличиваем общий счетчик пришедших заявок
                free_ch = -1  # Переменная для хранения номера найденного свободного канала (-1 значит не найден)
                for i in range(self.n):  # Перебираем все каналы, чтобы найти свободный
                    if channel_free[i] <= event_time:  # Если канал освободился до текущего момента времени
                        free_ch = i  # Запоминаем номер этого свободного канала
                        break  # Выходим из цикла поиска, так как нашли свободный
                
                if free_ch >= 0:  # Если свободный канал найден
                    s = self.gen_service()  # Генерируем случайное время обслуживания
                    channel_free[free_ch] = event_time + s  # Записываем время, когда этот канал освободится
                    self.served += 1  # Увеличиваем счетчик обслуженных заявок
                    busy += 1  # Увеличиваем счетчик занятых каналов
                    heapq.heappush(events, (channel_free[free_ch], 0, 0, free_ch))  # Планируем событие "завершение обслуживания" (приоритет 0, чтобы шло раньше прибытий)
                else:  # Если свободного канала нет (все заняты)
                    self.refusals += 1  # Увеличиваем счетчик отказов (заявка уходит ни с чем)
                
                heapq.heappush(events, (event_time + self.gen_interarrival(), 1, 1, -1))  # Планируем следующее событие "прибытие" (приоритет 1)
            else:  # Иначе тип события 0, значит это "завершение обслуживания"
                busy -= 1  # Уменьшаем счетчик занятых каналов, так как один канал освободился

        self.state_times[busy] += self.T_max - last_change  # Добавляем остаток времени до T_max в текущее состояние

    def get_stats(self):  # Метод для расчета итоговых статистических характеристик
        total = float(np.sum(self.state_times))  # Считаем общее время моделирования (сумма по всем состояниям)
        P = self.state_times / total  # Находим вероятности состояний (делим время в состоянии на общее время)
        p_refusal = self.refusals / self.total_arrivals if self.total_arrivals > 0 else 0.0  # Вероятность отказа (отказы / всего заявок)
        return {  # Возвращаем словарь с результатами
            'P': P, 'p_refusal': p_refusal, 'q': 1.0 - p_refusal,  # Вероятности, отказ и относительная пропускная способность
            'A': self.lambda_rate * (1.0 - p_refusal),  # Абсолютная пропускная способность
            'k_bar': sum(i * P[i] for i in range(self.n + 1)),  # Среднее число занятых линий (мат. ожидание)
            'total': self.total_arrivals, 'served': self.served, 'refusals': self.refusals  # Счетчики заявок
        }

def analytical_mmn0(n, lambda_rate, mu_rate):  # Функция для расчета аналитических характеристик СМО M/M/n/0
    rho = lambda_rate / mu_rate  # Вычисляем приведенную интенсивность нагрузки (ро)
    denom = sum(rho ** k / factorial(k) for k in range(n + 1))  # Считаем знаменатель для формулы Эрланга (сумма ро^k / k!)
    P = np.array([rho ** k / factorial(k) / denom for k in range(n + 1)])  # Вычисляем массив вероятностей состояний
    return {  # Возвращаем словарь с аналитическими результатами
        'rho': rho, 'P': P, 'p_refusal': P[n], 'q': 1.0 - P[n],  # Нагрузка, вероятности, отказ и пропускная способность
        'A': lambda_rate * (1.0 - P[n]), 'k_bar': sum(k * P[k] for k in range(n + 1))  # Абсолютная пропускная способность и среднее число занятых
    }

if __name__ == '__main__':  
    random.seed(42)  
    np.random.seed(42)  

    LAMBDA = 42.0  # Задаем интенсивность поступления (42 звонка в час по условию)
    MU = 13.0  # Задаем интенсивность обслуживания одной линии (13 звонков в час)
    N = 3  # Задаем количество каналов/линий (3 линии)
    T_MAX = 50_000.0  # Задаем время моделирования (50 000 часов достаточно для стационара)

    print("Моделирование многоканальной СМО методом Монте-Карло")  
    print("Параметры системы:")  
    print(f"  λ = {LAMBDA} звонков/час") 
    print(f"  μ = {MU} звонков/час")  
    print(f"  n = {N} линии")  
    print(f"  T = {T_MAX} часов моделирования")  
    print("  Очередь не предусмотрена (при занятости всех линий - отказ)")  

    print("\n1. Закон распределения: Показательный (экспоненциальный)")  # Начинаем блок с показательным законом
    sys1 = MMCSystem(N, LAMBDA, MU, T_MAX)  # Создаем объект системы (по умолчанию используются показательные законы)
    sys1.simulate()  # Запускаем моделирование
    st1 = sys1.get_stats()  # Получаем результаты моделирования
    ana = analytical_mmn0(N, LAMBDA, MU)  # Считаем аналитические значения для проверки

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

    print("\n2. Закон распределения: Вейбула (a=2) для поступления, Показательный для обслуживания")  # Переходим к закону Вейбулла
    sys_w = MMCSystem(N, LAMBDA, MU, T_MAX, arrival_dist='weibull', arrival_params={'a': 2.0})  # Создаем систему с законом Вейбулла на входе
    sys_w.simulate()  # Запускаем моделирование
    st_w = sys_w.get_stats()  # Получаем результаты
    print(f"Результаты моделирования:")  
    print(f"  Вероятность простоя (p0): {st_w['P'][0]:.4f}") 
    print(f"  Вероятность отказа (p_отк): {st_w['p_refusal']:.4f}")  
    print(f"  Среднее число занятых линий (k_cp): {st_w['k_bar']:.4f}") 
    print(f"  Абсолютная пропускная способность (A): {st_w['A']:.4f} зв./час") 

    print("\n3. Закон распределения: Гамма (η=3) для поступления, Показательный для обслуживания")  # Переходим к гамма-распределению
    sys_g = MMCSystem(N, LAMBDA, MU, T_MAX, arrival_dist='gamma', arrival_params={'eta': 3})  # Создаем систему с гамма-распределением на входе
    sys_g.simulate()  # Запускаем моделирование
    st_g = sys_g.get_stats()  # Получаем результаты
    print(f"Результаты моделирования:")  
    print(f"  Вероятность простоя (p0): {st_g['P'][0]:.4f}") 
    print(f"  Вероятность отказа (p_отк): {st_g['p_refusal']:.4f}") 
    print(f"  Среднее число занятых линий (k_cp): {st_g['k_bar']:.4f}") 
    print(f"  Абсолютная пропускная способность (A): {st_g['A']:.4f} зв./час")  