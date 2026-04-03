from pyparsing import Each

import traci

Sumo_config = [
    'sumo-gui',
    '-c', 'Test.sumocfg',
    '--step-length', '0.05',
    '--delay', '1000',
    '--lateral-resolution', '0.1'
]

traci.start(Sumo_config)
total_waiting_time = 0
vehicle_count = 0

emergency_waiting_time = 0
emergency_count = 0

max_waiting_time = 0
prev_wait = {}

saved_tls_states = {}
emg_distance_threshold = 100
SIMULATION_TIME = 100


def generate_new_state(tlsID,to_lane_ids,from_lane):
    links = traci.trafficlight.getControlledLinks(tlsID)
    new_state = ""
    for ind in links:
       
        if ind[0][1] in to_lane_ids and ind[0][0] == from_lane: 
            new_state+= 'G'
        else:
            new_state+= 'r'
    return new_state

def Flag_downstream_congestion(from_lane, lane_downstream_map):
    congested_lanes = []
    free_lanes = []
    if from_lane in lane_downstream_map.keys():
        for each_lane in lane_downstream_map[from_lane]:
            if traci.lane.getLastStepHaltingNumber(each_lane["to_lane"]) > 0 and traci.lane.getLastStepMeanSpeed(each_lane["to_lane"]) < 2:
                congested_lanes.append(each_lane["to_lane"])
            else:
                free_lanes.append(each_lane["to_lane"])
    return True if len(congested_lanes) > 0 else False, congested_lanes, free_lanes

def build_emergency_vehicle_graph():
    emg_graph = {}

    vehIDs = traci.vehicle.getIDList()
    
    for vehID in vehIDs:
        if traci.vehicle.getTypeID(vehID) in  ["emergency", "emergency_1", "emergency_2"]:
            current_lane = traci.vehicle.getLaneID(vehID)
            #========================= Find the tls the vehicle is approaching =========================
            next_tls = traci.vehicle.getNextTLS(vehID)
            if next_tls:
                tlsID, tlsIndex, distance, State = next_tls[0]
                emg_graph[vehID] = {
                    "speed": traci.vehicle.getSpeed(vehID),
                    "current_lane": current_lane,
                    "approaching_tls": tlsID,
                    "distance_to_tls": distance
                }
                
    return emg_graph


                    
                                    
                                    
                

def build_lane_graphs():
    lane_upstream_map = {}
    lane_downstream_map = {}

    tls_ids = traci.trafficlight.getIDList()

    for tls in tls_ids:
        links = traci.trafficlight.getControlledLinks(tls)

        for link_group in links:
            if not link_group:
                continue

            for link in link_group:
                from_lane = link[0]
                to_lane = link[1]

                # ========================
                # UPSTREAM GRAPH
                # ========================
                if to_lane not in lane_upstream_map:
                    lane_upstream_map[to_lane] = []

                lane_upstream_map[to_lane].append({
                    "tls": tls,
                    "from_lane": from_lane
                })

                # ========================
                # DOWNSTREAM GRAPH
                # ========================
                if from_lane not in lane_downstream_map:
                    lane_downstream_map[from_lane] = []

                lane_downstream_map[from_lane].append({
                    "tls": tls,
                    "to_lane": to_lane
                })

    return lane_upstream_map, lane_downstream_map



lane_upstream_map, lane_downstream_map = build_lane_graphs()

while traci.simulation.getTime() < SIMULATION_TIME:
    traci.simulationStep()  
    emergency_lane_graph = build_emergency_vehicle_graph()
    # print(emergency_lane_graph)
    # print(f"lane_upstream_map: {lane_upstream_map}")
    # print(f"lane_downstream_map: {lane_downstream_map}")
    vehIDs = traci.vehicle.getIDList()
    for vehID in vehIDs:
        curr_lane = traci.vehicle.getLaneID(vehID)
        if traci.vehicle.getTypeID(vehID) in  ["emergency", "emergency_1", "emergency_2"] and vehID in emergency_lane_graph.keys() and curr_lane in lane_downstream_map.keys():
            # Level 1 Downstream Congestion Logic
            G_L1_Congestion, G_L1_Congested_lanes, G_L1_Free_lanes = Flag_downstream_congestion(emergency_lane_graph[vehID]["current_lane"], lane_downstream_map)
            if G_L1_Congestion:
                G_L2_Congestion = False
                G_L2_Congested_lanes = []
                G_L2_Free_lanes = []
                for each in G_L1_Congested_lanes+G_L1_Free_lanes:
                    L2_Cong, L2_Congested_lanes, L2_Free_lanes = Flag_downstream_congestion(each, lane_downstream_map)
                    G_L2_Congested_lanes.extend(L2_Congested_lanes)
                    G_L2_Free_lanes.extend(L2_Free_lanes)
                    if L2_Cong:
                        G_L2_Congestion = True
                if G_L2_Congestion:
                    print(f"for {vehID} we found L1 Congested and L2 Congested")
                    None
                else:
                    print(f"for {vehID} we found L1 Congested and L2 Free")
                    #check if the current vech has blocked the L1 tls already or not and got struct due to L2 Tls Blockage
                    if emergency_lane_graph[vehID]["approaching_tls"] in saved_tls_states.keys():
                        
                        NtlsID = lane_downstream_map[G_L1_Congested_lanes[0]][0]["tls"]
                        suggested_state = generate_new_state(NtlsID, G_L2_Free_lanes, G_L1_Congested_lanes[0])
                        print(f"{vehID} is suggesting {NtlsID} to swicth to {suggested_state}")
                        if emergency_lane_graph[vehID]["distance_to_tls"] < emg_distance_threshold and NtlsID not in saved_tls_states.keys() and suggested_state is not None:
                            CurrentPhase = traci.trafficlight.getPhase(NtlsID)
                            saved_tls_states[NtlsID] = {
                                "program": traci.trafficlight.getProgram(NtlsID),
                                "phase": CurrentPhase,
                                "Cool Down": 3,
                                "Caused Vehicle": vehID,
                                "Actual Cause TLS": emergency_lane_graph[vehID]["approaching_tls"]
                            }
                            traci.trafficlight.setRedYellowGreenState(NtlsID,suggested_state)
                            print(f"Emergency Vehicle ID: {vehID}")
                            print(f"Switching traffic light L1 cong and L2 free{NtlsID} to phase {suggested_state} due to vehicle {vehID}")
                            break
                        None
                     
                    else:   
                        None
                    # NtlsID = lane_downstream_map[G_L1_Congested_lanes[0]][0]["tls"]
                    # suggested_state = generate_new_state(tlsID, G_L2_Free_lanes, G_L1_Congested_lanes[0])
                    # print(f"{vehID} is suggesting {tlsID} to swicth to {suggested_state}")
                    # print(f"{vehID} has GL2 free lanes {G_L2_Free_lanes} and congested lanes {G_L2_Congested_lanes}")
                    # if emergency_lane_graph[vehID]["distance_to_tls"] < emg_distance_threshold and NtlsID not in saved_tls_states.keys() and suggested_state is not None:
                    #     CurrentPhase = traci.trafficlight.getPhase(NtlsID)
                    #     saved_tls_states[NtlsID] = {
                    #         "program": traci.trafficlight.getProgram(NtlsID),
                    #         "phase": CurrentPhase,
                    #         "Cool Down": 3,
                    #         "Caused Vehicle": vehID,
                    #         "Actual Cause TLS": emergency_lane_graph[vehID]["approaching_tls"]
                    #     }
                    #     traci.trafficlight.setRedYellowGreenState(NtlsID,suggested_state)
                    #     print(f"Emergency Vehicle ID: {vehID}")
                    #     print(f"Switching traffic light L1 cong and L2 free{NtlsID} to phase {suggested_state} due to vehicle {vehID}")
                    #     break

            else:
                
                G_L2_Congestion = False
                G_L2_Congested_lanes = []
                G_L2_Free_lanes = []
                for each in G_L1_Free_lanes:
                    L2_Cong, L2_Congested_lanes, L2_Free_lanes = Flag_downstream_congestion(each, lane_downstream_map)
                    G_L2_Congested_lanes.extend(L2_Congested_lanes)
                    G_L2_Free_lanes.extend(L2_Free_lanes)
                    if L2_Cong:
                        G_L2_Congestion = True
                if G_L2_Congestion:
                        print(f"for {vehID} we found L1 Free and L2 Congested")
                        None
                else:
                    print(f"for {vehID} we found L1 Free and L2 Free")
                    #before suggesting the state , we need to check how long the L2 tls stays green for now only thinking no code written
                    
                    suggested_state = generate_new_state(emergency_lane_graph[vehID]["approaching_tls"], G_L1_Free_lanes, emergency_lane_graph[vehID]["current_lane"])
                    #print(f"{emergency_lane_graph[vehID]["distance_to_tls"]} < {emg_distance_threshold} and {emergency_lane_graph[vehID]["approaching_tls"]} not in {saved_tls_states.keys()} and {suggested_state} is not None")
                    if emergency_lane_graph[vehID]["distance_to_tls"] < emg_distance_threshold and emergency_lane_graph[vehID]["approaching_tls"] not in saved_tls_states.keys() and suggested_state is not None:
                        CurrentPhase = traci.trafficlight.getPhase(emergency_lane_graph[vehID]["approaching_tls"])
                        saved_tls_states[emergency_lane_graph[vehID]["approaching_tls"]] = {
                            "program": traci.trafficlight.getProgram(emergency_lane_graph[vehID]["approaching_tls"]),
                            "phase": CurrentPhase,
                            "Cool Down": 3,
                            "Caused Vehicle": vehID,
                            "Actual Cause TLS": emergency_lane_graph[vehID]["approaching_tls"]
                        }
                        traci.trafficlight.setRedYellowGreenState(emergency_lane_graph[vehID]["approaching_tls"],suggested_state)
                        print(f"Emergency Vehicle ID: {vehID}")
                        print(f"Switching traffic light L1 L2 both free {emergency_lane_graph[vehID]['approaching_tls']} to phase {suggested_state} due to vehicle {vehID}")
                        break
                        
                            
    for tlsID in list(saved_tls_states.keys()):
        emergency_active = False
        for veh in vehIDs:
            
            if traci.vehicle.getTypeID(veh) in  ["emergency", "emergency_1", "emergency_2"]:
                next_tls = traci.vehicle.getNextTLS(veh)

                if next_tls:
                    next_tls_id, _, distance, _ = next_tls[0]
                    # along with distance we also check whether the vehicle which caused the traffic light change is still approaching the traffic light or not, if yes then we will not restore the traffic light, if no then we can restore the traffic light
                    if next_tls_id == tlsID and distance < emg_distance_threshold and veh == saved_tls_states[tlsID]["Caused Vehicle"]:
                        emergency_active = True
                        break   
                    if next_tls_id == saved_tls_states[tlsID]["Actual Cause TLS"] and distance < emg_distance_threshold and veh == saved_tls_states[tlsID]["Caused Vehicle"]:
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




