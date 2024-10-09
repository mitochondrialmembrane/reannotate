import cv2
import os
import json
from moviepy.editor import *
import math
import bisect
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QSlider, QPushButton, QLineEdit, QHBoxLayout
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap

TEXT_FILE_PATH = "sym/2024-07-01-03-action-sewing/scripts.txt"
VIDEO_FOLDER_PATH = "sym/2024-07-01-03-action-sewing/mano"
OUTPUT_PATH = "2024-07-01-03-action-sewing.json"
SCENE="2024-07-01-03-action-sewing"

actions = []

class VideoPlayerWidget(QWidget):
    def __init__(self, video_path, start, end):
        super().__init__()
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)

        # Video metadata
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.video_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.video_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # GUI components
        self.video_label = QLabel(self)
        self.video_label.setFixedSize(1036, 500)  # Set fixed size for video display

        self.slider = QSlider(Qt.Horizontal, self)
        self.start = start
        self.end = min(end, self.frame_count - 1)
        self.slider.setMinimum(self.start)
        self.slider.setMaximum(self.end)
        self.slider.sliderMoved.connect(self.seek_video)

        # Play/Pause Button
        self.play_button = QPushButton('Pause', self)
        self.play_button.clicked.connect(self.toggle_play_pause)

        # Layouts
        control_layout = QHBoxLayout()
        control_layout.addWidget(self.play_button)

        layout = QVBoxLayout()
        layout.addWidget(self.video_label)
        layout.addWidget(self.slider)
        layout.addLayout(control_layout)
        self.setLayout(layout)

        # Timer for updating the video
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)

        self.move(0, 0)
        self.is_paused = False
        self.current_frame = self.start
        self.timer.start(int(1000 / self.fps))  # Adjust the timer for frame rate

    def update_frame(self):
        if not self.is_paused and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret and (self.current_frame < self.end):
                self.current_frame += 1
                self.slider.setValue(self.current_frame)

                # Resize the frame to fit the QLabel (640x480)
                frame = cv2.resize(frame, (1036, 500), interpolation=cv2.INTER_AREA)

                # Convert frame to RGB format for display in QLabel
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                cv2.putText(frame,  
                    "frame: " + str(self.current_frame),  
                    (50, 50),  
                    cv2.FONT_HERSHEY_SIMPLEX, 1,  
                    (0, 0, 0),  
                    4,  
                    cv2.LINE_4)
                # Create QImage from the frame
                image = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
                self.video_label.setPixmap(QPixmap.fromImage(image))
            else:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.start)
                self.current_frame = self.start

    def toggle_play_pause(self):
        """Toggles between play and pause states."""
        if self.is_paused:
            self.play_button.setText('Pause')
            self.timer.start(int(1000 / self.fps))  # Resume the timer
        else:
            self.play_button.setText('Play')
            self.timer.stop()  # Stop the timer
        self.is_paused = not self.is_paused

    def seek_video(self, position):
        """Seek the video to a specific frame."""
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, position)
        self.current_frame = position

        ret, frame = self.cap.read()
        if ret:
            # Resize the frame to fit the QLabel (640x480)
            frame = cv2.resize(frame, (1036, 500), interpolation=cv2.INTER_AREA)

            # Convert frame to RGB format for display in QLabel
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            cv2.putText(frame,  
                "frame: " + str(self.current_frame),  
                (50, 50),  
                cv2.FONT_HERSHEY_SIMPLEX, 1,  
                (0, 0, 0),  
                4,  
                cv2.LINE_4)
            # Create QImage from the frame
            image = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
            self.video_label.setPixmap(QPixmap.fromImage(image))

    def closeEvent(self, event):
        self.cap.release()


def load_text(path):
    with open(path, 'r') as f:
        #lines = [line.split(".mp3")[1].strip() for line in f]
        return [line for line in f]

def load_video_paths(path):
    files = [os.path.join(path, file) for file in sorted(os.listdir(path))]
    return list(filter(lambda f: f.endswith(".mp4"), files))

def play_video(path, start_frame=0, end_frame=math.inf):
    cap = cv2.VideoCapture(path)
    # Check if camera opened successfully
    if cap.isOpened() == False:
        print("Error opening video file")
    # Read until video is completed
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame-1)
    i = start_frame
    while cap.isOpened() and i < end_frame:   
    # Capture frame-by-frame
        ret, frame = cap.read()
        if ret == True:
            cv2.putText(frame,  
                "frame: " + str(i),  
                (50, 50),  
                cv2.FONT_HERSHEY_SIMPLEX, 1,  
                (0, 0, 0),  
                4,  
                cv2.LINE_4)
        # Display the resulting frame
            cv2.imshow('Frame', frame)
            i += 1
        # Press Q on keyboard to exit
            if cv2.waitKey(25) & 0xFF == ord('q'):
                break
    # Break the loop
        else:
            break
    # When everything done, release
    # the video capture object
    cap.release()
    # Closes all the frames
    cv2.destroyAllWindows()

def get_end_frame(path):
    cap = cv2.VideoCapture(path)
    return int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

def show_video(path, start_frame=0, end_frame=math.inf):
    player = VideoPlayerWidget(path, start_frame, end_frame)
    player.setWindowTitle('Matcher')
    player.show()

'''
def split_video(path, time):
    clip = VideoFileClip(path)
    first_half_path = append_id(path, "0")
    second_half_path = append_id(path, "1")
    clip.subclip(0, time).write_videofile(first_half_path)
    clip.subclip(time, clip.duration).write_videofile(second_half_path)
    return first_half_path, second_half_path
'''

def append_id(path, id):
  return "{0}_{2}{1}".format(*os.path.splitext(path) + (id,))

app = QApplication(sys.argv)
curr_video_num = 0
final_annotations = []
orig_annotations = load_text(TEXT_FILE_PATH)
curr_annotation = orig_annotations.pop(0)
video_paths = load_video_paths(VIDEO_FOLDER_PATH)
curr_video_path = video_paths.pop(0)

player = VideoPlayerWidget(curr_video_path, 0, math.inf)
player.setWindowTitle('Matcher')
player.show()

new_annotations = 0
deleted_annotations = 0
splits = [math.inf]
curr_start = 0

while True:
    print(f"Current annotation: {curr_annotation}")
    print("Option 1: Match annotation to video.")
    print("Option 2: Add new annotation for this video")
    print("Option 3: Remove the current annotation")
    print("Option 4: Split video")
    print("Option 5: Remove split")
    print("Option 6: Undo match")
    choice = input("Enter your choice: ")
    if choice == '1':
        out_dict = {
            "scene": SCENE,
            "sequence": os.path.basename(curr_video_path).rsplit(".", 1)[0],
            "annotation": curr_annotation,
            "start_frame_id": curr_start
        }
        # if there are no splits left
        if len(splits) == 1:
            out_dict["end_frame_id"] = get_end_frame(curr_video_path)
            curr_start = 0
            if video_paths:
                curr_video_path = video_paths.pop(0)
            else: 
                break
        else:
            curr_start = splits.pop(0)
            out_dict["end_frame_id"] = curr_start - 1

        final_annotations.append(out_dict)
        if orig_annotations:
            curr_annotation = orig_annotations.pop(0)
        else: 
            curr_annotation = None
        curr_video_num += 1

        player = VideoPlayerWidget(curr_video_path, curr_start, splits[0])
        player.setWindowTitle('Matcher')
        player.show()
    elif choice == '2':
        new_annotation = input("Enter your new annotation: ")
        out_dict = {
            "scene": SCENE,
            "sequence": os.path.basename(curr_video_path).rsplit(".", 1)[0],
            "annotation": new_annotation,
            "start_frame_id": curr_start
        }

        if len(splits) == 1:
            out_dict["end_frame_id"] = get_end_frame(curr_video_path)
            curr_start = 0
            if video_paths:
                curr_video_path = video_paths.pop(0)
            else: 
                break
        else:
            curr_start = splits.pop(0)
            out_dict["end_frame_id"] = curr_start - 1

        final_annotations.append(out_dict)
        new_annotations += 1
        player = VideoPlayerWidget(curr_video_path, curr_start, splits[0])
        player.setWindowTitle('Matcher')
        player.show()
    elif choice == '3':
        if orig_annotations:
            curr_annotation = orig_annotations.pop(0)
        else:
            curr_annotation = None
    elif choice == '4':
        frame = int(input("Enter frame to cut at: "))
        if frame > curr_start:
            bisect.insort(splits, frame)
        player = VideoPlayerWidget(curr_video_path, curr_start, splits[0])
        player.setWindowTitle('Matcher')
        player.show()
    elif choice == '5':
        if len(splits) > 1:
            splits.pop(0)
            player = VideoPlayerWidget(curr_video_path, curr_start, splits[0])
            player.setWindowTitle('Matcher')
            player.show()
        else:
            print("No splits to remove")
    
    # input("Press Enter to continue...")  # Wait for user confirmation
    print('='*24)
    # send_control_space()  # Send ctrl+space to start video recording

json_object = json.dumps(final_annotations, indent=4)

with open(OUTPUT_PATH, "w") as outfile:
    outfile.write(json_object)
