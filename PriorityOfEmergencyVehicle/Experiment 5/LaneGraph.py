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
                temp_lane = []
                if current_lane in lane_downstream_map.keys():
                    for each_lane in lane_downstream_map[current_lane]:
                        temp_lane.append(
                            {
                                "tls": each_lane["tls"],
                                "to_lane": each_lane["to_lane"], 
                                "status": "Blocked" if traci.lane.getLastStepHaltingNumber(each_lane["to_lane"]) > 0 and traci.lane.getLastStepMeanSpeed(each_lane["to_lane"]) < 2 else "clear"
                            }
                        )
                emg_graph[vehID] = {
                    "speed": traci.vehicle.getSpeed(vehID),
                    "current_lane": current_lane,
                    "approaching_tls": tlsID,
                    "distance_to_tls": distance,
                    "potential_conflict_lanes": temp_lane
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

while traci.simulation.getMinExpectedNumber() < SIMULATION_TIME:
    traci.simulationStep()  
    emergency_lane_graph = build_emergency_vehicle_graph()
    for tls in traci.trafficlight.getIDList():
        if tls in list(set([emergency_lane_graph[each]['approaching_tls'] for each in emergency_lane_graph.keys()])):
            emergency_vech_near_current_tls = [each for each in emergency_lane_graph.keys() if emergency_lane_graph[each]['approaching_tls'] == tls and emergency_lane_graph[each]['distance_to_tls'] < emg_distance_threshold]
            current_phase = traci.trafficlight.getPhase(tls)
            closest_emg_vech = None
            min_distance = 1000000000.00
            for vehID, details in emergency_lane_graph.items():
                
                if details["distance_to_tls"] < min_distance and vehID in emergency_vech_near_current_tls:
                    closest_emg_vech = (vehID, details)
                    min_distance = details["distance_to_tls"]
           
            if closest_emg_vech:
                vehID, details = closest_emg_vech
                if not any(key == tls and saved_tls_states[key].get('Caused Vehicle') == vehID for key in saved_tls_states.keys()):
                    if any(conflict['status'] == "Blocked" for conflict in details['potential_conflict_lanes']):
                        print(f"\nEmergency Vehicle {vehID} is approaching TLS {details['approaching_tls']} and few next lanes are blocked!")
                        new_state = generate_new_state(details['approaching_tls'], [conflict['to_lane'] for conflict in details['potential_conflict_lanes']], details['current_lane'])
                        print(f"suggested new state for TLS {details['approaching_tls']} for the vechicle {vehID}: {new_state} to pass smoothly.")
                
                    elif all(conflict['status'] == "clear" for conflict in details['potential_conflict_lanes']):
                        print(f"\nEmergency Vehicle {vehID} is approaching TLS {details['approaching_tls']} and has all next lanes free to pass.")
                        new_state = generate_new_state(details['approaching_tls'], [conflict['to_lane'] for conflict in details['potential_conflict_lanes']], details['current_lane'])
                        print(f"suggested new state for TLS {details['approaching_tls']} for the vechicle {vehID}: {new_state} to pass smoothly.")
                        saved_tls_states[details['approaching_tls']] = {
                            "program": traci.trafficlight.getProgram(details['approaching_tls']),
                            "phase": current_phase,
                            "Cool Down": 3,
                            "Caused Vehicle": vehID
                        }
                        traci.trafficlight.setRedYellowGreenState(details['approaching_tls'], new_state)
                        print(f"Switching traffic light {details['approaching_tls']} to phase {new_state} due to vehicle {vehID}")
              
    emergency_active = False
    for tlsID in [each for each in saved_tls_states.keys()]:
        if tlsID == traci.vehicle.getNextTLS(saved_tls_states[tlsID]['Caused Vehicle']):
            emergency_active = True
            break
    if emergency_active == False:
            if saved_tls_states[tlsID]['Cool Down'] == 0:
                traci.trafficlight.setProgram(tlsID, saved_tls_states[tlsID]['program'])
                traci.trafficlight.setPhase(tlsID, saved_tls_states[tlsID]['phase'])
                print(f"Restoring traffic light {tlsID} to original state after emergency vehicle {vehID} has passed.")
                del saved_tls_states[tlsID]
                break
            else:
                saved_tls_states[tlsID]['Cool Down'] -= 1
            
                  
                                    
              
                    
                
    
    
        
                    
                    
    
    


traci.close()




# def print_graph_upstream_summary(lane_upstream_map):
#     print("\n===== LANE DEPENDENCY GRAPH =====")

#     for to_lane, upstream_list in lane_upstream_map.items():
#         print(f"\nLane: {to_lane}")
#         for entry in upstream_list:
#             print(f"   <- {entry['from_lane']} via TLS {entry['tls']}")
            
# def print_graph_downstream_summary(lane_downstream_map):
#     print("\n===== LANE DEPENDENCY GRAPH =====")

#     for from_lane, downstream_list in lane_downstream_map.items():
#         print(f"\nLane: {from_lane}")
#         for entry in downstream_list:
#             print(f"   -> {entry['to_lane']} via TLS {entry['tls']}")

# def inspect_specific_upstream_lane(lane_upstream_map, lane_id):
#     print(f"\n===== INSPECTING LANE: {lane_id} =====")

#     if lane_id not in lane_upstream_map:
#         print("No upstream dependencies found.")
#         return

#     for entry in lane_upstream_map[lane_id]:
#         print(f"From Lane: {entry['from_lane']} | TLS: {entry['tls']}")
        
# def inspect_specific_downstream_lane(lane_downstream_map, lane_id):
#     print(f"\n===== INSPECTING LANE: {lane_id} =====")

#     if lane_id not in lane_downstream_map:
#         print("No downstream dependencies found.")
#         return

#     for entry in lane_downstream_map[lane_id]:
#         print(f"From Lane: {entry['to_lane']} | TLS: {entry['tls']}")


# =========================
# PRINT FULL GRAPH
# =========================
# print_graph_upstream_summary(lane_upstream_map)
# print_graph_downstream_summary(lane_downstream_map)

# =========================
# TEST: Inspect one lane
# (replace with actual lane id from your network)
# =========================
# inspect_specific_upstream_lane(lane_upstream_map, "Node2-5-NB_0")
# inspect_specific_downstream_lane(lane_downstream_map, "Node2-5-NB_0")


# for vehID, details in emergency_lane_graph.items():
#         if len(traci.vehicle.getIDList())>2:
#             current_phase = traci.trafficlight.getPhase(details['approaching_tls'])
#             if details["distance_to_tls"] < emg_distance_threshold and details['speed'] ==0:  
#                 if any(conflict['status'] == "Blocked" for conflict in details['potential_conflict_lanes']) and details['approaching_tls'] not in saved_tls_states.keys():
                
#                     print(f"\nEmergency Vehicle {vehID} is approaching TLS {details['approaching_tls']} and few next lanes are blocked!")
#                     new_state = generate_new_state(details['approaching_tls'], [conflict['to_lane'] for conflict in details['potential_conflict_lanes']], details['current_lane'])
                
#                     print(f"suggested new state for TLS {details['approaching_tls']} for the vechicle {vehID}: {new_state} to pass smoothly.")
#                     saved_tls_states[details['approaching_tls']] = {
#                             "program": traci.trafficlight.getProgram(details['approaching_tls']),
#                             "phase": current_phase,
#                             "Cool Down": 3,
#                             "Caused Vehicle": vehID
#                     }
#                     traci.trafficlight.setRedYellowGreenState(details['approaching_tls'], new_state)
#                     print(f"Switching traffic light {details['approaching_tls']} to phase {new_state} due to vehicle {vehID}")
                
#                 elif all(conflict['status'] == "clear" for conflict in details['potential_conflict_lanes']) and details['approaching_tls'] not in saved_tls_states.keys():
                
#                     print(f"\nEmergency Vehicle {vehID} is approaching TLS {details['approaching_tls']} and has all next lanes free to pass.")
#                     new_state = generate_new_state(details['approaching_tls'], [conflict['to_lane'] for conflict in details['potential_conflict_lanes']], details['current_lane'])
#                     print(f"suggested new state for TLS {details['approaching_tls']} for the vechicle {vehID}: {new_state} to pass smoothly.")
#                     saved_tls_states[details['approaching_tls']] = {
#                             "program": traci.trafficlight.getProgram(details['approaching_tls']),
#                             "phase": current_phase,
#                             "Cool Down": 3,
#                             "Caused Vehicle": vehID
#                     }
#                     traci.trafficlight.setRedYellowGreenState(details['approaching_tls'], new_state)
#                     print(f"Switching traffic light {details['approaching_tls']} to phase {new_state} due to vehicle {vehID}")
                
#                 else:
#                     emergency_active = False
#                     for each in [each for each in saved_tls_states.keys() if saved_tls_states[each]['Caused Vehicle'] == vehID]:
#                         if each == details['approaching_tls'] and details['distance_to_tls'] < emg_distance_threshold:
#                             emergency_active = True
#                             break
#                         else:
#                             if saved_tls_states[each]['Cool Down'] == 0:
#                                 traci.trafficlight.setProgram(each, saved_tls_states[each]['program'])
#                                 traci.trafficlight.setPhase(each, saved_tls_states[each]['phase'])
#                                 print(f"Restoring traffic light {each} to original state after emergency vehicle {vehID} has passed.")
#                                 del saved_tls_states[each]
#                                 break
#                             saved_tls_states[each]['Cool Down'] -= 1

