from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
import sys


class MainApp(QMainWindow):
    """This is the class of the MainApp GUI system"""
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        """This method creates our GUI"""
        centralwidget = QWidget()
        self.setCentralWidget(centralwidget)
        lay = QVBoxLayout(centralwidget)
        # Box Layout to organize our GUI
        # labels
        types1 = QLabel('Label')
        lay.addWidget(types1)

        self.model = QFileSystemModel()
        self.model.setRootPath('')
        self.tree = QTreeView()
        self.tree.setModel(self.model)

        self.tree.setAnimated(False)
        self.tree.setIndentation(20)
        self.tree.setSortingEnabled(True)
        lay.addWidget(self.tree)

        self.setGeometry(50, 50, 1800, 950)
        # self.setFixedSize(self.size())
        self.setWindowTitle('MainApp')
        self.setWindowIcon(QIcon('image/logo.png'))
        self.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MainApp()
    sys.exit(app.exec())