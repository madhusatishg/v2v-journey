import traci

Sumo_config = [
    'sumo-gui',
    '-c', 'Test.sumocfg',
    '--step-length', '0.05',
    '--delay', '1000',
    '--lateral-resolution', '0.1'
]

saved_tls_states = {}
Emergency_Distance = 1000

# =========================
# METRICS INITIALIZATION
# =========================
total_waiting_time = 0
vehicle_count = 0

emergency_waiting_time = 0
emergency_count = 0

max_waiting_time = 0
prev_wait = {}

# =========================
# SIMULATION TIME (FIXED)
# =========================
SIMULATION_TIME = 100  # seconds

traci.start(Sumo_config)

while traci.simulation.getTime() < SIMULATION_TIME:
    traci.simulationStep()

    vehIDs = traci.vehicle.getIDList()

    # =========================
    # METRICS COLLECTION
    # =========================

    # =========================
    # EMERGENCY LOGIC
    # =========================
    for veh in vehIDs:
        if traci.vehicle.getTypeID(veh) == 'emergency' or traci.vehicle.getTypeID(veh) == 'emergency_1' or traci.vehicle.getTypeID(veh) == 'emergency_2':
            next_tls = traci.vehicle.getNextTLS(veh)

            if next_tls:
                tlsID, tlsIndex, distance, State = next_tls[0]

                full_state = traci.trafficlight.getRedYellowGreenState(tlsID)

                if distance < Emergency_Distance and full_state[tlsIndex] in ['r', 'R']:

                    logics = traci.trafficlight.getAllProgramLogics(tlsID)
                    phases = logics[0].getPhases()

                    for i, phase in enumerate(phases):
                        if phase.state[tlsIndex] in ['G', 'g']:
                            CurrentPhase = traci.trafficlight.getPhase(tlsID)

                            if CurrentPhase != i:
                                if tlsID not in saved_tls_states:
                                    saved_tls_states[tlsID] = {
                                        "program": traci.trafficlight.getProgram(tlsID),
                                        "phase": CurrentPhase
                                    }

                                print(f"Switching traffic light {tlsID} to phase {i}")
                                traci.trafficlight.setPhase(tlsID, i)
                                break

    # =========================
    # RESTORE LOGIC
    # =========================
    for tlsID in list(saved_tls_states.keys()):
        emergency_active = False

        for veh in vehIDs:
            if traci.vehicle.getTypeID(veh) == 'emergency':
                next_tls = traci.vehicle.getNextTLS(veh)

                if next_tls:
                    next_tls_id, _, distance, _ = next_tls[0]

                    if next_tls_id == tlsID and distance < Emergency_Distance:
                        emergency_active = True
                        break

        if not emergency_active:
            print(f"Restoring Traffic Light {tlsID}")

            original_program = saved_tls_states[tlsID]["program"]
            original_phase = saved_tls_states[tlsID]["phase"]

            traci.trafficlight.setProgram(tlsID, original_program)
            traci.trafficlight.setPhase(tlsID, original_phase)

            del saved_tls_states[tlsID]

    for veh in vehIDs:
        curr_wait = traci.vehicle.getWaitingTime(veh)
        prev = prev_wait.get(veh, 0)
        delta_wait = max(0, curr_wait - prev)
        prev_wait[veh] = curr_wait

        total_waiting_time += delta_wait

        if curr_wait > max_waiting_time:
            max_waiting_time = curr_wait

        if traci.vehicle.getTypeID(veh) in ['emergency', 'emergency_1', 'emergency_2']:
            emergency_waiting_time += delta_wait

    for veh in traci.simulation.getDepartedIDList():
         if traci.vehicle.getTypeID(veh) in ['emergency', 'emergency_1', 'emergency_2']:
            emergency_count +=1
         else:
            vehicle_count +=1

# =========================
# PRINT RESULTS
# =========================
print("\n===== EXPERIMENT RESULTS =====")
print(f"Total Waiting Time: {total_waiting_time}")
print(f"Max Waiting Time: {max_waiting_time}")
print(f"emergency waiting time: {emergency_waiting_time}")
print(f"Total Vehicles: {vehicle_count}")
print(f"Total Emergency Vehicles: {emergency_count}")

traci.close()