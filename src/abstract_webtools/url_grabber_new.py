from PyQt5 import QtWidgets, QtCore
from abstract_webtools import urlManager, requestManager, SoupManager, LinkManager
from abstract_gui import get_user_agents, get_cipher_list

class UrlGrabberWidget(QtWidgets.QWidget):
    def __init__(self, initial_url="https://example.com", parent=None):
        super().__init__(parent)
        self.initial_url = initial_url
        self.setup_ui()
        self.setup_logic()
        self.init_managers()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # URL input and grab button
        self.url_input = QtWidgets.QLineEdit(self.initial_url)
        self.status_label = QtWidgets.QLabel("Status: Unknown")
        self.grab_btn = QtWidgets.QPushButton("Grab URL")

        url_layout = QtWidgets.QHBoxLayout()
        url_layout.addWidget(QtWidgets.QLabel("URL:"))
        url_layout.addWidget(self.url_input)
        url_layout.addWidget(self.grab_btn)

        # User agent input
        self.user_agent_box = QtWidgets.QComboBox()
        self.user_agent_box.addItems(get_user_agents())

        # Source output
        self.source_code_edit = QtWidgets.QPlainTextEdit()
        self.source_code_edit.setReadOnly(True)

        # Soup output
        self.soup_result_edit = QtWidgets.QPlainTextEdit()

        # Action buttons
        self.action_btn = QtWidgets.QPushButton("Parse")
        self.get_text_btn = QtWidgets.QPushButton("Get All Text")
        self.send_btn = QtWidgets.QPushButton("Send Soup")

        # Assemble layout
        layout.addLayout(url_layout)
        layout.addWidget(self.status_label)
        layout.addWidget(QtWidgets.QLabel("User-Agent:"))
        layout.addWidget(self.user_agent_box)
        layout.addWidget(QtWidgets.QLabel("Source Code:"))
        layout.addWidget(self.source_code_edit)
        layout.addWidget(QtWidgets.QLabel("Soup Result:"))
        layout.addWidget(self.soup_result_edit)

        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.addWidget(self.action_btn)
        btn_layout.addWidget(self.get_text_btn)
        btn_layout.addWidget(self.send_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def setup_logic(self):
        self.grab_btn.clicked.connect(self.grab_url)
        self.action_btn.clicked.connect(self.parse_html)
        self.get_text_btn.clicked.connect(self.get_all_text)
        self.send_btn.clicked.connect(self.send_soup)

    def init_managers(self):
        self.url_mgr = urlManager(url=self.initial_url)
        self.request_mgr = None
        self.soup_mgr = None
        self.link_mgr = None

    def grab_url(self):
        url = self.url_input.text().strip()
        self.url_mgr = urlManager(url=url)
        self.request_mgr = requestManager(url_mgr=self.url_mgr)
        if self.request_mgr.source_code:
            self.soup_mgr = SoupManager(url_mgr=self.url_mgr, request_mgr=self.request_mgr)
            self.link_mgr = LinkManager(url_mgr=self.url_mgr, request_mgr=self.request_mgr, soup_mgr=self.soup_mgr)
            self.status_label.setText("Status: Success")
            self.source_code_edit.setPlainText(self.request_mgr.source_code)
        else:
            self.status_label.setText("Status: Failed")

    def parse_html(self):
        if self.soup_mgr:
            self.soup_result_edit.setPlainText(self.soup_mgr.soup)

    def get_all_text(self):
        if self.soup_mgr:
            self.soup_result_edit.setPlainText(self.soup_mgr.extract_text_sections())

    def send_soup(self):
        soup = self.soup_result_edit.toPlainText()
        print("Soup sent:", soup[:300])  # or emit a signal

