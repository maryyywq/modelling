import tkinter as tk
from tkinter import ttk
import itertools

# Чтение данных из файла (для любого числа станков)
def load_jobs(filename):
    """
    Загружает данные из текстового файла.
    Формат: каждая строка содержит числа, разделённые ';' (a;b;c;...).
    Количество чисел определяет число станков.
    Возвращает список словарей: каждый содержит 'id' (начиная с 1) и 'times' (список времён).
    """
    jobs = []  # итоговый список
    with open(filename, encoding="utf-8") as f:
        # enumerate даёт номер строки (начиная с 0) и саму строку
        for i, line in enumerate(f):
            line = line.strip()         # убираем пробелы и переводы строк
            if not line:                # если строка пустая — пропускаем
                continue
            # разбиваем по ';' и преобразуем каждую часть в целое число
            times = [int(x) for x in line.split(";")]
            # сохраняем с id = i+1 (нумерация с 1)
            jobs.append({"id": i+1, "times": times})
    return jobs

# Алгоритм Джонсона для трёх станков (если применимо)
def johnson_sequence(jobs):
    """
    Реализует алгоритм Джонсона для трёх станков, если выполнено условие сводимости.
    Условие: (min a >= max b) ИЛИ (min c >= max b).
    Если условие не выполнено или число станков не равно 3, возвращает None.
    При сводимости задача преобразуется к двухстаночной:
        d_i = a_i + b_i
        e_i = b_i + c_i
    Затем применяется стандартный алгоритм Джонсона для двух станков.
    Возвращает список id деталей в оптимальном порядке или None.
    """
    # Проверяем, что число станков равно 3 (иначе алгоритм не применим)
    if len(jobs[0]["times"]) != 3:
        return None

    # Извлекаем времена для каждого станка в отдельные списки
    # (используем генераторы для удобства)
    min_a = min(j["times"][0] for j in jobs)   # минимум на станке 1
    max_b = max(j["times"][1] for j in jobs)   # максимум на станке 2
    min_c = min(j["times"][2] for j in jobs)   # минимум на станке 3

    # Проверяем условие сводимости: (min_a >= max_b) ИЛИ (min_c >= max_b)
    if not (min_a >= max_b or min_c >= max_b):
        return None   # алгоритм неприменим

    # Строим новую таблицу для двух фиктивных станков:
    # d = a + b, e = b + c
    new_jobs = [{"id": j["id"], 
                 "d": j["times"][0] + j["times"][1],
                 "e": j["times"][1] + j["times"][2]} for j in jobs]

    # Стандартный алгоритм Джонсона для двух станков 
    remaining = new_jobs.copy()   # копируем, чтобы не изменять исходный список
    front, back = [], []          # front – в начало, back – в конец (собирается в обратном порядке)

    while remaining:
        # Минимальные значения d и e среди оставшихся
        min_d = min(r["d"] for r in remaining)
        min_e = min(r["e"] for r in remaining)

        if min_d <= min_e:
            # Если минимум по d – деталь идёт в начало
            for r in remaining:
                if r["d"] == min_d:
                    front.append(r["id"])
                    remaining.remove(r)
                    break
        else:
            # Иначе минимум по e – деталь идёт в конец
            for r in remaining:
                if r["e"] == min_e:
                    back.insert(0, r["id"])   # вставляем в начало back (чтобы потом получился правильный порядок)
                    remaining.remove(r)
                    break

    # Итоговая последовательность: front + back
    return front + back

# Расчёт расписания для любого числа станков
def schedule(jobs, sequence):
    """
    По заданной последовательности деталей (sequence) вычисляет временные интервалы
    обработки на каждом станке. Число станков определяется по длине списка times в jobs.
    Возвращает:
        sched - список словарей, каждый содержит id детали и словарь ops,
                где ключ – номер станка (0..M-1), значение – (start, finish).
        makespan - общее время выполнения (время окончания на последнем станке).
    """
    num_machines = len(jobs[0]["times"])  # определяем число станков
    machine_times = [0] * num_machines    # текущие моменты освобождения каждого станка

    sched = []  # здесь будем хранить результат

    for jid in sequence:
        # Ищем времена для текущей детали (перебор по списку jobs)
        times = next(j["times"] for j in jobs if j["id"] == jid)
        start_finish = {}   # словарь для хранения (начало, конец) по каждому станку

        for m in range(num_machines):
            if m == 0:
                # Для первого станка: начало = текущее время освобождения станка 0
                s = machine_times[m]
            else:
                # Для остальных станков: начало = max(освобождение этого станка,
                #                                     окончание предыдущего станка для этой детали)
                s = max(machine_times[m], start_finish[m-1][1])
            f = s + times[m]          # конец = начало + время обработки
            start_finish[m] = (s, f)  # сохраняем
            machine_times[m] = f      # обновляем время освобождения станка

        # Добавляем информацию о детали в расписание
        sched.append({"id": jid, "ops": start_finish})

    # Общее время выполнения – момент освобождения последнего станка
    makespan = machine_times[-1]
    return sched, makespan

# Полный перебор (точное решение)
def brute_force(jobs):
    """
    Выполняет полный перебор всех возможных последовательностей (n! перестановок)
    и выбирает ту, которая даёт минимальное общее время (makespan).
    Возвращает список id деталей в оптимальном порядке.
    Работает для любого числа станков, но из-за факториальной сложности применима
    только для небольших n (обычно до 10).
    """
    best_seq = None                # лучшая последовательность
    best_ms = float("inf")         # лучшее время (изначально бесконечность)

    # itertools.permutations генерирует все перестановки id деталей
    for perm in itertools.permutations([j["id"] for j in jobs]):
        # Для каждой перестановки считаем расписание и makespan
        _, ms = schedule(jobs, perm)
        # Если текущее время меньше лучшего – обновляем
        if ms < best_ms:
            best_ms = ms
            best_seq = perm

    return list(best_seq)   # возвращаем как список

# Отрисовка диаграммы Ганта (для любого числа станков) 
def draw_gantt(canvas, sched, title, y_offset, canvas_width=1200, left_margin=100, right_margin=20):
    """
    Рисует диаграмму Ганта на canvas для произвольного числа станков.
    Автоматически подбирает масштаб по времени и ширине canvas.
    Параметры:
        canvas - объект tk.Canvas
        sched  - расписание, полученное из schedule()
        title  - заголовок диаграммы
        y_offset - вертикальное смещение начала диаграммы
        canvas_width - фиксированная ширина для расчёта масштаба
        left_margin, right_margin - отступы слева и справа
    Возвращает y-координату нижней границы диаграммы (для позиционирования следующей).
    """
    if not sched:
        return

    # Определяем число станков по количеству записей в первой операции
    num_machines = len(sched[0]["ops"])
    # Максимальное время окончания на последнем станке
    makespan = max(r["ops"][num_machines-1][1] for r in sched)
    if makespan == 0:
        makespan = 1   # защита от деления на ноль

    # Доступная ширина для рисования графика
    plot_width = canvas_width - left_margin - right_margin
    if plot_width < 10:
        plot_width = 10

    # Масштаб: пикселей на единицу времени
    scale_x = plot_width / makespan

    # Заголовок 
    canvas.create_text(left_margin, y_offset + 2, text=title, anchor="w",
                       font=("Arial", 11, "bold"), fill="#333")

    # Параметры строк
    row_height = 45          # высота одной строки станка
    block_height = 28        # высота прямоугольника
    y_start = y_offset + 30  # начало первой строки

    # Подписи станков 
    for m in range(num_machines):
        y_m = y_start + m * row_height
        canvas.create_text(left_margin - 10, y_m, text=f"Станок {m+1}", anchor="e",
                           font=("Arial", 9, "bold"))

    # Цветовая палитра 
    colors = ["#FFB3BA", "#BAFFC9", "#BAE1FF", "#FFFFBA", "#E8BAFF", "#FFD1BA",
              "#B3E6CC", "#FFB3D9", "#B3B3FF", "#FFCC99", "#99FFCC", "#FF9999"]

    # Временная сетка 
    # Подбираем шаг так, чтобы меток было не более 15
    step = 5
    while makespan / step > 15:
        step *= 2
    if step < 1:
        step = 1

    # Координата нижней границы (последняя строка + половина высоты)
    y_last = y_start + (num_machines - 1) * row_height
    y_bottom = y_last + row_height//2

    # Рисуем вертикальные линии и подписи времени
    for t in range(0, makespan + 1, step):
        x = left_margin + t * scale_x
        if x > left_margin + plot_width:
            break
        canvas.create_line(x, y_start - row_height//2, x, y_bottom,
                           fill="#e0e0e0", dash=(2,2))
        canvas.create_text(x, y_bottom + 15, text=str(t),
                           anchor="n", font=("Arial", 8), fill="#555")

    # Рисуем прямоугольники для каждой детали на каждом станке 
    for i, item in enumerate(sched):
        jid = item["id"]
        color = colors[i % len(colors)]
        for m in range(num_machines):
            s, f = item["ops"][m]   # начало и конец на этом станке
            x1 = left_margin + s * scale_x
            x2 = left_margin + f * scale_x
            y0 = y_start + m * row_height - block_height//2
            y1 = y0 + block_height
            canvas.create_rectangle(x1, y0, x2, y1, fill=color, outline="black", width=1)
            # Если блок широкий, пишем номер детали внутри
            if x2 - x1 > 20:
                canvas.create_text((x1+x2)/2, (y0+y1)/2, text=str(jid),
                                   font=("Arial", 9, "bold"), fill="#000")

    # Подпись общего времени (makespan)
    canvas.create_text(left_margin + plot_width//2, y_bottom + 45,
                       text=f"Общее время: {makespan}",
                       font=("Arial", 10, "bold"), fill="#006600")

    # Возвращаем нижнюю границу, чтобы разместить следующую диаграмму
    return y_bottom + 45

# Основная программа 
# Загружаем данные из файла "jobs.csv"
jobs = load_jobs("jobs.csv")

# Исходная последовательность (порядок в файле)
orig_seq = [j["id"] for j in jobs]
# Рассчитываем её расписание
sched_orig, ms_orig = schedule(jobs, orig_seq)

# Оптимальная последовательность по алгоритму Джонсона (только для 3 станков)
opt_seq = johnson_sequence(jobs)
# Если применим, считаем расписание
sched_opt, ms_opt = (schedule(jobs, opt_seq) if opt_seq else (None, None))

# Точное решение полным перебором (для любого числа станков)
best_seq = brute_force(jobs)
sched_best, ms_best = schedule(jobs, best_seq)

# Создаём графический интерфейс
root = tk.Tk()
root.title(f"Перебор + Джонсон (станков: {len(jobs[0]['times'])})")

# Таблица с исходными данными
frame = ttk.Frame(root)
frame.pack(fill="x", padx=10, pady=5)
lbl = ttk.Label(frame, text="Исходные данные (время на станках):", font=("Arial", 12, "bold"))
lbl.pack(anchor="w", pady=5)

cols = [f"m{i+1}" for i in range(len(jobs[0]["times"]))]
tree = ttk.Treeview(frame, columns=cols, show="headings", height=len(jobs))
for i, col in enumerate(cols):
    tree.heading(col, text=f"Станок {i+1}")
for j in jobs:
    tree.insert("", "end", values=j["times"])
tree.pack(fill="x")

# Контейнер для Canvas с вертикальной прокруткой
canvas_frame = tk.Frame(root)
canvas_frame.pack(fill="both", expand=True, padx=10, pady=10)

canvas = tk.Canvas(canvas_frame, width=1200, height=600, bg="white")
scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
canvas.configure(yscrollcommand=scrollbar.set)
scrollbar.pack(side="right", fill="y")
canvas.pack(side="left", fill="both", expand=True)

# Отрисовка диаграмм 
y = 20                    # текущее вертикальное смещение
left_margin = 100         # для выравнивания сообщения

# Исходная последовательность
seq_str_orig = "(" + ",".join(map(str, orig_seq)) + ")"
bottom_orig = draw_gantt(canvas, sched_orig, "Исходная последовательность: " + seq_str_orig,
                         y_offset=y, canvas_width=1200)
y = bottom_orig + 40      # отступ перед следующей диаграммой

# Алгоритм Джонсона (если применим)
if sched_opt:
    seq_str_opt = "(" + ",".join(map(str, opt_seq)) + ")"
    bottom_opt = draw_gantt(canvas, sched_opt, "Алгоритм Джонсона: " + seq_str_opt,
                            y_offset=y, canvas_width=1200)
    y = bottom_opt + 40
else:
    # Сообщение о неприменимости выводим с отступом left_margin
    canvas.create_text(left_margin, y, text="Алгоритм Джонсона неприменим для этих данных",
                       anchor="w", font=("Arial", 12, "bold"), fill="red")
    y += 75

# Перебор (точное решение)
seq_str_best = "(" + ",".join(map(str, best_seq)) + ")"
draw_gantt(canvas, sched_best, "Перебор (точное решение): " + seq_str_best,
           y_offset=y, canvas_width=1200)

# Устанавливаем область прокрутки так, чтобы охватить всё содержимое
canvas.config(scrollregion=canvas.bbox("all"))

# Запускаем главный цикл
root.mainloop()