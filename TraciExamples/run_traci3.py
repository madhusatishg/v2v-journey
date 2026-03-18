import traci
import threading

Sumo_config = [
    'sumo-gui',
    '-c', 'TraciExample.sumocfg',
    '--step-length', '0.05',
    '--delay', '1000',
    '--lateral-resolution', '0.1'
]

traci.start(Sumo_config)

ego_id = "t_2"
command = None  # shared variable


# 🔹 Input thread function
def keyboard_listener():
    global command
    while True:
        command = input()


# Start keyboard thread
thread = threading.Thread(target=keyboard_listener, daemon=True)
thread.start()

print("\nControls:")
print("  s = STOP veh1")
print("  g = GO (resume veh1)")
print("  q = QUIT\n")


while traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep()

    if ego_id in traci.vehicle.getIDList():

        if command == "s":
            traci.vehicle.setSpeedMode(ego_id, 0)
            traci.vehicle.setSpeed(ego_id, 0)
            print("EGO STOPPED")
            command = None

        elif command == "g":
            traci.vehicle.setSpeedMode(ego_id, 31)
            traci.vehicle.setSpeed(ego_id, -1)
            print("EGO RESUMED")
            command = None

        elif command == "q":
            break

        speed = traci.vehicle.getSpeed(ego_id)
        print(f"Vehicle speed: {speed:.2f} m/s")

traci.close()
print("Simulation ended.")

