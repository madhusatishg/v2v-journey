import traci

Sumo_config = [
    'sumo-gui',
    '-c', 'Test.sumocfg',
    '--step-length', '0.05',
    '--delay', '1000',
    '--lateral-resolution', '0.1'
]

saved_tls_states = {}
emg_distance_threshold = 100

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

def calculate_tls_route(tlsID):
    links = traci.trafficlight.getControlledLinks(tlsID)
    # For Each Link, we try to see how each lane is connected with rest of lanes, example lane A is connect to lane B and C, then we will have lane_to_indexes[A] = [index of link connecting A to B, index of link connecting A to C]
    lane_to_indexes = {}
    # For each link we also calculate the occupancy of to lane, example for link connecting A to B, we will calculate the occupancy of lane B and store it in to_lane_occupany with key as index of link connecting A to B
    to_lane_occupany = {}
    for idx, link in enumerate(links): 
        from_lane = link[0][0]
        to_lane = link[0][1]
        if from_lane not in lane_to_indexes:
            lane_to_indexes[from_lane] = []
        if idx not in to_lane_occupany.keys():
            avg_speed = traci.lane.getLastStepMeanSpeed(to_lane)
            halt_count = traci.lane.getLastStepHaltingNumber(to_lane)
            to_lane_occupany[idx] = {
                "lane": to_lane,
                "speed": avg_speed,
                "halt": halt_count
            }
        lane_to_indexes[from_lane].append(idx)
    return lane_to_indexes, to_lane_occupany

def generate_new_state(full_state, index_tobe_green):
    new_state = ""
    for ind in range(len(full_state)):
        if ind in index_tobe_green: 
            new_state+= 'G'
        else:
            new_state+= 'r'
    return new_state
   
    


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
        #Curr_veh_speed = traci.vehicle.getSpeed(veh)
        #Get Current Vechile Lane ID, we will use this lane id to check whether this lane is connected to traffic light or not
        lane_id = traci.vehicle.getLaneID(veh)
        
        if traci.vehicle.getTypeID(veh) == 'emergency' or traci.vehicle.getTypeID(veh) == 'emergency_1' or traci.vehicle.getTypeID(veh) == 'emergency_2':
            next_tls = traci.vehicle.getNextTLS(veh)
            if next_tls:
                tlsID, tlsIndex, distance, State = next_tls[0]
                lane_to_indexes, to_lane_occupany = calculate_tls_route(tlsID)
                # index_tobe_green will give the index of link which is connected to lane in which emergency vehicle is present, example if emergency vehicle is present in lane A and lane A is connected to lane B and C with link 0 and 1 respectively, then lane_to_indexes[A] = [0,1] and index_tobe_green will be [0,1]   
                index_tobe_green = lane_to_indexes.get(lane_id) or []

                Current_state = traci.trafficlight.getRedYellowGreenState(tlsID)
                #Generate new state for traffic light, giving green for the lanes conencted to current emergency vehicle lane and red for rest of the lanes
                if index_tobe_green is not None and index_tobe_green != []:
                    new_state = generate_new_state(Current_state, index_tobe_green)
                
               

                if distance < emg_distance_threshold and not(Current_state == new_state) and tlsID not in saved_tls_states and all(to_lane_occupany[i]["speed"] > 5 and to_lane_occupany[i]["halt"] == 0 for i in index_tobe_green) and index_tobe_green is not None and index_tobe_green != []:
                    if tlsID not in saved_tls_states:
                        CurrentPhase = traci.trafficlight.getPhase(tlsID)
                        saved_tls_states[tlsID] = {
                            "program": traci.trafficlight.getProgram(tlsID),
                            "phase": CurrentPhase,
                            "Cool Down": 3,
                            "Caused Vehicle": veh
                        }
                        traci.trafficlight.setRedYellowGreenState(tlsID,new_state)
                        print(f"Switching traffic light {tlsID} to phase {new_state} due to vehicle {veh}")
                        break

    # =========================F
    # RESTORE LOGIC
    # =========================
    for tlsID in list(saved_tls_states.keys()):
        emergency_active = False
        for veh in vehIDs:
            
            if traci.vehicle.getTypeID(veh) == 'emergency' or traci.vehicle.getTypeID(veh) == 'emergency_1' or traci.vehicle.getTypeID(veh) == 'emergency_2':
                next_tls = traci.vehicle.getNextTLS(veh)

                if next_tls:
                    next_tls_id, _, distance, _ = next_tls[0]
                    # along with distance we also check whether the vehicle which caused the traffic light change is still approaching the traffic light or not, if yes then we will not restore the traffic light, if no then we can restore the traffic light
                    if next_tls_id == tlsID and distance < emg_distance_threshold and veh == saved_tls_states[tlsID]["Caused Vehicle"]:
                        emergency_active = True
                        break

        if not emergency_active:
            if saved_tls_states[tlsID]["Cool Down"] > 0:
                saved_tls_states[tlsID]["Cool Down"] -= 1
            else:
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


# ===== EXPERIMENT RESULTS =====
# Total Waiting Time: 1039.4999999996023
# Max Waiting Time: 50.75
# emergency waiting time: 42.9
# Total Vehicles: 39
# Total Emergency Vehicles: 3