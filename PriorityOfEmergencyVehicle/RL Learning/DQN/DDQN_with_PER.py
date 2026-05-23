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
max_steps = 200
batch_size = 64

target_update_freq = 5

memory = []   # 🔥 now list with priorities

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

model = build_model()
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
# PRIORITY HELPERS
# =========================

def get_priority(error):
    return abs(error) + 1e-6

# =========================
# STORE MEMORY
# =========================

def store_transition(s, a, r, s2, done):
    memory.append([s, a, r, s2, done, 1.0])  # initial priority = 1

# =========================
# SAMPLE FROM PRIORITY
# =========================

def sample_batch():
    priorities = np.array([m[5] for m in memory], dtype=np.float32)
    probs = priorities / np.sum(priorities)

    indices = np.random.choice(len(memory), batch_size, p=probs)

    batch = [memory[i] for i in indices]
    return batch, indices

# =========================
# TRAIN
# =========================

def train():

    if len(memory) < batch_size:
        return

    batch, indices = sample_batch()

    states = np.array([preprocess_state(x[0]) for x in batch])
    actions = np.array([x[1] for x in batch])
    rewards = np.array([x[2] for x in batch])
    next_states = np.array([preprocess_state(x[3]) for x in batch])
    dones = np.array([x[4] for x in batch])

    q_values = model.predict(states, verbose=0)
    q_next_online = model.predict(next_states, verbose=0)
    q_next_target = target_model.predict(next_states, verbose=0)

    for i in range(batch_size):

        if dones[i]:
            target = rewards[i]
        else:
            best_action = np.argmax(q_next_online[i])
            target = rewards[i] + gamma * q_next_target[i][best_action]

        error = target - q_values[i][actions[i]]

        # 🔥 update priority
        memory[indices[i]][5] = get_priority(error)

        q_values[i][actions[i]] = target

    model.fit(states, q_values, epochs=1, verbose=0)

# =========================
# TRAIN LOOP
# =========================

print("===== PER + DOUBLE DQN START =====")

for episode in range(episodes):

    state = reset()
    total_reward = 0
    done = False
    step_count = 0

    while not done and step_count < max_steps:

        action = choose_action(state)

        next_state, reward, done = step(action)

        store_transition(state, action, reward, next_state, done)

        state = next_state
        total_reward += reward
        step_count += 1

        train()

    # update target network
    if episode % target_update_freq == 0:
        target_model.set_weights(model.get_weights())
        print("🔄 Target network updated")

    if epsilon > epsilon_min:
        epsilon *= epsilon_decay

    if episode % 20 == 0:
        print(f"Episode {episode}, Reward: {total_reward}, Epsilon: {epsilon:.3f}")

print("\nTRAINING COMPLETE")


print(model.summary())







# print("\n===== TESTING AGENT =====")

# state = reset()
# done = False
# steps = 0

# path = []

# epsilon_backup = epsilon
# epsilon = 0   # 🔥 no exploration (VERY IMPORTANT)

# while not done and steps < 50:

#     path.append(state.copy())

#     q_values = model.predict(np.array([preprocess_state(state)]), verbose=0)[0]
#     action = np.argmax(q_values)

#     next_state, reward, done = step(action)

#     state = next_state
#     steps += 1

# path.append(state)

# print("Path taken:")
# print(path)

# epsilon = epsilon_backup