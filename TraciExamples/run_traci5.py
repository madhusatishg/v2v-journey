import sumolib  

#Step 4: Define Sumo configuration
#IT DOES NOT HAVE

#Step 5:  Open connection between SUMO and SUMOLib
net = sumolib.net.readNet('TraciExample.net.xml')  # Load network file for analysis

#Step 6: Define Variables
speedsum = 0
edgecount = 0
avgSpeed = 0

#Step 7: Define Functions 
for edge in net.getEdges():
    speedsum += edge.getSpeed()  # Sum up the speeds of all edges
    edgecount += 1  # Count the number of edges

if edgecount > 0:
    avgSpeed = speedsum / edgecount  # Calculate average speed
    print(f"Average speed in all edges: {avgSpeed}")

#Step 8: Take simulation steps until there are no more vehicles in the network
#IT DOES NOT HAVE

#Step 9: close connection between sumo and traci
#IT DOES NOT HAVE
