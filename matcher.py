import os
import json
import cv2
from moviepy.editor import *
import math
import bisect
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QSlider, QPushButton, QLineEdit, QHBoxLayout, QTextEdit
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap

# file with current annotations
# TEXT_FILE_PATH = "brics-mini-annotation-gui/alex_0620/scene17.txt"
TEXT_FILE_PATH = "/Users/alexj/Documents/matcher/brics-mini-annotation-gui/scripts.txt"
# True if processing a scene#.txt file, False if processing a scripts.txt file
PROCESSING_SCENE_TXT = False
# path to folder with videos
VIDEO_FOLDER_PATH = "brics-mini/2024-06-18/mano"
# output json path
OUTPUT_PATH = "reannotate/reannotation_tmp/tool/2024-06-18-action-alex-tool.json"
# scene string for annotations in the output json
SCENE="2024-06-18-action-alex-tool"
# specifies the start and end video files (for folders with multiple scenes)
# just put 0 and None otherwise 
START=339
END=None

actions = []

class VideoPlayerWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.curr_video_num = 0
        self.final_annotations = []
        self.orig_annotations = load_text(TEXT_FILE_PATH)
        if len(orig_annotations) > 0:
            self.curr_annotation = orig_annotations.pop(0)
        else: self.curr_annotation = "None"
        self.video_paths = load_video_paths(VIDEO_FOLDER_PATH)
        self.curr_video_path = video_paths.pop(0)
        self.cap = cv2.VideoCapture(self.curr_video_path)

        self.new_annotations = 0
        self.deleted_annotations = 0
        self.splits = [math.inf]
        self.curr_start = 0

        # Video metadata
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.video_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.video_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # GUI components
        self.video_label = QLabel(self)
        self.video_label.setFixedSize(1036, 500)  # Set fixed size for video display

        self.slider = QSlider(Qt.Horizontal, self)
        self.start = 0
        self.end = self.frame_count - 1
        self.slider.setMinimum(self.start)
        self.slider.setMaximum(self.end)
        self.slider.sliderMoved.connect(self.seek_video)

        # New Input Boxes
        self.input_box = QLineEdit(self)
        self.input_box.returnPressed.connect(self.handle_input)
        self.input_box.hide()
        self.input_box.textChanged.connect(self.on_text_changed)
        self.input_is_annotation = False
        self.input_length = 0

        # Play/Pause Button
        self.play_button = QPushButton('Pause', self)
        self.play_button.clicked.connect(self.toggle_play_pause)

        # Back Frame Button
        self.back_button = QPushButton('-1 Frame', self)
        self.back_button.clicked.connect(self.back_frame)

        # Forward Frame Button
        self.forward_button = QPushButton('+1 Frame', self)
        self.forward_button.clicked.connect(self.forward_frame)

        # Match Button
        self.match_button = QPushButton('Match Annotation', self)
        self.match_button.clicked.connect(self.match_annotation)

        # Add Button
        self.add_button = QPushButton('Add Annotation', self)
        self.add_button.clicked.connect(self.add_annotation)

        # Remove Button
        self.remove_button = QPushButton('Remove Annotation', self)
        self.remove_button.clicked.connect(self.remove_annotation)

        # Add Split Button
        self.add_split_button = QPushButton('Split Video', self)
        self.add_split_button.clicked.connect(self.add_split)

        # Remove Split Button
        self.remove_split_button = QPushButton('Remove Split', self)
        self.remove_split_button.clicked.connect(self.remove_split)

        self.annotation_label = QLabel()
        self.annotation_label.setText(self.curr_annotation)

        # Layouts
        self.control_layout = QHBoxLayout()
        self.control_layout.addWidget(self.play_button)
        self.control_layout.addWidget(self.forward_button)
        self.control_layout.addWidget(self.back_button)

        self.annotate_layout = QHBoxLayout()
        self.annotate_layout.addWidget(self.match_button)
        self.annotate_layout.addWidget(self.add_button)
        self.annotate_layout.addWidget(self.remove_button)
        self.annotate_layout.addWidget(self.add_split_button)
        self.annotate_layout.addWidget(self.remove_split_button)

        layout = QVBoxLayout()
        layout.addWidget(self.video_label)
        layout.addWidget(self.slider)
        layout.addWidget(self.annotation_label)
        layout.addLayout(self.control_layout)
        layout.addLayout(self.annotate_layout)
        layout.addWidget(self.input_box)
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
    
    def back_frame(self):
        if self.current_frame > self.start:
            self.seek_video(self.current_frame - 1)

    def forward_frame(self):
        if self.current_frame < self.end:
            self.seek_video(self.current_frame + 1)

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
    
    def change_video(self):
        """Change the video being played."""
        # Release the current video capture
        self.cap.release()

        # Load the new video
        self.cap = cv2.VideoCapture(self.curr_video_path)
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.video_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.video_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Update the slider with the new frame count
        self.timer.stop()
        self.start = self.curr_start
        self.end = min(self.splits[0], self.frame_count - 1)
        self.slider.blockSignals(True)
        self.slider.setMinimum(self.start)
        self.slider.setMaximum(self.end)
        self.slider.setValue(self.start)
        self.slider.blockSignals(False)

        # Reset the video display
        self.seek_video(self.start)
        self.is_paused = False
        self.timer.start(int(1000 / self.fps))
        self.play_button.setText('Pause')
    
    def match_annotation(self):
        out_dict = {
            "scene": SCENE,
            "sequence": os.path.basename(self.curr_video_path).rsplit(".", 1)[0],
            "annotation": self.curr_annotation,
            "start_frame_id": self.curr_start
        }
        # if there are no splits left
        if len(self.splits) == 1:
            out_dict["end_frame_id"] = get_end_frame(self.curr_video_path)
            self.curr_start = 0
            self.final_annotations.append(out_dict)
            if self.video_paths:
                self.curr_video_path = self.video_paths.pop(0)
            else: 
                self.write_to_file()
        else:
            self.curr_start = self.splits.pop(0)
            out_dict["end_frame_id"] = self.curr_start - 1
            self.final_annotations.append(out_dict)

        if self.orig_annotations:
            self.curr_annotation = self.orig_annotations.pop(0)
        else: 
            self.curr_annotation = None
        self.curr_video_num += 1

        self.change_video()
        self.annotation_label.setText(self.curr_annotation)

    def add_annotation(self):
        self.hide_annotate_buttons()
        self.input_box.show()
        self.input_box.setPlaceholderText("Enter annotation")
        self.input_is_annotation = True
        self.input_length = 0


    def remove_annotation(self):
        if self.orig_annotations:
            self.curr_annotation = self.orig_annotations.pop(0)
            self.annotation_label.setText(self.curr_annotation)
        else:
            self.curr_annotation = None
            self.annotation_label.setText("None")

    def add_split(self):
        self.hide_annotate_buttons()
        self.input_box.show()
        self.input_box.setPlaceholderText("Enter split frame")
        self.input_is_annotation = False
        self.input_length = 0
        

    def remove_split(self):
        if len(self.splits) > 1:
            self.splits.pop(0)
            self.change_video()
        else:
            print("No splits to remove")

    def handle_input(self):
        if self.input_is_annotation:
            new_annotation = self.input_box.text()
            self.input_box.clear()
            self.input_box.hide()

            out_dict = {
                "scene": SCENE,
                "sequence": os.path.basename(self.curr_video_path).rsplit(".", 1)[0],
                "annotation": new_annotation,
                "start_frame_id": self.curr_start
            }

            if len(self.splits) == 1:
                out_dict["end_frame_id"] = get_end_frame(self.curr_video_path)
                self.curr_start = 0
                self.final_annotations.append(out_dict)
                if self.video_paths:
                    self.curr_video_path = self.video_paths.pop(0)
                else: 
                    self.write_to_file()
            else:
                self.curr_start = self.splits.pop(0)
                out_dict["end_frame_id"] = self.curr_start - 1
                self.final_annotations.append(out_dict)

            self.new_annotations += 1
            self.show_annotate_buttons()
            self.change_video()
        else:
            """Handle the input from the input box when Enter is pressed."""
            input_text = self.input_box.text()
            self.input_box.clear()
            self.input_box.hide()

            frame = int(input_text)
            if frame > self.curr_start:
                bisect.insort(self.splits, frame)
            self.show_annotate_buttons()
            self.change_video()
    
    def write_to_file(self):
        json_object = json.dumps(self.final_annotations, indent=4)

        with open(OUTPUT_PATH, "w") as outfile:
            outfile.write(json_object)
        
        sys.exit(app.exec_())
        
    
    def hide_annotate_buttons(self):
        self.match_button.hide()
        self.add_button.hide()
        self.remove_button.hide()
        self.add_split_button.hide()
        self.remove_split_button.hide()
    
    def show_annotate_buttons(self):
        self.match_button.show()
        self.add_button.show()
        self.remove_button.show()
        self.add_split_button.show()
        self.remove_split_button.show()
    
    def on_text_changed(self):
        current_text = self.input_box.text()
        if len(current_text) > self.input_length:  # Check if there's text to delete
            self.input_box.setText(current_text[:-1])
        self.input_length = len(current_text)


def load_text(path):
    if os.path.exists(path):
        with open(path, 'r') as f:
            if PROCESSING_SCENE_TXT:
                lines = []
                for line in f:
                    x = line.split("\t")
                    if len(x) > 1:
                        lines.append(x[1])
                    else:
                        lines.append(line)
                return [line for line in lines]
            return [line for line in f]
    return ["None"]

def load_video_paths(path):
    files = [os.path.join(path, file) for file in sorted(os.listdir(path))]
    return list(filter(lambda f: f.endswith(".mp4"), files))[START:END]

def get_end_frame(path):
    cap = cv2.VideoCapture(path)
    return int(cap.get(cv2.CAP_PROP_FRAME_COUNT))


def append_id(path, id):
  return "{0}_{2}{1}".format(*os.path.splitext(path) + (id,))

app = QApplication(sys.argv)
curr_video_num = 0
final_annotations = []
orig_annotations = load_text(TEXT_FILE_PATH)
curr_annotation = orig_annotations.pop(0)
video_paths = load_video_paths(VIDEO_FOLDER_PATH)
curr_video_path = video_paths.pop(0)

player = VideoPlayerWidget()
player.setWindowTitle('Matcher')
player.show()
sys.exit(app.exec_())
'''
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

        player.change_video(curr_video_path, curr_start, splits[0])
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
        player.change_video(curr_video_path, curr_start, splits[0])
    elif choice == '3':
        if orig_annotations:
            curr_annotation = orig_annotations.pop(0)
        else:
            curr_annotation = None
    elif choice == '4':
        frame = int(input("Enter frame to cut at: "))
        if frame > curr_start:
            bisect.insort(splits, frame)
        player.change_video(curr_video_path, curr_start, splits[0])
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
'''
