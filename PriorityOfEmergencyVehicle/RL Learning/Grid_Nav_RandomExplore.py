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

# Agent starting position
agent_pos = [0, 0]


# =========================
# PRINT GRID
# =========================

def print_grid():

    for row in range(len(grid)):

        row_output = ""

        for col in range(len(grid[row])):

            # Show Agent
            if [row, col] == agent_pos:
                row_output += "A "

            else:
                row_output += grid[row][col] + " "

        print(row_output)

    print()


# =========================
# RESET ENVIRONMENT
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

    row, col = agent_pos

    # -------------------------
    # ACTIONS
    # -------------------------

    # UP
    if action == 0:
        new_row = row - 1
        new_col = col

    # DOWN
    elif action == 1:
        new_row = row + 1
        new_col = col

    # LEFT
    elif action == 2:
        new_row = row
        new_col = col - 1

    # RIGHT
    elif action == 3:
        new_row = row
        new_col = col + 1

    else:
        return agent_pos, -5, False

    # -------------------------
    # BOUNDARY CHECK
    # -------------------------

    if new_row < 0 or new_row >= len(grid):
        return agent_pos, -5, False

    if new_col < 0 or new_col >= len(grid[0]):
        return agent_pos, -5, False

    # -------------------------
    # OBSTACLE CHECK
    # -------------------------

    if grid[new_row][new_col] == 'X':
        return agent_pos, -5, False

    # -------------------------
    # MOVE AGENT
    # -------------------------

    agent_pos = [new_row, new_col]

    # -------------------------
    # GOAL CHECK
    # -------------------------

    if grid[new_row][new_col] == 'G':
        return agent_pos, 100, True

    # -------------------------
    # NORMAL MOVE
    # -------------------------

    return agent_pos, -1, False


# =========================
# RANDOM AGENT
# =========================

print("===== RANDOM AGENT =====")

state = reset()

done = False
steps = 0
total_reward = 0

while not done and steps < 50:

    print_grid()

    # Random action
    action = random.randint(0, 3)

    # Take action
    next_state, reward, done = step(action)

    total_reward += reward

    print("Action:", action)

    if action == 0:
        print("Action Name: UP")

    elif action == 1:
        print("Action Name: DOWN")

    elif action == 2:
        print("Action Name: LEFT")

    elif action == 3:
        print("Action Name: RIGHT")

    print("Next State:", next_state)
    print("Reward:", reward)
    print("Done:", done)

    print("-------------------------")

    steps += 1


# =========================
# EPISODE SUMMARY
# =========================

print("===== EPISODE FINISHED =====")
print("Total Steps:", steps)
print("Total Reward:", total_reward)