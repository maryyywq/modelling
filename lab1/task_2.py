import tkinter as tk
from tkinter import ttk

# Чтение данных из файла (для 3 станков)
def load_jobs(filename):
    """
    Загружает данные из текстового файла.
    Ожидается формат: каждая строка содержит три числа, разделённых ';' : a;b;c
    a - время на станке 1, b - на станке 2, c - на станке 3.
    Возвращает список словарей с ключами: 'id', 'a', 'b', 'c'.
    """
    jobs = []  # итоговый список деталей
    # открываем файл в кодировке utf-8 
    with open(filename, encoding="utf-8") as f:
        # enumerate даёт номер строки (начиная с 0) и саму строку
        for i, line in enumerate(f):
            line = line.strip()   # убираем пробелы и переводы строк
            if not line:          # если строка пустая — пропускаем
                continue
            # разбиваем по разделителю ';' и получаем три строки
            a, b, c = line.split(";")
            # добавляем словарь: id = i+1 (чтобы нумерация начиналась с 1),
            # времена преобразуем в целые числа
            jobs.append({"id": i+1, "a": int(a), "b": int(b), "c": int(c)})
    return jobs

# Алгоритм Джонсона для трёх станков
def johnson_sequence(jobs):
    """
    Реализует алгоритм Джонсона для трёх станков, если выполнено условие сводимости.
    Условие: (min a >= max b) ИЛИ (min c >= max b) для всех деталей.
    Если условие не выполнено, возвращает None (алгоритм неприменим).
    При сводимости задача преобразуется к двухстаночной:
        d_i = a_i + b_i   (время на "первом" фиктивном станке)
        e_i = b_i + c_i   (время на "втором" фиктивном станке)
    Затем применяется обычный алгоритм Джонсона для двух станков.
    Возвращает список id деталей в оптимальном порядке или None.
    """
    # Вычисляем минимальное время на станке 1 среди всех деталей
    min_a = min(j["a"] for j in jobs)
    # Максимальное время на станке 2
    max_b = max(j["b"] for j in jobs)
    # Минимальное время на станке 3
    min_c = min(j["c"] for j in jobs)

    # Проверяем условие сводимости: (min_a >= max_b) ИЛИ (min_c >= max_b)
    # Если ни одно из условий не истинно, алгоритм Джонсона неприменим
    if not (min_a >= max_b or min_c >= max_b):
        return None  # возвращаем None, чтобы программа могла обработать этот случай

    # Строим новую таблицу для двух станков: d = a+b, e = b+c
    # Каждый элемент - словарь с id, d, e
    new_jobs = [{"id": j["id"], "d": j["a"]+j["b"], "e": j["b"]+j["c"]} for j in jobs]

    # Далее идёт стандартный алгоритм Джонсона для двух станков (как в задании 1)
    remaining = new_jobs.copy()   # копируем, чтобы не испортить исходный список
    front, back = [], []          # front - детали в начало, back - в конец (в обратном порядке)

    # Пока остались нераспределённые детали
    while remaining:
        # Минимальное значение d среди оставшихся
        min_d = min(r["d"] for r in remaining)
        # Минимальное значение e среди оставшихся
        min_e = min(r["e"] for r in remaining)

        # Если минимальное d меньше или равно минимальному e,
        # то деталь с минимальным d идёт в начало
        if min_d <= min_e:
            for r in remaining:
                if r["d"] == min_d:
                    front.append(r["id"])   # добавляем в начало
                    remaining.remove(r)     # удаляем из рассмотрения
                    break
        else:
            # Иначе деталь с минимальным e идёт в конец
            for r in remaining:
                if r["e"] == min_e:
                    back.insert(0, r["id"]) # вставляем в начало списка back (т.к. будем его разворачивать)
                    remaining.remove(r)
                    break

    # Итоговая последовательность: сначала front (в порядке добавления), затем back
    return front + back

# Расчёт расписания для трёх станков
def schedule(jobs, sequence):
    """
    По заданной последовательности деталей (sequence) вычисляет временные интервалы
    обработки на каждом из трёх станков.
    Возвращает:
        sched - список словарей, каждый содержит id детали и времена начала/конца
                на станках 1, 2, 3 (s1,f1, s2,f2, s3,f3).
        makespan - общее время выполнения (время окончания на станке 3).
    """
    # Создаём словарь для быстрого доступа к временам по id детали:
    # ключ - id, значение - кортеж (a, b, c)
    info = {j["id"]: (j["a"], j["b"], j["c"]) for j in jobs}

    sched = []          # здесь будем хранить результат
    t1 = t2 = t3 = 0    # текущие моменты освобождения станков 1, 2, 3 (начало с 0)

    # Проходим по деталям в указанной последовательности
    for jid in sequence:
        # Получаем времена обработки для текущей детали
        a, b, c = info[jid]

        # Станок 1 
        # Начинает сразу, как освободился (t1)
        s1 = t1
        f1 = t1 + a

        # Станок 2
        # Может начать только после того, как деталь закончилась на станке 1 (f1)
        # и когда станок 2 освободился (t2). Поэтому старт = max(t2, f1).
        s2 = max(t2, f1)
        f2 = s2 + b

        # Станок 3
        # Начинает после того, как деталь прошла станок 2 (f2)
        # и когда станок 3 освободился (t3).
        s3 = max(t3, f2)
        f3 = s3 + c

        # Сохраняем все времена в словарь
        sched.append({
            "id": jid,
            "s1": s1, "f1": f1,
            "s2": s2, "f2": f2,
            "s3": s3, "f3": f3
        })

        # Обновляем времена освобождения станков
        t1 = f1
        t2 = f2
        t3 = f3

    # Общее время выполнения - момент окончания последней детали на станке 3
    makespan = t3
    return sched, makespan

# Отрисовка диаграммы Ганта для трёх станков
def draw_gantt(canvas, sched, title, y_offset):
    """
    Рисует на canvas диаграмму Ганта для трёх станков.
    Параметры:
        canvas - объект tk.Canvas
        sched  - расписание, полученное из schedule()
        title  - заголовок диаграммы (строка)
        y_offset - вертикальное смещение начала диаграммы (чтобы разместить несколько графиков)
    """
    # Если расписание пустое, ничего не рисуем
    if not sched:
        return

    # Определяем makespan как максимальное время окончания на станке 3
    makespan = max(r["f3"] for r in sched)
    if makespan == 0:   # защита от деления на ноль
        makespan = 1

    # Отступы и размеры элементов
    left_margin = 100   # отступ слева для подписей станков
    right_margin = 20   # отступ справа
    row_height = 45     # высота одной строки (для одного станка)
    block_height = 28   # высота прямоугольника, изображающего обработку

    # Получаем ширину canvas (в пикселях)
    canvas_width = int(canvas.cget("width"))
    # Доступная ширина для графика (без учёта левого и правого отступов)
    plot_width = canvas_width - left_margin - right_margin
    if plot_width < 10:
        plot_width = 10

    # Масштаб: сколько пикселей соответствует одной единице времени
    scale_x = plot_width / makespan

    # Заголовок диаграммы
    # Размещаем текст по координате x = left_margin, y = y_offset + 2 (чуть выше)
    canvas.create_text(left_margin, y_offset + 2, text=title, anchor="w",
                       font=("Arial", 11, "bold"), fill="#333")

    # Y-координаты центров строк для каждого станка
    y1 = y_offset + 30               # станок 1
    y2 = y1 + row_height             # станок 2
    y3 = y2 + row_height             # станок 3

    # Подписи станков (выравнивание по правому краю от левого отступа)
    canvas.create_text(left_margin - 10, y1, text="Станок 1", anchor="e",
                       font=("Arial", 9, "bold"))
    canvas.create_text(left_margin - 10, y2, text="Станок 2", anchor="e",
                       font=("Arial", 9, "bold"))
    canvas.create_text(left_margin - 10, y3, text="Станок 3", anchor="e",
                       font=("Arial", 9, "bold"))

    # Палитра цветов для разных деталей (повторяется, если деталей больше)
    colors = ["#FFB3BA", "#BAFFC9", "#BAE1FF", "#FFFFBA", "#E8BAFF", "#FFD1BA",
              "#B3E6CC", "#FFB3D9", "#B3B3FF", "#FFCC99", "#99FFCC", "#FF9999"]

    # Построение временной сетки 
    # Подбираем шаг так, чтобы меток было не слишком много (не более 15)
    step = 5
    while makespan / step > 15:
        step *= 2
    if step < 1:
        step = 1

    # Проходим от 0 до makespan с выбранным шагом
    for t in range(0, makespan + 1, step):
        x = left_margin + t * scale_x   # координата x на canvas
        if x > left_margin + plot_width:
            break
        # Рисуем вертикальную пунктирную линию на всю высоту диаграммы
        canvas.create_line(x, y1 - row_height//2, x, y3 + row_height//2,
                           fill="#e0e0e0", dash=(2,2))
        # Подписываем значение времени под станцией 3
        canvas.create_text(x, y3 + row_height//2 + 15, text=str(t),
                           anchor="n", font=("Arial", 8), fill="#555")

    # Рисуем прямоугольники для каждой детали на каждом станке
    for i, item in enumerate(sched):
        jid = item["id"]                # номер детали
        color = colors[i % len(colors)] # выбираем цвет

        # Станок 1
        x1 = left_margin + item["s1"] * scale_x
        x2 = left_margin + item["f1"] * scale_x
        y0 = y1 - block_height//2
        y1_line = y1 + block_height//2
        canvas.create_rectangle(x1, y0, x2, y1_line, fill=color, outline="black", width=1)
        # Если блок достаточно широк, пишем внутри номер детали
        if x2 - x1 > 20:
            canvas.create_text((x1+x2)/2, (y0+y1_line)/2, text=str(jid),
                               font=("Arial", 9, "bold"), fill="#000")

        # Станок 2
        x1 = left_margin + item["s2"] * scale_x
        x2 = left_margin + item["f2"] * scale_x
        y0 = y2 - block_height//2
        y1_line = y2 + block_height//2
        canvas.create_rectangle(x1, y0, x2, y1_line, fill=color, outline="black", width=1)
        if x2 - x1 > 20:
            canvas.create_text((x1+x2)/2, (y0+y1_line)/2, text=str(jid),
                               font=("Arial", 9, "bold"), fill="#000")

        # Станок 3
        x1 = left_margin + item["s3"] * scale_x
        x2 = left_margin + item["f3"] * scale_x
        y0 = y3 - block_height//2
        y1_line = y3 + block_height//2
        canvas.create_rectangle(x1, y0, x2, y1_line, fill=color, outline="black", width=1)
        if x2 - x1 > 20:
            canvas.create_text((x1+x2)/2, (y0+y1_line)/2, text=str(jid),
                               font=("Arial", 9, "bold"), fill="#000")

    # Подпись общего времени выполнения (makespan)
    # Размещается по центру под осью времени (под станцией 3)
    canvas.create_text(left_margin + plot_width//2, y3 + row_height//2 + 45,
                       text=f"Общее время: {makespan}",
                       font=("Arial", 10, "bold"), fill="#006600")

# Основная программа 
# Загружаем данные из файла "jobs.csv" 
jobs = load_jobs("jobs.csv")

# Исходная последовательность — просто порядок номеров 1..n
orig_seq = [j["id"] for j in jobs]

# Оптимальная последовательность по алгоритму Джонсона (может быть None)
opt_seq = johnson_sequence(jobs)

# Рассчитываем расписание для исходного порядка
sched_orig, ms_orig = schedule(jobs, orig_seq)

# Переменные для оптимального расписания (изначально None)
sched_opt = None
ms_opt = None

# Если алгоритм Джонсона вернул последовательность (не None), считаем расписание
if opt_seq:
    sched_opt, ms_opt = schedule(jobs, opt_seq)

# Создаём главное окно
root = tk.Tk()
root.title("Алгоритм Джонсона (3 станка)")

# Таблица с исходными данными
frame = ttk.Frame(root)
frame.pack(fill="x", padx=10, pady=5)

lbl = ttk.Label(frame, text="Исходные данные (время на станках):", font=("Arial", 12, "bold"))
lbl.pack(anchor="w", pady=5)

# Создаём таблицу с тремя колонками: a, b, c
tree = ttk.Treeview(frame, columns=("a","b","c"), show="headings", height=len(jobs))
tree.heading("a", text="Станок 1 (a)")
tree.heading("b", text="Станок 2 (b)")
tree.heading("c", text="Станок 3 (c)")

# Заполняем таблицу данными из списка jobs
for j in jobs:
    tree.insert("", "end", values=(j["a"], j["b"], j["c"]))
tree.pack(fill="x")

# Контейнер с вертикальной прокруткой для Canvas 
canvas_container = ttk.Frame(root)
canvas_container.pack(fill="both", expand=True, padx=10, pady=10)

# Полоса прокрутки (вертикальная)
v_scrollbar = ttk.Scrollbar(canvas_container, orient="vertical")
v_scrollbar.pack(side="right", fill="y")

# Холст для рисования диаграмм
canvas = tk.Canvas(canvas_container, width=1000, height=600, bg="white",
                   yscrollcommand=v_scrollbar.set)
canvas.pack(side="left", fill="both", expand=True)

# Привязываем полосу прокрутки к canvas
v_scrollbar.config(command=canvas.yview)

# Начальная область прокрутки (будет уточнена после отрисовки)
canvas.config(scrollregion=(0, 0, 1000, 700))

# Отрисовка диаграмм 
# Исходная последовательность (смещение y=20)
seq_str_orig = "(" + ",".join(map(str, orig_seq)) + ")"
draw_gantt(canvas, sched_orig, "Исходная последовательность: " + seq_str_orig, y_offset=20)

# Если оптимальная последовательность существует, рисуем её (смещение y=280)
if sched_opt:
    seq_str_opt = "(" + ",".join(map(str, opt_seq)) + ")"
    draw_gantt(canvas, sched_opt, "Оптимальная последовательность: " + seq_str_opt, y_offset=280)
else:
    # Иначе выводим сообщение о неприменимости алгоритма
    # Текст располагается с отступом 10 
    canvas.create_text(10, 280, text="Алгоритм Джонсона неприменим для этих данных",
                       anchor="w", font=("Arial", 12, "bold"), fill="red")

# Обновляем холст, чтобы вычислить реальные размеры всех нарисованных объектов
canvas.update_idletasks()
# Устанавливаем область прокрутки равной ограничивающему прямоугольнику всего содержимого
canvas.config(scrollregion=canvas.bbox("all"))

# Запускаем главный цикл обработки событий
root.mainloop()