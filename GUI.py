import os

from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import Qt, QPoint, pyqtSignal
from PyQt5.QtGui import QColor, QMouseEvent
from PyQt5.QtWidgets import QDesktopWidget, QCheckBox, QStyleFactory, QFileDialog, QPushButton
from ui_2 import Ui_MainWindow


class TextWindow(QtWidgets.QMainWindow):
    update_text = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.txt_dir = os.path.join(os.getcwd(), './txt')
        self.txt_file = []
        self.text_browser_content = {}
        self.text_browser_box = {}
        self.mousePressed = False
        self.oldPos = None
        self.ui = Ui_MainWindow()
        self.setAutoFillBackground(True)
        # self.setWindowFlags(Qt.CustomizeWindowHint | Qt.WindowStaysOnTopHint)  # 去掉标题栏, 窗口置顶
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)  # 去掉标题栏, 窗口置顶
        # self.setAttribute(Qt.WA_TranslucentBackground, True)  # 窗体透明
        self.setStyle(QStyleFactory.create('Fusion'))
        self.statusBar().showMessage('')
        self.update_text.connect(self.text_browser_flush)
        self.ui.setupUi(self)
        self.initUI()

    def initUI(self):
        self.ui.txtDirFlush.clicked.connect(self.txtDirFlush_click)
        # 打开文件夹
        self.ui.txtDirButton.clicked.connect(self.open_txt_dir)
        self.show()
        # 自定义工具栏 --原文
        self.add_source_checkbox('原文')
        # 自定义工具栏 --识别
        self.add_source_checkbox('识别', True)
        self.add_text_browser('识别')
        self.txtDirFlush_click()

    def text_accept_emit(self, d):
        self.update_text.emit(d)

    def text_browser_flush(self, txt_dict=None):
        if txt_dict is None:
            txt_dict = {}
        for k_ in self.text_browser_content.keys():
            if k_ in txt_dict:
                # print(self.text_gen(txt_dict[k_]))
                self.text_browser_content[k_].setHtml(self.text_gen(txt_dict[k_]))
            else:
                self.text_browser_content[k_].setHtml(self.text_gen(' '))
        pass

    def txtDirFlush_click(self):
        if not os.path.exists(self.txt_dir):
            return
        self.txt_file = []
        for file in os.listdir(self.txt_dir):
            if file.endswith('.txt'):
                self.txt_file.append(file[:-4])
        for name in self.txt_file:
            for suffix in ['_color', '_bg']:
                temp = self.ui.centralwidget.findChild(QPushButton, f'{name}{suffix}')
                if temp is not None:
                    temp.deleteLater()
            temp_2 = self.ui.centralwidget.findChild(QCheckBox, f'{name}_checkbox')
            if temp_2 is not None:
                temp_2.deleteLater()
            self.add_source_checkbox(name, name in self.text_browser_box)

    def open_txt_dir(self):
        dir_choose = QFileDialog.getExistingDirectory(None, '选择txt文件夹', self.txt_dir)
        if dir_choose != '':
            self.txt_dir = dir_choose
        self.txtDirFlush_click()

    @staticmethod
    def change_content_color(block, now_color=QColor(0, 0, 0)):
        col = QtWidgets.QColorDialog.getColor(now_color)
        if col.isValid():
            print(col.name())
            block.setStyleSheet(f"background-color: {col.name()}; color: transparent;")

    def add_source_checkbox(self, name, checked=False):
        color_btn = QtWidgets.QPushButton(self.ui.centralwidget)
        color_btn.setStyleSheet("background-color: rgb(255, 255, 255); color: transparent;")
        color_btn.setFixedWidth(20)
        color_btn.setFixedHeight(20)
        color_btn.clicked.connect(lambda: self.change_content_color(color_btn, color_btn.palette().button().color()))
        color_btn.setObjectName(f'{name}_color')
        color_btn.setAutoFillBackground(True)
        self.ui.toolBox.addWidget(color_btn)
        bg_btn = QtWidgets.QPushButton(self.ui.centralwidget)
        bg_btn.setStyleSheet("background-color: rgb(0, 0, 0); color: transparent; margin-right: 2px;")
        bg_btn.setFixedWidth(20)
        bg_btn.setFixedHeight(20)
        bg_btn.clicked.connect(lambda: self.change_content_color(bg_btn, bg_btn.palette().button().color()))
        bg_btn.setObjectName(f'{name}_bg')
        self.ui.toolBox.addWidget(bg_btn)
        checkBox = QtWidgets.QCheckBox(self.ui.centralwidget)
        checkBox.setObjectName("checkBox")
        checkBox.setText(name)
        checkBox.setObjectName(f'{name}_checkbox')
        checkBox.setChecked(checked)
        checkBox.setStyleSheet("color: #eee;")
        checkBox.toggled.connect(lambda: self.check_box_toggle(checkBox.isChecked(), name))
        self.ui.toolBox.addWidget(checkBox)
        pass

    def check_box_toggle(self, is_checked, browser_name):
        if not is_checked:
            # 先删除控件
            self.text_browser_box[browser_name].deleteLater()
            item_list = list(range(self.text_browser_box[browser_name].count()))
            item_list.reverse()
            for i in item_list:
                item = self.text_browser_box[browser_name].itemAt(i)
                self.text_browser_box[browser_name].removeItem(item)
                if item.widget():
                    item.widget().deleteLater()
            self.text_browser_content.pop(browser_name)
            self.text_browser_box.pop(browser_name)
        else:
            self.add_text_browser(browser_name)
        pass

    def add_text_browser(self, name):
        text_content = QtWidgets.QHBoxLayout()
        text_content.setContentsMargins(-1, -1, 4, 2)
        text_content.setSpacing(2)
        text_content.setObjectName(f'{name}_box')
        textBrowser_name = QtWidgets.QTextBrowser(self.ui.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Ignored)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(textBrowser_name.sizePolicy().hasHeightForWidth())
        textBrowser_name.setSizePolicy(sizePolicy)
        textBrowser_name.setMinimumSize(QtCore.QSize(0, 0))
        textBrowser_name.setFont(QtGui.QFont('', 9))
        textBrowser_name.setStyleSheet("background-color: rgba(255, 255, 255, 0);")
        textBrowser_name.setFrameShape(QtWidgets.QFrame.NoFrame)
        textBrowser_name.setFrameShadow(QtWidgets.QFrame.Sunken)
        textBrowser_name.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        textBrowser_name.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        textBrowser_name.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        textBrowser_name.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        textBrowser_name.setObjectName(f'{name}_name')
        textBrowser_name.setHtml(self.text_gen(name))
        text_content.addWidget(textBrowser_name)
        textBrowser_content = QtWidgets.QTextBrowser(self.ui.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Ignored)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(textBrowser_content.sizePolicy().hasHeightForWidth())
        textBrowser_content.setSizePolicy(sizePolicy)
        textBrowser_content.setMinimumSize(QtCore.QSize(0, 0))
        textBrowser_content.setFont(QtGui.QFont('', 9))
        textBrowser_content.setStyleSheet("background-color: rgba(255, 255, 255, 0);")
        textBrowser_content.setFrameShape(QtWidgets.QFrame.NoFrame)
        textBrowser_content.setFrameShadow(QtWidgets.QFrame.Sunken)
        textBrowser_content.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        textBrowser_content.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        textBrowser_content.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        textBrowser_content.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        textBrowser_content.setObjectName(f'{name}_content')
        text_content.addWidget(textBrowser_content)
        text_content.setStretch(1, 1)
        self.ui.outerBox.addLayout(text_content)
        self.ui.outerBox.setStretch(self.ui.outerBox.count() - 1, 1)
        self.text_browser_content[name] = textBrowser_content  # 文本框地址，便于修改文本
        self.text_browser_box[name] = text_content  # layout地址，便于删除

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.mousePressed = True
            self.oldPos = event.globalPos()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.mousePressed = False

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.mousePressed and self.oldPos:
            delta = QPoint(event.globalPos() - self.oldPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPos()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    @staticmethod
    def text_gen(_content):
        return f'<span style="color: #fff; text-shadow: 0 0 5px #f700ff; margin:0; ' \
               f'font-size:14pt; font-weight: bold;">{_content}</span>'
