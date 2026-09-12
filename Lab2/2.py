import random
import itertools
import tkinter as tk
from tkinter import ttk

# Палитра для диаграммы Ганта
GANTT_COLORS = ["#FFB3BA", "#BAFFC9", "#BAE1FF", "#FFFFBA", "#E8BAFF", "#FFD1BA",
                "#B3E6CC", "#FFB3D9", "#B3B3FF", "#FFCC99", "#99FFCC", "#FF9999"]

# Читает файл, где каждая строка — времена обработки детали по станкам
def load_jobs(filename):
    jobs = []  # сюда собираем все детали

    # Открываем файл для чтения, кодировка UTF-8
    with open(filename, encoding="utf-8") as f:

        # enumerate нумерует строки с нуля: i — индекс, line — сама строка
        for i, line in enumerate(f):

            # Убираем пробелы/переносы в начале и в конце
            line = line.strip()

            # Пустые строки пропускаем
            if not line:
                continue

            # Разбиваем по ';' и превращаем в целые числа
            times = [int(x) for x in line.split(";")]

            # id = номер строки + 1, times = времена операций
            jobs.append({"id": i + 1, "times": times})

    return jobs

def schedule(jobs, sequence):
    # Строит расписание обработки деталей для заданной последовательности.
    # jobs     — список деталей
    # sequence — порядок запуска (список id)

    # Возвращает:
    # sched — список, по одному элементу на каждую деталь, в том порядке, в котором они запускались (совпадает
    # с sequence). Каждый элемент — словарь:
    # {
    #   "id":  <номер детали>,
    #   "ops": { <номер станка>: (<start>, <finish>), ... }
                                                            # } 
    # makespan — Cmax = время завершения последней операции

    # Число станков — одинаковое у всех деталей
    num_machines = len(jobs[0]["times"])

    # machine_times[m] — когда станок m освободится (сначала все свободны, 0)
    machine_times = [0] * num_machines

    # Итоговое расписание
    sched = []

    # Идём по деталям в порядке sequence
    for jid in sequence:

        # Достаём времена обработки детали по её id
        times = next(j["times"] for j in jobs if j["id"] == jid)

        # Пары (старт, конец) по каждому станку для этой детали
        start_finish = {}

        # Проходим по всем станкам по порядку
        for m in range(num_machines):

            # Первый станок: старт = когда станок освободится
            if m == 0:
                s = machine_times[0]

            # Остальные станки
            else:
                # Нулевая операция: станок не занимается,
                # старт = конец предыдущей операции детали
                if times[m] == 0:
                    s = start_finish[m - 1][1]
                # Обычная операция: старт = максимум из:
                #   1) освобождения станка
                #   2) окончания предыдущей операции детали
                else:
                    s = max(machine_times[m], start_finish[m - 1][1])

            # Конец = старт + длительность
            f = s + times[m]

            # Сохраняем пару
            start_finish[m] = (s, f)

            # Обновляем время освобождения станка (нулевые операции не занимают станок)
            if times[m] != 0:
                machine_times[m] = f

        # Добавляем в общий список запись по этой детали
        sched.append({"id": jid, "ops": start_finish})

    # Cmax = когда освободится последний станок
    makespan = machine_times[-1]

    return sched, makespan

# Алгоритм полного перебора
def brute_force(jobs):
    # Пробует ВСЕ перестановки деталей (n! вариантов).
    # Возвращает лучшую последовательность и её Cmax.
    best_seq = None               # лучшая последовательность
    best_ms = float("inf")        # лучший Cmax (пока бесконечность)

    # itertools.permutations генерирует все перестановки id
    for perm in itertools.permutations([j["id"] for j in jobs]):

        # Считаем Cmax. Расписание не нужно, поэтому кладём в _
        _, ms = schedule(jobs, perm)

        # Нашли быстрее — запоминаем
        if ms < best_ms:
            best_ms = ms
            best_seq = perm

    return list(best_seq), best_ms

# Параметры Петрова (P1, P2, λ) для каждой детали
def compute_petrov_params(jobs):
    # Метод Петрова делит маршрут на две половины:
      # P1 = сумма первой половины операций
      # P2 = сумма второй половины операций
      # λ = P2 − P1

    # Четное m: ровно пополам (m/2 и m/2).
    # Нечетное m: средняя операция входит в ОБЕ суммы.

    m = len(jobs[0]["times"])  # число станков. Оно одинаково у всех деталей, поэтому берём его у первой попавшейся детали
    params = []

    # Чётное число станков — делим пополам
    if m % 2 == 0:
        k = m // 2  # k — индекс, на котором заканчивается первая половина
        for j in jobs:
            times = j["times"]             # времена обработки детали
            P1 = sum(times[0:k])           # первая половина: индексы 0, 1, ..., k−1
            P2 = sum(times[k:m])           # вторая половина: индексы k, k+1, ..., m−1
            lam = P2 - P1                  # λ — насколько «вторая половина» тяжелее первой
            params.append({"id": j["id"], "P1": P1, "P2": P2,   # Складываем всё в общий список
                           "lambda": lam, "times": times})

    # Нечётное — средняя операция попадает в обе суммы
    else:
        k = (m + 1) // 2    # k = (m + 1) / 2 — длина первой половины, включая центральный станок
        for j in jobs:
            times = j["times"]
            P1 = sum(times[0:k])           # Первая половина: индексы 0, 1, ..., k−1
            P2 = sum(times[k-1:m])         # Вторая половина: НАЧИНАЯ С ЦЕНТРАЛЬНОГО (индекс k−1),
                                           # а не с индекса k. Именно поэтому средний станок
                                           # учитывается и в P1, и в P2.
            lam = P2 - P1
            params.append({"id": j["id"], "P1": P1, "P2": P2,
                           "lambda": lam, "times": times})

    return params

# Сортировки для правил Петрова
def sort_by_P1(lst):
    # По P1 по возрастанию.
    # При равенстве P1 — по λ по УБЫВАНИЮ (−x["lambda"]).
    # При равенстве λ — по id
    return sorted(lst, key=lambda x: (x["P1"], -x["lambda"], x["id"]))


def sort_by_P2(lst):
    # По P2 по убыванию (−x["P2"]).
    # При равенстве P2 — по λ по УБЫВАНИЮ.
    # При равенстве λ — по id
    return sorted(lst, key=lambda x: (-x["P2"], -x["lambda"], x["id"]))

# Правило 2 Петрова
def rule2(params):
    # Правило 2:
      # 1) Детали разбиваются на группы с одинаковым λ.
      # 2) Группы идут в порядке убывания λ.
      # 3) Внутри группы:
           # λ >= 0 -> сортировка по P1 (возрастание),
           # λ < 0 -> сортировка по P2 (убывание).
      # 4) Если у нескольких деталей совпадают и P1, и P2 — их порядок случаен

    # used[i] = True означает «деталь i уже добавлена в какую-то группу».
    # Нужен, чтобы одну и ту же деталь не засунуть в две группы
    used = [False] * len(params)  
    groups = []                    # пары (λ, [детали])
                                   # После формирования отсортируем этот список по убыванию λ.

    # Формируем группы деталей с одинаковым λ
    for i, p in enumerate(params):
        # Если деталь уже попала в какую-то группу — пропускаем
        if used[i]:
            continue

        same = [p]                # новая группа начинается с текущей деталью
        used[i] = True

        # Проходим по всем деталям после i и ищем такие же λ
        for j in range(i + 1, len(params)):
            if not used[j] and params[j]["lambda"] == p["lambda"]:
                same.append(params[j])
                used[j] = True

        groups.append((p["lambda"], same))

    # Группы — по убыванию λ
    groups.sort(key=lambda x: -x[0])

    # Сюда будем складывать итоговый порядок деталей
    ordered = []  
    # Обходим группы по очереди и сортируем детали внутри
    for lam_val, group in groups:

        # Случай A: λ >= 0 
        if lam_val >= -1e-9:  # -1e-9 — допуск на погрешность float
            # Сортируем группу по P1 по возрастанию.
            # При равенстве P1 — по id 
            group_sorted = sorted(group, key=lambda x: (x["P1"], x["id"]))

            # Теперь идём по отсортированной группе и ищем части
            # с одинаковым P1. Такие куски нужно обработать отдельно:
            # если у этих частей совпадает ещё и P2 — перемешать
            i = 0
            while i < len(group_sorted):
                # Ищем правую границу куска с тем же P1, что и у элемента i
                j = i + 1
                while j < len(group_sorted) and group_sorted[j]["P1"] == group_sorted[i]["P1"]:
                    j += 1

                # bucket — это срез [i:j], все элементы с одинаковым P1
                bucket = group_sorted[i:j]

                # Если у всех в куске одинаков ещё и P2 — все параметры
                # у них полностью совпадают. Тогда сортировка по P1 и P2
                # ничего не решает, и мы перемешиваем случайно
                if all(b["P2"] == bucket[0]["P2"] for b in bucket):
                    random.shuffle(bucket)

                # Добавляем готовый кусок в итоговый список
                ordered.extend(bucket)
                # Переходим к следующему куску
                i = j

        # λ < 0: сортируем по P2 (убывание)
        else:
            # Сортируем группу по P2 по УБЫВАНИЮ.
            # Минус перед x["P2"] даёт обратный порядок.
            # При равенстве P2 — по id
            group_sorted = sorted(group, key=lambda x: (-x["P2"], x["id"]))

            # Ищем куски с одинаковым P2
            i = 0
            while i < len(group_sorted):
                # Правая граница куска с тем же P2
                j = i + 1
                while j < len(group_sorted) and group_sorted[j]["P2"] == group_sorted[i]["P2"]:
                    j += 1

                # Срез с одинаковым P2
                bucket = group_sorted[i:j]

                # Если у всех в куске совпадает ещё и P1 — параметры
                # полностью одинаковые, перемешиваем
                if all(b["P1"] == bucket[0]["P1"] for b in bucket):
                    random.shuffle(bucket)

                # Добавляем кусок в итог
                ordered.extend(bucket)
                # Следующий кусок
                i = j

    return ordered

# Формирование 4 последовательностей по правилам Петрова
def petrov_sequences(jobs):
    # Возвращает 4 последовательности (Петров-1..4) и параметры (P1, P2, λ).

    # Детали делятся на классы:
      # D1 — λ > 0
      # D0 — λ = 0
      # D2 — λ < 0
      
    # params — список словарей с P1, P2, λ и временами каждой детали
    params = compute_petrov_params(jobs)

    # Разбиение на три класса
    D1 = [p for p in params if p["lambda"] > 0]
    D0 = [p for p in params if p["lambda"] == 0]
    D2 = [p for p in params if p["lambda"] < 0]

    # Правило 1 
    # λ >= 0 (D1+D0) по P1 возрастанию, затем λ < 0 (D2) по P2 убыванию
    # Объединяем D1 и D0 в один список и сортируем по P1 (возрастание)
    D10 = sort_by_P1(D1 + D0)
    # D2 сортируем отдельно — по P2 (убывание)
    D2_sorted = sort_by_P2(D2)
    # Склеиваем два отсортированных списка и берём только id деталей
    seq1 = [p["id"] for p in D10] + [p["id"] for p in D2_sorted]

    # Правило 2
    # Функция rule2() группирует по λ, сортирует группы по λ убыванию,
    # внутри группы — по P1 (для λ >= 0) или по P2 (для λ < 0)
    seq2 = [p["id"] for p in rule2(params)]

    # Правило 3
    # Порядок трёх классов строго друг за другом: D1, потом D0, потом D2
    # Каждый класс внутри сортируется своим правилом

    # D1 по P1 (возрастание)
    # D0 тоже по P1 (возрастание) 
    # D2 по P2 (убывание)
    seq3 = [p["id"] for p in sort_by_P1(D1)] + \
           [p["id"] for p in sort_by_P1(D0)] + \
           [p["id"] for p in sort_by_P2(D2)]

    # Правило 4
    # Вспомогательная функция: разбивает список на пары и сортирует их
    def pairwise_order_and_sort(lst):
        # Первая в паре — деталь с максимальным P2
        # Вторая в паре — деталь с минимальным P1 из оставшихся
        # Пары сортируются по убыванию delta = P2_first − P1_second
        # a — копия списка, чтобы не менять оригинал (мы из него удаляем)
        a = lst.copy()
        # pairs — список сформированных пар
        pairs = []

        # Пока в списке есть хотя бы 2 элемента — можем собрать пару
        while len(a) >= 2:
            # Ищем first — максимум по P2 (при равенстве — по λ, потом по id)
            first = max(a, key=lambda x: (x["P2"], x["lambda"], -x["id"]))
            # Удаляем first из списка, чтобы он не попал во вторую часть
            a.remove(first)
            # Ищем second — минимум по P1 (при равенстве — по −λ, потом по id)
            second = min(a, key=lambda x: (x["P1"], -x["lambda"], x["id"]))
            # Удаляем second из списка
            a.remove(second)
            # Сохраняем готовую пару
            pairs.append((first, second))

        # Если после разбиения на пары остался один элемент — это leftover (одиночный элемент)
        leftover = a[0] if a else None

        # Сортируем пары по убыванию разности delta (reverse=True даёт убывание)
        pairs.sort(key=lambda pr: (pr[0]["P2"] - pr[1]["P1"]), reverse=True)
        # Возвращаем пары и возможный одиночный элемент
        return pairs, leftover

    # seq4_list — сюда будем складывать детали правила 4 в нужном порядке
    seq4_list = []

    # Шаг 1: обрабатываем класс D1
    # Разбиваем D1 на пары и получаем возможный одиночный элемент
    pairs1, leftover1 = pairwise_order_and_sort(D1)

    # Если в D1 остался одиночный элемент — ищем ему пару
    if leftover1:
        # Сначала пробуем взять пару из D0 (там детали с λ = 0)
        if D0:
            # Берём из D0 деталь с минимальным P1
            candidate = min(D0, key=lambda x: (x["P1"], -x["lambda"], x["id"]))
            # Убираем её из D0, чтобы не использовать повторно
            D0 = [x for x in D0 if x["id"] != candidate["id"]]
            # Добавляем новую пару (одиночный из D1 + взятый из D0)
            pairs1.append((leftover1, candidate))
            # Пересортировываем пары после добавления новой
            pairs1.sort(key=lambda pr: (pr[0]["P2"] - pr[1]["P1"]), reverse=True)
            # Одиночный элемент теперь «пристроен», обнуляем флаг
            leftover1 = None
        # Если D0 пуст — пробуем взять пару из D2
        elif D2:
            # Берём из D2 деталь с минимальным P1
            candidate = min(D2, key=lambda x: (x["P1"], -x["lambda"], x["id"]))
            # Убираем её из D2
            D2 = [x for x in D2 if x["id"] != candidate["id"]]
            # Формируем пару из одиночного D1 и этой детали D2
            pairs1.append((leftover1, candidate))
            # Пересортировываем пары
            pairs1.sort(key=lambda pr: (pr[0]["P2"] - pr[1]["P1"]), reverse=True)
            # Одиночного больше нет
            leftover1 = None

    # Распаковываем пары D1 в итоговый список seq4_list (по порядку пар)
    for a, b in pairs1:
        seq4_list.append(a)
        seq4_list.append(b)

    # Шаг 2: обрабатываем класс D0
    # Разбиваем D0 на пары (D0 мог уменьшиться, если из него брали пару для D1)
    pairs0, leftover0 = pairwise_order_and_sort(D0)
    # Распаковываем пары D0 в общий список
    for a, b in pairs0:
        seq4_list.append(a)
        seq4_list.append(b)

    # Если в D0 остался одиночный элемент — ищем ему пару в D2
    if leftover0:
        if D2:
            # Берём из D2 деталь с минимальным P1
            candidate = min(D2, key=lambda x: (x["P1"], -x["lambda"], x["id"]))
            # Убираем её из D2
            D2 = [x for x in D2 if x["id"] != candidate["id"]]
            # Добавляем одиночного из D0 и пару к нему из D2
            seq4_list.append(leftover0)
            seq4_list.append(candidate)
            # Одиночного больше нет
            leftover0 = None
        else:
            # Если D2 пуст — просто добавляем одиночного в конец списка
            seq4_list.append(leftover0)
            leftover0 = None

    # Шаг 3: обрабатываем класс D2
    # Разбиваем оставшийся D2 на пары
    pairs2, leftover2 = pairwise_order_and_sort(D2)
    # Распаковываем пары D2 в общий список
    for a, b in pairs2:
        seq4_list.append(a)
        seq4_list.append(b)

    # Если после D2 остался одиночный элемент — назовём его dx
    dx = None
    if leftover2:
        dx = leftover2

    # Считаем итоговое количество элементов (с учётом возможного dx)
    total_count = len(seq4_list) + (1 if dx is not None else 0)
    # Если общее число нечетное и есть одиночный dx — нужно его куда-то вставить
    if total_count % 2 == 1 and dx is not None:
        # Флаг: удалось ли найти место для dx
        placed = False
        # Сколько целых пар в seq4_list
        num_pairs = len(seq4_list) // 2

        # Идём по парам (кроме последней) и ищем подходящее место
        for p in range(num_pairs - 1):
            # Левая пара: элементы с индексами 2p и 2p+1
            left1 = seq4_list[2 * p]
            left2 = seq4_list[2 * p + 1]
            # Правая пара: элементы с индексами 2(p+1) и 2(p+1)+1
            right1 = seq4_list[2 * (p + 1)]
            right2 = seq4_list[2 * (p + 1) + 1]

            # Максимум λ в левой паре
            max_left_lambda = max(left1["lambda"], left2["lambda"])
            # Минимум λ в правой паре
            min_right_lambda = min(right1["lambda"], right2["lambda"])

            # Условие: λ(dx) «между» левой и правой парами по λ
            if max_left_lambda >= dx["lambda"] and dx["lambda"] >= min_right_lambda:
                # Вставляем dx между парами: после элементов левой пары
                insert_pos = 2 * p + 2
                seq4_list.insert(insert_pos, dx)
                # Место найдено
                placed = True
                break

        # Если подходящего места не нашли — просто добавляем dx в конец
        if not placed:
            seq4_list.append(dx)

    # Превращаем список словарей в список id деталей
    seq4 = [p["id"] for p in seq4_list]

    # Возвращаем словарь со всеми 4 последовательностями + исходные параметры
    return {"Петров-1": seq1, "Петров-2": seq2, "Петров-3": seq3,
            "Петров-4": seq4, "params": params}

# Формирование случайной последовательности
def random_sequence_from_bag(jobs):
    # Возвращает (последовательность, её Cmax).

    # Собираем все id деталей в список
    ids = [j["id"] for j in jobs]
    seq = ids[:]              # копия, чтобы не портить оригинал
    random.shuffle(seq)       # перемешиваем

    # Считаем расписание для этой случайной последовательности.
    # schedule возвращает (sched, makespan). Само расписание нам не нужно,
    # поэтому первое значение кладём в _, а Cmax — в ms.
    # tuple(seq) — потому что schedule ожидает последовательность,
    # и кортеж тут работает точно так же, как список.
    _, ms = schedule(jobs, tuple(seq))
    return seq, ms

# Правило Джонсона (вспомогательное для CDS)
def johnson_2machine(pairs):

    remaining = list(pairs)   # копия для удаления
    front, back = [], []      # front — детали, которые ставим в начало
                              # back  — детали, которые ставим в конец

    # Работаем, пока есть нераспределённые детали
    while remaining:
        # Минимальное t1 среди оставшихся деталей
        min_t1 = min(r["t1"] for r in remaining)
        # Минимальное t2 среди оставшихся деталей
        min_t2 = min(r["t2"] for r in remaining)

        # Минимум по t1, значит добавляем в начало
        if min_t1 <= min_t2:
            # Ищем первую деталь с t1 == min_t1
            for idx, r in enumerate(remaining):
                if r["t1"] == min_t1:
                    front.append(r["id"])
                    remaining.pop(idx)
                    break
        # Минимум по t2, значит добавляем в конец
        else:
            for idx, r in enumerate(remaining):
                if r["t2"] == min_t2:
                    back.insert(0, r["id"])  # вставляем в начало back (идём с конца)
                    remaining.pop(idx)
                    break

    return front + back

# Алгоритм CDS 
def cds_algorithm(jobs):
    # Обобщение правила Джонсона на m станков.
    # Для каждого k = 1..m−1:
        # t1 = сумма первых k операций детали
        # t2 = сумма последних (m−k) операций детали
    # К каждой такой двухмашинной задаче применяется правило Джонсона.
    # Из всех m−1 последовательностей выбирается лучшая по реальному Cmax.
    # Возвращает: (лучшая последовательность, её Cmax, номер лучшего k, все результаты).

    m = len(jobs[0]["times"])   # число станков

    best_seq = None             # лучшая последовательность
    best_ms = float("inf")      # лучший Cmax
    best_k = None               # при каком k он достигнут
    all_results = []            # все промежуточные результаты

    # Перебираем все k от 1 до m−1
    for k in range(1, m):

        # Шаг 1. Формируем двухмашинную задачу для текущего k
        pairs = []
        for j in jobs:
            times = j["times"]
            # t1 — сумма первых k операций детали
            # times[0:k] — срез от индекса 0 до k−1 включительно
            t1 = sum(times[0:k]) 
            t2 = sum(times[k:m])    # последние m−k операций
            pairs.append({"id": j["id"], "t1": t1, "t2": t2}) # Складываем получившуюся «двухмашинную» пару для этой детали

        # Шаг 2. Применяем к двухмашинной задаче правило Джонсона
        seq = johnson_2machine(pairs)

        # Шаг 3. Считаем РЕАЛЬНЫЙ Cmax для исходной задачи.
        _, ms = schedule(jobs, seq)

        # Шаг 4. Сохраняем результат для этого k
        all_results.append({"k": k, "seq": seq, "ms": ms})

        # Шаг 5. Обновляем лучший результат
        if ms < best_ms:
            best_ms = ms
            best_seq = seq
            best_k = k

    return best_seq, best_ms, best_k, all_results

# Отрисовка диаграммы Ганта
def draw_gantt(canvas, sched, title, y_offset, canvas_width=1200):
    # Рисует диаграмму Ганта на холсте.
    # sched        — расписание из schedule()
    # title        — заголовок над диаграммой
    # y_offset     — с какой вертикальной позиции начинать
    # canvas_width — ширина холста (для расчёта масштаба)
    # Возвращает вертикальную координату, с которой можно рисовать следующую
    # диаграмму.

    # Нет данных — пишем красным и выходим
    if sched is None:
        canvas.create_text(10, y_offset, text=title + " (нет данных)",
                           anchor="w", font=("Arial", 12, "bold"), fill="red")
        return y_offset + 60

    num_machines = len(sched[0]["ops"])  # число станков

    # Cmax = максимум окончаний на последнем станке
    makespan = max(r["ops"][num_machines - 1][1] for r in sched)
    if makespan == 0:
        makespan = 1  # защита от деления на ноль

    # Геометрия
    left_margin = 100    # слева — подписи «Станок N»
    right_margin = 20
    row_height = 45      # расстояние между дорожками станков
    block_height = 28    # высота прямоугольника операции

    # Ширина рабочей области
    plot_width = canvas_width - left_margin - right_margin
    if plot_width < 10:
        plot_width = 10

    # Пикселей на одну единицу времени
    scale_x = plot_width / makespan

    # Заголовок
    canvas.create_text(left_margin, y_offset + 2, text=title, anchor="w",
                       font=("Arial", 11, "bold"), fill="#333")

    # Y-координата центра каждой дорожки станка
    y_rows = [y_offset + 30 + mm * row_height for mm in range(num_machines)]

    # Подписи «Станок 1», «Станок 2», ... слева
    for mm, yy in enumerate(y_rows):
        canvas.create_text(left_margin - 10, yy, text=f"Станок {mm+1}",
                           anchor="e", font=("Arial", 9, "bold"))

    # Границы сетки сверху/снизу
    y_top = y_rows[0] - row_height // 2
    y_bot = y_rows[-1] + row_height // 2

    # Авто-шаг меток: не больше ~15 делений
    step = 5
    while makespan / step > 15:
        step *= 2
    if step < 1:
        step = 1

    # Вертикальная сетка + подписи времени
    for t in range(0, makespan + 1, step):
        x = left_margin + t * scale_x
        if x > left_margin + plot_width:
            break
        canvas.create_line(x, y_top, x, y_bot, fill="#e0e0e0", dash=(2, 2))
        canvas.create_text(x, y_bot + 15, text=str(t),
                           anchor="n", font=("Arial", 8), fill="#555")

    # Рисуем блоки операций
    for i, r in enumerate(sched):
        jid = r["id"]
        color = GANTT_COLORS[i % len(GANTT_COLORS)]  # цвет по кругу

        for mm, yy in enumerate(y_rows):
            s, f = r["ops"][mm]

            # Нулевые операции не рисуем
            if f - s <= 0:
                continue

            # Координаты прямоугольника
            x1 = left_margin + s * scale_x
            x2 = left_margin + f * scale_x
            y0 = yy - block_height // 2
            y1l = yy + block_height // 2

            # Сам прямоугольник
            canvas.create_rectangle(x1, y0, x2, y1l, fill=color,
                                    outline="black", width=1)

            # Номер детали внутри — если блок достаточно широкий
            if x2 - x1 > 20:
                canvas.create_text((x1 + x2) / 2, (y0 + y1l) / 2,
                                   text=str(jid), font=("Arial", 9, "bold"),
                                   fill="#000")

    # Зелёная надпись «Общее время: X» под диаграммой
    canvas.create_text(left_margin + plot_width // 2, y_bot + 45,
                       text=f"Общее время: {makespan}",
                       font=("Arial", 10, "bold"), fill="#006600")

    # Возвращаем y для следующей диаграммы (+100 px запаса)
    return y_bot + 100

# 1) Загрузка данных
jobs = load_jobs("jobs.csv")

# 2) Исходная последовательность (по порядку id)
orig_seq = [j["id"] for j in jobs]
sched_orig, ms_orig = schedule(jobs, orig_seq)

# 3) Последовательности по правилам Петрова
petrov_res = petrov_sequences(jobs)
petrov_seqs = {k: v for k, v in petrov_res.items() if k.startswith("Петров")}

# Считаем расписание и Cmax для каждой из 4 последовательностей
petrov_schedules = {}
petrov_makespans = {}
for name, seq in petrov_seqs.items():
    sched, ms = schedule(jobs, seq)
    petrov_schedules[name] = sched
    petrov_makespans[name] = ms

# 4) CDS — лучшая последовательность, Cmax и лучший k
cds_seq, cds_ms, cds_k, cds_all = cds_algorithm(jobs)
sched_cds, _ = schedule(jobs, cds_seq)

# 5) Случайная последовательность
rand_seq, rand_ms = random_sequence_from_bag(jobs)
sched_rand, _ = schedule(jobs, rand_seq)

# 6) Полный перебор (оптимум для сравнения)
brute_seq, brute_ms = brute_force(jobs)
sched_brute, _ = schedule(jobs, brute_seq)

# Главное окно
root = tk.Tk()
root.title(f"Метод Петрова + CDS + Случайный + Перебор (станков: {len(jobs[0]['times'])})")

# Таблица с исходными данными
frame = ttk.Frame(root)
frame.pack(fill="x", padx=10, pady=5)

lbl = ttk.Label(frame, text="Исходные данные (по строкам — детали):",
                font=("Arial", 12, "bold"))
lbl.pack(anchor="w", pady=5)

# Отдельный фрейм для таблицы, чтобы приделать ползунок
table_frame = ttk.Frame(frame)
table_frame.pack(fill="x", padx=4, pady=4)

# Вертикальный ползунок справа
tree_v_scroll = ttk.Scrollbar(table_frame, orient="vertical")
tree_v_scroll.pack(side="right", fill="y")

# Имена столбцов m1, m2, ...
cols = [f"m{i+1}" for i in range(len(jobs[0]["times"]))]

# Высота таблицы — не больше 10 строк (иначе появляется ползунок)
tree_height = min(len(jobs), 10)

tree = ttk.Treeview(table_frame, columns=cols, show="headings",
                    height=tree_height, yscrollcommand=tree_v_scroll.set)
tree_v_scroll.config(command=tree.yview)  # связываем ползунок и таблицу

# Заголовки столбцов
for i, col in enumerate(cols):
    tree.heading(col, text=f"Станок {i+1}")
    tree.column(col, width=80, anchor="center")

# Заполняем таблицу временами обработки
for j in jobs:
    tree.insert("", "end", values=j["times"])
tree.pack(side="left", fill="x", expand=True)

# Контейнер для диаграмм (Canvas + ползунок) 
canvas_container = ttk.Frame(root)
canvas_container.pack(fill="both", expand=True, padx=10, pady=10)

v_scrollbar = ttk.Scrollbar(canvas_container, orient="vertical")
v_scrollbar.pack(side="right", fill="y")

CANVAS_WIDTH = 1200
canvas = tk.Canvas(canvas_container, width=CANVAS_WIDTH, height=600,
                   bg="white", yscrollcommand=v_scrollbar.set)
canvas.pack(side="left", fill="both", expand=True)

v_scrollbar.config(command=canvas.yview)

# Рисуем диаграммы одну за другой

y = 20  # текущая вертикальная позиция

# Исходная
y = draw_gantt(canvas, sched_orig,
               f"Исходная последовательность: {tuple(orig_seq)}",
               y, CANVAS_WIDTH)

# Правила Петрова
for name, sched in petrov_schedules.items():
    y = draw_gantt(canvas, sched,
                   f"{name}: {tuple(petrov_seqs[name])}",
                   y, CANVAS_WIDTH)

# CDS (с указанием лучшего k)
y = draw_gantt(canvas, sched_cds,
               f"CDS (k = {cds_k}): {tuple(cds_seq)}",
               y, CANVAS_WIDTH)

# Случайная
y = draw_gantt(canvas, sched_rand,
               f"Случайная последовательность: {tuple(rand_seq)}",
               y, CANVAS_WIDTH)

# Полный перебор
y = draw_gantt(canvas, sched_brute,
               f"Перебор (лучшее): {tuple(brute_seq)}",
               y, CANVAS_WIDTH)

# Обновляем scrollregion, чтобы всё нарисованное было доступно 
canvas.update_idletasks()          # пересчёт размеров
bbox = canvas.bbox("all")          # границы нарисованного
if bbox:
    canvas.config(scrollregion=(bbox[0], bbox[1], bbox[2], bbox[3] + 80))

# Запуск главного цикла (без него окно мгновенно закроется)
root.mainloop()