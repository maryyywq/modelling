import numpy as np
from typing import List, Tuple
import csv

class TransportProblem:
    def __init__(self, supplies, demands, costs):
        self.supplies = list(supplies)
        self.demands = list(demands)
        self.costs = [list(row) for row in costs]
        self.n = len(self.supplies)
        self.m = len(self.demands)

        # Проверка сбалансированности
        total_supply = sum(self.supplies)
        total_demand = sum(self.demands)

        if total_supply != total_demand:
            print(f"Задача несбалансированна! Сумма поставок: {total_supply}, Сумма потребностей: {total_demand}")
            if total_supply > total_demand:
                self.demands.append(total_supply - total_demand)
                self.m += 1
                for i in range(self.n):
                    self.costs[i].append(0)
            else:
                self.supplies.append(total_demand - total_supply)
                self.n += 1
                self.costs.append([0] * self.m)

        self.x = np.zeros((self.n, self.m), dtype=float)

    # ---------- Северо-западный угол ----------
    def north_west_corner(self):
        x = np.zeros((self.n, self.m), dtype=float)
        basis = np.zeros((self.n, self.m), dtype=bool)

        a = self.supplies.copy()
        b = self.demands.copy()
        i, j = 0, 0

        while i < self.n and j < self.m:
            if abs(a[i]) < 1e-12:
                i += 1
                continue
            if abs(b[j]) < 1e-12:
                j += 1
                continue

            amount = min(a[i], b[j])
            x[i, j] = amount
            basis[i, j] = True

            a[i] -= amount
            b[j] -= amount

            if abs(a[i]) < 1e-12 and abs(b[j]) < 1e-12:
                # Одновременно обнулились строка и столбец – добавляем нулевую клетку,
                # чтобы сохранить n+m-1 базисных клеток
                if i < self.n - 1:
                    basis[i + 1, j] = True
                    x[i + 1, j] = 0.0
                elif j < self.m - 1:
                    basis[i, j + 1] = True
                    x[i, j + 1] = 0.0
                i += 1
                j += 1
            elif abs(a[i]) < 1e-12:
                i += 1
            elif abs(b[j]) < 1e-12:
                j += 1

        # Приводим базис к правильному размеру и связности
        self._ensure_connected_basis(x, basis)
        return x, basis

    # ---------- Проверка и восстановление базиса ----------
    def _ensure_connected_basis(self, x, basis):
        """Гарантирует, что базис содержит ровно n+m-1 клеток и является связным."""
        needed = self.n + self.m - 1

        # 1. Если клеток меньше, добавляем нулевые так, чтобы не потерять связность
        while np.sum(basis) < needed:
            added = False
            for i in range(self.n):
                for j in range(self.m):
                    if not basis[i, j] and abs(x[i, j]) < 1e-12:
                        basis[i, j] = True
                        if self._is_connected(basis):
                            added = True
                            break
                        else:
                            basis[i, j] = False
                if added:
                    break
            if not added:
                # Если связную клетку подобрать не удалось, добавляем первую попавшуюся
                for i in range(self.n):
                    for j in range(self.m):
                        if not basis[i, j]:
                            basis[i, j] = True
                            added = True
                            break
                    if added:
                        break
                if not added:
                    break

        # 2. Если клеток больше, удаляем лишние нулевые, сохраняя связность
        while np.sum(basis) > needed:
            removed = False
            for i in range(self.n):
                for j in range(self.m):
                    if basis[i, j] and abs(x[i, j]) < 1e-12:
                        basis[i, j] = False
                        if self._is_connected(basis):
                            removed = True
                            break
                        else:
                            basis[i, j] = True
                if removed:
                    break
            if not removed:
                break

    def _is_connected(self, basis):
        """Проверяет связность базиса (все базисные клетки достижимы)."""
        cells = list(zip(*np.where(basis)))
        if not cells:
            return True
        visited = set()
        stack = [cells[0]]
        while stack:
            i, j = stack.pop()
            if (i, j) in visited:
                continue
            visited.add((i, j))
            for jj in range(self.m):
                if basis[i, jj] and (i, jj) not in visited:
                    stack.append((i, jj))
            for ii in range(self.n):
                if basis[ii, j] and (ii, j) not in visited:
                    stack.append((ii, j))
        return len(visited) == len(cells)

    # ---------- Потенциалы ----------
    def calculate_potentials(self, basis):
        u = [None] * self.n
        v = [None] * self.m
        u[0] = 0

        changed = True
        while changed:
            changed = False
            for i in range(self.n):
                for j in range(self.m):
                    if basis[i, j]:
                        if u[i] is not None and v[j] is None:
                            v[j] = self.costs[i][j] - u[i]
                            changed = True
                        elif v[j] is not None and u[i] is None:
                            u[i] = self.costs[i][j] - v[j]
                            changed = True
        return u, v

    # ---------- Оценки свободных клеток ----------
    def calculate_deltas(self, u, v, basis):
        deltas = np.full((self.n, self.m), np.nan)
        for i in range(self.n):
            for j in range(self.m):
                if not basis[i, j]:
                    if u[i] is not None and v[j] is not None:
                        deltas[i, j] = self.costs[i][j] - (u[i] + v[j])
        return deltas

    # ---------- Поиск цикла пересчёта ----------
    def find_cycle(self, start_i, start_j, basis):
        """Ищет цикл пересчёта, начиная с клетки (start_i, start_j)."""
        temp_basis = basis.copy()
        temp_basis[start_i, start_j] = True

        def dfs(path, direction):
            i, j = path[-1]
            if len(path) > 1 and (i, j) == (start_i, start_j):
                return path
            moves = []
            if direction != 'h':
                for jj in range(self.m):
                    if jj != j and temp_basis[i, jj]:
                        moves.append((i, jj, 'h'))
            if direction != 'v':
                for ii in range(self.n):
                    if ii != i and temp_basis[ii, j]:
                        moves.append((ii, j, 'v'))
            for ni, nj, nd in moves:
                if len(path) > 1 and (ni, nj) == path[-2]:
                    continue
                res = dfs(path + [(ni, nj)], nd)
                if res:
                    return res
            return None

        for first_dir in ['h', 'v']:
            moves = []
            if first_dir == 'h':
                for jj in range(self.m):
                    if jj != start_j and temp_basis[start_i, jj]:
                        moves.append((start_i, jj, 'h'))
            else:
                for ii in range(self.n):
                    if ii != start_i and temp_basis[ii, start_j]:
                        moves.append((ii, start_j, 'v'))
            for ni, nj, nd in moves:
                res = dfs([(start_i, start_j), (ni, nj)], nd)
                if res:
                    if res[-1] == res[0]:
                        res = res[:-1]
                    return res
        return []

    # ---------- Метод потенциалов ----------
    def improve_solution(self, x, basis):
        iteration = 0
        max_iterations = 1000

        while iteration < max_iterations:
            iteration += 1
            print(f"Итерация {iteration}")

            u, v = self.calculate_potentials(basis)
            print(f"Потенциалы u: {[f'{val:.1f}' if val is not None else 'None' for val in u]}")
            print(f"Потенциалы v: {[f'{val:.1f}' if val is not None else 'None' for val in v]}")

            deltas = self.calculate_deltas(u, v, basis)
            print("Матрица оценок:")
            for row in deltas:
                print([
                    '   —  ' if np.isnan(val) else f'{val:6.1f}'
                    for val in row
                ])

            finite = deltas[~np.isnan(deltas)]
            min_delta = np.min(finite) if finite.size else 0.0
            if min_delta >= -1e-10:
                print("Решение оптимально!")
                return x, basis, True

            improving_cells = []
            for i in range(self.n):
                for j in range(self.m):
                    if not np.isnan(deltas[i, j]) and deltas[i, j] < -1e-10:
                        improving_cells.append((i, j, deltas[i, j]))

            if not improving_cells:
                print("Нет клеток для улучшения!")
                return x, basis, True

            improving_cells.sort(key=lambda cell: cell[2])
            i0, j0, min_delta_val = improving_cells[0]
            print(f"Выбрана клетка ({i0},{j0}) с оценкой delta = {min_delta_val:.3f}")

            cycle = self.find_cycle(i0, j0, basis)
            if not cycle:
                print("Цикл не найден! Пропускаем эту клетку")
                deltas[i0, j0] = np.nan
                continue

            print(f"Найден цикл: {cycle}")

            # Определяем theta (минимум в минусовых клетках)
            theta = float('inf')
            minus_cells = []
            for idx in range(1, len(cycle), 2):
                i, j = cycle[idx]
                if x[i, j] < theta:
                    theta = x[i, j]
                minus_cells.append((i, j))

            if theta < 1e-10:
                print("theta = 0. Выполняется вырожденный переход: "
                      "план не изменяется, меняется только базис.")
                theta = 0.0
            else:
                print(f"theta = {theta}")

            # Перераспределяем поставки
            for idx, (i, j) in enumerate(cycle):
                if idx % 2 == 0:
                    x[i, j] += theta
                else:
                    x[i, j] -= theta

            # Обновляем базис: обязательно добавляем выбранную клетку
            basis[i0, j0] = True

            # Удаляем первую обнулившуюся минусовую клетку
            removed = False
            for i, j in minus_cells:
                if abs(x[i, j]) < 1e-10:
                    basis[i, j] = False
                    print(f"Удалена клетка ({i},{j})")
                    removed = True
                    break
            if not removed and minus_cells:
                i, j = minus_cells[0]
                basis[i, j] = False
                print(f"Удалена клетка ({i},{j}) (принудительно, θ=0)")

            self._ensure_connected_basis(x, basis)

            print("\nНовый план перевозок:")
            for row in x:
                print([f'{val:6.1f}' for val in row])

            cost = np.sum(x * np.array(self.costs))
            print(f"Текущая стоимость: {cost:.1f}\n")

        print("Достигнуто максимальное количество итераций!")
        return x, basis, False

    # ---------- Решение ----------
    def solve(self):
        print("\n\tРешение транспортной задачи")
        print(f"Запасы: {self.supplies}")
        print(f"Потребности: {self.demands}")
        print("Матрица стоимостей:")
        for row in self.costs:
            print([f'{val:4.1f}' for val in row])

        print("\n\tПостроение начального плана методом северо-западного угла")
        x, basis = self.north_west_corner()

        print("Начальный план перевозок:")
        for row in x:
            print([f'{val:6.1f}' for val in row])

        initial_cost = np.sum(x * np.array(self.costs))
        print(f"Начальная стоимость: {initial_cost:.1f}")

        print("\n\tИспользование метода потенциалов")
        x, basis, optimal = self.improve_solution(x, basis)

        print("\n\tОптимальный план перевозок:")
        for i, row in enumerate(x):
            print(f"Поставщик {i + 1}: {[f'{val:6.1f}' for val in row]}")

        final_cost = np.sum(x * np.array(self.costs))
        print(f"Минимальная стоимость перевозок: {final_cost:.1f}")

        return x, final_cost


# ---------- Чтение CSV ----------
def read_input_from_csv(filename: str):
    supplies = []
    demands = []
    costs = []

    with open(filename, 'r', newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=' ')
        rows = []
        for row in reader:
            if row and any(cell.strip() for cell in row):
                filtered_row = [cell for cell in row if cell.strip()]
                rows.append([float(x) for x in filtered_row])

        if rows:
            demands = rows[-1]
            for row in rows[:-1]:
                if len(row) > 1:
                    supplies.append(row[-1])
                    costs.append(row[:-1])

    return supplies, demands, costs


# ---------- Запуск ----------
if __name__ == "__main__":
    try:
        supplies, demands, costs = read_input_from_csv('input.csv')

        print(f"Запасы: {supplies}")
        print(f"Потребности: {demands}")
        print("Матрица стоимостей:")
        for row in costs:
            print(row)

        problem = TransportProblem(supplies, demands, costs)
        solution, total_cost = problem.solve()
    except FileNotFoundError:
        print("Файл input.csv не найден!")