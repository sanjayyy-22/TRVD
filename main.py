import sys
import time
import json
import base64
import cv2
import os

import numpy as np

print(cv2.__version__)

from vehicle_counter import VehicleCounter

road = None

frame_count=0

road_name = "80_donner_lake" #to get as input

with open('settings.json') as f:
	data = json.load(f)

	try:
		road = data[road_name]
	except KeyError:
		raise Exception('Road name not recognized.')

WAIT_TIME = 1

# Colors for drawing on processed frames
DIVIDER_COLOR = (255, 255, 0)
BOUNDING_BOX_COLOR = (255, 0, 0)
CENTROID_COLOR = (0, 0, 255)

# For cropped rectangles
ref_points = []
ref_rects = []

def nothing(x):
	pass

def click_and_crop (event, x, y, flags, param):
	global ref_points

	if event == cv2.EVENT_LBUTTONDOWN:
		ref_points = [(x,y)]

	elif event == cv2.EVENT_LBUTTONUP:
		(x1, y1), x2, y2 = ref_points[0], x, y

		ref_points[0] = ( min(x1,x2), min(y1,y2) )		

		ref_points.append ( ( max(x1,x2), max(y1,y2) ) )

		ref_rects.append( (ref_points[0], ref_points[1]) )

def save_cropped():
    global ref_rects, frame_count
    with open("flag.txt", "r") as file:
        flag = file.read().strip()  # Read the flag from the file
        if flag == "True":
            cap=cv2.VideoCapture("src-file")
        elif flag=="False":
            cap=cv2.VideoCapture(0)

    ret, frame = cap.read()

    save_directory = "saved_images"

    if not os.path.exists(save_directory):
        os.makedirs(save_directory)

    frame_count += 1
    image_filename = os.path.join(save_directory, f"captured_image_{frame_count}.jpg")
    cv2.imwrite(image_filename, frame)

    try:
        with open(image_filename, "rb") as img:
            image_b64 = base64.b64encode(img.read()).decode()

        try:
            with open("settings.json", "r") as ff:
                settings = json.load(ff)
        except (FileNotFoundError, json.JSONDecodeError):
            settings = {}

        settings[road_name]["image"] = str(image_b64)

        with open("settings.json", "w") as file:
            json.dump(settings, file, indent=4)
        print("Image converted to base64 and stored in settings.json")
    except FileNotFoundError:
        print("Image file not found.")
    except Exception as e:
        print("An error occurred:", str(e))

    with open('settings.json', 'r+') as f:
        a = json.load(f)
        a[road_name]['cropped_rects'] = ref_rects
        f.seek(0)
        json.dump(a, f, indent=4)
        f.truncate()

    print('Saved ref_rects to settings.json!')


def load_cropped ():
	global ref_rects

	ref_rects = road['cropped_rects']

	print('Loaded ref_rects from settings.json!')

def remove_cropped (gray, color):
	cropped = gray.copy()
	cropped_color = color.copy()

	for rect in ref_rects:
		cropped[ rect[0][1]:rect[1][1], rect[0][0]:rect[1][0] ] = 0
		cropped_color[ rect[0][1]:rect[1][1], rect[0][0]:rect[1][0] ] = (0,0,0)


	return cropped, cropped_color

def filter_mask (mask):
	kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (20, 20))
	kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (8, 8))
	kernel_dilate = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

	opening = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel_open)
	
	closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel_close)

	dilation = cv2.dilate(closing, kernel_dilate, iterations = 2)

	return dilation

def get_centroid (x, y, w, h):
	x1 = w // 2
	y1 = h // 2

	return(x+x1, y+y1)

def detect_vehicles (mask):

	MIN_CONTOUR_WIDTH = 10
	MIN_CONTOUR_HEIGHT = 10

	contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

	matches = []

	for (i, contour) in enumerate(contours):
		x, y, w, h = cv2.boundingRect(contour)
		contour_valid = (w >= MIN_CONTOUR_WIDTH) and (h >= MIN_CONTOUR_HEIGHT)

		if not contour_valid or not hierarchy[0,i,3] == -1:
			continue

		centroid = get_centroid(x, y, w, h)

		matches.append( ((x,y,w,h), centroid) )

	return matches

def process_frame(frame_number, frame, bg_subtractor, car_counter):
	processed = frame.copy()

	gray = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)

	# remove specified cropped regions
	cropped, processed = remove_cropped(gray, processed)

	if car_counter.is_horizontal:
		cv2.line(processed, (0, car_counter.divider), (frame.shape[1], car_counter.divider), DIVIDER_COLOR, 1)
	else:
		cv2.line(processed, (car_counter.divider, 0), (car_counter.divider, frame.shape[0]), DIVIDER_COLOR, 1)

	fg_mask = bg_subtractor.apply(cropped)
	fg_mask = filter_mask(fg_mask)

	matches = detect_vehicles(fg_mask)

	for (i, match) in enumerate(matches):
		contour, centroid = match

		x,y,w,h = contour

		cv2.rectangle(processed, (x,y), (x+w-1, y+h-1), BOUNDING_BOX_COLOR, 1)
		cv2.circle(processed, centroid, 2, CENTROID_COLOR, -1)

	car_counter.update_count(matches, frame_number, processed)

	cv2.imshow('Filtered Mask', fg_mask)

	return processed

def main ():
    bg_subtractor = cv2.createBackgroundSubtractorKNN(detectShadows=True)
    car_counter = None
    
    load_cropped()

    cap = cv2.VideoCapture(road['stream_url'])
    #cap=cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 2)

    cv2.namedWindow('Source Image')
    cv2.setMouseCallback('Source Image', click_and_crop)

    frame_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    frame_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)

    frame_number = -1

    while True:
        frame_number += 1
        ret, frame = cap.read()

        if not ret:
            print('Frame capture failed, stopping...')
            break
        
        if car_counter is None:
            car_counter = VehicleCounter(frame.shape[:2], road, cap.get(cv2.CAP_PROP_FPS), samples=10)

        processed = process_frame(frame_number, frame, bg_subtractor, car_counter)

        cv2.imshow('Source Image', frame)
        cv2.imshow('Processed Image', processed)

        key = cv2.waitKey(WAIT_TIME)

        if key == ord('s'): 
            save_cropped()
        elif key == ord('q') or key == 27:
            break

        time.sleep( 1.0 / cap.get(cv2.CAP_PROP_FPS) )


    print('Closing video capture...')
    cap.release()
    cv2.destroyAllWindows()
    print('Done.')



if __name__ == '__main__':
	main()