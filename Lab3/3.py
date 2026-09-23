import numpy as np
import sys

class SimplexSolver:
    def __init__(self):
        self.tableaux = []  # Список для хранения всех симплекс-таблиц
        self.iteration = 0  # Счетчик итераций
        self.max_iterations = 100  # Максимальное количество итераций
        self.basic_vars = []  # Для отслеживания базисных переменных
        self.all_vars = []   # Имена всех переменных

        self.no_solution = False # есть или нет решения
        
    def load_from_csv(self, filename):
        # Загружает данные задачи из CSV-файла
        # Первая строка: тип задачи (max или min)
        # Вторая строка: коэффициенты целевой функции
        # Последующие строки: матрица ограничений (последний столбец - свободные члены)
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except FileNotFoundError:
            print(f"Ошибка: Файл {filename} не найден!")
            sys.exit(1)
           
        # Удаляем символы новой строки и пробелы
        lines = [line.strip() for line in lines if line.strip()]
        
        # Определяем тип задачи
        problem_type = lines[0].strip().lower()
        maximize = (problem_type == 'max')
        
        # Коэффициенты целевой функции
        c_values = [float(x) for x in lines[1].split(',')]
        c = np.array(c_values)
        n_vars = len(c)
        
        # Создаем имена переменных: x1, x2, ... для основных
        self.all_vars = [f'x{i+1}' for i in range(n_vars)]
        
        # Матрица ограничений
        constraints_data = []
        for i in range(2, len(lines)):
            row = [float(x) for x in lines[i].split(',')]
            if len(row) != n_vars + 1:
                print(f"Ошибка: Строка {i+1} должна содержать {n_vars + 1} элементов, а содержит {len(row)}")
                sys.exit(1)
            constraints_data.append(row)
        
        constraints_array = np.array(constraints_data)
        A = constraints_array[:, :-1] # все кроме последнего столбца
        b = constraints_array[:, -1] # последний столбец
        
        # Добавляем имена дополнительных переменных
        m_constraints = len(b)
        for i in range(m_constraints):
            self.all_vars.append(f'x{n_vars + i + 1}')
        
        return A, b, c, maximize
    
    def solve(self, A, b, c, maximize=True):
        # Решает задачу линейного программирования табличным симплекс-методом
        self.iteration = 0
        self.tableaux = []
        self.basic_vars = []
        
        m, n = A.shape
        
        # Если минимизация, преобразуем в максимизацию
        if not maximize:
            c = -c
        
        # Создаем начальную симплекс-таблицу
        # Столбцы: [свободные члены, x1, x2, ..., xn, дополнительные переменные]
        table = np.zeros((m + 1, n + m + 1))
        
        # Заполняем ограничения
        for i in range(m):
            table[i, 0] = b[i]  # свободный член
            table[i, 1:n+1] = A[i, :]  # коэффициенты при основных переменных
            table[i, n + i + 1] = 1  # дополнительная переменная
        
        # Заполняем целевую функцию (последняя строка)
        table[m, 1:n+1] = -c  # коэффициенты с противоположным знаком
        
        # Инициализируем базисные переменные (дополнительные переменные)
        initial_basis = [f'x{n+i+1}' for i in range(m)]
        self.basic_vars.append(initial_basis)
        
        # Сохраняем начальную таблицу
        self.tableaux.append(table.copy())

        # выводим начальную таблицу
        print("Начальная таблица")
        self.print_table(table, self.iteration)

        # Основной цикл симплекс-метода
        while self.iteration < self.max_iterations:
            self.iteration += 1
            
            print(f"\nИтерация {self.iteration}")
            
            # Проверяем критерий оптимальности
            if self.is_optimal(table, maximize):
                print("Критерий оптимальности выполнен")
                break
            
            # Находим разрешающий столбец
            pivot_col = self.find_pivot_column(table, maximize)
            if pivot_col is None:
                print("Не удалось найти разрешающий столбец")
                self.no_solution = True
                break
            
            entering_var = self.get_var_name(pivot_col, n)
            print(f"Вводимая переменная: {entering_var} (столбец {pivot_col})")
            
            # Находим разрешающую строку
            pivot_row = self.find_pivot_row(table, pivot_col)
            if pivot_row is None:
                print("Задача не имеет конечного оптимального решения (F = ∞)")
                self.no_solution = True
                break
            
            leaving_var = self.basic_vars[-1][pivot_row]
            print(f"Выводимая переменная: {leaving_var} (строка {pivot_row})")
            print(f"Разрешающий элемент: [{pivot_row}, {pivot_col}] = {table[pivot_row, pivot_col]:.3f}")
            
            # Выполняем преобразование Жордана-Гаусса
            table = self.pivot(table, pivot_row, pivot_col)
            
            # Обновляем базисные переменные
            new_basis = self.basic_vars[-1].copy()
            new_basis[pivot_row] = entering_var
            self.basic_vars.append(new_basis)
            
            # Сохраняем таблицу
            self.tableaux.append(table.copy())
            
            # Проверяем на зацикливание
            if self.check_cycling():
                print("Обнаружено зацикливание!")
                self.no_solution = True
                break

            # выводим таблицу
            self.print_table(table, self.iteration)
        else:
            print("Достигнуто максимальное количество итераций")
            self.no_solution = True
        
        return table
    
    def get_var_name(self, col_index, n_vars):
        # Возвращает имя переменной по индексу столбца
        if col_index == 0:
            return "B"
        elif 1 <= col_index <= len(self.all_vars):
            return self.all_vars[col_index - 1]
        else:
            return f"x{col_index}"
    
    def is_optimal(self, table, maximize):
        # Проверяет критерий оптимальности
        last_row = table[-1, 1:]  # исключаем столбец свободных членов
        
        if maximize:
            return np.all(last_row >= -1e-10)
        else:
            return np.all(last_row <= 1e-10)
    
    def find_pivot_column(self, table, maximize):
        # Находит разрешающий столбец
        last_row = table[-1, 1:]  # исключаем столбец свободных членов
        
        if maximize:
            negative_indices = np.where(last_row < -1e-10)[0]
            if len(negative_indices) == 0:
                return None
            # Выбираем столбец с наименьшим значением (наибольший по модулю отрицательный)
            pivot_col = negative_indices[np.argmin(last_row[negative_indices])] + 1
        else:
            positive_indices = np.where(last_row > 1e-10)[0]
            if len(positive_indices) == 0:
                return None
            # Выбираем столбец с наибольшим значением
            pivot_col = positive_indices[np.argmax(last_row[positive_indices])] + 1
        
        return pivot_col
    
    def find_pivot_row(self, table, pivot_col):
        # Находит разрешающую строку по минимальному отношению
        m = table.shape[0] - 1
        
        min_ratio = float('inf')
        pivot_row = None
        
        for i in range(m):
            if table[i, pivot_col] > 1e-10:  # a_is > 0
                ratio = table[i, 0] / table[i, pivot_col]
                if ratio >= 0 and ratio < min_ratio - 1e-10:
                    min_ratio = ratio
                    pivot_row = i
        
        return pivot_row
    
    def pivot(self, table, pivot_row, pivot_col):
        # Выполняет преобразование матрицы
        new_table = table.copy()
        pivot_element = table[pivot_row, pivot_col]
        
        # Нормализуем разрешающую строку
        new_table[pivot_row, :] = table[pivot_row, :] / pivot_element
        
        # Обновляем остальные строки
        for i in range(table.shape[0]):
            if i != pivot_row:
                factor = table[i, pivot_col] / pivot_element
                new_table[i, :] = table[i, :] - factor * table[pivot_row, :]
        
        return new_table
    
    def check_cycling(self):
        # Проверяет наличие зацикливания
        if len(self.tableaux) < 3:
            return False
        
        current = self.tableaux[-1]
        for i in range(len(self.tableaux) - 2):
            if np.allclose(current, self.tableaux[i], atol=1e-6):
                return True
        
        return False
    
    def print_table(self, table, tableau_index):
        # Выводит одну симплекс-таблицу
        m, n = table.shape
        
        # Заголовок таблицы
        headers = ["Базис", "Св.член"]
        headers.extend(self.all_vars)
        
        # Выводим заголовок
        header_line = " | ".join(f"{header:>10}" for header in headers)
        print(header_line)
        print("-" * len(header_line))
        
        # Выводим строки ограничений
        basis_vars = self.basic_vars[tableau_index]
        
        for i in range(m - 1):
            if i < len(basis_vars):
                row_name = basis_vars[i]
                row = [row_name, f"{table[i, 0]:.3f}"]
                row.extend(f"{table[i, j]:.3f}" for j in range(1, n))
                print(" | ".join(f"{item:>10}" for item in row))
        
        # Выводим целевую функцию
        row = ["F", f"{table[m-1, 0]:.3f}"]
        row.extend(f"{table[m-1, j]:.3f}" for j in range(1, n))
        print(" | ".join(f"{item:>10}" for item in row))
        
        # Выводим текущий базис
        print(f"Текущий базис: {', '.join(basis_vars)}")
    
    def get_solution(self, table, maximize=True):
        # Извлекает решение из конечной симплекс-таблицы
        solution = np.zeros(len(self.all_vars))
        
        # Получаем текущий базис
        current_basis = self.basic_vars[-1]
        
        # Для каждой базисной переменной находим ее значение
        for i, var_name in enumerate(current_basis):
            if i < len(table):
                # Находим индекс переменной в all_vars
                if var_name in self.all_vars:
                    var_index = self.all_vars.index(var_name)
                    solution[var_index] = table[i, 0]
        
        # Значение целевой функции
        optimal_value = table[-1, 0]
        if not maximize:
            optimal_value = -optimal_value
        
        return solution, optimal_value


# Загружаем данные
solver = SimplexSolver()
try:
    A, b, c, maximize = solver.load_from_csv('input.csv')
except Exception as e:
    print(f"Ошибка при загрузке данных: {e}")
    exit(-1)
    
# Решаем задачу
final_table = solver.solve(A, b, c, maximize)
    
# Выводим результат
solution, optimal_value = solver.get_solution(final_table, maximize)
    
print(f"\n{'='*9}")
print("Результат")
print(f"{'='*9}")
print(f"Количество итераций: {solver.iteration}")
print(f"Статус: {'Оптимального решения нет' if solver.no_solution else 'Оптимальное решение найдено'}")

print(f"Полученное решение:")
for i, var_name in enumerate(solver.all_vars):
    if i < len(c):  # Только основные переменные
        print(f"{var_name} = {solution[i]:.3f}")
        
print(f"Значение целевой функции F = {optimal_value:.3f}")