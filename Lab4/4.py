import numpy as np
import csv


# Класс, описывающий транспортную задачу
class TransportProblem:
    # Конструктор: принимает запасы, потребности и матрицу стоимостей
    def __init__(self, supplies, demands, costs):
        # Копируем список запасов поставщиков
        self.supplies = list(supplies)
        # Копируем список потребностей потребителей
        self.demands = list(demands)
        # Глубокая копия матрицы тарифов
        self.costs = [list(row) for row in costs]
        # Количество поставщиков (число строк)
        self.n = len(self.supplies)
        # Количество потребителей (число столбцов)
        self.m = len(self.demands)

        # Суммарный запас всех поставщиков
        total_supply = sum(self.supplies)
        # Суммарная потребность всех потребителей
        total_demand = sum(self.demands)

        # Если суммы не равны — задача открытая
        if total_supply != total_demand:
            # Выводим сообщение о несбалансированности
            print(f"Задача несбалансированна! Сумма поставок: {total_supply}, Сумма потребностей: {total_demand}")
            # Если запасов больше, чем нужно
            if total_supply > total_demand:
                # Добавляем фиктивного потребителя
                self.demands.append(total_supply - total_demand)
                # Увеличиваем число столбцов
                self.m += 1
                # Для каждой строки добавляем нулевой тариф
                for i in range(self.n):
                    self.costs[i].append(0)
            # Если потребностей больше, чем запасов
            else:
                # Добавляем фиктивного поставщика
                self.supplies.append(total_demand - total_supply)
                # Увеличиваем число строк
                self.n += 1
                # Добавляем строку из нулевых тарифов
                self.costs.append([0] * self.m)

        # Матрица перевозок, изначально заполнена нулями
        self.x = np.zeros((self.n, self.m), dtype=float)

    # Метод северо-западного угла: строит начальный опорный план
    def north_west_corner(self):
        # Матрица объёмов перевозок
        x = np.zeros((self.n, self.m), dtype=float)
        # Булева матрица: True = клетка базисная
        basis = np.zeros((self.n, self.m), dtype=bool)

        # Копии запасов
        a = self.supplies.copy()
        # Копии потребностей
        b = self.demands.copy()
        # Текущая позиция — левый верхний угол
        i, j = 0, 0

        # Основной цикл: пока не вышли за пределы таблицы
        while i < self.n and j < self.m:
            # Если запас i-го поставщика исчерпан
            if abs(a[i]) < 1e-12:
                # Переходим к следующей строке
                i += 1
                # И заново проверяем условие
                continue
            # Если потребность j-го потребителя удовлетворена
            if abs(b[j]) < 1e-12:
                # Переходим к следующему столбцу
                j += 1
                # И заново проверяем условие
                continue

            # Объём перевозки = минимум из остатка запаса и остатка потребности
            amount = min(a[i], b[j])
            # Записываем этот объём в текущую клетку
            x[i, j] = amount
            # Помечаем клетку как базисную
            basis[i, j] = True

            # Уменьшаем остаток запаса
            a[i] -= amount
            # Уменьшаем остаток потребности
            b[j] -= amount

            # Если одновременно исчерпаны и запас, и потребность
            if abs(a[i]) < 1e-12 and abs(b[j]) < 1e-12:
                # Чтобы сохранить m+n-1 базисных клеток, добавляем нулевую базисную клетку
                # Если есть следующая строка — идём в неё
                if i < self.n - 1:
                    basis[i + 1, j] = True # True означает, что клетка входит в базис 
                    x[i + 1, j] = 0.0
                # Иначе — в следующий столбец
                elif j < self.m - 1:
                    basis[i, j + 1] = True
                    x[i, j + 1] = 0.0
                # Сдвигаемся по диагонали. Это нужно потому, что и запас
                # текущего поставщика, и потребность текущего потребителя
                # полностью исчерпаны — оба больше не участвуют в заполнении
                i += 1
                j += 1
            # Если исчерпан только запас
            elif abs(a[i]) < 1e-12:
                # Переходим к следующей строке
                i += 1
            # Если удовлетворена только потребность
            elif abs(b[j]) < 1e-12:
                # Переходим к следующему столбцу
                j += 1

        # После завершения заполнения проверяем и корректируем базис
        self._ensure_connected_basis(x, basis)
        # Возвращаем план и множество базисных клеток
        return x, basis

    # Проверка и восстановление базиса (m+n-1 связных клеток)
    def _ensure_connected_basis(self, x, basis):
        # Сколько базисных клеток должно быть
        needed = self.n + self.m - 1

        # Случай 1: базисных клеток МЕНЬШЕ, чем нужно
        while np.sum(basis) < needed:
            # Флаг: удалось ли добавить клетку
            added = False
            # Перебираем все строки
            for i in range(self.n):
                # И все столбцы
                for j in range(self.m):
                    # Ищем небазисную клетку с нулевой перевозкой
                    if not basis[i, j] and abs(x[i, j]) < 1e-12:
                        # Временно делаем её базисной
                        basis[i, j] = True
                        # Проверяем, не нарушилась ли связность
                        if self._is_connected(basis):
                            # Если связность сохранилась — клетка подходит
                            added = True
                            break
                        else:
                            # Иначе откатываем изменение
                            basis[i, j] = False
                if added:
                    # Если нашли подходящую клетку — выходим из внешнего цикла
                    break
            # Если ни одна клетка не подошла без нарушения связности
            if not added:
                # Берём первую попавшуюся свободную клетку
                for i in range(self.n):
                    for j in range(self.m):
                        if not basis[i, j]:
                            basis[i, j] = True
                            added = True
                            break
                    if added:
                        break
                if not added:
                    # Если совсем ничего нет — прерываем
                    break

        # Случай 2: базисных клеток БОЛЬШЕ, чем нужно
        while np.sum(basis) > needed:
            # Флаг: удалось ли удалить
            removed = False
            # Перебираем все клетки
            for i in range(self.n):
                for j in range(self.m):
                    # Ищем базисную клетку с нулевой перевозкой
                    if basis[i, j] and abs(x[i, j]) < 1e-12:
                        # Временно убираем её из базиса
                        basis[i, j] = False
                        # Проверяем связность
                        if self._is_connected(basis):
                            # Если связность сохранилась — удаление корректно
                            removed = True
                            break
                        else:
                            # Иначе возвращаем клетку обратно
                            basis[i, j] = True
                if removed:
                    break
            if not removed:
                break

    # Проверка связности базиса (обход по строкам и столбцам)
    def _is_connected(self, basis):
        # Список всех базисных клеток как (i, j)
        # Функция zip «сшивает» элементы нескольких последовательностей попарно
        # и так далее, пока не закончатся элементы
        cells = list(zip(*np.where(basis)))
        # Если базис пуст
        if not cells:
            # Считаем его связным (вырожденный случай)
            return True
        # Множество посещённых клеток
        visited = set()
        # Стек для DFS, начинаем с первой базисной клетки
        stack = [cells[0]]

        # Обход в глубину (DFS)
        while stack:
            # Берём очередную клетку из стека
            i, j = stack.pop()
            # Если её уже посещали
            if (i, j) in visited:
                # Пропускаем
                continue
            # Помечаем как посещённую
            visited.add((i, j))

            # Ищем соседей по строке (все базисные клетки в той же строке)
            for jj in range(self.m):
                if basis[i, jj] and (i, jj) not in visited:
                    stack.append((i, jj))

            # Ищем соседей по столбцу (все базисные клетки в том же столбце)
            for ii in range(self.n):
                if basis[ii, j] and (ii, j) not in visited:
                    stack.append((ii, j))

        # Если количество посещённых совпадает с общим числом базисных клеток — базис связный
        return len(visited) == len(cells)

    # Вычисление потенциалов u_i и v_j
    def calculate_potentials(self, basis):
        # Массив потенциалов поставщиков, изначально неизвестны (None)
        u = [None] * self.n
        # Массив потенциалов потребителей
        v = [None] * self.m
        # Один потенциал задаём произвольно (обычно u_1 = 0)
        u[0] = 0

        # Итеративно распространяем известные потенциалы через базисные клетки
        changed = True
        while changed:
            # Сбрасываем флаг
            changed = False
            # Перебираем все базисные клетки
            for i in range(self.n):
                for j in range(self.m):
                    # Если клетка базисная, для неё верно u_i + v_j = c_ij
                    if basis[i, j]:
                        # Если u_i известен, а v_j — нет
                        if u[i] is not None and v[j] is None:
                            # Находим v_j
                            v[j] = self.costs[i][j] - u[i]
                            changed = True
                        # Если v_j известен, а u_i — нет
                        elif v[j] is not None and u[i] is None:
                            # Находим u_i
                            u[i] = self.costs[i][j] - v[j]
                            changed = True
        return u, v

    # Вычисление оценок свободных клеток delta_ij
    def calculate_deltas(self, u, v, basis):
        # Матрица оценок, по умолчанию NaN (для базисных клеток оценок нет)
        deltas = np.full((self.n, self.m), np.nan)
        # Проходим по всем клеткам
        for i in range(self.n):
            for j in range(self.m):
                # Оцениваем только свободные клетки
                if not basis[i, j]:
                    if u[i] is not None and v[j] is not None:
                        # delta_ij = c_ij − (u_i + v_j)
                        deltas[i, j] = self.costs[i][j] - (u[i] + v[j])
        return deltas

    # Поиск цикла пересчёта для выбранной клетки
    def find_cycle(self, start_i, start_j, basis):
        # Временная копия базиса
        temp_basis = basis.copy()
        # Временно добавляем стартовую клетку
        temp_basis[start_i, start_j] = True

        # Рекурсивный поиск в глубину с чередованием направлений
        def dfs(path, direction):
            # Текущая клетка — последняя в пути
            i, j = path[-1]
            # Если вернулись в начало (и путь не пустой)
            if len(path) > 1 and (i, j) == (start_i, start_j):
                # Цикл найден — возвращаем его
                return path
            # Список возможных ходов
            moves = []
            # Если предыдущий ход не был горизонтальным
            if direction != 'h':
                # Ищем базисные клетки в той же строке
                for jj in range(self.m):
                    if jj != j and temp_basis[i, jj]:
                        # Добавляем как горизонтальный ход
                        moves.append((i, jj, 'h'))
            # Если предыдущий ход не был вертикальным
            if direction != 'v':
                # Ищем базисные клетки в том же столбце
                for ii in range(self.n):
                    if ii != i and temp_basis[ii, j]:
                        # Добавляем как вертикальный ход
                        moves.append((ii, j, 'v'))

            # ni, nj — координаты новой клетки, в которую делаем ход,
            # nd — направление этого хода ('h' — горизонтальный, 'v' — вертикальный),
            # нужно для чередования направлений на следующем шаге
            for ni, nj, nd in moves:
                # Не возвращаемся в предыдущую клетку
                # path[-2] — предпоследняя клетка в текущем пути
                if len(path) > 1 and (ni, nj) == path[-2]:
                    continue
                # Рекурсивно продолжаем поиск
                res = dfs(path + [(ni, nj)], nd)
                if res:
                    return res
            return None

        # Пробуем начать движение как по горизонтали, так и по вертикали
        for first_dir in ['h', 'v']:
            # Список первых ходов
            moves = []
            # Вариант 1: первый ход — горизонтальный.
            # Ищем все базисные клетки в той же строке, что и стартовая клетка
            if first_dir == 'h':
                for jj in range(self.m):
                    if jj != start_j and temp_basis[start_i, jj]:
                        moves.append((start_i, jj, 'h'))
            # Вариант 2: первый ход — вертикальный.
            # Ищем все базисные клетки в том же столбце, что и стартовая клетка
            else:
                for ii in range(self.n):
                    if ii != start_i and temp_basis[ii, start_j]:
                        moves.append((ii, start_j, 'v'))

            # Пробуем каждый первый ход: запускаем DFS из пути,
            # уже содержащего стартовую клетку и первую клетку хода
            for ni, nj, nd in moves:
                res = dfs([(start_i, start_j), (ni, nj)], nd)
                if res:
                    # DFS возвращает путь, в котором последний элемент
                    # снова совпадает со стартовой клеткой (замыкание цикла).
                    # Для дальнейшего использования этот дубликат не нужен —
                    # убираем его, оставляя только уникальные вершины цикла
                    if res[-1] == res[0]:
                        res = res[:-1]
                    return res
        # Цикл не найден
        return []

    # Метод потенциалов: итерационное улучшение плана
    def improve_solution(self, x, basis):
        # Номер итерации
        iteration = 0
        # Защита от зацикливания
        max_iterations = 1000

        while iteration < max_iterations:
            # Увеличиваем счётчик
            iteration += 1
            print(f"Итерация {iteration}")

            # 1. Расчёт потенциалов
            u, v = self.calculate_potentials(basis)
            print(f"Потенциалы u: {[f'{val:.1f}' if val is not None else 'None' for val in u]}")
            print(f"Потенциалы v: {[f'{val:.1f}' if val is not None else 'None' for val in v]}")

            # 2. Расчёт оценок свободных клеток
            deltas = self.calculate_deltas(u, v, basis)
            print("Матрица оценок:")
            for row in deltas:
                # NaN -> прочерк (базисные клетки)
                print(['   —  ' if np.isnan(val) else f'{val:6.1f}' for val in row])

            # 3. Проверка оптимальности
            # Берём только числовые оценки
            finite = deltas[~np.isnan(deltas)]
            min_delta = np.min(finite) if finite.size else 0.0
            # Если все оценки неотрицательны — план оптимален
            if min_delta >= -1e-10:
                print("Решение оптимально!")
                return x, basis, True

            # 4. Выбор клетки для улучшения
            # Список отрицательных клеток
            improving_cells = []
            for i in range(self.n):
                for j in range(self.m):
                    if not np.isnan(deltas[i, j]) and deltas[i, j] < -1e-10:
                        improving_cells.append((i, j, deltas[i, j]))

            # Если таковых нет
            if not improving_cells:
                print("Нет клеток для улучшения!")
                return x, basis, True

            # Сортируем по возрастанию (самая отрицательная — первая)
            improving_cells.sort(key=lambda cell: cell[2])
            # Берём самую отрицательную клетку
            i0, j0, min_delta_val = improving_cells[0]
            print(f"Выбрана клетка ({i0},{j0}) с оценкой delta = {min_delta_val:.3f}")

            # 5. Поиск цикла пересчёта
            cycle = self.find_cycle(i0, j0, basis)
            # Цикл не найден — пропускаем клетку
            if not cycle:
                print("Цикл не найден! Пропускаем эту клетку")
                deltas[i0, j0] = np.nan
                continue

            print(f"Найден цикл: {cycle}")

            # 6. Определение theta
            # theta = минимум в минусовых клетках
            theta = float('inf')
            # Список минусовых клеток
            minus_cells = []
            # Нечётные позиции в цикле — знак «−»
            for idx in range(1, len(cycle), 2):
                i, j = cycle[idx]
                if x[i, j] < theta:
                    theta = x[i, j]
                minus_cells.append((i, j))

            # Если theta = 0 — вырожденный переход
            if theta < 1e-10:
                print("theta = 0. Выполняется вырожденный переход: "
                      "план не изменяется, меняется только базис.")
                theta = 0.0
            else:
                print(f"theta = {theta}")

            # 7. Перераспределение поставок
            for idx, (i, j) in enumerate(cycle):
                # Чётные позиции — знак «+»
                if idx % 2 == 0:
                    x[i, j] += theta
                # Нечётные — знак «−»
                else:
                    x[i, j] -= theta

            # 8. Обновление базиса
            # Вводим выбранную клетку в базис
            basis[i0, j0] = True

            # Флаг: удалось ли вывести клетку
            removed = False
            # Ищем минусовую клетку, обнулившуюся после пересчёта
            for i, j in minus_cells:
                if abs(x[i, j]) < 1e-10:
                    basis[i, j] = False
                    print(f"Удалена клетка ({i},{j})")
                    removed = True
                    break
            # Если не нашли — принудительно удаляем первую
            if not removed and minus_cells:
                i, j = minus_cells[0]
                basis[i, j] = False
                print(f"Удалена клетка ({i},{j}) (принудительно, θ=0)")

            # Восстанавливаем нужное число и связность
            self._ensure_connected_basis(x, basis)

            # 9. Вывод нового плана
            print("\nНовый план перевозок:")
            for row in x:
                print([f'{val:6.1f}' for val in row])

            # Пересчёт стоимости
            cost = np.sum(x * np.array(self.costs))
            print(f"Текущая стоимость: {cost:.1f}\n")

        print("Достигнуто максимальное количество итераций!")
        return x, basis, False

    # Главный метод: полное решение задачи
    def solve(self):
        print("\n\tРешение транспортной задачи")
        print(f"Запасы: {self.supplies}")
        print(f"Потребности: {self.demands}")
        print("Матрица стоимостей:")
        for row in self.costs:
            print([f'{val:4.1f}' for val in row])

        # Шаг 1. Построение начального плана
        print("\n\tПостроение начального плана методом северо-западного угла")
        x, basis = self.north_west_corner()

        print("Начальный план перевозок:")
        for row in x:
            print([f'{val:6.1f}' for val in row])

        # Стоимость начального плана
        initial_cost = np.sum(x * np.array(self.costs))
        print(f"Начальная стоимость: {initial_cost:.1f}")

        # Шаг 2. Оптимизация методом потенциалов
        print("\n\tИспользование метода потенциалов")
        x, basis, optimal = self.improve_solution(x, basis)

        # Шаг 3. Вывод оптимального решения
        print("\n\tОптимальный план перевозок:")
        for i, row in enumerate(x):
            print(f"Поставщик {i + 1}: {[f'{val:6.1f}' for val in row]}")

        # Минимальная стоимость
        final_cost = np.sum(x * np.array(self.costs))
        print(f"Минимальная стоимость перевозок: {final_cost:.1f}")

        return x, final_cost


# Чтение входных данных из CSV-файла
def read_input_from_csv(filename: str):
    # Список запасов
    supplies = []
    # Список потребностей
    demands = []
    # Матрица стоимостей
    costs = []

    # Открываем файл
    with open(filename, 'r', newline='') as csvfile:
        # Разделитель — пробел
        reader = csv.reader(csvfile, delimiter=' ')
        # Сюда собираем все строки
        rows = []
        for row in reader:
            # Пропускаем пустые строки
            if row and any(cell.strip() for cell in row):
                # Убираем пустые ячейки
                filtered_row = [cell for cell in row if cell.strip()]
                # Преобразуем в числа
                rows.append([float(x) for x in filtered_row])

        if rows:
            # Последняя строка — потребности
            demands = rows[-1]
            # Все предыдущие строки — поставщики
            for row in rows[:-1]:
                if len(row) > 1:
                    # Последний элемент — запас
                    supplies.append(row[-1])
                    # Остальные элементы — тарифы
                    costs.append(row[:-1])

    return supplies, demands, costs


# Точка входа: запуск программы
if __name__ == "__main__":
    try:
        # Читаем входные данные
        supplies, demands, costs = read_input_from_csv('input.csv')

        print(f"Запасы: {supplies}")
        print(f"Потребности: {demands}")
        print("Матрица стоимостей:")
        for row in costs:
            print(row)

        # Создаём объект задачи
        problem = TransportProblem(supplies, demands, costs)
        # Запускаем решение
        solution, total_cost = problem.solve()
    except FileNotFoundError:
        # Если файла нет — сообщаем
        print("Файл input.csv не найден!")