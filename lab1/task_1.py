import tkinter as tk
from tkinter import ttk

# Чтение данных
def load_jobs(filename):
    # Загружает данные из файла (разделитель ;)
    # Возвращает список словарей: {'id': номер_детали, 'a': время_станок_1, 'b': время_станок_2}
    jobs = []
    with open(filename, encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            a, b = line.split(";")
            jobs.append({"id": i+1, "a": int(a), "b": int(b)})
    return jobs

# Алгоритм Джонсона для 2-х станков
def johnson_sequence(jobs):
    """
    Алгоритм Джонсона для двух станков:
    1. Выбираем минимальное время среди всех a и b
    2. Если минимальное время принадлежит a (станок 1),
       то ставим эту деталь в начало последовательности
    3. Если минимальное время принадлежит b (станок 2),
       то ставим эту деталь в конец последовательности
    4. Убираем выбранную деталь из списка и повторяем, пока не останутся все детали
    """

    remaining = jobs.copy()
    front, back = [], []
    while remaining:
        # минимальные времена для станка a и b
        min_a = min(r["a"] for r in remaining)
        min_b = min(r["b"] for r in remaining)

        if min_a <= min_b:
            # Если минимальное значение среди a:
            # деталь должна выполняться раньше -> добавляем в начало
            for r in remaining:
                if r["a"] == min_a:
                    front.append(r["id"])
                    remaining.remove(r)
                    break
        else:
            # Если минимальное значение среди b:
            # деталь должна выполняться позже -> добавляем в конец
            for r in remaining:
                if r["b"] == min_b:
                    back.insert(0, r["id"])
                    remaining.remove(r)
                    break
    return front + back

# Расчёт расписания
def schedule(jobs, sequence):
    # Превратим список jobs в словарь для быстрого доступа по id:
    # info[id] = (время на станке 1, время на станке 2)
    info = {j["id"]: (j["a"], j["b"]) for j in jobs}

    sched = [] # сюда складываем результат (по каждой детали)
    t1 = t2 = 0 # текущее время окончания работы на станке 1 и станке 2

    # Проходим детали в том порядке, который задан sequence
    for jid in sequence:
        a, b = info[jid]  # время на станке 1 и станке 2 для этой детали

        # Станок 1:
        # начинает сразу после предыдущей детали (t1),
        # заканчивает через a единиц времени
        s1 = t1
        f1 = s1 + a

        # Станок 2:
        # может начать только когда:
        #   1) закончилась эта деталь на станке 1 (f1)
        #   2) и станок 2 освободился после предыдущей детали (t2)
        # поэтому старт = max(t2, f1)
        s2 = max(t2, f1)
        f2 = s2 + b

        # Записываем результат для этой детали
        sched.append({
            "id": jid,
            "s1": s1, "f1": f1, # начало/конец на станке 1
            "s2": s2, "f2": f2  # начало/конец на станке 2
        })

        # Обновляем "текущее время" для станков
        t1 = f1 # станок 1 освободится в момент f1
        t2 = f2 # станок 2 освободится в момент f2

    # Время завершения всей работы = момент окончания последней детали на станке 2
    makespan = t2
    return sched, makespan

# Функция отрисовки Ганта
def draw_gantt(canvas, sched, title, y_offset):
    if not sched:
        return

    makespan = max(r["f2"] for r in sched)
    if makespan == 0:
        makespan = 1

    left_margin = 100
    right_margin = 20
    row_height = 50
    block_height = 30

    canvas_width = int(canvas.cget("width"))
    plot_width = canvas_width - left_margin - right_margin
    if plot_width < 10:
        plot_width = 10

    scale_x = plot_width / makespan

    # Заголовок (поднят выше)
    canvas.create_text(left_margin, y_offset + 2, text=title, anchor="w",
                       font=("Arial", 11, "bold"), fill="#333")

    y1 = y_offset + 30          # центр строки станка 1
    y2 = y_offset + 30 + row_height  # центр строки станка 2

    canvas.create_text(left_margin - 10, y1, text="Станок 1", anchor="e",
                       font=("Arial", 9, "bold"))
    canvas.create_text(left_margin - 10, y2, text="Станок 2", anchor="e",
                       font=("Arial", 9, "bold"))

    colors = ["#FFB3BA", "#BAFFC9", "#BAE1FF", "#FFFFBA", "#E8BAFF", "#FFD1BA",
              "#B3E6CC", "#FFB3D9", "#B3B3FF", "#FFCC99", "#99FFCC", "#FF9999"]

    # Сетка по времени
    step = 5
    while makespan / step > 15:
        step *= 2
    if step < 1:
        step = 1

    for t in range(0, makespan + 1, step):
        x = left_margin + t * scale_x
        if x > left_margin + plot_width:
            break
        canvas.create_line(x, y1 - row_height//2, x, y2 + row_height//2,
                           fill="#e0e0e0", dash=(2,2))
        canvas.create_text(x, y2 + row_height//2 + 15, text=str(t),
                           anchor="n", font=("Arial", 8), fill="#555")

    # Рисуем блоки
    for i, item in enumerate(sched):
        jid = item["id"]
        color = colors[i % len(colors)]

        # Станок 1
        x1 = left_margin + item["s1"] * scale_x
        x2 = left_margin + item["f1"] * scale_x
        y0 = y1 - block_height//2
        y1_line = y1 + block_height//2
        canvas.create_rectangle(x1, y0, x2, y1_line, fill=color,
                                outline="black", width=1)
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

    # Подпись "Общее время" – теперь чуть ниже (отступ +45 вместо +35)
    canvas.create_text(left_margin + plot_width//2, y2 + row_height//2 + 45,
                       text=f"Общее время: {makespan}",
                       font=("Arial", 10, "bold"), fill="#006600")

# ----------------------------------------------------------------------
# Основная программа
# ----------------------------------------------------------------------
jobs = load_jobs("jobs.csv")

orig_seq = [j["id"] for j in jobs]
opt_seq = johnson_sequence(jobs)

sched_orig, ms_orig = schedule(jobs, orig_seq)
sched_opt, ms_opt = schedule(jobs, opt_seq)

root = tk.Tk()
root.title("Алгоритм Джонсона (2 станка)")

# Таблица с исходными данными
frame = ttk.Frame(root)
frame.pack(fill="x", padx=10, pady=5)
lbl = ttk.Label(frame, text="Исходные данные (время на станках):", font=("Arial", 12, "bold"))
lbl.pack(anchor="w", pady=5)

tree = ttk.Treeview(frame, columns=("a","b"), show="headings", height=len(jobs))
tree.heading("a", text="Станок 1 (a)")
tree.heading("b", text="Станок 2 (b)")
for j in jobs:
    tree.insert("", "end", values=(j["a"], j["b"]))
tree.pack(fill="x")

# Canvas для графиков
canvas = tk.Canvas(root, width=900, height=500, bg="white")
canvas.pack(fill="both", expand=True, padx=10, pady=10)

seq_str_orig = "(" + ",".join(map(str, orig_seq)) + ")"
seq_str_opt = "(" + ",".join(map(str, opt_seq)) + ")"
draw_gantt(canvas, sched_orig, "Исходная последовательность: " + seq_str_orig, y_offset=20)
draw_gantt(canvas, sched_opt, "Оптимальная последовательность: " + seq_str_opt, y_offset=200)

root.mainloop()