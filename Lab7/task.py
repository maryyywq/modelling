import math
import csv
import sys


class SMOCalculator:
    def __init__(self):
        self.params = {}
        self.system_type = ""
        self.results = {}

    # ==================== ВВОД ====================

    def load_from_csv(self, filename='input.csv'):
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                line = file.readline().strip()
                if not line:
                    print("Файл пустой")
                    return False

                values = line.split(';')

                if len(values) >= 4:
                    try:
                        self.params['lambda'] = float(values[0])
                        self.params['mu'] = float(values[1])
                        self.params['n'] = int(float(values[2]))

                        m_str = values[3].strip().lower()
                        if m_str in ['inf', 'бесконечность', '∞', '']:
                            self.params['m'] = None
                        else:
                            self.params['m'] = int(float(m_str))

                        print("\nПараметры успешно загружены:")
                        print(f"  λ = {self.params['lambda']}")
                        print(f"  μ = {self.params['mu']}")
                        print(f"  n = {self.params['n']}")
                        print(f"  m = "
                              f"{self.params['m'] if self.params['m'] is not None else 'бесконечность'}")
                        return True

                    except ValueError as e:
                        print(f"Ошибка преобразования данных: {e}")
                        return False
                else:
                    print("Недостаточно параметров в файле")
                    return False

        except FileNotFoundError:
            print(f"Файл {filename} не найден")
            print("Создайте файл input.csv с содержимым вида: λ; μ; n; m")
            print("где m может быть 'inf' для бесконечной очереди")
            return False
        except Exception as e:
            print(f"Ошибка при чтении файла: {e}")
            return False

    # ==================== ВАЛИДАЦИЯ ====================

    def _validate_rates(self):
        lam = self.params.get('lambda')
        mu = self.params.get('mu')
        if lam is None or mu is None:
            print("Ошибка валидации: не заданы λ или μ")
            return False
        if lam <= 0:
            print(f"Ошибка валидации: λ должно быть > 0 (получено {lam})")
            return False
        if mu <= 0:
            print(f"Ошибка валидации: μ должно быть > 0 (получено {mu})")
            return False
        return True

    def _validate_n(self, min_n=1):
        n = self.params.get('n')
        if n is None:
            print("Ошибка валидации: не задан параметр n")
            return False
        if n < min_n:
            print(f"Ошибка валидации: n должно быть ≥ {min_n} (получено {n})")
            return False
        return True

    def _validate_m(self, min_m=0):
        m = self.params.get('m')
        if m is None:
            print("Ошибка валидации: для этого типа СМО параметр m обязателен (конечное число)")
            return False
        if m < min_m:
            print(f"Ошибка валидации: m должно быть ≥ {min_m} (получено {m})")
            return False
        return True

    # ==================== ВЫБОР ТИПА ====================

    def select_system_type(self):
        print("\nВыберите тип системы:")
        print("1. M|M|n|0  (многоканальная с отказами)")
        print("2. M|M|1|m  (одноканальная с ограниченной очередью)")
        print("3. M|M|1|∞  (одноканальная с неограниченной очередью)")
        print("4. M|M|n|m  (многоканальная с ограниченной очередью)")
        print("5. M|M|n|∞  (многоканальная с неограниченной очередью)")
        print("6. Замкнутая одноканальная СМО")
        print("7. Замкнутая многоканальная СМО")

        while True:
            choice = input("Введите номер типа системы (1-7): ").strip()

            if choice == '1':
                self.system_type = "M|M|n|0"
                return True
            elif choice == '2':
                self.system_type = "M|M|1|m"
                return True
            elif choice == '3':
                self.system_type = "M|M|1|∞"
                return True
            elif choice == '4':
                self.system_type = "M|M|n|m"
                return True
            elif choice == '5':
                self.system_type = "M|M|n|∞"
                return True
            elif choice == '6':
                self.system_type = "Замкнутая одноканальная"
                return True
            elif choice == '7':
                self.system_type = "Замкнутая многоканальная"
                return True
            else:
                print("Неверный выбор. Попробуйте снова.")

    # ==================== РАСЧЁТЫ ====================

    def calculate_mmn_0(self):
        if not self._validate_rates():
            return False
        if not self._validate_n(min_n=1):
            return False

        lambd = self.params['lambda']
        mu = self.params['mu']
        n = self.params['n']

        rho = lambd / mu

        sum_series = 0.0
        for k in range(n + 1):
            sum_series += rho**k / math.factorial(k)

        p0 = 1.0 / sum_series
        pn = (rho**n / math.factorial(n)) * p0

        p_otk = pn
        q = 1 - p_otk
        A = lambd * q
        k_sr = rho * (1 - pn)

        self.results = {
            'Тип системы': self.system_type,
            'Параметры': f'λ={lambd}, μ={mu}, n={n}',
            'ρ (приведенная интенсивность)': rho,
            'p₀ (вероятность простоя)': p0,
        }
        # Промежуточные вероятности p_1..p_{n-1}
        for k in range(1, n):
            self.results[f'p_{k} (вероятность того, что занято {k} каналов)'] = \
                (rho**k / math.factorial(k)) * p0
        self.results.update({
            'pₙ (вероятность занятости всех каналов)': pn,
            'p_отк (вероятность отказа)': p_otk,
            'q (относительная пропускная способность)': q,
            'A (абсолютная пропускная способность)': A,
            'k_ср (среднее число занятых каналов)': k_sr,
        })
        return True

    def calculate_mm1_m(self):
        if not self._validate_rates():
            return False
        if not self._validate_n(min_n=1):
            return False
        if self.params['n'] != 1:
            print(f"Предупреждение: для M|M|1|m параметр n должен быть 1 "
                  f"(получено {self.params['n']}). Будет использовано n=1.")
            self.params['n'] = 1
        if not self._validate_m(min_m=0):
            return False

        lambd = self.params['lambda']
        mu = self.params['mu']
        m = self.params['m']

        rho = lambd / mu
        rho_is_one = math.isclose(rho, 1.0, rel_tol=1e-9, abs_tol=1e-12)

        if rho_is_one:
            # ρ = 1 — предельный случай
            p0 = 1.0 / (m + 2)
            p = [p0] * (m + 2)
            r_sr = m * (m + 1) / (2.0 * (m + 2))
            omega_sr = (m + 1) / (m + 2.0)
        else:
            p0 = (1 - rho) / (1 - rho**(m + 2))
            p = [0.0] * (m + 2)
            p[0] = p0
            for k in range(1, m + 2):
                p[k] = rho**k * p0
            numerator = rho**2 * (1 - rho**m * (m + 1 - m * rho))
            denominator = (1 - rho**(m + 2)) * (1 - rho)
            r_sr = numerator / denominator
            omega_sr = (rho - rho**(m + 2)) / (1 - rho**(m + 2))

        p_otk = p[m + 1]
        q = 1 - p_otk
        A = lambd * q
        v_sr = r_sr + omega_sr
        t_ozh = r_sr / lambd
        t_sist = t_ozh + q / mu

        self.results = {
            'Тип системы': self.system_type,
            'Параметры': f'λ={lambd}, μ={mu}, m={m}',
            'ρ (коэффициент загрузки)': rho,
            'p₀ (вероятность простоя)': p0,
            'p_отк (вероятность отказа)': p_otk,
            'q (относительная пропускная способность)': q,
            'A (абсолютная пропускная способность)': A,
            'r_ср (средняя длина очереди)': r_sr,
            'ω_ср (среднее число заявок под обслуживанием)': omega_sr,
            'v_ср (среднее число заявок в системе)': v_sr,
            't_ож (среднее время ожидания)': t_ozh,
            't_сист (среднее время пребывания в системе)': t_sist,
        }
        return True

    def calculate_mm1_inf(self):
        if not self._validate_rates():
            return False
        if not self._validate_n(min_n=1):
            return False
        if self.params['n'] != 1:
            print(f"Предупреждение: для M|M|1|∞ параметр n должен быть 1 "
                  f"(получено {self.params['n']}). Будет использовано n=1.")
            self.params['n'] = 1

        lambd = self.params['lambda']
        mu = self.params['mu']
        rho = lambd / mu

        if rho >= 1 or math.isclose(rho, 1.0, rel_tol=1e-9, abs_tol=1e-12):
            self.results = {
                'Тип системы': self.system_type,
                'Параметры': f'λ={lambd}, μ={mu}',
                'ρ (коэффициент загрузки)': rho,
                'Статус': 'Очередь растёт бесконечно',
                'Причина': 'ρ ≥ 1, стационарного режима не существует',
                'Рекомендация': 'Увеличьте интенсивность обслуживания μ или уменьшите λ',
            }
            return True

        p0 = 1 - rho
        r_sr = rho**2 / (1 - rho)
        v_sr = rho / (1 - rho)
        t_ozh = rho / (mu * (1 - rho))
        t_sist = 1 / (mu * (1 - rho))

        self.results = {
            'Тип системы': self.system_type,
            'Параметры': f'λ={lambd}, μ={mu}',
            'ρ (коэффициент загрузки)': rho,
            'Условие стационарности': 'ρ < 1 — выполнено',
            'p₀ (вероятность простоя)': p0,
            'r_ср (средняя длина очереди)': r_sr,
            'v_ср (среднее число заявок в системе)': v_sr,
            't_ож (среднее время ожидания)': t_ozh,
            't_сист (среднее время пребывания в системе)': t_sist,
        }
        return True

    def calculate_mmn_m(self):
        if not self._validate_rates():
            return False
        if not self._validate_n(min_n=1):
            return False
        if not self._validate_m(min_m=0):
            return False

        lambd = self.params['lambda']
        mu = self.params['mu']
        n = self.params['n']
        m = self.params['m']

        rho = lambd / mu
        gamma = rho / n
        gamma_is_one = math.isclose(gamma, 1.0, rel_tol=1e-9, abs_tol=1e-12)

        sum1 = 0.0
        for k in range(n + 1):
            sum1 += rho**k / math.factorial(k)

        if gamma_is_one:
            sum2 = m
        else:
            sum2 = gamma * (1 - gamma**m) / (1 - gamma)

        p0 = 1.0 / (sum1 + (rho**n / math.factorial(n)) * sum2)

        p_otk = (rho**(n + m) / (n**m * math.factorial(n))) * p0
        q = 1 - p_otk
        A = lambd * q
        k_sr = rho * (1 - p_otk)

        if gamma_is_one:
            r_sr = (rho**(n + 1) * p0 / (math.factorial(n) * n)) * (m * (m + 1) / 2.0)
        else:
            numerator = rho**(n + 1) * p0 * (1 - (m + 1) * gamma**m + m * gamma**(m + 1))
            denominator = math.factorial(n) * n * (1 - gamma)**2
            r_sr = numerator / denominator

        v_sr = k_sr + r_sr
        t_ozh = r_sr / lambd
        t_sist = t_ozh + q / mu

        self.results = {
            'Тип системы': self.system_type,
            'Параметры': f'λ={lambd}, μ={mu}, n={n}, m={m}',
            'ρ (коэффициент загрузки)': rho,
            'γ (ρ/n)': gamma,
            'p₀ (вероятность простоя)': p0,
            'p_отк (вероятность отказа)': p_otk,
            'q (относительная пропускная способность)': q,
            'A (абсолютная пропускная способность)': A,
            'k_ср (среднее число занятых каналов)': k_sr,
            'r_ср (средняя длина очереди)': r_sr,
            'v_ср (среднее число заявок в системе)': v_sr,
            't_ож (среднее время ожидания)': t_ozh,
            't_сист (среднее время пребывания в системе)': t_sist,
        }
        return True

    def calculate_mmn_inf(self):
        if not self._validate_rates():
            return False
        if not self._validate_n(min_n=1):
            return False

        lambd = self.params['lambda']
        mu = self.params['mu']
        n = self.params['n']

        rho = lambd / mu
        gamma = rho / n

        if gamma >= 1 or math.isclose(gamma, 1.0, rel_tol=1e-9, abs_tol=1e-12):
            self.results = {
                'Тип системы': self.system_type,
                'Параметры': f'λ={lambd}, μ={mu}, n={n}',
                'ρ (коэффициент загрузки)': rho,
                'γ (ρ/n)': gamma,
                'Статус': 'Очередь растёт бесконечно',
                'Причина': 'γ ≥ 1, стационарного режима не существует',
                'Рекомендация': f'Увеличьте число каналов n > {rho} или уменьшите λ',
            }
            return True

        sum1 = 0.0
        for k in range(n + 1):
            sum1 += rho**k / math.factorial(k)

        sum2 = rho**(n + 1) / (math.factorial(n) * (n - rho))

        p0 = 1.0 / (sum1 + sum2)

        r_sr = (rho**(n + 1) * p0) / (math.factorial(n) * n * (1 - gamma)**2)
        k_sr = rho
        v_sr = k_sr + r_sr
        t_ozh = r_sr / lambd
        t_sist = t_ozh + 1 / mu

        self.results = {
            'Тип системы': self.system_type,
            'Параметры': f'λ={lambd}, μ={mu}, n={n}',
            'ρ (коэффициент загрузки)': rho,
            'γ (ρ/n)': gamma,
            'Условие стационарности': 'γ < 1 — выполнено',
            'p₀ (вероятность простоя)': p0,
            'r_ср (средняя длина очереди)': r_sr,
            'k_ср (среднее число занятых каналов)': k_sr,
            'v_ср (среднее число заявок в системе)': v_sr,
            't_ож (среднее время ожидания)': t_ozh,
            't_сист (среднее время пребывания в системе)': t_sist,
        }
        return True

    def calculate_closed_mm1(self):
        # N = число источников (станков) задаётся в позиции n входного файла
        if not self._validate_rates():
            return False
        if not self._validate_n(min_n=1):
            return False

        N = self.params['n']
        lambd = self.params['lambda']
        mu = self.params['mu']

        rho = lambd / mu

        sum_series = 0.0
        for i in range(N + 1):
            sum_series += math.factorial(N) / math.factorial(N - i) * rho**i

        p0 = 1.0 / sum_series
        A = (1 - p0) * mu
        z_sr = N - (1 - p0) / rho
        omega_sr = 1 - p0
        r_sr = z_sr - omega_sr
        Lambda_sr = A

        t_ozh = r_sr / Lambda_sr if Lambda_sr > 0 else 0.0
        t_sist = z_sr / Lambda_sr if Lambda_sr > 0 else 0.0

        self.results = {
            'Тип системы': self.system_type,
            'Параметры': f'N={N} источников, λ={lambd}, μ={mu}',
            'ρ (коэффициент загрузки)': rho,
            'p₀ (вероятность простоя рабочего)': p0,
            'A (абсолютная пропускная способность)': A,
            'z_ср (среднее число неисправных станков)': z_sr,
            'ω_ср (среднее число станков под обслуживанием)': omega_sr,
            'r_ср (среднее число станков в очереди)': r_sr,
            'Λ_ср (средняя интенсивность входящего потока)': Lambda_sr,
            't_ож (среднее время ожидания ремонта)': t_ozh,
            't_сист (среднее время в системе)': t_sist,
            'Коэффициент простоя станков': z_sr / N if N > 0 else 0.0,
            'Коэффициент занятости рабочего': 1 - p0,
        }
        return True

    def calculate_closed_mmn(self):
        # N — число источников (станков) в позиции n
        # m — число каналов (рабочих) в позиции m
        if not self._validate_rates():
            return False
        if not self._validate_n(min_n=1):
            return False

        N = self.params['n']
        lambd = self.params['lambda']
        mu = self.params['mu']

        m = self.params['m']
        if m is None:
            print("Ошибка валидации: для замкнутой многоканальной СМО "
                  "параметр m (число каналов) обязателен")
            return False
        if m < 1:
            print(f"Ошибка валидации: число каналов m должно быть ≥ 1 (получено {m})")
            return False
        if m > N:
            print(f"Ошибка валидации: число каналов m={m} "
                  f"не может превышать число источников N={N}")
            return False

        rho = lambd / mu

        sum_series = 0.0
        for i in range(m + 1):
            sum_series += (math.factorial(N) /
                           (math.factorial(i) * math.factorial(N - i))) * rho**i
        for i in range(m + 1, N + 1):
            sum_series += (math.factorial(N) /
                           (math.factorial(m) * math.factorial(N - i) *
                            m**(i - m))) * rho**i

        p0 = 1.0 / sum_series

        p = [0.0] * (N + 1)
        p[0] = p0
        for i in range(1, m + 1):
            p[i] = (math.factorial(N) /
                    (math.factorial(i) * math.factorial(N - i))) * rho**i * p0
        for i in range(m + 1, N + 1):
            p[i] = (math.factorial(N) /
                    (math.factorial(m) * math.factorial(N - i) *
                     m**(i - m))) * rho**i * p0

        k_sr = 0.0
        for i in range(1, m + 1):
            k_sr += i * p[i]
        for i in range(m + 1, N + 1):
            k_sr += m * p[i]

        A = k_sr * mu
        z_sr = N - k_sr / rho
        r_sr = z_sr - k_sr
        Lambda_sr = A

        t_ozh = r_sr / Lambda_sr if Lambda_sr > 0 else 0.0
        t_sist = z_sr / Lambda_sr if Lambda_sr > 0 else 0.0

        self.results = {
            'Тип системы': self.system_type,
            'Параметры': f'N={N} источников, m={m} каналов, λ={lambd}, μ={mu}',
            'ρ (коэффициент загрузки)': rho,
            'p₀ (вероятность простоя всех рабочих)': p0,
            'A (абсолютная пропускная способность)': A,
            'k_ср (среднее число занятых рабочих)': k_sr,
            'z_ср (среднее число неисправных станков)': z_sr,
            'r_ср (среднее число станков в очереди)': r_sr,
            'Λ_ср (средняя интенсивность входящего потока)': Lambda_sr,
            't_ож (среднее время ожидания ремонта)': t_ozh,
            't_сист (среднее время в системе)': t_sist,
            'Коэффициент простоя станков': z_sr / N if N > 0 else 0.0,
            'Коэффициент занятости рабочих': k_sr / m if m > 0 else 0.0,
        }
        return True

    # ==================== ДИСПЕТЧЕР ====================

    def calculate(self):
        if not self.params:
            print("Нет загруженных параметров")
            return False

        if self.system_type == "M|M|n|0":
            return self.calculate_mmn_0()
        elif self.system_type == "M|M|1|m":
            return self.calculate_mm1_m()
        elif self.system_type == "M|M|1|∞":
            return self.calculate_mm1_inf()
        elif self.system_type == "M|M|n|m":
            return self.calculate_mmn_m()
        elif self.system_type == "M|M|n|∞":
            return self.calculate_mmn_inf()
        elif self.system_type == "Замкнутая одноканальная":
            return self.calculate_closed_mm1()
        elif self.system_type == "Замкнутая многоканальная":
            return self.calculate_closed_mmn()
        else:
            print("Неизвестный тип системы")
            return False

    def print_results(self):
        if not self.results:
            print("Нет результатов для вывода")
            return

        print("\nРезультаты расчёта характеристик СМО")
        print(f"Тип системы: {self.results.get('Тип системы', 'Не указан')}")
        print(f"Параметры: {self.results.get('Параметры', 'Не указаны')}")

        for key, value in self.results.items():
            if key in ('Тип системы', 'Параметры'):
                continue
            if isinstance(value, float):
                print(f"{key}: {value:.6f}")
            else:
                print(f"{key}: {value}")


def main():
    print("Программа для расчёта характеристик СМО")

    calculator = SMOCalculator()

    while True:
        filename = input("\nВведите имя файла с параметрами "
                         "(по умолчанию input.csv): ").strip()
        if filename == '':
            filename = 'input.csv'

        if not calculator.load_from_csv(filename):
            choice = input("Хотите попробовать другой файл? (да/нет): ").strip().lower()
            if choice in ('да', 'yes', 'y', 'д'):
                continue
            break

        if not calculator.select_system_type():
            break

        if calculator.calculate():
            calculator.print_results()
        else:
            print("Ошибка при расчёте характеристик")

        print("\nВыберите действие:")
        print("1. Загрузить новые параметры")
        print("2. Выйти из программы")

        choice = input("Ваш выбор (1-2): ").strip()
        if choice == '1':
            continue
        elif choice == '2':
            print("Выход из программы...")
            break
        else:
            print("Неверный выбор. Продолжаем с новыми параметрами.")


if __name__ == "__main__":
    main()