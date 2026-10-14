import sys
import os
import cv2
import subprocess
import urllib.request
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QSettings, QBuffer, QByteArray
from PyQt5.QtGui import QImage, QPixmap, QKeyEvent, QMovie
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QSlider, QLabel, QFileDialog, QListWidget,
                             QTableWidget, QTableWidgetItem, QLineEdit, QComboBox, QDialog,
                             QDialogButtonBox, QFormLayout, QAbstractItemView, QMessageBox,
                             QListWidgetItem)
from dotenv import load_dotenv
import exercise_backend as backend

VIDEO_EXTENSIONS = (".mp4", ".avi", ".mov", ".mkv")
GIF_COL = 3


class GifViewerDialog(QDialog):
    """Shows a gif from a URL or a local file path."""
    def __init__(self, title, source, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        layout = QVBoxLayout(self)
        label = QLabel()
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        if source.lower().startswith("http"):
            data = urllib.request.urlopen(source, timeout=20).read()
            self._bytes = QByteArray(data)
            self._buffer = QBuffer(self._bytes)
            self._buffer.open(QBuffer.ReadOnly)
            self.movie = QMovie(self._buffer, QByteArray(b"gif"))
        else:
            self.movie = QMovie(source)
        label.setMovie(self.movie)
        self.movie.start()


class NewExerciseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Exercise")
        self.resize(560, 700)
        form = QFormLayout(self)
        self.name_edit = QLineEdit()
        form.addRow("Name", self.name_edit)
        self.equipment = self._checklist(backend.EQUIPMENT)
        form.addRow("Equipment", self.equipment)
        self.pfcs = self._checklist(backend.PHYSICAL_FITNESS_COMPONENTS)
        form.addRow("Physical fitness components", self.pfcs)
        self.categories = self._checklist(backend.MOVEMENT_CATEGORIES)
        form.addRow("Movement categories", self.categories)
        self.muscles = self._checklist(backend.MUSCLES)
        form.addRow("Primary muscles", self.muscles)
        self.doubled = QComboBox()
        self.doubled.addItems(["no", "yes"])
        form.addRow("Resistance doubled", self.doubled)
        self.origin_edit = QLineEdit(backend.DEFAULT_ORIGIN)
        form.addRow("Origin", self.origin_edit)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._validate)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    @staticmethod
    def _checklist(values):
        widget = QListWidget()
        widget.setMinimumHeight(110)
        for v in values:
            item = QListWidgetItem(v)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            widget.addItem(item)
        return widget

    @staticmethod
    def _checked(widget):
        return [widget.item(i).text() for i in range(widget.count())
                if widget.item(i).checkState() == Qt.Checked]

    def _validate(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "New Exercise", "Name is required.")
            return
        self.accept()

    def values(self):
        return dict(name=self.name_edit.text(),
                    equipment=self._checked(self.equipment),
                    pfcs=self._checked(self.pfcs),
                    movement_categories=self._checked(self.categories),
                    primary_muscles=self._checked(self.muscles),
                    resistance_doubled=self.doubled.currentText() == "yes",
                    origin=self.origin_edit.text())

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
        self.setGeometry(50, 50, 1600, 850)
        self.settings = QSettings("LifeTimeLines", "v2g")
        self.exercises = []
        self.current_exercise = None
        self.current_gif_path = None
        self.gif_movie = None

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

        window_layout.addLayout(self.build_exercise_panel(), stretch=3)
        window_layout.addLayout(left_layout, stretch=4)
        right_layout.insertWidget(0, self.build_video_and_gif_panel(), stretch=3)
        window_layout.addLayout(right_layout, stretch=2)
        
        # Enforce strong keyboard monitoring focus to global window
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()

    def build_exercise_panel(self):
        layout = QVBoxLayout()
        header = QHBoxLayout()
        header.addWidget(QLabel("Exercises"))
        self.btn_new_exercise = QPushButton("New Exercise...")
        self.btn_new_exercise.clicked.connect(self.new_exercise)
        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.clicked.connect(self.load_exercises)
        header.addStretch()
        header.addWidget(self.btn_new_exercise)
        header.addWidget(self.btn_refresh)
        layout.addLayout(header)

        filters = QHBoxLayout()
        self.name_filter = QLineEdit()
        self.name_filter.setPlaceholderText("Filter name...")
        self.name_filter.textChanged.connect(self.apply_exercise_filters)
        self.origin_filter = QComboBox()
        self.origin_filter.addItem("All origins")
        self.origin_filter.currentIndexChanged.connect(self.apply_exercise_filters)
        filters.addWidget(self.name_filter, stretch=2)
        filters.addWidget(self.origin_filter, stretch=1)
        layout.addLayout(filters)

        self.exercise_table = QTableWidget(0, 4)
        self.exercise_table.setHorizontalHeaderLabels(["Id", "Name", "Origin", "Gif"])
        self.exercise_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.exercise_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.exercise_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.exercise_table.verticalHeader().setVisible(False)
        self.exercise_table.horizontalHeader().setStretchLastSection(False)
        self.exercise_table.setColumnWidth(0, 90)
        self.exercise_table.setColumnWidth(1, 220)
        self.exercise_table.setColumnWidth(2, 70)
        self.exercise_table.setColumnWidth(3, 50)
        self.exercise_table.setFocusPolicy(Qt.NoFocus)
        self.exercise_table.itemSelectionChanged.connect(self.on_exercise_selected)
        self.exercise_table.cellClicked.connect(self.on_exercise_cell_clicked)
        layout.addWidget(self.exercise_table)

        self.current_exercise_label = QLabel("Exercise in focus: (none)")
        self.current_exercise_label.setStyleSheet("font-weight: bold;")
        self.current_exercise_label.setWordWrap(True)
        layout.addWidget(self.current_exercise_label)
        return layout

    def build_video_and_gif_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        folder_row = QHBoxLayout()
        folder_row.addWidget(QLabel("Videos"))
        self.btn_folder = QPushButton("Choose Folder...")
        self.btn_folder.clicked.connect(self.choose_video_folder)
        self.btn_folder.setFocusPolicy(Qt.NoFocus)
        folder_row.addStretch()
        folder_row.addWidget(self.btn_folder)
        layout.addLayout(folder_row)

        self.video_list_widget = QListWidget()
        self.video_list_widget.setFocusPolicy(Qt.NoFocus)
        self.video_list_widget.itemClicked.connect(self.on_video_selected)
        layout.addWidget(self.video_list_widget, stretch=1)

        layout.addWidget(QLabel("Generated GIF (in focus):"))
        self.gif_label = QLabel("No GIF generated yet")
        self.gif_label.setAlignment(Qt.AlignCenter)
        self.gif_label.setMinimumHeight(240)
        self.gif_label.setStyleSheet("background-color: #222; color: white;")
        layout.addWidget(self.gif_label, stretch=2)

        self.btn_link = QPushButton("Upload GIF && Link to Exercise")
        self.btn_link.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold;")
        self.btn_link.setFocusPolicy(Qt.NoFocus)
        self.btn_link.clicked.connect(self.link_gif_to_exercise)
        layout.addWidget(self.btn_link)
        return panel

    # ---- Exercises ----
    def load_exercises(self):
        try:
            self.exercises = backend.get_exercises()
        except Exception as e:
            QMessageBox.critical(self, "Exercises", f"Could not load exercises:\n{e}")
            return
        self.refresh_origin_filter()
        self.apply_exercise_filters()

    def refresh_origin_filter(self):
        current = self.origin_filter.currentText()
        origins = sorted({r["origin"] for r in self.exercises if r["origin"]})
        self.origin_filter.blockSignals(True)
        self.origin_filter.clear()
        self.origin_filter.addItem("All origins")
        self.origin_filter.addItems(origins)
        idx = self.origin_filter.findText(current)
        self.origin_filter.setCurrentIndex(max(idx, 0))
        self.origin_filter.blockSignals(False)

    def apply_exercise_filters(self):
        text = self.name_filter.text().strip().lower()
        origin = self.origin_filter.currentText() if self.origin_filter.currentIndex() > 0 else None
        visible = [r for r in self.exercises
                   if (not text or text in r["name"].lower()) and (origin is None or r["origin"] == origin)]
        self.exercise_table.blockSignals(True)
        self.exercise_table.setRowCount(len(visible))
        focus_id = self.current_exercise["id"] if self.current_exercise else None
        for i, r in enumerate(visible):
            self.exercise_table.setItem(i, 0, QTableWidgetItem(r["id"]))
            self.exercise_table.setItem(i, 1, QTableWidgetItem(r["name"]))
            self.exercise_table.setItem(i, 2, QTableWidgetItem(r["origin"]))
            gif_item = QTableWidgetItem("view" if r["gif"] else "")
            if r["gif"]:
                gif_item.setForeground(Qt.blue)
                gif_item.setToolTip(r["gif"])
            self.exercise_table.setItem(i, GIF_COL, gif_item)
            self.exercise_table.item(i, 0).setData(Qt.UserRole, r["id"])
            if r["id"] == focus_id:
                self.exercise_table.selectRow(i)
        self.exercise_table.blockSignals(False)

    def row_for_id(self, exercise_id):
        return next((r for r in self.exercises if r["id"] == exercise_id), None)

    def on_exercise_selected(self):
        rows = self.exercise_table.selectionModel().selectedRows()
        if not rows:
            return
        self.set_current_exercise(self.row_for_id(self.exercise_table.item(rows[0].row(), 0).data(Qt.UserRole)))

    def set_current_exercise(self, row):
        self.current_exercise = row
        if row:
            self.current_exercise_label.setText(f"Exercise in focus: {row['name']} ({row['id']})")
        else:
            self.current_exercise_label.setText("Exercise in focus: (none)")

    def on_exercise_cell_clicked(self, row, col):
        if col != GIF_COL:
            return
        r = self.row_for_id(self.exercise_table.item(row, 0).data(Qt.UserRole))
        if r and r["gif"]:
            try:
                GifViewerDialog(r["name"], r["gif"], self).exec_()
            except Exception as e:
                QMessageBox.warning(self, "GIF", f"Could not display gif:\n{e}")

    def new_exercise(self):
        dlg = NewExerciseDialog(self)
        if dlg.exec_() != QDialog.Accepted:
            return
        try:
            row = backend.create_exercise(**dlg.values())
        except Exception as e:
            QMessageBox.critical(self, "New Exercise", f"Could not create exercise:\n{e}")
            return
        self.exercises.append(row)
        self.exercises.sort(key=lambda r: r["name"].lower())
        self.name_filter.clear()
        self.refresh_origin_filter()
        self.set_current_exercise(row)
        self.apply_exercise_filters()
        self.exercise_table.scrollToItem(self.exercise_table.currentItem())

    # ---- Video list ----
    def choose_video_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Video Folder", self.settings.value("video_folder", ""))
        if folder:
            self.settings.setValue("video_folder", folder)
            self.populate_video_list()

    def populate_video_list(self):
        self.video_list_widget.clear()
        folder = self.settings.value("video_folder", "")
        if not folder or not os.path.isdir(folder):
            return
        for name in sorted(os.listdir(folder), key=str.lower):
            if name.lower().endswith(VIDEO_EXTENSIONS):
                item = QListWidgetItem(name)
                item.setData(Qt.UserRole, os.path.join(folder, name))
                self.video_list_widget.addItem(item)

    def on_video_selected(self, item):
        self.load_video(item.data(Qt.UserRole))

    # ---- GIF preview and linking ----
    def show_gif_preview(self, path):
        self.current_gif_path = path
        if self.gif_movie:
            self.gif_movie.stop()
        self.gif_movie = QMovie(path)
        self.gif_label.setMovie(self.gif_movie)
        self.gif_movie.start()

    def link_gif_to_exercise(self):
        if not self.current_exercise:
            QMessageBox.information(self, "Link GIF", "Select or create an exercise first.")
            return
        if not self.current_gif_path or not os.path.isfile(self.current_gif_path):
            QMessageBox.information(self, "Link GIF", "Generate a GIF first.")
            return
        ex = self.current_exercise
        try:
            blob_name = backend.gif_blob_name(ex["name"])
            msg = f"Upload as '{blob_name}' and link to '{ex['name']}'?"
            if ex["gif"]:
                msg += "\n\nThis exercise already has a gif; it will be replaced."
            if QMessageBox.question(self, "Link GIF", msg) != QMessageBox.Yes:
                return
            uri = backend.upload_gif_and_link(ex, self.current_gif_path)
        except Exception as e:
            QMessageBox.critical(self, "Link GIF", f"Upload failed:\n{e}")
            return
        self.marks_list_widget.addItem(f"Linked: {uri}")
        self.apply_exercise_filters()

    def open_video(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Video File", "", "Videos (*.mp4 *.avi *.mov *.mkv)")
        if file_path:
            self.load_video(file_path)

    def load_video(self, file_path):
        if self.cap is not None:
            self.cap.release()
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

        self.output_gif_path = os.path.splitext(self.video_path)[0] + "_optimized.gif"
        input_file = f'"{self.video_path}"'
        output_file = f'"{self.output_gif_path}"'
        
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
        if status_text.startswith("GIF generated") and os.path.isfile(self.output_gif_path):
            self.show_gif_preview(self.output_gif_path)
        self.setFocus()
    # Framework Keyboard Event Overrides
    def keyPressEvent(self, event):
        # FIX 1: Explicit key intercept mappings to avoid widget context confusion
        if event.key() in (Qt.Key_Left, Qt.Key_Right):
            if self.cap is not None:
                # Ctrl jumps about one second of video; otherwise a single frame
                step = max(1, int(round(self.fps))) if event.modifiers() & Qt.ControlModifier else 1
                if event.key() == Qt.Key_Left:
                    target = max(0, self.current_frame_idx - step)
                else:
                    target = min(self.total_frames - 1, self.current_frame_idx + step)
                if target != self.current_frame_idx:
                    self.show_frame(target)
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
    try:
        load_dotenv('../.env')
        backend.init()
        window.load_exercises()
    except Exception as e:
        QMessageBox.warning(window, "Azure", f"Azure storage unavailable; exercise features disabled:\n{e}")
    window.populate_video_list()
    sys.exit(app.exec_())
