import tkinter as tk
from tkinter import ttk
import itertools

# Чтение данных (формат: a;b;c;...)
def load_jobs(filename):
    jobs = []
    with open(filename, encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            times = [int(x) for x in line.split(";")]
            jobs.append({"id": i+1, "times": times})
    return jobs

# Алгоритм Джонсона (только для 3 станков)
def johnson_sequence(jobs):
    if len(jobs[0]["times"]) != 3:
        return None
    min_a = min(j["times"][0] for j in jobs)
    max_b = max(j["times"][1] for j in jobs)
    min_c = min(j["times"][2] for j in jobs)
    if not (min_a >= max_b or min_c >= max_b):
        return None

    new_jobs = [{"id": j["id"], "d": j["times"][0]+j["times"][1], "e": j["times"][1]+j["times"][2]} for j in jobs]
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

# Расчёт расписания для любого числа станков
def schedule(jobs, sequence):
    num_machines = len(jobs[0]["times"])
    machine_times = [0] * num_machines
    sched = []
    for jid in sequence:
        times = next(j["times"] for j in jobs if j["id"] == jid)
        start_finish = {}
        for m in range(num_machines):
            if m == 0:
                s = machine_times[m]
            else:
                s = max(machine_times[m], start_finish[m-1][1])
            f = s + times[m]
            start_finish[m] = (s, f)
            machine_times[m] = f
        sched.append({"id": jid, "ops": start_finish})
    makespan = machine_times[-1]
    return sched, makespan

# Полный перебор
def brute_force(jobs):
    best_seq = None
    best_ms = float("inf")
    for perm in itertools.permutations([j["id"] for j in jobs]):
        _, ms = schedule(jobs, perm)
        if ms < best_ms:
            best_ms = ms
            best_seq = perm
    return list(best_seq)

# Отрисовка Ганта (ширина фиксирована 1200, автоподбор масштаба)
def draw_gantt(canvas, sched, title, y_offset, canvas_width=1200, left_margin=100, right_margin=20):
    if not sched:
        return
    num_machines = len(sched[0]["ops"])
    makespan = max(r["ops"][num_machines-1][1] for r in sched)
    if makespan == 0:
        makespan = 1

    plot_width = canvas_width - left_margin - right_margin
    if plot_width < 10:
        plot_width = 10

    scale_x = plot_width / makespan

    # Заголовок
    canvas.create_text(left_margin, y_offset + 2, text=title, anchor="w",
                       font=("Arial", 11, "bold"), fill="#333")

    row_height = 45
    block_height = 28
    y_start = y_offset + 30

    # Подписи станков
    for m in range(num_machines):
        y_m = y_start + m * row_height
        canvas.create_text(left_margin - 10, y_m, text=f"Станок {m+1}", anchor="e",
                           font=("Arial", 9, "bold"))

    colors = ["#FFB3BA", "#BAFFC9", "#BAE1FF", "#FFFFBA", "#E8BAFF", "#FFD1BA",
              "#B3E6CC", "#FFB3D9", "#B3B3FF", "#FFCC99", "#99FFCC", "#FF9999"]

    # Сетка
    step = 5
    while makespan / step > 15:
        step *= 2
    if step < 1:
        step = 1

    y_last = y_start + (num_machines - 1) * row_height
    y_bottom = y_last + row_height//2

    for t in range(0, makespan + 1, step):
        x = left_margin + t * scale_x
        if x > left_margin + plot_width:
            break
        canvas.create_line(x, y_start - row_height//2, x, y_bottom,
                           fill="#e0e0e0", dash=(2,2))
        canvas.create_text(x, y_bottom + 15, text=str(t),
                           anchor="n", font=("Arial", 8), fill="#555")

    # Прямоугольники
    for i, item in enumerate(sched):
        jid = item["id"]
        color = colors[i % len(colors)]
        for m in range(num_machines):
            s, f = item["ops"][m]
            x1 = left_margin + s * scale_x
            x2 = left_margin + f * scale_x
            y0 = y_start + m * row_height - block_height//2
            y1 = y0 + block_height
            canvas.create_rectangle(x1, y0, x2, y1, fill=color, outline="black", width=1)
            if x2 - x1 > 20:
                canvas.create_text((x1+x2)/2, (y0+y1)/2, text=str(jid),
                                   font=("Arial", 9, "bold"), fill="#000")

    # Общее время
    canvas.create_text(left_margin + plot_width//2, y_bottom + 45,
                       text=f"Общее время: {makespan}",
                       font=("Arial", 10, "bold"), fill="#006600")
    return y_bottom + 45  # возвращаем нижнюю границу

# -------------------- Основная программа --------------------
jobs = load_jobs("jobs.csv")

orig_seq = [j["id"] for j in jobs]
sched_orig, ms_orig = schedule(jobs, orig_seq)

opt_seq = johnson_sequence(jobs)
sched_opt, ms_opt = (schedule(jobs, opt_seq) if opt_seq else (None, None))

best_seq = brute_force(jobs)
sched_best, ms_best = schedule(jobs, best_seq)

root = tk.Tk()
root.title(f"Перебор + Джонсон (станков: {len(jobs[0]['times'])})")

# Таблица с данными
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

# Canvas с прокруткой
canvas_frame = tk.Frame(root)
canvas_frame.pack(fill="both", expand=True, padx=10, pady=10)

canvas = tk.Canvas(canvas_frame, width=1200, height=600, bg="white")
scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
canvas.configure(yscrollcommand=scrollbar.set)
scrollbar.pack(side="right", fill="y")
canvas.pack(side="left", fill="both", expand=True)

# Отрисовка диаграмм
num_machines = len(jobs[0]["times"])
y = 20
left_margin = 100  # для выравнивания сообщения

seq_str_orig = "(" + ",".join(map(str, orig_seq)) + ")"
bottom_orig = draw_gantt(canvas, sched_orig, "Исходная последовательность: " + seq_str_orig, y_offset=y, canvas_width=1200)
y = bottom_orig + 40

if sched_opt:
    seq_str_opt = "(" + ",".join(map(str, opt_seq)) + ")"
    bottom_opt = draw_gantt(canvas, sched_opt, "Алгоритм Джонсона: " + seq_str_opt, y_offset=y, canvas_width=1200)
    y = bottom_opt + 40
else:
    # Сообщение теперь выводится с отступом left_margin (100), а не с x=10
    canvas.create_text(left_margin, y, text="Алгоритм Джонсона неприменим для этих данных",
                       anchor="w", font=("Arial", 12, "bold"), fill="red")
    y += 75

seq_str_best = "(" + ",".join(map(str, best_seq)) + ")"
draw_gantt(canvas, sched_best, "Перебор (точное решение): " + seq_str_best, y_offset=y, canvas_width=1200)

# Устанавливаем область прокрутки
canvas.config(scrollregion=canvas.bbox("all"))

root.mainloop()