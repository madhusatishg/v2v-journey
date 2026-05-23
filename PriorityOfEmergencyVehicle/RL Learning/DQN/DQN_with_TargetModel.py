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
epsilon_decay = 0.97
epsilon_min = 0.1

episodes = 200
max_steps = 2000
batch_size = 64

# 🔥 target network sync frequency
target_update_freq = 5  # episodes

memory = deque(maxlen=5000)

# =========================
# STATE
# =========================

def preprocess_state(state):
    r, c = state
    return np.array([r/3.0, c/3.0], dtype=np.float32)

# =========================
# MODEL
# =========================

def build_model():
    model = keras.Sequential([
        layers.Input(shape=(2,)),
        layers.Dense(32, activation='relu'),
        layers.Dense(32, activation='relu'),
        layers.Dense(4, activation='linear')
    ])
    model.compile(optimizer=keras.optimizers.Adam(0.001), loss='mse')
    return model

# 🔵 ONLINE NETWORK
model = build_model()

# 🔵 TARGET NETWORK (frozen copy)
target_model = build_model()
target_model.set_weights(model.get_weights())

# =========================
# ENV
# =========================

def reset():
    global agent_pos
    agent_pos = [0, 0]
    return agent_pos


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

    if nr < 0 or nr >= 4 or nc < 0 or nc >= 4:
        return agent_pos, -5, False

    if grid[nr][nc] == 'X':
        return agent_pos, -5, False

    agent_pos = [nr, nc]

    if grid[nr][nc] == 'G':
        return agent_pos, 100, True

    return agent_pos, -1, False

# =========================
# ACTION
# =========================

def choose_action(state):
    global epsilon

    if random.random() < epsilon:
        return random.randint(0, 3)

    q_values = model.predict(np.array([preprocess_state(state)]), verbose=0)[0]
    return np.argmax(q_values)

# =========================
# TRAINING
# =========================

def train():

    if len(memory) < batch_size:
        return

    batch = random.sample(memory, batch_size)

    states = np.array([preprocess_state(x[0]) for x in batch])
    actions = np.array([x[1] for x in batch])
    rewards = np.array([x[2] for x in batch])
    next_states = np.array([preprocess_state(x[3]) for x in batch])
    dones = np.array([x[4] for x in batch])

    # 🔵 predict CURRENT Q (online)
    q_values = model.predict(states, verbose=0)

    # 🔵 predict NEXT Q (TARGET network — IMPORTANT CHANGE)
    q_next = target_model.predict(next_states, verbose=0)

    for i in range(batch_size):
        if dones[i]:
            q_values[i][actions[i]] = rewards[i]
        else:
            q_values[i][actions[i]] = rewards[i] + gamma * np.max(q_next[i])

    model.fit(states, q_values, epochs=1, verbose=0)

# =========================
# TRAIN LOOP
# =========================

print("===== DQN WITH TARGET NETWORK START =====")

for episode in range(episodes):

    state = reset()
    total_reward = 0
    done = False
    step_count = 0

    while not done and step_count < max_steps:

        action = choose_action(state)

        next_state, reward, done = step(action)

        memory.append((state, action, reward, next_state, done))

        state = next_state
        total_reward += reward
        step_count += 1

    # 🔥 train after episode
    train()

    # 🔥 update target network every few episodes
    if episode % target_update_freq == 0:
        target_model.set_weights(model.get_weights())
        print("🔄 Target network updated")

    # epsilon decay
    if epsilon > epsilon_min:
        epsilon *= epsilon_decay

    if episode % 20 == 0:
        print(f"Episode {episode}, Reward: {total_reward}, Epsilon: {epsilon:.3f}")

print("\nTRAINING COMPLETE")
print(model.summary())