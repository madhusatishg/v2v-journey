import random
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

# =========================
# GRID WORLD
# =========================

grid = [
    ['S', '.', '.', '.'],
    ['.', 'X', '.', '.'],
    ['.', 'X', '.', '.'],
    ['.', '.', '.', 'G']
]

actions = [0, 1, 2, 3]  # UP, DOWN, LEFT, RIGHT

# =========================
# STATE
# =========================

agent_pos = [0, 0]

# =========================
# HYPERPARAMETERS
# =========================

alpha = 0.1
gamma = 0.9
epsilon = 0.2
episodes = 200

# =========================
# Q-TABLE (still kept for now)
# =========================

Q_table = {}

for r in range(len(grid)):
    for c in range(len(grid[0])):
        if grid[r][c] != 'X':
            Q_table[(r, c)] = [0, 0, 0, 0]

# =========================
# PREPROCESS STATE (FOR DQN)
# =========================

def preprocess_state(state):
    r, c = state
    return np.array([r / 3.0, c / 3.0], dtype=np.float32)

# =========================
# DQN MODEL
# =========================

def build_model():

    model = keras.Sequential([
        layers.Input(shape=(2,)),
        layers.Dense(24, activation='relu'),
        layers.Dense(24, activation='relu'),
        layers.Dense(4, activation='linear')
    ])

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001),
        loss='mse'
    )

    return model


model = build_model()

# =========================
# RESET
# =========================

def reset():
    global agent_pos
    agent_pos = [0, 0]
    return agent_pos

# =========================
# STEP FUNCTION
# =========================

def step(action):

    global agent_pos

    r, c = agent_pos

    if action == 0:
        nr, nc = r - 1, c
    elif action == 1:
        nr, nc = r + 1, c
    elif action == 2:
        nr, nc = r, c - 1
    else:
        nr, nc = r, c + 1

    # boundary
    if nr < 0 or nr >= len(grid) or nc < 0 or nc >= len(grid[0]):
        return agent_pos, -5, False

    # obstacle
    if grid[nr][nc] == 'X':
        return agent_pos, -5, False

    agent_pos = [nr, nc]

    # goal
    if grid[nr][nc] == 'G':
        return agent_pos, 100, True

    return agent_pos, -1, False

# =========================
# EPSILON GREEDY (Q-learning version for now)
# =========================

def choose_action(state):

    if random.random() < epsilon:
        return random.randint(0, 3)

    return Q_table[tuple(state)].index(max(Q_table[tuple(state)]))

# =========================
# TRAINING LOOP (still Q-learning style)
# =========================

for episode in range(episodes):

    state = reset()
    done = False
    total_reward = 0

    while not done:

        state_tuple = tuple(state)

        action = choose_action(state)

        next_state, reward, done = step(action)
        next_tuple = tuple(next_state)

        # Q-learning update (still active)
        if next_tuple in Q_table:

            old_q = Q_table[state_tuple][action]
            max_future_q = max(Q_table[next_tuple])

            Q_table[state_tuple][action] = old_q + alpha * (
                reward + gamma * max_future_q - old_q
            )

        state = next_state
        total_reward += reward

    if episode % 20 == 0:
        print(f"Episode {episode}, Reward: {total_reward}")

# =========================
# MODEL READY (DQN NEXT STEP)
# =========================

print("\nDQN MODEL READY")
print(model.summary())