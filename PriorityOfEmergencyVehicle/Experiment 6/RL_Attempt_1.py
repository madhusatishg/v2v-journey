import random
import numpy as np
import traci

# =========================================================
# CONFIG
# =========================================================

SUMO_CONFIG = [
    "sumo-gui",
    "-c",
    "Test.sumocfg",
    "--step-length",
    "1"
]

SIMULATION_TIME = 300

# IMPORTANT:
# Replace this with your actual TLS ID
TARGET_TLS = "J1"

# Emergency vehicle types
EMERGENCY_TYPES = ["emergency", "emergency_1", "emergency_2"]


# =========================================================
# RL ENVIRONMENT
# =========================================================

class SumoEnvironment:

    def __init__(self):

        self.step_count = 0

        self.total_reward = 0

        self.prev_emergency_wait = 0
        self.prev_normal_wait = 0

    # =====================================================
    # RESET ENVIRONMENT
    # =====================================================

    def reset(self):

        try:
            traci.close()
        except:
            pass

        traci.start(SUMO_CONFIG)

        self.step_count = 0
        self.total_reward = 0

        self.prev_emergency_wait = 0
        self.prev_normal_wait = 0

        return self.get_state()

    # =====================================================
    # FIND CLOSEST EMERGENCY VEHICLE
    # =====================================================

    def get_closest_emergency_vehicle(self):

        veh_ids = traci.vehicle.getIDList()

        best_vehicle = None
        best_distance = 999999

        for veh in veh_ids:

            if traci.vehicle.getTypeID(veh) not in EMERGENCY_TYPES:
                continue

            next_tls = traci.vehicle.getNextTLS(veh)

            if len(next_tls) == 0:
                continue

            tls_id, _, distance, _ = next_tls[0]

            if tls_id != TARGET_TLS:
                continue

            if distance < best_distance:
                best_distance = distance
                best_vehicle = veh

        return best_vehicle, best_distance

    # =====================================================
    # GET STATE
    # =====================================================

    def get_state(self):

        emergency_vehicle, distance = self.get_closest_emergency_vehicle()

        # -------------------------------------------------
        # NO EMERGENCY VEHICLE FOUND
        # -------------------------------------------------

        if emergency_vehicle is None:

            state = np.array([
                999,   # distance
                0,     # speed
                0,     # current phase
                0,     # emergency lane queue
                0      # total queue
            ], dtype=np.float32)

            return state

        # -------------------------------------------------
        # VEHICLE INFO
        # -------------------------------------------------

        speed = traci.vehicle.getSpeed(emergency_vehicle)

        current_lane = traci.vehicle.getLaneID(emergency_vehicle)

        # -------------------------------------------------
        # CURRENT TLS PHASE
        # -------------------------------------------------

        current_phase = traci.trafficlight.getPhase(TARGET_TLS)

        # -------------------------------------------------
        # EMERGENCY LANE QUEUE
        # -------------------------------------------------

        emergency_lane_queue = traci.lane.getLastStepHaltingNumber(
            current_lane
        )

        # -------------------------------------------------
        # TOTAL QUEUE AROUND TLS
        # -------------------------------------------------

        controlled_lanes = traci.trafficlight.getControlledLanes(
            TARGET_TLS
        )

        total_queue = 0

        for lane in controlled_lanes:
            total_queue += traci.lane.getLastStepHaltingNumber(
                lane
            )

        # -------------------------------------------------
        # STATE VECTOR
        # -------------------------------------------------

        state = np.array([
            distance,
            speed,
            current_phase,
            emergency_lane_queue,
            total_queue
        ], dtype=np.float32)

        return state

    # =====================================================
    # APPLY ACTION
    # =====================================================

    def apply_action(self, action):

        # ---------------------------------------------
        # ACTION 0 = KEEP CURRENT PHASE
        # ---------------------------------------------

        if action == 0:
            return

        # ---------------------------------------------
        # ACTION 1 = FORCE GREEN
        # ---------------------------------------------

        elif action == 1:

            emergency_vehicle, _ = self.get_closest_emergency_vehicle()

            if emergency_vehicle is None:
                return

            emergency_lane = traci.vehicle.getLaneID(
                emergency_vehicle
            )

            links = traci.trafficlight.getControlledLinks(
                TARGET_TLS
            )

            new_state = ""

            for group in links:

                if len(group) == 0:
                    continue

                from_lane = group[0][0]

                if from_lane == emergency_lane:
                    new_state += "G"
                else:
                    new_state += "r"

            try:
                traci.trafficlight.setRedYellowGreenState(
                    TARGET_TLS,
                    new_state
                )
            except:
                pass

    # =====================================================
    # CALCULATE REWARD
    # =====================================================

    def calculate_reward(self):

        emergency_wait = 0
        normal_wait = 0

        veh_ids = traci.vehicle.getIDList()

        for veh in veh_ids:

            wait = traci.vehicle.getWaitingTime(veh)

            if traci.vehicle.getTypeID(veh) in EMERGENCY_TYPES:
                emergency_wait += wait
            else:
                normal_wait += wait

        # -------------------------------------------------
        # DELTA WAIT
        # -------------------------------------------------

        delta_emergency_wait = (
            emergency_wait - self.prev_emergency_wait
        )

        delta_normal_wait = (
            normal_wait - self.prev_normal_wait
        )

        self.prev_emergency_wait = emergency_wait
        self.prev_normal_wait = normal_wait

        # -------------------------------------------------
        # REWARD FUNCTION
        # -------------------------------------------------

        reward = (
            -1.0 * delta_emergency_wait
            -0.1 * delta_normal_wait
        )

        return reward

    # =====================================================
    # STEP
    # =====================================================

    def step(self, action):

        self.apply_action(action)

        traci.simulationStep()

        self.step_count += 1

        next_state = self.get_state()

        reward = self.calculate_reward()

        self.total_reward += reward

        done = self.is_done()

        return next_state, reward, done

    # =====================================================
    # DONE CONDITION
    # =====================================================

    def is_done(self):

        if traci.simulation.getTime() >= SIMULATION_TIME:
            return True

        return False

    # =====================================================
    # CLOSE
    # =====================================================

    def close(self):

        traci.close()


# =========================================================
# RANDOM AGENT TEST
# =========================================================

if __name__ == "__main__":

    env = SumoEnvironment()

    state = env.reset()

    done = False

    while not done:

        # RANDOM ACTION
        action = random.randint(0, 1)

        next_state, reward, done = env.step(action)

        print("STATE:", next_state)
        print("ACTION:", action)
        print("REWARD:", reward)
        print("-" * 50)

        state = next_state

    print("\n===== EPISODE COMPLETE =====")
    print("TOTAL REWARD:", env.total_reward)

    env.close()