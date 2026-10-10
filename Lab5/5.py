import numpy as np  
import copy  
import heapq  
import os  
import csv  

# Класс для решения задачи коммивояжёра алгоритмом Литтла
class TSPSolver:  
    def __init__(self, cost_matrix):  # конструктор
        self.n = len(cost_matrix)  # размер матрицы
        self.original_matrix = np.array(cost_matrix, dtype=float)  # сохраняем исходную матрицу как numpy-массив
        for i in range(self.n):  # проходим по всем строкам
            self.original_matrix[i][i] = float('inf')  # заполняем диагональные элементы
        self.log_file = open('tsp_solution_log.txt', 'w', encoding='utf-8')  # открываем файл для записи лога
        self.step_counter = 0  # счётчик шагов алгоритма
        self.tree_nodes = {}  # словарь для хранения узлов дерева ветвления
        self.current_node_id = 0  # идентификатор текущего узла

    # Метод для записи шага в лог
    # Принимает:
        # matrix — текущая приведённая матрица стоимостей
        # reduced_constants — сумма констант
        # theta — нижняя оценка стоимости всех маршрутов в этом узле
        # edge — ребро (i, j), по которому ветвимся на этом шаге. Может быть None (например, на первом шаге)
        # penalty — штраф за неиспользование этого ребра
        # node_info — строка-пояснение 
    # Ничего не возвращает, просто пишет всё это в лог-файл
    def log_step(self, matrix, reduced_constants, theta, edge, penalty, node_info=""):  
        self.step_counter += 1  # увеличиваем номер шага
        self.log_file.write(f"Шаг {self.step_counter}\n")  # записываем номер шага
        if node_info:  # если передана дополнительная информация об узле
            self.log_file.write(f"{node_info}\n")  # записываем её
        self.log_file.write("Текущая матрица стоимостей:\n")  # заголовок для матрицы
        for row in matrix:  # проходим по строкам матрицы
            self.log_file.write("[" + " ".join(  # формируем строку для вывода
                f"{x:6.1f}" if x != float('inf') else "   inf " for x in row) + "]\n")  # выводим элементы с форматированием
        self.log_file.write(f"Сумма приводящих констант: {reduced_constants}\n")  # записываем сумму констант приведения
        self.log_file.write(f"Оценка затрат: {theta}\n")  # записываем текущую оценку theta
        if edge:  # если указано ребро
            self.log_file.write(f"Ребро маршрута: ({edge[0] + 1},{edge[1] + 1})\n")  # выводим ребро (с индексацией от 1)
        if penalty is not None:  # если указан штраф
            self.log_file.write(f"Штраф за неиспользование: {penalty}\n")  # выводим штраф

    # Метод приведения матрицы
    # Принимает:
        # matrix — матрица, которую надо привести
    # Возвращает:
        # приведённую матрицу и сумму всех вычтенных констант
    def reduce_matrix(self, matrix): 
        reduced_matrix = copy.deepcopy(matrix)  # создаём копию матрицы
        reduction_cost = 0  # сумма приводящих констант
        n = len(reduced_matrix)  # размер матрицы

        # По строкам
        for i in range(n):  # проходим по всем строкам
            min_val = min(reduced_matrix[i])  # находим минимальный элемент в строке
            if min_val != float('inf') and min_val > 0:  # если минимум конечен и положителен
                reduction_cost += min_val  # добавляем к сумме констант
                for j in range(n):  # проходим по всем элементам строки
                    if reduced_matrix[i][j] != float('inf'):  # если элемент не бесконечен
                        reduced_matrix[i][j] -= min_val  # вычитаем минимум

        # По столбцам
        for j in range(n):  # проходим по всем столбцам
            min_val = min(reduced_matrix[i][j] for i in range(n))  # находим минимальный элемент в столбце
            if min_val != float('inf') and min_val > 0:  # если минимум конечен и положителен
                reduction_cost += min_val  # добавляем к сумме констант
                for i in range(n):  # проходим по всем элементам столбца
                    if reduced_matrix[i][j] != float('inf'):  # если элемент не бесконечен
                        reduced_matrix[i][j] -= min_val  # вычитаем минимум

        return reduced_matrix, reduction_cost  # возвращаем приведённую матрицу и сумму констант

    # Метод вычисления штрафов для нулевых элементов
    # Принимает:
        # matrix — приведённая матрица (в ней уже есть нули).
    # Возвращает:
        # матрицу штрафов: для каждого нулевого элемента (i,j) считаем,
        # насколько увеличится оценка, если мы НЕ включим это ребро.
        # Штраф = минимум в строке i + минимум в столбце j.
        # Для ненулевых элементов штраф = -1 (как бы "не считается")
    def calculate_penalties(self, matrix):  
        n = len(matrix)  # размер матрицы
        penalties = np.full((n, n), -1.0)  # инициализируем матрицу штрафов значением -1

        for i in range(n):  # проходим по строкам
            for j in range(n):  # проходим по столбцам
                if matrix[i][j] == 0:  # если элемент нулевой
                    row_vals = [matrix[i][k] for k in range(n)  # собираем элементы строки i (не считая сам элемент)
                                if k != j and matrix[i][k] != float('inf')]  # исключая бесконечности
                    min_row = min(row_vals) if row_vals else 0  # минимум в строке (если есть)

                    col_vals = [matrix[k][j] for k in range(n)  # собираем элементы столбца j (не считая сам элемент)
                                if k != i and matrix[k][j] != float('inf')]  # исключая бесконечности
                    min_col = min(col_vals) if col_vals else 0  # минимум в столбце (если есть)

                    penalties[i][j] = min_row + min_col  # штраф = сумма минимумов

        return penalties  # возвращаем матрицу штрафов
    
    # Метод поиска ребра с максимальным штрафом
    # Принимает:
        # penalties — матрица штрафов 
    # Возвращает:
        # ребро с максимальным штрафом и сам этот штраф.
    def find_max_penalty_edge(self, penalties):  
        max_penalty = -1  # начальное значение максимального штрафа
        best_edge = None  # лучшее ребро
        n = len(penalties)  # размер матрицы штрафов

        for i in range(n):  # проходим по строкам
            for j in range(n):  # проходим по столбцам
                if penalties[i][j] > max_penalty:  # если штраф больше текущего максимума
                    max_penalty = penalties[i][j]  # обновляем максимум
                    best_edge = (i, j)  # запоминаем ребро

        return best_edge, max_penalty  # возвращаем ребро и штраф

    # Метод включения ребра в маршрут
    # Принимает:
        # matrix — текущая матрица стоимостей
        # edge — ребро (i, j), которое мы ВКЛЮЧАЕМ в маршрут
        # current_path — список уже включённых в маршрут рёбер 
    # Возвращает
        # новую матрицу, в которой:
        #   - все переходы ИЗ города i запрещены, кроме (i,j);
        #   - все переходы В город j запрещены, кроме (i,j);
        #   - диагональ снова бесконечность;
        #   - запрещено ребро, которое замкнуло бы подцикл (если такой образуется)
    def include_edge(self, matrix, edge, current_path):  
        i, j = edge  # распаковываем ребро
        n = len(matrix)  # размер матрицы
        new_matrix = copy.deepcopy(matrix)  # создаём копию матрицы

        # Запрещаем другие переходы из i и в j
        for k in range(n):  # проходим по всем элементам
            new_matrix[i][k] = float('inf')  # запрещаем выход из i в любой другой город
            new_matrix[k][j] = float('inf')  # запрещаем вход в j из любого другого города

        # Восстанавливаем диагональ (на всякий случай)
        for k in range(n):  # проходим по диагонали
            new_matrix[k][k] = float('inf')  # запрещаем петли

        # Собираем текущие рёбра как граф
        out_edge = {}  # словарь исходящих рёбер
        in_edge = {}  # словарь входящих рёбер
        for a, b in current_path:  # проходим по уже выбранным рёбрам
            out_edge[a] = b  # заполняем исходящие
            in_edge[b] = a  # заполняем входящие
        out_edge[i] = j  # добавляем новое ребро
        in_edge[j] = i  # добавляем новое ребро

        # Находим начало цепочки, заканчивающейся в i 
        start_chain = i  # начинаем с i
        seen = set()  # множество посещённых вершин

        # 1) start_chain in in_edge — для текущего города есть предшественник
        # 2) start_chain not in seen — мы ещё не были в этом городе
        while start_chain in in_edge and start_chain not in seen:  
            seen.add(start_chain)  # отмечаем посещение
            start_chain = in_edge[start_chain]  # переходим к предыдущему

        # Находим конец цепочки, начинающейся в j (идём вперёд по out_edge)
        end_chain = j  # начинаем с j
        seen = set()  # сбрасываем множество
        while end_chain in out_edge and end_chain not in seen:  # идём вперёд по цепочке
            seen.add(end_chain)  # отмечаем посещение
            end_chain = out_edge[end_chain]  # переходим к следующему

        # Запрещаем ребро (end_chain -> start_chain), чтобы не замкнуть подцикл
        if end_chain != start_chain:  # если цепочка не замкнулась
            new_matrix[end_chain][start_chain] = float('inf')  # запрещаем замыкающее ребро

        return new_matrix  # возвращаем изменённую матрицу

    # Основной метод решения задачи
    # Возвращает два значения:
    #   best_solution — оптимальный маршрут (список рёбер вида (i, j));
    #   best_cost — суммарная стоимость этого маршрута по исходной матрице
    def solve(self):  
        # Начальное приведение матрицы
        current_matrix, r0 = self.reduce_matrix(self.original_matrix)  # приводим исходную матрицу
        theta_min = r0  # начальная оценка равна сумме констант

        self.log_step(current_matrix, r0, theta_min, None, None,  # логируем начальное приведение
                      "Начальное приведение матрицы")

        # Очередь с приоритетом
        priority_queue = []  # создаём пустую очередь с приоритетом
        heapq.heappush(priority_queue,  # помещаем в очередь начальный узел
                       (theta_min, self.current_node_id, current_matrix, [], r0))  # с оценкой, id, матрицей, путём и суммой
        self.tree_nodes[self.current_node_id] = {  # сохраняем информацию об узле в дереве
            'theta': theta_min,  # оценка
            'matrix': current_matrix,  # матрица
            'path': [],  # путь
            'parent': None,  # родитель
            'edge': None,  # ребро
            'included': None  # включено/исключено
        }

        best_solution = None  # лучшее найденное решение
        best_cost = float('inf')  # его стоимость
        max_iterations = 100000  # ограничение на число итераций
        iteration = 0  # счётчик итераций

        while priority_queue and iteration < max_iterations:  # пока очередь не пуста и не превышен лимит
            iteration += 1  # увеличиваем счётчик итераций
            theta, node_id, matrix, path, reduction_cost = heapq.heappop(priority_queue)  # извлекаем узел с минимальной оценкой

            if theta >= best_cost:  # если оценка не меньше лучшей стоимости
                continue  # пропускаем узел

            # Путь длиной n-1 ребра — осталось замкнуть цикл
            if len(path) == self.n - 1:  # если уже выбрано n-1 ребро
                used_from = set(e[0] for e in path)  # множество использованных начал
                used_to = set(e[1] for e in path)  # множество использованных концов

                from_node = list(set(range(self.n)) - used_from)  # находим конец цепочки
                to_node = list(set(range(self.n)) - used_to)  # находим начало цепочки

                if len(from_node) == 1 and len(to_node) == 1:  # если ровно по одному
                    from_node = from_node[0]  # извлекаем
                    to_node = to_node[0]  # извлекаем

                    if self.original_matrix[from_node][to_node] != float('inf'):  # если замыкающее ребро существует
                        complete_path = path + [(from_node, to_node)]  # добавляем его к пути
                        # Проверяем, что получился именно гамильтонов цикл
                        cycle = self.edges_to_cycle(complete_path)  # преобразуем рёбра в цикл
                        if cycle is not None and len(cycle) == self.n:  # если цикл корректен
                            complete_cost = self.calculate_path_cost(complete_path)  # считаем стоимость
                            if complete_cost < best_cost:  # если лучше текущей лучшей
                                best_solution = complete_path  # обновляем решение
                                best_cost = complete_cost  # обновляем стоимость
                continue  # переходим к следующей итерации

            if len(matrix) < 2:  # если матрица слишком мала
                continue  # пропускаем

            penalties = self.calculate_penalties(matrix)  # вычисляем штрафы
            edge, max_penalty = self.find_max_penalty_edge(penalties)  # находим ребро с максимальным штрафом

            if edge is None:  # если ребра нет
                continue  # пропускаем

            self.log_step(matrix, reduction_cost, theta, edge, max_penalty,  # логируем шаг
                          f"Узел {node_id}, текущий путь: "
                          f"{[(a + 1, b + 1) for a, b in path]}")

            # Ветвь 1: включаем ребро
            matrix_with_edge = self.include_edge(matrix, edge, path)  # включаем ребро в матрицу
            reduced_with_edge, reduction_with_edge = self.reduce_matrix(matrix_with_edge)  # приводим матрицу
            theta_with_edge = theta + reduction_with_edge  # новая оценка

            new_path_with_edge = path + [edge]  # добавляем ребро в путь
            self.current_node_id += 1  # увеличиваем id узла
            heapq.heappush(priority_queue,  # помещаем в очередь
                           (theta_with_edge, self.current_node_id,
                            reduced_with_edge, new_path_with_edge, reduction_with_edge))

            self.tree_nodes[self.current_node_id] = {  # сохраняем узел в дереве
                'theta': theta_with_edge,
                'matrix': reduced_with_edge,
                'path': new_path_with_edge,
                'parent': node_id,
                'edge': edge,
                'included': True
            }

            # Ветвь 2: исключаем ребро 
            matrix_without_edge = copy.deepcopy(matrix)  # копируем матрицу
            matrix_without_edge[edge[0]][edge[1]] = float('inf')  # запрещаем ребро
            reduced_without_edge, reduction_without_edge = self.reduce_matrix(matrix_without_edge)  # приводим матрицу
            theta_without_edge = theta + max_penalty  # новая оценка = старая + штраф

            self.current_node_id += 1  # увеличиваем id узла
            heapq.heappush(priority_queue,  # помещаем в очередь
                           (theta_without_edge, self.current_node_id,
                            reduced_without_edge, path, reduction_without_edge))

            self.tree_nodes[self.current_node_id] = {  # сохраняем узел в дереве
                'theta': theta_without_edge,
                'matrix': reduced_without_edge,
                'path': path,
                'parent': node_id,
                'edge': edge,
                'included': False
            }

        self.log_file.write("Оптимальное решение\n")  # записываем заголовок

        if best_solution:  # если решение найдено
            cycle = self.edges_to_cycle(best_solution)  # преобразуем в цикл
            path_str = "->".join(str(x + 1) for x in cycle)  # формируем строку маршрута
            self.log_file.write(f"Оптимальная последовательность: {path_str}\n")  # записываем последовательность
            self.log_file.write(f"Минимальная стоимость: {best_cost}\n")  # записываем стоимость
        else:  # если решение не найдено
            self.log_file.write("Решение не найдено\n")  # записываем сообщение

        self.save_tree_structure()  # сохраняем дерево ветвления в файл
        self.log_file.close()  # закрываем лог-файл
        return best_solution, best_cost  # возвращаем решение и стоимость
    
    # Метод подсчёта стоимости пути
    def calculate_path_cost(self, edges): 
        total_cost = 0  # начальная стоимость
        for i, j in edges:  # проходим по всем рёбрам
            total_cost += self.original_matrix[i][j]  # суммируем стоимости из исходной матрицы
        return total_cost  # возвращаем итог
    
    # Метод преобразования списка рёбер в цикл
    def edges_to_cycle(self, edges):  
        if len(edges) != self.n:  # если рёбер не n
            return None  # это не полный цикл

        graph = {}  # словарь для графа
        for i, j in edges:  # проходим по рёбрам
            if i in graph:  # если из вершины уже есть ребро
                return None  # это не цикл (две дуги из одной вершины)
            graph[i] = j  # запоминаем переход
        if len(graph) != self.n:  # если не все вершины задействованы
            return None  # не цикл

        start = 0  # начинаем с вершины 0
        cycle = [start]  # список для цикла
        current = start  # текущая вершина
        for _ in range(self.n - 1):  # проходим n-1 шаг
            if current not in graph:  # если нет исходящего ребра
                return None  # не цикл
            current = graph[current]  # переходим
            if current in cycle:  # если вершина уже была
                return None  # подцикл
            cycle.append(current)  # добавляем в цикл

        # Замыкающее ребро
        if graph.get(current, None) != start:  # проверяем замыкание
            return None  # не цикл
        return cycle  # возвращаем цикл

    # Метод-обёртка
    def get_cycle_from_edges(self, edges):  
        return self.edges_to_cycle(edges)  # вызывает edges_to_cycle

    # Метод сохранения дерева ветвления
    def save_tree_structure(self):  
        tree_file = open('tsp_tree.txt', 'w', encoding='utf-8')  # открываем файл
        tree_file.write("Дерево ветвления\n")  # заголовок

        def print_node(node_id, level=0):  # рекурсивная функция вывода узла
            node = self.tree_nodes[node_id]  # получаем узел
            indent = "  " * level  # отступ по уровню

            if node['edge']:  # если есть ребро
                i, j = node['edge']  # распаковываем
                edge_str = f"{i + 1}->{j + 1}"  # форматируем
            else:  # если корень
                edge_str = "корень"  # строка "корень"

            if node['included'] is True:  # если ребро включено
                include_str = "вкл"  # "вкл"
            elif node['included'] is False:  # если исключено
                include_str = "искл"  # "искл"
            else:  # если не определено
                include_str = ""  # пустая строка

            tree_file.write(f"{indent}+ Узел {node_id}: "  # записываем строку узла
                            f"θ={node['theta']:.1f} {edge_str} {include_str}\n")

            children = [nid for nid, n in self.tree_nodes.items()  # находим дочерние узлы
                        if n['parent'] == node_id]
            for child_id in sorted(children):  # сортируем и обходим
                print_node(child_id, level + 1)  # рекурсивно выводим

        root_nodes = [nid for nid, node in self.tree_nodes.items()  # находим корневые узлы
                      if node['parent'] is None]
        if root_nodes:  # если есть корень
            print_node(root_nodes[0])  # выводим дерево от корня

        tree_file.close()  # закрываем файл

# Функция чтения матрицы из CSV
def read_matrix_from_csv(filename):  
    matrix = []  # список для матрицы
    with open(filename, 'r', encoding='utf-8') as file:  # открываем файл
        csv_reader = csv.reader(file)  # создаём читатель CSV
        for row in csv_reader:  # проходим по строкам
            matrix_row = []  # строка матрицы
            for cell in row:  # проходим по ячейкам
                cell = cell.strip()  # убираем пробелы
                if cell.lower() == 'inf' or cell == '':  # если бесконечность или пусто
                    matrix_row.append(float('inf'))  # добавляем бесконечность
                else:  
                    try:  # пытаемся преобразовать в число
                        matrix_row.append(float(cell))  # добавляем число
                    except ValueError:  # если не число
                        matrix_row.append(float('inf'))  # добавляем бесконечность
            matrix.append(matrix_row)  # добавляем строку в матрицу
    return matrix  # возвращаем матрицу

def main():  
    if not os.path.exists('input.csv'):  # проверяем наличие файла
        print("Файл input.csv не найден!")  
        print("Создайте файл input.csv с матрицей стоимостей " 
              "(inf для запрещённых переходов).")
        return  # выход

    cost_matrix = read_matrix_from_csv('input.csv')  # читаем матрицу

    n = len(cost_matrix)  # размер матрицы
    for row in cost_matrix:  # проверяем квадратность
        if len(row) != n:  # если длина строки не равна n
            print("Ошибка: матрица должна быть квадратной!") 
            return  

    solver = TSPSolver(cost_matrix)  
    solution, cost = solver.solve()  # запускаем решение

    print("Решение завершено!")  

    if solution:  # если решение есть
        cycle = solver.edges_to_cycle(solution)  # получаем цикл
        if cycle:  # если цикл корректен
            path_str = "->".join(str(x + 1) for x in cycle)  # формируем строку
            print(f"\nОптимальная последовательность: {path_str}")  
            print(f"Минимальная стоимость: {cost}")  
        else:  # если цикл не корректен
            print("\nРешение содержит подциклы, проверьте лог")  
    else:  # если решения нет
        print("\nОптимальное решение не найдено, проверьте файл лога") 


if __name__ == "__main__":  
    main()  