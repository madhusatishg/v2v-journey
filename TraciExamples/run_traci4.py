import traci # Module for controlling SUMO simulations via TraCI

# Step 4: Define SUMO configuration
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
def process_vehicles():
    #vehicles_list = traci.vehicle.getIDList()
    if 't_2' in traci.vehicle.getIDList():
        traci.vehicle.moveToXY('t_2', 'E0.62', '0', 13, -10, 0, keepRoute=2)
        position = traci.vehicle.getPosition('t_2') # Get the (x, y) position of the vehicle
        angle = traci.vehicle.getAngle('t_2')
        print(f"Vehicle ID: {'t_2'}, Position: {position}, Angle: {angle}")

# Step 8: Take simulation steps until there are no more vehicles in the network
while traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep() # Move simulation forward 1 step
    # Here you can decide what to do with simulation data at each step
    process_vehicles()
    
# Step 9: Close connection between SUMO and Traci
traci.close()
