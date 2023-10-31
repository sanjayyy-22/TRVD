import math

# Given data
minimum_angle_degrees = -150  # Replace with your measured minimum angle
maximum_angle_degrees = -110  # Replace with your measured maximum angle
distance_meters = 0.0314394      # Replace with your measured distance
time_seconds = 5            # Replace with your measured time

# Convert angles to radians
minimum_angle_radians = math.radians(minimum_angle_degrees)
maximum_angle_radians = math.radians(maximum_angle_degrees)

# Calculate the angle change
angle_change_radians = maximum_angle_radians - minimum_angle_radians

# Calculate speed
speed = distance_meters / (time_seconds * math.cos(angle_change_radians))

print(f"The speed is {speed} meters per second.")
