import traci

Sumo_config = [
    'sumo-gui',
    '-c', 'Test.sumocfg',
    '--step-length', '0.05',
    '--delay', '1000',
    '--lateral-resolution', '0.1'
]

saved_tls_states = {}
Emergency_Distance = 20

traci.start(Sumo_config)
while traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep() 
    vehIDs = traci.vehicle.getIDList()
    for veh in vehIDs:
        if traci.vehicle.getTypeID(veh) == 'emergency':
            next_tls = traci.vehicle.getNextTLS(veh)
            if next_tls:
                tlsID, tlsIndex, distance, State = next_tls[0]
                print(f"Vehicle {veh} is approaching traffic light {tlsID} at distance {distance} to the Index {tlsIndex} with state {State}")
                full_state = traci.trafficlight.getRedYellowGreenState(tlsID)
                print(f"Full state of traffic light {tlsID} is {full_state}")
                print("Lane State Index",full_state[tlsIndex])
                print("----------------")
                if distance < Emergency_Distance and full_state[tlsIndex] in ['r', 'R']:
                    logics = traci.trafficlight.getAllProgramLogics(tlsID)
                    phases = logics[0].getPhases()
                    for i,phase in enumerate(phases):
                        if phase.state[tlsIndex] in ['G', 'g']:
                            CurrentPhase = traci.trafficlight.getPhase(tlsID)
                            if CurrentPhase != i:
                                if tlsID not in saved_tls_states:
                                    saved_tls_states[tlsID] = {
                                        "prgram": traci.trafficlight.getProgram(tlsID),
                                        "phase": CurrentPhase
                                    }
                                print("Swicthing traffic light",tlsID,"to phase",i)
                                traci.trafficlight.setPhase(tlsID, i)
                                break
    for tlsID in list(saved_tls_states.keys()):
        emergency_active = False

        for veh in traci.vehicle.getIDList():
            if traci.vehicle.getTypeID(veh) == 'emergency':
                next_tls = traci.vehicle.getNextTLS(veh)
                if next_tls:
                    next_tls_id,_,distance,_ = next_tls[0]
                    if next_tls_id == tlsID and distance < Emergency_Distance:
                        emergency_active = True
                        break
        if not emergency_active:
            print("Restoring Traffic Light",tlsID)
            orginal_program = saved_tls_states[tlsID]["prgram"]
            orginal_phase = saved_tls_states[tlsID]["phase"]
            traci.trafficlight.setProgram(tlsID, orginal_program)
            traci.trafficlight.setPhase(tlsID, orginal_phase)
            del saved_tls_states[tlsID]


                           
                    






traci.close()
