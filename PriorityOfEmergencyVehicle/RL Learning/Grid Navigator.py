# =========================
# STEP 3 — GRID WORLD WITH REWARDS
# =========================

# Grid Layout
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

            # Show agent
            if [row, col] == agent_pos:
                row_output += "A "

            else:
                row_output += grid[row][col] + " "

        print(row_output)

    print()


# =========================
# STEP FUNCTION
# =========================

def step(action):

    global agent_pos

    row, col = agent_pos

    # -------------------------
    # Decide movement
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
    # Boundary Check
    # -------------------------

    if new_row < 0 or new_row >= len(grid):
        return agent_pos, -5, False

    if new_col < 0 or new_col >= len(grid[0]):
        return agent_pos, -5, False

    # -------------------------
    # Obstacle Check
    # -------------------------

    if grid[new_row][new_col] == 'X':
        return agent_pos, -5, False

    # -------------------------
    # Move Agent
    # -------------------------

    agent_pos = [new_row, new_col]

    # -------------------------
    # Goal Check
    # -------------------------

    if grid[new_row][new_col] == 'G':
        return agent_pos, 100, True

    # -------------------------
    # Normal Move
    # -------------------------

    return agent_pos, -1, False


# =========================
# TESTING
# =========================

print("Initial Grid")
print_grid()

# RIGHT
state, reward, done = step(3)

print("After RIGHT")
print("State:", state)
print("Reward:", reward)
print("Done:", done)

print_grid()


# DOWN
state, reward, done = step(1)

print("After DOWN")
print("State:", state)
print("Reward:", reward)
print("Done:", done)

print_grid()


# DOWN AGAIN (blocked by obstacle)
state, reward, done = step(1)

print("After DOWN")
print("State:", state)
print("Reward:", reward)
print("Done:", done)

print_grid()