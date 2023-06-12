import socket
import threading
import cv2
import numpy as np
import time
import json
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def wait_for_connection():
    global client_socket
    while True:  # Keep trying until a connection is made
        try:
            print("Waiting for connection...")
            client_socket, addr = server_socket.accept()
            print(f"Connection made with {addr}.")
            connection_event.set()  # Set the event to signal that the client has connected
            break  # If connection is made, break out of the loop
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)  # Wait for a second before trying again

# Create a new server socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to a specific network interface and port number
server_socket.bind(("localhost", 1235))

# Tell the operating system to add the socket to the list of sockets
# that should be actively listening for incoming connections.
server_socket.listen(1)

# Start a new thread that waits for a client to connect
client_socket = None
connection_event = threading.Event()  # Create a new threading Event
connection_thread = threading.Thread(target=wait_for_connection)
connection_thread.start()
#connection_event.wait()

def get_center_of_contour(contour):
    M = cv2.moments(contour)
    if M["m00"] == 0:
        return None
    else:
        return (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

def draw_ROI(frame):
    fig,ax = plt.subplots(1)
    ax.imshow(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))  # Convert color for matplotlib display
    ROI = plt.ginput(4)  # Select the 4 corners of your rectangle
    if len(ROI) > 0:  # Check if ROI is not empty
        ROI.append(ROI[0])  # add the first point to the end to close the rectangle
        rect = patches.Polygon(ROI, linewidth=1, edgecolor='r', facecolor='none')  # Create a Rectangle patch
        ax.add_patch(rect)  # Add the patch to the Axes
        plt.show()
    else:
        print("No valid points were selected.")
        ROI = None
    return ROI
print("Waiting for camera...")
cap = cv2.VideoCapture(0)
print("Camera is on!")

lower_green = np.array([36, 25, 25])
upper_green = np.array([86, 255, 255])

# define range for red color
lower_red = np.array([0, 64, 0])
upper_red = np.array([11, 255, 255])

red_cross_centers = None

# define range for yellow
lower_yellow = np.array([24, 24, 204])
upper_yellow = np.array([53, 61, 255])

# define range for white color (light)
lower_white_light = np.array([0, 0, 200])
upper_white_light = np.array([179, 12, 255])

# define range for white color (shadow)
lower_white_shadow = np.array([16, 79, 203])
upper_white_shadow = np.array([86, 140, 255])

# define range for orange color
lower_orange = np.array([10, 114, 240])
upper_orange = np.array([51, 255, 255])

frame_corners = None
last_print_time = time.time()

balls_position = []
orange_balls_position = []
robot_position = None
last_robot_print_time = time.time()

cell_size = 10

robot_angle = None

last_send_time = time.time()

def get_angle(p1, p2):
    if p1 is None or p2 is None:
        return None
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    return math.degrees(math.atan2(dy, dx))

def get_vector(p1, p2):
    if p1 is None or p2 is None:
        return None
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    return dx, dy


ball_ids = {}  # A dict to store the IDs of the balls
next_ball_id = 1  # The ID that will be assigned to the next new ball
ball_threshold = 20  # If a ball moves more than this many pixels between frames, it is considered a new ball

def assign_ids_to_balls(balls_position):
    global next_ball_id, ball_ids
    new_ball_ids = {}
    for pos in balls_position:
        closest_id = None
        closest_dist = ball_threshold
        for id, old_pos in ball_ids.items():
            dist = ((pos[0] - old_pos[0]) ** 2 + (pos[1] - old_pos[1]) ** 2) ** 0.5
            if dist < closest_dist:
                closest_id = id
                closest_dist = dist
        if closest_id is not None:
            new_ball_ids[closest_id] = pos
        elif len(ball_ids) < 10:  # Only assign a new ID if there are less than 10 balls being tracked
            new_ball_ids[next_ball_id] = pos
            next_ball_id = (next_ball_id % 10) + 1  # This will make the ID number go back to 1 after reaching 10
    ball_ids = new_ball_ids

while True:
    _, frame = cap.read()
    
    if frame_corners is None:
        frame_corners = draw_ROI(frame)
        if frame_corners is not None:  # Check if draw_ROI returned valid points
            frame_corners = [(int(p[0]), int(p[1])) for p in frame_corners]
            # Calculate grid size
            max_x = max(p[0] for p in frame_corners)
            max_y = max(p[1] for p in frame_corners)
            grid_size = (max_x, max_y)

    if frame_corners is not None:  # This is a new conditional block
        polygon = np.array(frame_corners[:-1])

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        green_mask = cv2.inRange(hsv, lower_green, upper_green)
        green_contours, _ = cv2.findContours(green_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Get a binary image isolating the white pixels (light)
        white_mask_light = cv2.inRange(hsv, lower_white_light, upper_white_light)
    
        # Get a binary image isolating the white pixels (shadow)
        white_mask_shadow = cv2.inRange(hsv, lower_white_shadow, upper_white_shadow)

        # Combine the white masks (light and shadow)
        white_mask = cv2.bitwise_or(white_mask_light, white_mask_shadow)
        white_contours, _ = cv2.findContours(white_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Get a binary image isolating the orange pixels
        orange_mask = cv2.inRange(hsv, lower_orange, upper_orange)
        orange_contours, _ = cv2.findContours(orange_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
        # Get a binary image isolating the yellow pixels
        yellow_mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
        yellow_contours, _ = cv2.findContours(yellow_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    

        if green_contours:
            robot_contour = max(green_contours, key=cv2.contourArea)
            robot_center = get_center_of_contour(robot_contour)

            if robot_center is not None and cv2.pointPolygonTest(polygon, robot_center, False) >= 0:
                cv2.circle(frame, robot_center, 5, (255, 0, 0), -1)
                robot_position = (robot_center[0] - polygon[0][0], polygon[0][1] - robot_center[1])
                if time.time() - last_robot_print_time >= 3:
                    print(f"Robot at: {robot_position}")
                    if client_socket is not None:
                        robot_position = tuple(int(x) for x in robot_position)  # Convert numpy ints to python ints
                        try:
                            client_socket.send((json.dumps({"robot": robot_position}) + '\n').encode())
                        except Exception as e:
                            print(f"Error sending robot position: {e}")
                            break
                    last_robot_print_time = time.time()

                    # After identifying the yellow part of the robot:

            if yellow_contours:  # Check for the yellow dot at the back of the robot
                tail_contour = max(yellow_contours, key=cv2.contourArea)
                tail_center = get_center_of_contour(tail_contour)
                if tail_center is not None and cv2.pointPolygonTest(polygon, tail_center, False) >= 0:
                    cv2.circle(frame, tail_center, 5, (0, 255, 255), -1)  # Yellow circle
                    robot_vector = get_vector(robot_center, tail_center)


        balls_position = []  # Reset the white balls position at each frame
        orange_balls_position = []  # Reset the orange balls position at each frame
    
        min_contour_area = 100  # adjust this value to suit your needs

        # red cross
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Get a binary image isolating the red pixels
        red_mask = cv2.inRange(hsv, lower_red, upper_red)
        red_contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # If the red cross centers have not been computed yet
        if red_cross_centers is None:
            red_cross_centers = []
            for contour in red_contours:
                if cv2.contourArea(contour) < min_contour_area:
                    continue

                for point in contour:
                    point = tuple(point[0])  # convert from [[x y]] to (x, y)
                    if cv2.pointPolygonTest(polygon, (int(point[0]), int(point[1])), False) >= 0:
                        grid_point = (point[0] // cell_size, point[1] // cell_size)  # Convert from pixel coordinates to grid coordinates
                        red_cross_centers.append(point)
                        cv2.circle(frame, point, 5, (255, 192, 203), -1)  # Draw the center of the red cross in light blue

                print(f"Red Cross at: {red_cross_centers}")

        # Find white balls
        for contour in white_contours:
            # Sort contours by area and keep only the largest 10
            white_contours = sorted(white_contours, key=cv2.contourArea, reverse=True)[:10]

            if cv2.contourArea(contour) < min_contour_area:
                continue
            ball_center = get_center_of_contour(contour)
            if ball_center is not None and cv2.pointPolygonTest(polygon, ball_center, False) >= 0:
                cv2.circle(frame, ball_center, 5, (203, 192, 255), -1)
                balls_position.append((ball_center[0] - polygon[0][0], polygon[0][1] - ball_center[1]))
        
        assign_ids_to_balls(balls_position)  # NEW

        # Draw the number of balls on the frame
        #cv2.putText(frame, str(len(balls_position)), (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)


        # Before assigning IDs, draw balls and their IDs
        # for id, pos in ball_ids.items():
        #     cv2.circle(frame, pos, 5, (203, 192, 255), -1)
        #     cv2.putText(frame, str(id), (pos[0] + 10, pos[1]), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)  # Green number for ball ID
        for id, pos in ball_ids.items():
            cv2.putText(frame, str(id), (pos[0] + 10, pos[1]), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)  # Green number for ball ID


        # Calculate the vector between the robot and each ball
        if robot_position is not None and robot_vector is not None:
            for id, ball_position in ball_ids.items():
                ball_vector = get_vector(robot_position, ball_position)
                # If the vectors are similar, they are aligned. You might want to adjust the comparison based on your needs.
                if abs(robot_vector[0] - ball_vector[0]) < 5 and abs(robot_vector[1] - ball_vector[1]) < 5:
                    print(f"Robot is aligned with ball {id}")


        # Find orange balls
        for contour in orange_contours:
            if cv2.contourArea(contour) < min_contour_area:
                continue
            ball_center = get_center_of_contour(contour)
            if ball_center is not None and cv2.pointPolygonTest(polygon, ball_center, False) >= 0:
                cv2.circle(frame, ball_center, 5, (0, 165, 255), -1)
                orange_balls_position.append((ball_center[0] - polygon[0][0], polygon[0][1] - ball_center[1]))

        if time.time() - last_send_time >= 1:  # Send the data every second
            last_send_time = time.time()

            # Create a dictionary to hold all the data
            data = {
                "white_balls": [tuple(int(x) for x in pos) for pos in balls_position],
                "orange_balls": [tuple(int(x) for x in pos) for pos in orange_balls_position],
                "robot": None if robot_position is None else tuple(int(x) for x in robot_position),
                "red_crosses": [tuple(int(x) for x in pos) for pos in red_cross_centers],
                "grid_size": None if grid_size is None else tuple(int(x) for x in grid_size)
            }

            # Remove any None values
            data = {k: v for k, v in data.items() if v is not None}

            if client_socket is not None and connection_event.is_set():  # Only send data if the script is connected
                try:
                    client_socket.send((json.dumps(data) + '\n').encode())
                except Exception as e:  # If there's an error (like a disconnection), go back to trying to connect
                    print(f"Error sending data: {e}")
                    connection_event.clear()  # Clear the event to signal that the client has disconnected
                    connection_thread = threading.Thread(target=wait_for_connection)  # Start a new connection thread
                    connection_thread.start()
    
        cv2.polylines(frame, [polygon], True, (0,255,0), 2)
        cv2.imshow('Frame', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
client_socket.close()
server_socket.close()