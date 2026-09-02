import tkinter as tk
from tkinter import ttk

# Чтение данных (формат a;b;c)
def load_jobs(filename):
    jobs = []
    with open(filename, encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            a, b, c = line.split(";")
            jobs.append({"id": i+1, "a": int(a), "b": int(b), "c": int(c)})
    return jobs

# Алгоритм Джонсона для 3-х станков
def johnson_sequence(jobs):
    min_a = min(j["a"] for j in jobs)
    max_b = max(j["b"] for j in jobs)
    min_c = min(j["c"] for j in jobs)
    if not (min_a >= max_b or min_c >= max_b):
        return None

    new_jobs = [{"id": j["id"], "d": j["a"]+j["b"], "e": j["b"]+j["c"]} for j in jobs]
    remaining = new_jobs.copy()
    front, back = [], []
    while remaining:
        min_d = min(r["d"] for r in remaining)
        min_e = min(r["e"] for r in remaining)
        if min_d <= min_e:
            for r in remaining:
                if r["d"] == min_d:
                    front.append(r["id"])
                    remaining.remove(r)
                    break
        else:
            for r in remaining:
                if r["e"] == min_e:
                    back.insert(0, r["id"])
                    remaining.remove(r)
                    break
    return front + back

# Расчёт расписания на 3 станках
def schedule(jobs, sequence):
    info = {j["id"]: (j["a"], j["b"], j["c"]) for j in jobs}
    sched = []
    t1 = t2 = t3 = 0
    for jid in sequence:
        a, b, c = info[jid]
        s1, f1 = t1, t1 + a
        s2, f2 = max(t2, f1), max(t2, f1) + b
        s3, f3 = max(t3, f2), max(t3, f2) + c
        sched.append({"id": jid, "s1": s1, "f1": f1,
                                 "s2": s2, "f2": f2,
                                 "s3": s3, "f3": f3})
        t1, t2, t3 = f1, f2, f3
    return sched, t3

# Функция отрисовки Ганта для 3 станков
def draw_gantt(canvas, sched, title, y_offset):
    if not sched:
        return

    makespan = max(r["f3"] for r in sched)
    if makespan == 0:
        makespan = 1

    left_margin = 100
    right_margin = 20
    row_height = 45
    block_height = 28

    canvas_width = int(canvas.cget("width"))
    plot_width = canvas_width - left_margin - right_margin
    if plot_width < 10:
        plot_width = 10

    scale_x = plot_width / makespan

    canvas.create_text(left_margin, y_offset + 2, text=title, anchor="w",
                       font=("Arial", 11, "bold"), fill="#333")

    y1 = y_offset + 30
    y2 = y1 + row_height
    y3 = y2 + row_height

    canvas.create_text(left_margin - 10, y1, text="Станок 1", anchor="e",
                       font=("Arial", 9, "bold"))
    canvas.create_text(left_margin - 10, y2, text="Станок 2", anchor="e",
                       font=("Arial", 9, "bold"))
    canvas.create_text(left_margin - 10, y3, text="Станок 3", anchor="e",
                       font=("Arial", 9, "bold"))

    colors = ["#FFB3BA", "#BAFFC9", "#BAE1FF", "#FFFFBA", "#E8BAFF", "#FFD1BA",
              "#B3E6CC", "#FFB3D9", "#B3B3FF", "#FFCC99", "#99FFCC", "#FF9999"]

    step = 5
    while makespan / step > 15:
        step *= 2
    if step < 1:
        step = 1

    for t in range(0, makespan + 1, step):
        x = left_margin + t * scale_x
        if x > left_margin + plot_width:
            break
        canvas.create_line(x, y1 - row_height//2, x, y3 + row_height//2,
                           fill="#e0e0e0", dash=(2,2))
        canvas.create_text(x, y3 + row_height//2 + 15, text=str(t),
                           anchor="n", font=("Arial", 8), fill="#555")

    for i, item in enumerate(sched):
        jid = item["id"]
        color = colors[i % len(colors)]

        # Станок 1
        x1 = left_margin + item["s1"] * scale_x
        x2 = left_margin + item["f1"] * scale_x
        y0 = y1 - block_height//2
        y1_line = y1 + block_height//2
        canvas.create_rectangle(x1, y0, x2, y1_line, fill=color, outline="black", width=1)
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

    canvas.create_text(left_margin + plot_width//2, y3 + row_height//2 + 45,
                       text=f"Общее время: {makespan}",
                       font=("Arial", 10, "bold"), fill="#006600")

# -------------------- Основная программа --------------------
jobs = load_jobs("jobs.csv")

orig_seq = [j["id"] for j in jobs]
opt_seq = johnson_sequence(jobs)

sched_orig, ms_orig = schedule(jobs, orig_seq)
sched_opt = None
ms_opt = None
if opt_seq:
    sched_opt, ms_opt = schedule(jobs, opt_seq)

root = tk.Tk()
root.title("Алгоритм Джонсона (3 станка)")

# Таблица с данными
frame = ttk.Frame(root)
frame.pack(fill="x", padx=10, pady=5)
lbl = ttk.Label(frame, text="Исходные данные (время на станках):", font=("Arial", 12, "bold"))
lbl.pack(anchor="w", pady=5)

tree = ttk.Treeview(frame, columns=("a","b","c"), show="headings", height=len(jobs))
tree.heading("a", text="Станок 1 (a)")
tree.heading("b", text="Станок 2 (b)")
tree.heading("c", text="Станок 3 (c)")
for j in jobs:
    tree.insert("", "end", values=(j["a"], j["b"], j["c"]))
tree.pack(fill="x")

# Создаём контейнер с прокруткой для Canvas
canvas_container = ttk.Frame(root)
canvas_container.pack(fill="both", expand=True, padx=10, pady=10)

# Scrollbar
v_scrollbar = ttk.Scrollbar(canvas_container, orient="vertical")
v_scrollbar.pack(side="right", fill="y")

# Canvas
canvas = tk.Canvas(canvas_container, width=1000, height=600, bg="white",
                   yscrollcommand=v_scrollbar.set)
canvas.pack(side="left", fill="both", expand=True)

v_scrollbar.config(command=canvas.yview)

# Определяем общую высоту, необходимую для размещения двух диаграмм
# Первая диаграмма: y_offset=20, высота примерно 170 (3 станка * 45 + отступы) -> до ~190
# Вторая диаграмма: y_offset=280, высота тоже ~170 -> до ~450
# Добавим запас 100 пикселей сверху и снизу -> общая высота ~600, но чтобы точно хватило, установим 800.
canvas.config(scrollregion=(0, 0, 1000, 700))

# Отрисовка исходной последовательности
seq_str_orig = "(" + ",".join(map(str, orig_seq)) + ")"
draw_gantt(canvas, sched_orig, "Исходная последовательность: " + seq_str_orig, y_offset=20)

# Отрисовка оптимальной (если применимо)
if sched_opt:
    seq_str_opt = "(" + ",".join(map(str, opt_seq)) + ")"
    draw_gantt(canvas, sched_opt, "Оптимальная последовательность: " + seq_str_opt, y_offset=280)
else:
    canvas.create_text(10, 280, text="Алгоритм Джонсона неприменим для этих данных",
                       anchor="w", font=("Arial", 12, "bold"), fill="red")

# Обновляем scrollregion после отрисовки, чтобы охватить всё содержимое
canvas.update_idletasks()
canvas.config(scrollregion=canvas.bbox("all"))

root.mainloop()