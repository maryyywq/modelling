import tkinter as tk
from tkinter import ttk

# Чтение данных из файла
def load_jobs(filename):
    """
    Загружает данные из текстового файла.
    Формат: каждая строка содержит два числа, разделённых точкой с запятой: a;b
    a - время обработки на станке 1, b - время на станке 2.
    Возвращает список словарей, каждый словарь содержит:
        'id' - номер детали (начиная с 1),
        'a' - время на станке 1,
        'b' - время на станке 2.
    """
    jobs = []  # результирующий список
    # открываем файл с указанием кодировки utf-8
    with open(filename, encoding="utf-8") as f:
        # enumerate(f) возвращает пары (индекс строки, строка), начиная с 0
        for i, line in enumerate(f):
            line = line.strip()          # удаляем пробелы и символы перевода строки в начале/конце
            if not line:                 # если строка пустая (например, пустая строка в файле)
                continue                 # пропускаем её
            # разбиваем строку по разделителю ';' и преобразуем каждую часть в целое число
            a, b = line.split(";")
            # добавляем словарь с номером детали (i+1, чтобы нумерация шла с 1) и временами
            jobs.append({"id": i+1, "a": int(a), "b": int(b)})
    return jobs

# Алгоритм Джонсона для двух станков 
def johnson_sequence(jobs):
    """
    Реализует алгоритм Джонсона для задачи упорядочения на двух станках.
    Принимает список словарей jobs (каждый с ключами 'id', 'a', 'b').
    Возвращает список номеров деталей в оптимальном порядке.
    """
    # создаём копию списка, чтобы не изменять исходный
    remaining = jobs.copy()
    # front - детали, которые будут поставлены в начало оптимальной последовательности
    # back  - детали, которые будут поставлены в конец (в обратном порядке)
    front, back = [], []

    # пока остались нераспределённые детали
    while remaining:
        # находим минимальное время на станке 1 среди оставшихся деталей
        min_a = min(r["a"] for r in remaining)
        # находим минимальное время на станке 2 среди оставшихся деталей
        min_b = min(r["b"] for r in remaining)

        # Если минимальное время на станке 1 меньше или равно минимальному на станке 2,
        # то выбираем деталь с минимальным a и ставим её в начало.
        if min_a <= min_b:
            # перебираем оставшиеся детали в поисках той, у которой a == min_a
            for r in remaining:
                if r["a"] == min_a:
                    # добавляем её номер в начало последовательности (front)
                    front.append(r["id"])
                    # удаляем выбранную деталь из списка оставшихся
                    remaining.remove(r)
                    break  # выходим из цикла, так как деталь найдена
        else:
            # Иначе минимальное время на станке 2 меньше, чем на станке 1.
            # Значит, деталь с минимальным b должна идти в конец последовательности.
            for r in remaining:
                if r["b"] == min_b:
                    # вставляем номер детали в начало списка back,
                    # потому что потом мы его развернём (back собирается в обратном порядке)
                    back.insert(0, r["id"])
                    remaining.remove(r)
                    break

    # объединяем front и back: сначала детали из front (в порядке добавления),
    # затем детали из back (уже в правильном порядке, т.к. мы вставляли в начало)
    return front + back

# Расчёт расписания по заданной последовательности 
def schedule(jobs, sequence):
    """
    По заданному порядку деталей (sequence) рассчитывает временные интервалы
    работы на каждом станке. Возвращает:
        sched - список словарей с информацией о каждой детали:
                {'id', 's1','f1','s2','f2'} (начало/конец на станке 1 и 2)
        makespan - общее время завершения всех работ (время окончания на станке 2)
    """
    # Создаём словарь для быстрого доступа к временам по id детали
    # info[id] = (a, b)
    info = {j["id"]: (j["a"], j["b"]) for j in jobs}

    sched = []          # здесь будем накапливать результат
    t1 = t2 = 0         # текущее время освобождения станка 1 и станка 2 (изначально 0)

    # Проходим по деталям в том порядке, который задан в sequence
    for jid in sequence:
        a, b = info[jid]  # получаем времена обработки для этой детали

        # Станок 1 
        # Станок 1 начинает обрабатывать деталь сразу после предыдущей,
        # т.е. в момент t1 (текущее время освобождения станка 1)
        s1 = t1
        # заканчивает через a единиц времени
        f1 = s1 + a

        # Станок 2 
        # Станок 2 может начать обработку только после того, как:
        #   1) деталь закончилась на станке 1 (f1)
        #   2) станок 2 освободился после предыдущей детали (t2)
        # Поэтому старт = max(t2, f1)
        s2 = max(t2, f1)
        # заканчивает через b единиц времени
        f2 = s2 + b

        # Сохраняем все времена для этой детали в словарь
        sched.append({
            "id": jid,
            "s1": s1, "f1": f1,
            "s2": s2, "f2": f2
        })

        # Обновляем текущие времена освобождения станков
        t1 = f1   # станок 1 теперь освободится в момент f1
        t2 = f2   # станок 2 теперь освободится в момент f2

    # Общее время выполнения всех работ = время освобождения последнего станка (станка 2)
    makespan = t2
    return sched, makespan

# Отрисовка диаграммы Ганта
def draw_gantt(canvas, sched, title, y_offset):
    """
    Рисует на canvas диаграмму Ганта для двух станков.
    Параметры:
        canvas - объект tk.Canvas, на котором рисуем
        sched  - расписание, полученное из schedule()
        title  - заголовок диаграммы (строка)
        y_offset - вертикальное смещение начала диаграммы (чтобы разместить несколько графиков)
    """
    # Если расписание пустое, ничего не рисуем
    if not sched:
        return

    # Определяем общее время выполнения (makespan) как максимум из времён окончания на станке 2
    makespan = max(r["f2"] for r in sched)
    if makespan == 0:          # защита от деления на ноль
        makespan = 1

    # Отступы и размеры элементов
    left_margin = 100    # отступ слева для названий станков
    right_margin = 20    # отступ справа
    row_height = 50      # высота строки одного станка
    block_height = 30    # высота прямоугольника, изображающего обработку

    # Получаем фактическую ширину canvas (в пикселях)
    canvas_width = int(canvas.cget("width"))
    # Доступная ширина для графика (без отступов)
    plot_width = canvas_width - left_margin - right_margin
    if plot_width < 10:
        plot_width = 10

    # Масштаб: сколько пикселей соответствует одной единице времени
    scale_x = plot_width / makespan

    # Заголовок диаграммы 
    # Текст заголовка располагается по координате x = left_margin,
    # y = y_offset + 2 (немного выше, чтобы не перекрывать график)
    canvas.create_text(left_margin, y_offset + 2, text=title, anchor="w",
                       font=("Arial", 11, "bold"), fill="#333")

    # Y-координаты центров строк для станков 
    y1 = y_offset + 30                     # центр строки станка 1
    y2 = y_offset + 30 + row_height        # центр строки станка 2

    # Подписи станков (справа от левого отступа)
    canvas.create_text(left_margin - 10, y1, text="Станок 1", anchor="e",
                       font=("Arial", 9, "bold"))
    canvas.create_text(left_margin - 10, y2, text="Станок 2", anchor="e",
                       font=("Arial", 9, "bold"))

    # Цвета для разных деталей (повторяются, если деталей больше, чем цветов)
    colors = ["#FFB3BA", "#BAFFC9", "#BAE1FF", "#FFFFBA", "#E8BAFF", "#FFD1BA",
              "#B3E6CC", "#FFB3D9", "#B3B3FF", "#FFCC99", "#99FFCC", "#FF9999"]

    # Построение временной сетки 
    # Подбираем шаг по времени так, чтобы меток было не слишком много (не более 15)
    step = 5
    while makespan / step > 15:
        step *= 2
    if step < 1:
        step = 1

    # Проходим по всем временным отметкам от 0 до makespan с шагом step
    for t in range(0, makespan + 1, step):
        x = left_margin + t * scale_x      # координата x на canvas
        if x > left_margin + plot_width:   # если вышли за правую границу – прерываем
            break
        # Рисуем вертикальную пунктирную линию на всю высоту диаграммы (от y1 до y2)
        canvas.create_line(x, y1 - row_height//2, x, y2 + row_height//2,
                           fill="#e0e0e0", dash=(2,2))
        # Подписываем значение времени под станцией 2
        canvas.create_text(x, y2 + row_height//2 + 15, text=str(t),
                           anchor="n", font=("Arial", 8), fill="#555")

    # Рисуем прямоугольники (блоки обработки) для каждой детали 
    for i, item in enumerate(sched):
        jid = item["id"]                # номер детали
        color = colors[i % len(colors)] # выбираем цвет по индексу

        # Станок 1 
        x1 = left_margin + item["s1"] * scale_x   # начало
        x2 = left_margin + item["f1"] * scale_x   # конец
        y0 = y1 - block_height//2                  # верхняя граница прямоугольника
        y1_line = y1 + block_height//2             # нижняя граница
        # Рисуем залитый прямоугольник с чёрной обводкой
        canvas.create_rectangle(x1, y0, x2, y1_line, fill=color,
                                outline="black", width=1)
        # Если ширина блока больше 20 пикселей, пишем внутри номер детали
        if x2 - x1 > 20:
            canvas.create_text((x1+x2)/2, (y0+y1_line)/2, text=str(jid),
                               font=("Arial", 9, "bold"), fill="#000")

        # Станок 2 
        x1 = left_margin + item["s2"] * scale_x
        x2 = left_margin + item["f2"] * scale_x
        y0 = y2 - block_height//2
        y1_line = y2 + block_height//2
        canvas.create_rectangle(x1, y0, x2, y1_line, fill=color,
                                outline="black", width=1)
        if x2 - x1 > 20:
            canvas.create_text((x1+x2)/2, (y0+y1_line)/2, text=str(jid),
                               font=("Arial", 9, "bold"), fill="#000")

    # Подпись общего времени выполнения (makespan)
    # Располагается по центру под осью времени (под станцией 2)
    canvas.create_text(left_margin + plot_width//2, y2 + row_height//2 + 45,
                       text=f"Общее время: {makespan}",
                       font=("Arial", 10, "bold"), fill="#006600")

# Основная программа
# Загружаем данные из файла "jobs.csv" 
jobs = load_jobs("jobs.csv")

# Исходная последовательность — просто порядок номеров 1..n
orig_seq = [j["id"] for j in jobs]

# Оптимальная последовательность по алгоритму Джонсона
opt_seq = johnson_sequence(jobs)

# Рассчитываем расписания для исходной и оптимальной последовательностей
sched_orig, ms_orig = schedule(jobs, orig_seq)
sched_opt, ms_opt = schedule(jobs, opt_seq)

# Создаём главное окно tkinter
root = tk.Tk()
root.title("Алгоритм Джонсона (2 станка)")

# Таблица с исходными данными
frame = ttk.Frame(root)
frame.pack(fill="x", padx=10, pady=5)
lbl = ttk.Label(frame, text="Исходные данные (время на станках):", font=("Arial", 12, "bold"))
lbl.pack(anchor="w", pady=5)

# Создаём таблицу (Treeview) с двумя колонками для времени на станках
tree = ttk.Treeview(frame, columns=("a","b"), show="headings", height=len(jobs))
tree.heading("a", text="Станок 1 (a)")
tree.heading("b", text="Станок 2 (b)")
for j in jobs:
    tree.insert("", "end", values=(j["a"], j["b"]))
tree.pack(fill="x")

# Canvas для рисования диаграмм Ганта
# Задаём размер холста 900x500 пикселей
canvas = tk.Canvas(root, width=900, height=500, bg="white")
canvas.pack(fill="both", expand=True, padx=10, pady=10)

# Формируем строки с последовательностями для заголовков
seq_str_orig = "(" + ",".join(map(str, orig_seq)) + ")"
seq_str_opt = "(" + ",".join(map(str, opt_seq)) + ")"

# Рисуем диаграмму для исходной последовательности (смещение по Y = 20)
draw_gantt(canvas, sched_orig, "Исходная последовательность: " + seq_str_orig, y_offset=20)

# Рисуем диаграмму для оптимальной последовательности (смещение 200, чтобы не пересекалась)
draw_gantt(canvas, sched_opt, "Оптимальная последовательность: " + seq_str_opt, y_offset=200)

# Запускаем главный цикл обработки событий tkinter
root.mainloop()