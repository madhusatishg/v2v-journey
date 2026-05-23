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

agent_pos = [0, 0]

# =========================
# HYPERPARAMETERS
# =========================

epsilon = 0.2

# =========================
# PREPROCESS STATE
# =========================

def preprocess_state(state):
    r, c = state
    return np.array([r / 3.0, c / 3.0], dtype=np.float32)

# =========================
# NEURAL NETWORK (DQN BRAIN)
# =========================

def build_model():

    model = keras.Sequential([
        layers.Input(shape=(2,)),
        layers.Dense(24, activation='relu'),
        layers.Dense(24, activation='relu'),
        layers.Dense(4, activation='linear')  # 4 actions
    ])

    model.compile(
        optimizer=keras.optimizers.Adam(0.001),
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

    # boundary check
    if nr < 0 or nr >= len(grid) or nc < 0 or nc >= len(grid[0]):
        return agent_pos, -5, False

    # obstacle check
    if grid[nr][nc] == 'X':
        return agent_pos, -5, False

    # move
    agent_pos = [nr, nc]

    # goal
    if grid[nr][nc] == 'G':
        return agent_pos, 100, True

    return agent_pos, -1, False

# =========================
# STEP 3: ACTION SELECTION (DQN ONLY)
# =========================

def choose_action(state):

    # exploration
    if random.random() < epsilon:
        return random.randint(0, 3)

    # exploitation using neural network
    state_input = preprocess_state(state).reshape(1, 2)

    q_values = model.predict(state_input, verbose=0)[0]

    return int(np.argmax(q_values))

# =========================
# TEST RUN (NO TRAINING YET)
# =========================

state = reset()
done = False
steps = 0

print("===== STEP 3 TEST RUN =====")

while not done and steps < 20:

    action = choose_action(state)

    next_state, reward, done = step(action)

    print("State:", state,
          "Action:", action,
          "Reward:", reward,
          "Next:", next_state)

    state = next_state
    steps += 1

print("Episode finished")