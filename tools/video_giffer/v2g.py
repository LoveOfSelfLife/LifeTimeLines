import sys
import os
import cv2
import subprocess
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QKeyEvent
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QSlider, QLabel, QFileDialog, QListWidget)

# Custom QSlider Subclass to implement instant click-to-jump behavior
class JumpSlider(QSlider):
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Calculate exact relative percentage of click along the slider's width
            val = self.minimum() + ((self.maximum() - self.minimum()) * event.x()) / self.width()
            self.setValue(int(round(val)))
            event.accept()
        super().mousePressEvent(event)

# Background Worker Thread to run FFmpeg without freezing the GUI
class FFmpegWorker(QThread):
    finished_signal = pyqtSignal(str)

    def __init__(self, command):
        super().__init__()
        self.command = command

    def run(self):
        try:
            subprocess.run(self.command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.finished_signal.emit("GIF generated successfully!")
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode().strip().split('\n')[-1]
            self.finished_signal.emit(f"FFmpeg Error: {error_msg}")

class VideoScrubberApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Marker Tool to FFmpeg GIF")
        self.setGeometry(100, 100, 950, 700)

        # Video State Variables
        self.video_path = None
        self.cap = None
        self.total_frames = 0
        self.fps = 0.0
        self.current_frame_idx = 0
        
        # Collection array for all frame markers
        self.marked_frames = set()
        self.worker = None

        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        window_layout = QHBoxLayout(main_widget)
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        # Left Column: Video Screen Display
        self.video_label = QLabel("No Video Loaded")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background-color: black; color: white; font-size: 16px;")
        self.video_label.setMinimumSize(640, 360)
        left_layout.addWidget(self.video_label, stretch=1)

        # Left Column: FIX 2 - Instantly Jump Slider Replacement
        self.slider = JumpSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(0)
        self.slider.valueChanged.connect(self.scrub_video)
        # Prevent slider from consuming spacebar focus
        self.slider.setFocusPolicy(Qt.NoFocus)
        left_layout.addWidget(self.slider)

        # Left Column: Throttling Timer to prevent OpenCV freeze drops
        self.scrub_timer = QTimer()
        self.scrub_timer.setSingleShot(True)
        self.scrub_timer.timeout.connect(self.delayed_frame_load)
        self.target_scrub_frame = 0

        # Left Column: Time Metadata Display
        self.meta_label = QLabel("Time: 00:00:00.000 / 00:00:00.000  (Frame: 0/0)")
        self.meta_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.meta_label)

        # Left Column: Action Control Row Layout
        control_layout = QHBoxLayout()
        self.btn_open = QPushButton("Open Video")
        self.btn_open.clicked.connect(self.open_video)
        self.btn_open.setFocusPolicy(Qt.NoFocus) # Prevent button focus theft
        
        self.btn_mark = QPushButton("Mark Point (Space)")
        self.btn_mark.clicked.connect(self.mark_current_point)
        self.btn_mark.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold;")
        self.btn_mark.setFocusPolicy(Qt.NoFocus) # Prevent button focus theft
        
        self.btn_clear = QPushButton("Clear Marks")
        self.btn_clear.clicked.connect(self.clear_marks)
        self.btn_clear.setStyleSheet("background-color: #e74c3c; color: white;")
        self.btn_clear.setFocusPolicy(Qt.NoFocus) # Prevent button focus theft
        
        self.btn_export = QPushButton("Process & Create GIF")
        self.btn_export.clicked.connect(self.export_and_run_ffmpeg)
        self.btn_export.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        self.btn_export.setFocusPolicy(Qt.NoFocus) # Prevent button focus theft

        control_layout.addWidget(self.btn_open)
        control_layout.addWidget(self.btn_mark)
        control_layout.addWidget(self.btn_clear)
        control_layout.addWidget(self.btn_export)
        left_layout.addLayout(control_layout)

        # Right Column: Sidebar List Window Panel
        list_header = QLabel("Logged Timestamps:")
        list_header.setStyleSheet("font-weight: bold; font-size: 13px;")
        right_layout.addWidget(list_header)
        
        self.marks_list_widget = QListWidget()
        self.marks_list_widget.setMinimumWidth(240)
        self.marks_list_widget.setFocusPolicy(Qt.NoFocus) # Prevent widget focus theft
        right_layout.addWidget(self.marks_list_widget)

        window_layout.addLayout(left_layout, stretch=3)
        window_layout.addLayout(right_layout, stretch=1)
        
        # Enforce strong keyboard monitoring focus to global window
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()

    def open_video(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Video File", "", "Videos (*.mp4 *.avi *.mov *.mkv)")
        if not file_path:
            return
        self.video_path = file_path
        self.cap = cv2.VideoCapture(file_path)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        if self.fps <= 0:
            self.fps = 25.0
        self.slider.setMaximum(self.total_frames - 1)
        self.current_frame_idx = 0
        self.slider.setValue(0)
        self.clear_marks()
        self.show_frame(self.current_frame_idx)
        self.setFocus() # Re-claim focus explicitly after dialog closes

    def show_frame(self, frame_number):
        if self.cap is None or not self.cap.isOpened():
            return
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = self.cap.read()
        if ret:
            self.current_frame_idx = frame_number
            
            # Update slider value without triggering extra feedback cycles
            self.slider.blockSignals(True)
            self.slider.setValue(frame_number)
            self.slider.blockSignals(False)
            
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_img)
            scaled_pixmap = pixmap.scaled(self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.video_label.setPixmap(scaled_pixmap)
            self.update_metadata_text()

    def scrub_video(self):
        self.target_scrub_frame = self.slider.value()
        self.scrub_timer.start(15) 

    def delayed_frame_load(self):
        self.show_frame(self.target_scrub_frame)

    def mark_current_point(self):
        if self.cap is None:
            return
        if self.current_frame_idx not in self.marked_frames:
            self.marked_frames.add(self.current_frame_idx)
            self.update_ui_list()
        self.setFocus() # Guarantee focus stays tied here

    def clear_marks(self):
        self.marked_frames.clear()
        self.update_ui_list()
        self.setFocus()

    def update_ui_list(self):
        self.marks_list_widget.clear()
        sorted_frames = sorted(list(self.marked_frames))
        for idx, frame in enumerate(sorted_frames, 1):
            timestamp_str = self.frame_to_timestamp(frame)
            self.marks_list_widget.addItem(f"{idx}. {timestamp_str} (f:{frame})")

    def frame_to_timestamp(self, frame_idx):
        if self.fps == 0:
            return "00:00:00.000"
        total_seconds = frame_idx / self.fps
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        milliseconds = int(round((total_seconds - int(total_seconds)) * 1000))
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"

    def update_metadata_text(self):
        current_time_str = self.frame_to_timestamp(self.current_frame_idx)
        total_time_str = self.frame_to_timestamp(self.total_frames)
        self.meta_label.setText(
            f"Time: {current_time_str} / {total_time_str}  (Frame: {self.current_frame_idx}/{self.total_frames})"
        )

    def export_and_run_ffmpeg(self):
        if not self.marked_frames:
            self.marks_list_widget.addItem("Error: No marks set.")
            return

        sorted_frames = sorted(list(self.marked_frames))
        select_string = "+".join([f"eq(n\\,{f})" for f in sorted_frames])
        
        pts_expressions = []
        base_time = sorted_frames[0] / self.fps
        for idx, frame in enumerate(sorted_frames):
            current_time = frame / self.fps
            delta_from_start = current_time - base_time
            pts_expressions.append(f"eq(N\\,{idx})*{delta_from_start}/TB")
        setpts_string = "+".join(pts_expressions)

        input_file = f'"{self.video_path}"'
        output_file = f'"{os.path.splitext(self.video_path)[0]}_optimized.gif"'
        
        ffmpeg_cmd = (
            f'ffmpeg -i {input_file} -filter_complex '
            f'"[0:v]select=\'{select_string}\','
            f'setpts=\'{setpts_string}\','
            f'scale=480:-1:flags=lanczos,split[s0][s1];'
            f'[s0]palettegen[p];[s1][p]paletteuse=dither=bayer:bayer_scale=3:diff_mode=rectangle" '
            f'-y {output_file}'
        )
        print("\n=== GENERATED & EXECUTING FFMPEG PIPELINE ===")
        print(ffmpeg_cmd)
        print("=============================================\n")
        QApplication.clipboard().setText(ffmpeg_cmd)
        self.marks_list_widget.addItem("Processing GIF...")
        self.btn_export.setEnabled(False)
        self.worker = FFmpegWorker(ffmpeg_cmd)
        self.worker.finished_signal.connect(self.on_ffmpeg_finished)
        self.worker.start()
    def on_ffmpeg_finished(self, status_text):
        self.marks_list_widget.addItem(status_text)
        self.btn_export.setEnabled(True)
        self.setFocus()
    # Framework Keyboard Event Overrides
    def keyPressEvent(self, event):
        # FIX 1: Explicit key intercept mappings to avoid widget context confusion
        if event.key() == Qt.Key_Left:
            if self.current_frame_idx > 0:
                self.show_frame(self.current_frame_idx - 1)
            event.accept()
        elif event.key() == Qt.Key_Right:
            if self.current_frame_idx < self.total_frames - 1:
                self.show_frame(self.current_frame_idx + 1)
            event.accept()
        elif event.key() == Qt.Key_Space:
            self.mark_current_point()
            event.accept()
        else:
            super().keyPressEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.video_path:
            self.show_frame(self.current_frame_idx)
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoScrubberApp()
    window.show()
    sys.exit(app.exec_())
