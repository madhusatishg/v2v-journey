import traci

sumoCmd = ["sumo-gui", "-c", "qickstart.sumocfg"]

traci.start(sumoCmd)

print("Simulation started...")

while traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep()

    vehicle_ids = traci.vehicle.getIDList()

    for veh_id in vehicle_ids:
        speed = traci.vehicle.getSpeed(veh_id)
        print(f"{veh_id} speed: {speed:.2f} m/s")

traci.close()
print("Simulation ended.")

