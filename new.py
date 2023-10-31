import tkinter as tk
from tkinter import filedialog
import cv2
import subprocess

def open_camera():
    with open("flag.txt", "w") as file:
        file.write("True")
    try:
        subprocess.Popen(['python', 'main.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        result_label.config(text="Error: File not found")
    except Exception as e:
        result_label.config(text="An error occurred: " + str(e))

def open_video_file():
    file_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4")])
    if file_path:
        with open("flag.txt", "w") as file:
            file.write("False")
    try:
        subprocess.Popen(['python', 'main.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        result_label.config(text="Error: File not found")
    except Exception as e:
        result_label.config(text="An error occurred: " + str(e))

    #cv2.destroyAllWindows()

app = tk.Tk()

result_label = tk.Label(app, text="")
result_label.pack()

camera_button = tk.Button(app, text="Open Camera", command=open_camera)
camera_button.pack()

video_button = tk.Button(app, text="Open Video File", command=open_video_file)
video_button.pack()

app.mainloop()
