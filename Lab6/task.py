import numpy as np
import matplotlib.pyplot as plt
from numpy.linalg import solve
import json

# Загрузка параметров из файла
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

N_STATES = config["N_STATES"]
STATE_NAMES = config["STATE_NAMES"]
lambdas = config["lambdas"]

# Извлечение интенсивностей
lambda_12 = lambdas["lambda_12"]
lambda_14 = lambdas["lambda_14"]
lambda_15 = lambdas["lambda_15"]
lambda_21 = lambdas["lambda_21"]
lambda_23 = lambdas["lambda_23"]
lambda_24 = lambdas["lambda_24"]
lambda_25 = lambdas["lambda_25"]
lambda_31 = lambdas["lambda_31"]
lambda_32 = lambdas["lambda_32"]
lambda_34 = lambdas["lambda_34"]
lambda_35 = lambdas["lambda_35"]
lambda_43 = lambdas["lambda_43"]
lambda_53 = lambdas["lambda_53"]
lambda_54 = lambdas["lambda_54"]

def add_transition(matrix, i, j, rate):
    matrix[j, i] += rate # вне диагонали: интенсивность перехода из i в j
    matrix[i, i] -= rate # на диагонали: минус сумма исходящих интенсивностей


# Исходная эргодичная система
Lambda = np.zeros((N_STATES, N_STATES), dtype=float) # создаём нулевую матрицу 5x5

# список всех переходов
transitions = [
    (0, 1, lambda_12),  # S1 -> S2
    (0, 3, lambda_14),  # S1 -> S4
    (0, 4, lambda_15),  # S1 -> S5
    (1, 0, lambda_21),  # S2 -> S1
    (1, 2, lambda_23),  # S2 -> S3
    (1, 3, lambda_24),  # S2 -> S4
    (1, 4, lambda_25),  # S2 -> S5
    (2, 0, lambda_31),  # S3 -> S1
    (2, 1, lambda_32),  # S3 -> S2
    (2, 3, lambda_34),  # S3 -> S4
    (2, 4, lambda_35),  # S3 -> S5
    (3, 2, lambda_43),  # S4 -> S3
    (4, 2, lambda_53),  # S5 -> S3
    (4, 3, lambda_54),  # S5 -> S4
]

for i, j, rate in transitions: # заполняем матрицу Lambda всеми переходами
    add_transition(Lambda, i, j, rate)

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
P0 = np.array(config["P0"]) # начальное условие: старт из S1
T = config["T"] # конечное время
h = config["h"] # шаг интегрирования
N = int(round(T / h)) # количество шагов
times = np.linspace(0.0, T, N + 1) # массив моментов времени (равномерное распределение)
I = np.eye(N_STATES) # единичная матрица 5x5
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

# Неэргодичная система: изолируем S4
# Удаляются ВСЕ стрелки, входящие в S4 или исходящие из S4:
# S1->S4, S2->S4, S3->S4, S4->S3, S5->S4.
isolated = config["isolated"]  # индекс S4
Lambda_mod = Lambda.copy() # копируем исходную матрицу
Lambda_mod[isolated, :] = 0.0 # обнуляем строку S4 (входящие переходы)
Lambda_mod[:, isolated] = 0.0 # обнуляем столбец S4 (исходящие переходы)

# Пересчёт диагоналей для оставшихся состояний
for j in range(N_STATES): # проходим по всем состояниям
    off_diagonal_sum = sum( # сумма вне-диагональных элементов в столбце j
        Lambda_mod[i, j] for i in range(N_STATES) if i != j
    )
    Lambda_mod[j, j] = -off_diagonal_sum # диагональ = минус сумма исходящих

print("\nМатрица Lambda_mod после удаления всех переходов, связанных с S4:")
print(Lambda_mod) # выводим модифицированную матрицу
print("Суммы столбцов Lambda_mod:", Lambda_mod.sum(axis=0))

# Предельное распределение для класса {S1,S2,S3,S5}
active_states = [i for i in range(N_STATES) if i != isolated] # индексы активных состояний (без S4)
Q = Lambda_mod[np.ix_(active_states, active_states)] # подматрица для активных состояний
M_class = Q.copy() # копия для решения СЛАУ
b_class = np.zeros(len(active_states)) # правая часть (нули)
M_class[-1, :] = 1.0 # заменяем последнюю строку условием нормировки
b_class[-1] = 1.0 # правая часть = 1
q_class = solve(M_class, b_class) # решаем систему для активных состояний

P_lim_mod = np.zeros(N_STATES) # вектор предельных вероятностей
P_lim_mod[active_states] = (1.0 - P0[isolated]) * q_class # заполняем активные состояния
P_lim_mod[isolated] = P0[isolated] # вероятность S4 остаётся начальной

print("\nПредельные вероятности модифицированной системы при старте из S1:")
for name, value in zip(STATE_NAMES, P_lim_mod): # выводим вероятности
    print(f"{name}: {value:.8f}")
print(f"Сумма вероятностей: {P_lim_mod.sum():.8f}") # проверка суммы

# Переходный процесс модифицированной системы
A_mod = I + h * Lambda_mod # матрица перехода для модифицированной системы
traj_mod = np.zeros((N + 1, N_STATES)) # массив для траектории
traj_mod[0] = P0 # начальное условие (старт из S1)
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
plt.title("Переходный режим неэргодичной системы (S4 изолировано)")
plt.grid(True, alpha=0.35)
plt.legend()
plt.tight_layout()
plt.show()