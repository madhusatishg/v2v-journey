import random

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
# ENV STATE
# =========================

start_state = [0, 0]
agent_pos = [0, 0]

# =========================
# HYPERPARAMETERS
# =========================

alpha = 0.1     # learning rate
gamma = 0.9     # discount factor
epsilon = 0.2   # exploration rate

episodes = 200

# =========================
# Q TABLE
# =========================

Q_table = {}

for r in range(len(grid)):
    for c in range(len(grid[0])):
        if grid[r][c] != 'X':
            Q_table[(r, c)] = [0, 0, 0, 0]


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
    elif action == 3:
        nr, nc = r, c + 1

    # boundary
    if nr < 0 or nr >= len(grid) or nc < 0 or nc >= len(grid[0]):
        return agent_pos, -5, False

    # obstacle
    if grid[nr][nc] == 'X':
        return agent_pos, -5, False

    # move
    agent_pos = [nr, nc]

    # goal
    if grid[nr][nc] == 'G':
        return agent_pos, 100, True

    return agent_pos, -1, False


# =========================
# EPSILON-GREEDY POLICY
# =========================

def choose_action(state):

    if random.random() < epsilon:
        return random.randint(0, 3)  # explore

    return Q_table[tuple(state)].index(max(Q_table[tuple(state)]))


# =========================
# TRAINING LOOP (Q-LEARNING)
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

        # if next state is valid in Q-table
        if next_tuple in Q_table:

            old_q = Q_table[state_tuple][action]
            max_future_q = max(Q_table[next_tuple])

            # =========================
            # Q-LEARNING UPDATE RULE
            # =========================
            Q_table[state_tuple][action] = old_q + alpha * (
                reward + gamma * max_future_q - old_q
            )

        state = next_state
        total_reward += reward

    if episode % 20 == 0:
        print(f"Episode {episode}, Reward: {total_reward}")


# =========================
# FINAL POLICY TEST
# =========================

print("\nFINAL Q TABLE:")
for k, v in Q_table.items():
    print(k, v)