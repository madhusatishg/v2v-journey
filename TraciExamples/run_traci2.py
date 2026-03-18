import traci
import sys
import select

Sumo_config = [
    'sumo-gui',
    '-c', 'TraciExample.sumocfg',
    '--step-length', '0.05',
    '--delay', '1000',
    '--lateral-resolution', '0.1'
]

traci.start(Sumo_config)

vehicle_speed = 0
ego_id = "t_2"

print("\nControls:")
print("  s = STOP veh1")
print("  g = GO (resume veh1)")
print("  q = QUIT\n")

while traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep()

    if ego_id in traci.vehicle.getIDList():

        # Non-blocking keyboard input
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            command = sys.stdin.readline().strip()

            if command == "s":
                traci.vehicle.setSpeedMode(ego_id, 0)
                traci.vehicle.setSpeed(ego_id, 0)
                print("EGO STOPPED")

            elif command == "g":
                traci.vehicle.setSpeedMode(ego_id, 31)
                traci.vehicle.setSpeed(ego_id, -1)
                print("EGO RESUMED")

            elif command == "q":
                break

        vehicle_speed = traci.vehicle.getSpeed(ego_id)

traci.close()
print("Simulation ended.")
