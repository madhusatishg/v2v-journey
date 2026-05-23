import random
import numpy as np
from collections import deque
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

agent_pos = [0, 0]

# =========================
# HYPERPARAMETERS
# =========================

gamma = 0.9
epsilon = 1.0
epsilon_decay = 0.995
epsilon_min = 0.1

learning_rate = 0.001
episodes = 300
batch_size = 32

# =========================
# REPLAY MEMORY
# =========================

memory = deque(maxlen=2000)

# =========================
# STATE PREPROCESSING
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
        optimizer=keras.optimizers.Adam(learning_rate),
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

    if grid[nr][nc] == 'G':
        return agent_pos, 100, True

    return agent_pos, -1, False

# =========================
# ACTION SELECTION (DQN POLICY)
# =========================

def choose_action(state):

    if random.random() < epsilon:
        return random.randint(0, 3)

    state_input = preprocess_state(state).reshape(1, 2)

    q_values = model.predict(state_input, verbose=0)[0]

    return np.argmax(q_values)

# =========================
# TRAINING FUNCTION
# =========================

def train():

    if len(memory) < batch_size:
        return

    batch = random.sample(memory, batch_size)

    states = []
    targets = []

    for state, action, reward, next_state, done in batch:

        state_input = preprocess_state(state)
        next_input = preprocess_state(next_state)

        target = model.predict(state_input.reshape(1, 2), verbose=0)[0]
        next_q = model.predict(next_input.reshape(1, 2), verbose=0)[0]

        if done:
            target[action] = reward
        else:
            target[action] = reward + gamma * np.max(next_q)

        states.append(state_input)
        targets.append(target)

    model.fit(np.array(states), np.array(targets), epochs=1, verbose=0)

# =========================
# TRAINING LOOP
# =========================
print("===== TRAINING START =====")

for episode in range(episodes):

    state = reset()
    done = False
    total_reward = 0

    while not done:

        action = choose_action(state)

        next_state, reward, done = step(action)

        memory.append((state, action, reward, next_state, done))

        state = next_state
        total_reward += reward

        train()

    # epsilon decay
    if epsilon > epsilon_min:
        epsilon *= epsilon_decay

    if episode % 20 == 0:
        print(f"Episode {episode}, Reward: {total_reward}, Epsilon: {epsilon:.3f}")

# =========================
# FINAL MODEL
# =========================

print("\nTRAINING COMPLETE")
print(model.summary())