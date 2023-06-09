import math
import heapq

def calculate_distance(position1, position2):
    # Check if the input types are correct
    if not (isinstance(position1, tuple) or isinstance(position1, list)) or len(position1) != 2:
        print(f"Invalid position1: {position1}")
        return
    if not (isinstance(position2, tuple) or isinstance(position2, list)) or len(position2) != 2:
        print(f"Invalid position2: {position2}")
        return

    # Calculate Euclidean distance between two positions
    if position2 is None:
        return float('100')  # Return infinity or another appropriate default value

    x1, y1 = position1
    x2, y2 = position2
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def find_nearest_ball(grid, robot_position, balls, red_crosses):
    #print("finding nearest ball")
    # Find the nearest ball to the robot's position
    min_distance = float('inf')
    nearest_ball = None

    for ball in balls:
        if ball not in red_crosses:  # Exclude red crosses
            distance = calculate_distance(robot_position, ball)
            if distance is not None and distance < min_distance:
                min_distance = distance
                nearest_ball = ball
    print("nearest ball: ",nearest_ball )

    return nearest_ball

def reconstruct_path(came_from, start, goal):
    print(goal)
    current = tuple(goal)
    path = []
    while current != tuple(start):
        path.append(list(current))
        if current not in came_from:
            print(f"KeyError: {current} not found in came_from")
            break
        current = came_from[current]
    path.append(list(start))
    path.reverse()
    return path

def astar(grid, start, goal):

    open_set = []
    heapq.heappush(open_set, (0, start))  
    came_from = {}
    cost_so_far = {}
    came_from[tuple(start)] = None
    cost_so_far[tuple(start)] = 0

    while open_set:
        current = heapq.heappop(open_set)[1]  
        current_tuple = tuple(current)  
        if current == goal:

            return came_from, cost_so_far, True

        for neighbor in get_neighbors(grid, current):
            neighbor_tuple = tuple(neighbor)  
            new_cost = cost_so_far[current_tuple] + 1  
            if neighbor_tuple not in cost_so_far or new_cost < cost_so_far[neighbor_tuple]:
                cost_so_far[neighbor_tuple] = new_cost
                priority = new_cost + calculate_distance(neighbor, goal)
                heapq.heappush(open_set, (priority, neighbor))
                came_from[neighbor_tuple] = current_tuple

    return came_from, cost_so_far, goal  

def get_neighbors(grid, position):
    # Get valid neighboring positions in the grid
    x, y = position
    neighbors = []

    grid_height = len(grid)
    
    # Check horizontal and vertical neighbors
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nx, ny = x + dx, y + dy
        if (0 <= nx < len(grid[0])) and (0 <= ny < grid_height) and (grid[grid_height-ny-1][nx] != 1):
            neighbors.append((nx, ny))

    # Check diagonal neighbors
    for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
        nx, ny = x + dx, y + dy
        if (0 <= nx < len(grid[0])) and (0 <= ny < grid_height) and (grid[grid_height-ny-1][nx] != 1):
            neighbors.append((nx, ny))

    return neighbors

