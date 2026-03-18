import traci

Sumo_config = [
    'sumo-gui',
    '-c', 'TraciExample.sumocfg',
    '--step-length', '0.05',
    '--delay', '1000',
    '--lateral-resolution', '0.1'
]

# Step 5: Open connection between SUMO and Traci
traci.start(Sumo_config)

# Step 6: Define Variables
vehicle_speed = 0
total_speed = 0

# Step 7: Define Functions

# Step 8: Take simulation steps until there are no more vehicles in the network
while traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep() # Move simulation forward 1 step
    # Here you can decide what to do with simulation data at each step
    if 't_2' in traci.vehicle.getIDList():
        vehicle_speed = traci.vehicle.getSpeed('t_2')
        total_speed = total_speed + vehicle_speed
    # step_count = step_count + 1
    print(f"Vehicle speed: {vehicle_speed} m/s")

# Step 9: Close connection between SUMO and Traci
traci.close()
