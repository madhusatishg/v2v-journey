import random
import traci


# =========================================================
# FAST SUMO CONFIG
# =========================================================

SUMO_CONFIG = [
    "sumo",
    "-c",
    "Test.sumocfg",
    "--start",
    "--quit-on-end",
    "--step-length", "0.1"
]

# NOTE:
# "sumo"     -> FAST no GUI
# "sumo-gui" -> GUI slower


# =========================================================
# SUMO RL ENVIRONMENT
# =========================================================

class SumoEnvironment:

    def __init__(self):

        self.simulation_time = 300

    # =====================================================
    # RESET ENVIRONMENT
    # =====================================================

    def reset(self):

        traci.start(SUMO_CONFIG)

        traci.simulationStep()

    # =====================================================
    # GET STATE
    # =====================================================

    def get_state(self):

        veh = "None"

        tls_id = "None"

        emergency_distance = 999

        emergency_speed = 0

        current_phase = 0

        congestion_flag = 0

        veh_ids = traci.vehicle.getIDList()

        for vehicle in veh_ids:

            veh_type = traci.vehicle.getTypeID(vehicle)

            if veh_type in [
                "emergency",
                "emergency_1",
                "emergency_2"
            ]:

                next_tls = traci.vehicle.getNextTLS(vehicle)

                if len(next_tls) > 0:

                    tls_id, _, distance, _ = next_tls[0]

                    veh = vehicle

                    emergency_distance = distance

                    emergency_speed = traci.vehicle.getSpeed(
                        vehicle
                    )

                    current_phase = traci.trafficlight.getPhase(
                        tls_id
                    )

                    # =====================================
                    # CONGESTION CHECK
                    # =====================================

                    current_lane = traci.vehicle.getLaneID(
                        vehicle
                    )

                    halting = traci.lane.getLastStepHaltingNumber(
                        current_lane
                    )

                    if halting > 3:

                        congestion_flag = 1

                    break

        state = [
            veh,
            tls_id,
            emergency_distance,
            emergency_speed,
            current_phase,
            congestion_flag
        ]

        return state

    # =====================================================
    # DISCRETIZE STATE
    # =====================================================

    def discretize_state(self, state):

        distance = state[2]

        current_phase = state[4]

        congestion_flag = state[5]

        # =============================================
        # DISTANCE BUCKETS
        # =============================================

        if distance < 25:

            distance_bucket = "NEAR"

        elif distance < 75:

            distance_bucket = "MEDIUM"

        else:

            distance_bucket = "FAR"

        discrete_state = (
            distance_bucket,
            current_phase,
            congestion_flag
        )

        return discrete_state

    # =====================================================
    # APPLY ACTION
    # =====================================================

    def apply_action(self, action, tls_id):

        if tls_id == "None":

            return

        # =============================================
        # ACTION 0 -> DO NOTHING
        # =============================================

        if action == 0:

            return

        # =============================================
        # ACTION 1 -> NEXT PHASE
        # =============================================

        elif action == 1:

            current_phase = traci.trafficlight.getPhase(
                tls_id
            )

            phase_count = len(
                traci.trafficlight.getAllProgramLogics(
                    tls_id
                )[0].phases
            )

            next_phase = (
                current_phase + 1
            ) % phase_count

            traci.trafficlight.setPhase(
                tls_id,
                next_phase
            )

    # =====================================================
    # REWARD FUNCTION
    # =====================================================

    def get_reward(self, state):

        emergency_speed = state[3]

        congestion_flag = state[5]

        reward = emergency_speed

        # congestion penalty
        if congestion_flag == 1:

            reward -= 2

        return reward

    # =====================================================
    # STEP FUNCTION
    # =====================================================

    def step(self, action):

        state = self.get_state()

        tls_id = state[1]

        self.apply_action(action, tls_id)

        traci.simulationStep()

        next_state = self.get_state()

        reward = self.get_reward(next_state)

        done = (
            traci.simulation.getTime()
            >= self.simulation_time
        )

        return next_state, reward, done

    # =====================================================
    # CLOSE
    # =====================================================

    def close(self):

        traci.close(False)


# =========================================================
# CREATE ENVIRONMENT
# =========================================================

env = SumoEnvironment()

# =========================================================
# Q TABLE
# =========================================================

Q = {}

actions = [0, 1]

# learning rate
alpha = 0.1

# discount factor
gamma = 0.9

# exploration
epsilon = 0.3

# =========================================================
# TRAINING
# =========================================================

episodes = 50

for episode in range(episodes):

    print("\nEPISODE:", episode)

    env.reset()

    done = False

    total_reward = 0

    while not done:

        # =============================================
        # CURRENT STATE
        # =============================================

        state = env.get_state()

        discrete_state = env.discretize_state(
            state
        )

        # initialize q values
        for action in actions:

            if (
                discrete_state,
                action
            ) not in Q:

                Q[
                    (
                        discrete_state,
                        action
                    )
                ] = 0

        # =============================================
        # EPSILON GREEDY POLICY
        # =============================================

        if random.random() < epsilon:

            action = random.choice(actions)

        else:

            action = max(
                actions,
                key=lambda a: Q[
                    (
                        discrete_state,
                        a
                    )
                ]
            )

        # =============================================
        # STEP
        # =============================================

        next_state, reward, done = env.step(
            action
        )

        total_reward += reward

        next_discrete_state = env.discretize_state(
            next_state
        )

        # initialize future q values
        for next_action in actions:

            if (
                next_discrete_state,
                next_action
            ) not in Q:

                Q[
                    (
                        next_discrete_state,
                        next_action
                    )
                ] = 0

        # =============================================
        # Q UPDATE
        # =============================================

        best_future_q = max(

            Q[
                (
                    next_discrete_state,
                    next_action
                )
            ]

            for next_action in actions
        )

        current_q = Q[
            (
                discrete_state,
                action
            )
        ]

        new_q = current_q + alpha * (

            reward
            + gamma * best_future_q
            - current_q
        )

        Q[
            (
                discrete_state,
                action
            )
        ] = new_q

    env.close()

    print(
        "Episode Reward:",
        round(total_reward, 2)
    )

# =========================================================
# FINAL Q TABLE
# =========================================================

print("\n========================")
print("FINAL Q TABLE")
print("========================\n")

for key, value in Q.items():

    print(
        key,
        "->",
        round(value, 2)
    )

print("\nTraining Finished")