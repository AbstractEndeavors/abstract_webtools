# -------------------------------------------------
# threaded thumbnail worker
# -------------------------------------------------
class ThumbWorker(QtCore.QRunnable):
    def __init__(self, path, size, signal):
        super().__init__()
        self.path, self.size, self.signal = path, size, signal

    def run(self):
        try:
            pm = QPixmap()
            if Path(self.path).exists():
                pm.load(self.path)
            else:
                b64 = postRequest(SERVER, "thumbnail", {"path": self.path, "size": self.size})
                if b64:
                    pm.loadFromData(base64.b64decode(b64))
            if not pm.isNull():
                pm = pm.scaled(self.size, self.size,
                               QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                               QtCore.Qt.TransformationMode.SmoothTransformation)
                self.signal.emit(self.path, pm)
        except Exception:
            pass


# -------------------------------------------------
# custom delegate for folder thumbnails
# -------------------------------------------------
class FolderPreviewDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, cache, signal, thread_pool):
        super().__init__()
        self.cache = cache
        self.signal = signal
        self.thread_pool = thread_pool
        self.size = 48  # thumbnail size
        self.signal.connect(self._thumb_ready)

    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        path = index.model().filePath(index)
        if not Path(path).is_dir():
            return

        rect = option.rect
        thumb_rects = self._thumb_positions(rect)
        thumbs = self.cache.get(path)

        if thumbs:
            for pm, r in zip(thumbs, thumb_rects):
                if isinstance(pm, QPixmap) and not pm.isNull():
                    painter.drawPixmap(r, pm)
        else:
            # schedule preview build
            self._load_previews(path)

    def _thumb_positions(self, rect):
        """Compute positions for 3 thumbnails on the right side of a row."""
        margin = 4
        size = self.size
        x0 = rect.right() - (size + margin) * 3 - margin
        y0 = rect.top() + (rect.height() - size) // 2
        return [QRect(x0 + i * (size + margin), y0, size, size) for i in range(3)]

    def _load_previews(self, folder):
        if folder in self.cache:
            return
        files = [p for p in Path(folder).iterdir() if p.suffix.lower() in IMAGE_EXTS]
        if not files:
            return
        small = files[:3]
        self.cache[folder] = [None] * len(small)
        for i, f in enumerate(small):
            worker = ThumbWorker(str(f), self.size, self.signal)
            worker.index = (folder, i)
            self.thread_pool.start(worker)

    @QtCore.pyqtSlot(str, QPixmap)
    def _thumb_ready(self, path, pm):
        folder = str(Path(path).parent)
        if folder in self.cache:
            thumbs = self.cache[folder]
            for i, existing in enumerate(thumbs):
                # fill first None slot
                if existing is None:
                    thumbs[i] = pm
                    break


# -------------------------------------------------
# main viewer
# -------------------------------------------------
class DirectoryImageViewer(QtWidgets.QWidget):
    thumb_ready = QtCore.pyqtSignal(str, QPixmap)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Directory Image Viewer with Folder Previews")
        self.resize(1280, 900)
        self.thread_pool = QtCore.QThreadPool.globalInstance()
        self.thread_pool.setMaxThreadCount(os.cpu_count() or 8)
        self.pix_cache = {}
        self.folder_cache = {}  # path -> list of 3 pixmaps

        # --- Tree (lazy QFileSystemModel) ---
        self.model = QFileSystemModel()
        self.model.setRootPath(ROOT_PATH)
        self.model.setNameFilters(["*.jpg", "*.jpeg", "*.png", "*.bmp", "*.gif"])
        self.model.setNameFilterDisables(False)

        self.tree = QtWidgets.QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(ROOT_PATH))
        self.tree.setHeaderHidden(True)
        self.tree.setAnimated(True)
        self.tree.setIndentation(16)
        self.tree.setItemDelegate(FolderPreviewDelegate(self.folder_cache, self.thumb_ready, self.thread_pool))
        self.tree.clicked.connect(self.on_folder_selected)

        # --- Image preview ---
        self.preview = QtWidgets.QLabel("Select an image folder", alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        self.preview.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        self.preview.setMinimumSize(400, 300)

        # --- Thumbnail flow ---
        self.thumb_widget = QtWidgets.QWidget()
        self.thumb_layout = QtWidgets.QGridLayout(self.thumb_widget)
        self.thumb_layout.setContentsMargins(6, 6, 6, 6)
        self.thumb_layout.setSpacing(6)
        self.thumb_scroll = QtWidgets.QScrollArea()
        self.thumb_scroll.setWidgetResizable(True)
        self.thumb_scroll.setWidget(self.thumb_widget)

        # --- Buttons ---
        self.prev_btn = QtWidgets.QPushButton("◀ Prev")
        self.next_btn = QtWidgets.QPushButton("Next ▶")
        self.open_btn = QtWidgets.QPushButton("📂 Open Folder")
        self.prev_btn.clicked.connect(self.prev_image)
        self.next_btn.clicked.connect(self.next_image)
        self.open_btn.clicked.connect(self.open_folder)
        btn_bar = QtWidgets.QHBoxLayout()
        for b in (self.prev_btn, self.next_btn, self.open_btn):
            btn_bar.addWidget(b)
        btn_bar.addStretch()

        # --- Layout ---
        right = QtWidgets.QVBoxLayout()
        right.addWidget(self.preview, 2)
        right.addLayout(btn_bar)
        right.addWidget(self.thumb_scroll, 3)
        right_w = QtWidgets.QWidget()
        right_w.setLayout(right)

        splitter = QtWidgets.QSplitter()
        splitter.addWidget(self.tree)
        splitter.addWidget(right_w)
        splitter.setStretchFactor(1, 3)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(6)
        splitter.setOpaqueResize(True)

        main = QtWidgets.QHBoxLayout(self)
        main.addWidget(splitter)

        # --- Data ---
        self.current_folder = Path(ROOT_PATH)
        self.image_list = []
        self.image_index = 0

    # ---------------------------------------------
    # Folder selection / thumbnail building
    # ---------------------------------------------
    def on_folder_selected(self, index):
        folder = Path(self.model.filePath(index))
        if not folder.is_dir():
            folder = folder.parent
        self.current_folder = folder
        self._load_thumbnails(folder)

    def _load_thumbnails(self, folder: Path):
        for i in reversed(range(self.thumb_layout.count())):
            w = self.thumb_layout.itemAt(i).widget()
            if w:
                w.deleteLater()
        self.image_list.clear()

        files = [p for p in folder.iterdir() if p.suffix.lower() in IMAGE_EXTS]
        files.sort()
        if not files:
            self.preview.setText("No images found")
            return

        self.image_list = files
        cols, size = 5, 160
        for i, p in enumerate(files[:50]):  # first 50 thumbs
            lbl = QtWidgets.QLabel("⏳")
            lbl.setFixedSize(size, size)
            lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("border:1px solid #444;")
            lbl.mousePressEvent = lambda e, path=p: self.show_image(path)
            self.thumb_layout.addWidget(lbl, i // cols, i % cols)
            worker = ThumbWorker(str(p), size, self.thumb_ready)
            self.thread_pool.start(worker)
            self.pix_cache[str(p)] = lbl
        self.show_image(files[0])

    @QtCore.pyqtSlot(str, QPixmap)
    def _on_thumb_ready(self, path, pm):
        lbl = self.pix_cache.get(path)
        if lbl:
            lbl.setPixmap(pm)

    # ---------------------------------------------
    # Image preview + navigation
    # ---------------------------------------------
    def show_image(self, path):
        if not path:
            return
        self.image_index = self.image_list.index(path)
        pm = QPixmap(str(path))
        if pm.isNull():
            self.preview.setText("Unable to load image")
            return
        scaled = pm.scaled(self.preview.size(),
                           QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                           QtCore.Qt.TransformationMode.SmoothTransformation)
        self.preview.setPixmap(scaled)
        self.preview.setText("")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.image_list:
            self.show_image(self.image_list[self.image_index])

    def next_image(self):
        if not self.image_list:
            return
        self.image_index = (self.image_index + 1) % len(self.image_list)
        self.show_image(self.image_list[self.image_index])

    def prev_image(self):
        if not self.image_list:
            return
        self.image_index = (self.image_index - 1) % len(self.image_list)
        self.show_image(self.image_list[self.image_index])

    def open_folder(self):
        if self.current_folder.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.current_folder)))


# -------------------------------------------------
# entry point
# -------------------------------------------------
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    viewer = DirectoryImageViewer()
    viewer.show()
    sys.exit(app.exec())
