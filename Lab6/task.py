import numpy as np
import matplotlib.pyplot as plt
from numpy.linalg import solve
import json

# Загрузка параметров из файла
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

N_STATES = config["N_STATES"]
STATE_NAMES = config["STATE_NAMES"]
P0 = np.array(config["P0"]) # начальное условие
T = config["T"] # конечное время
h = config["h"] # шаг интегрирования
isolated = config["isolated_state"] - 1  # индекс изолированного состояния (перевод в 0-индексацию)

def add_transition(matrix, i, j, rate):
    matrix[j, i] += rate # вне диагонали: интенсивность перехода из i в j
    matrix[i, i] -= rate # на диагонали: минус сумма исходящих интенсивностей


# Исходная эргодичная система
Lambda = np.zeros((N_STATES, N_STATES), dtype=float) # создаём нулевую матрицу

# Заполняем матрицу всеми переходами из JSON
for u, v, rate in config["transitions"]:
    add_transition(Lambda, u - 1, v - 1, rate) # вычитаем 1, так как в JSON индексация с 1

print("Матрица Lambda исходной системы:")
print(Lambda)
print("Суммы столбцов Lambda:", Lambda.sum(axis=0)) # проверка: суммы столбцов должны быть 0

# Предельные вероятности исходной системы
M = Lambda.copy() # копируем матрицу для решения СЛАУ
b = np.zeros(N_STATES) # вектор правой части (нули)
M[-1, :] = 1.0 # заменяем последнюю строку условием нормировки
b[-1] = 1.0 # правая часть для нормировки = 1
P_lim = solve(M, b) # решаем систему
print("\nПредельные вероятности исходной системы P_lim:")
for name, value in zip(STATE_NAMES, P_lim): # выводим вероятности по состояниям
    print(f"{name}: {value:.8f}")
print(f"Сумма вероятностей: {P_lim.sum():.8f}")

# Решение задачи Коши методом Эйлера
N = int(round(T / h)) # количество шагов
times = np.linspace(0.0, T, N + 1) # массив моментов времени (равномерное распределение)
I = np.eye(N_STATES) # единичная матрица
A = I + h * Lambda # матрица перехода для метода Эйлера

traj = np.zeros((N + 1, N_STATES)) # массив для хранения траектории 
traj[0] = P0 # начальное значение
P = P0.copy() # текущий вектор вероятностей
for k in range(N): # цикл по шагам времени
    P = A @ P # формула Эйлера
    traj[k + 1] = P # сохраняем результат

print("\nЗначения P(t) для исходной системы:")
for t_value in [0.0, 0.1, 0.5, 1.0, 2.0]: # выводим значения в выбранные моменты
    index = int(round(t_value / h)) # индекс в массиве traj
    values = ", ".join(f"{x:.6f}" for x in traj[index])
    print(f"t = {t_value:.1f}: [{values}]")

plt.figure(figsize=(10, 6)) # создаём график
for i, name in enumerate(STATE_NAMES): # рисуем кривые для каждого состояния
    plt.plot(times, traj[:, i], label=f"p{i + 1}(t)")
plt.xlabel("t") # подпись оси X
plt.ylabel("Вероятность") # подпись оси Y
plt.title("Переходный режим исходной эргодичной системы") # заголовок
plt.grid(True, alpha=0.35) # включаем сетку
plt.legend() # показываем легенду
plt.tight_layout()
plt.show() # отображаем график

# Неэргодичная система: изолируем состояние
Lambda_mod = Lambda.copy() # копируем исходную матрицу
Lambda_mod[isolated, :] = 0.0 # обнуляем строку (входящие переходы)
Lambda_mod[:, isolated] = 0.0 # обнуляем столбец (исходящие переходы)

# Пересчёт диагоналей для оставшихся состояний
for j in range(N_STATES): # проходим по всем состояниям
    off_diagonal_sum = sum( # сумма вне-диагональных элементов в столбце j
        Lambda_mod[i, j] for i in range(N_STATES) if i != j
    )
    Lambda_mod[j, j] = -off_diagonal_sum # диагональ = минус сумма исходящих

print(f"\nМатрица Lambda_mod после удаления всех переходов, связанных с {STATE_NAMES[isolated]}:")
print(Lambda_mod) # выводим модифицированную матрицу
print("Суммы столбцов Lambda_mod:", Lambda_mod.sum(axis=0))

# Предельное распределение для активных состояний
active_states = [i for i in range(N_STATES) if i != isolated] # индексы активных состояний
Q = Lambda_mod[np.ix_(active_states, active_states)] # подматрица для активных состояний
M_class = Q.copy() # копия для решения СЛАУ
b_class = np.zeros(len(active_states)) # правая часть (нули)
M_class[-1, :] = 1.0 # заменяем последнюю строку условием нормировки
b_class[-1] = 1.0 # правая часть = 1
q_class = solve(M_class, b_class) # решаем систему для активных состояний

P_lim_mod = np.zeros(N_STATES) # вектор предельных вероятностей
P_lim_mod[active_states] = (1.0 - P0[isolated]) * q_class # заполняем активные состояния
P_lim_mod[isolated] = P0[isolated] # вероятность изолированного состояния остаётся начальной

print(f"\nПредельные вероятности модифицированной системы:")
for name, value in zip(STATE_NAMES, P_lim_mod): # выводим вероятности
    print(f"{name}: {value:.8f}")
print(f"Сумма вероятностей: {P_lim_mod.sum():.8f}") # проверка суммы

# Переходный процесс модифицированной системы
A_mod = I + h * Lambda_mod # матрица перехода для модифицированной системы
traj_mod = np.zeros((N + 1, N_STATES)) # массив для траектории
traj_mod[0] = P0 # начальное условие
P = P0.copy() # текущий вектор
for k in range(N): # цикл по шагам
    P = A_mod @ P # формула Эйлера
    traj_mod[k + 1] = P

print("\nЗначения P(t) для модифицированной системы:")
for t_value in [0.0, 0.1, 0.5, 1.0, 2.0]: # выводим значения в моменты времени
    index = int(round(t_value / h)) # индекс
    values = ", ".join(f"{x:.6f}" for x in traj_mod[index])
    print(f"t = {t_value:.1f}: [{values}]") 

plt.figure(figsize=(10, 6))
for i, name in enumerate(STATE_NAMES):
    plt.plot(times, traj_mod[:, i], label=f"p{i + 1}(t)")
plt.xlabel("t")
plt.ylabel("Вероятность")
plt.title(f"Переходный режим неэргодичной системы ({STATE_NAMES[isolated]} изолировано)")
plt.grid(True, alpha=0.35)
plt.legend()
plt.tight_layout()
plt.show()