# Form implementation generated from reading ui file 'main.ui'
#
# Created by: PyQt6 UI code generator 6.7.0
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.

import subprocess
from PyQt6 import QtCore, QtGui, QtWidgets
import sys
import os
import importlib
from syntax import *
from autocomplete import *
from wizard import run_from_main_app
import json
import subprocess
import platform

class CustomPlainTextEdit(QtWidgets.QPlainTextEdit):
    def __init__(self, completer, parent=None, filename=None):
        super().__init__(parent)
        self.completer = completer
        self.indentation = " " * 4
        self.filename = filename

    def keyPressEvent(self, event):
        cursor = self.textCursor()
        current_line = cursor.block().text()
        current_position = cursor.positionInBlock()

        if event.key() in (QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Enter):
            cursor.insertText("\n")
            indent_level = self.calculate_indent_level(current_line)
            cursor.insertText(self.indentation * indent_level)
            return

        if event.key() == QtCore.Qt.Key.Key_Backspace:
            if current_line[:current_position].endswith(self.indentation):
                for _ in range(len(self.indentation)):
                    cursor.deletePreviousChar()
                return

        if event.key() == QtCore.Qt.Key.Key_Tab:
            cursor.insertText(self.indentation)
            return

        if self.completer.popup().isVisible():
            if event.key() in (QtCore.Qt.Key.Key_Enter, QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Escape, QtCore.Qt.Key.Key_Tab, QtCore.Qt.Key.Key_Backtab):
                event.ignore()
                return

        super().keyPressEvent(event)
        self.handle_autocomplete(event)

    def handle_autocomplete(self, event):
        isShortcut = (event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier) and event.key() == QtCore.Qt.Key.Key_Space
        if not self.completer or not isShortcut:
            return

        completionPrefix = self.textUnderCursor()
        if completionPrefix != self.completer.completionPrefix():
            self.completer.setCompletionPrefix(completionPrefix)
            self.completer.popup().setCurrentIndex(self.completer.completionModel().index(0, 0))

        cr = self.cursorRect()
        cr.setWidth(self.completer.popup().sizeHintForColumn(0) + self.completer.popup().verticalScrollBar().sizeHint().width())
        self.completer.complete(cr)

    def textUnderCursor(self):
        cursor = self.textCursor()
        cursor.select(QtGui.QTextCursor.SelectionType.WordUnderCursor)
        return cursor.selectedText()

    def calculate_indent_level(self, current_line):
        cursor = self.textCursor()
        block_number = cursor.blockNumber()
        indent_level = 0

        for i in range(block_number):
            block = self.document().findBlockByNumber(i)
            line = block.text().strip()

            if line.endswith(":") or line.endswith("{"):
                indent_level += 1
            elif line == "" or not line.endswith((":", "{")):
                indent_level = max(indent_level - 1, 0)

        return indent_level

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1264, 630)
        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayoutWidget = QtWidgets.QWidget(parent=self.centralwidget)
        self.gridLayoutWidget.setGeometry(QtCore.QRect(10, 10, 1251, 581))
        self.gridLayoutWidget.setObjectName("gridLayoutWidget")
        self.gridLayout = QtWidgets.QGridLayout(self.gridLayoutWidget)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setObjectName("gridLayout")
        self.plainTextEdit = CustomPlainTextEdit(None, parent=self.gridLayoutWidget)
        self.plainTextEdit.setObjectName("plainTextEdit")
        self.gridLayout.addWidget(self.plainTextEdit, 0, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(parent=MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1264, 18))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(parent=self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuActions = QtWidgets.QMenu(parent=self.menubar)
        self.menuActions.setObjectName("menuActions")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(parent=MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionSave = QtGui.QAction(parent=MainWindow)
        self.actionSave.setObjectName("actionSave")
        self.actionOpen = QtGui.QAction(parent=MainWindow)
        self.actionOpen.setObjectName("actionOpen")
        self.menuFile.addAction(self.actionSave)
        self.menuFile.addAction(self.actionOpen)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuActions.menuAction())  # Add menuActions to the menubar

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        self.actionSave.triggered.connect(self.save_file)
        self.actionOpen.triggered.connect(self.open_file)

        self.filename_to_editor = {}

        # Add Autocompletion
        self.completer = QtWidgets.QCompleter()
        self.completer.setWidget(self.plainTextEdit)
        self.model = QtGui.QStandardItemModel(self.completer)
        self.completer.setModel(self.model)
        self.completer.setCompletionMode(QtWidgets.QCompleter.CompletionMode.PopupCompletion)
        self.completer.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        self.completer.activated.connect(self.insert_completion)

        self.plainTextEdit.completer = self.completer
        self.plainTextEdit.textChanged.connect(self.update_completions)
        self.filename = None
        self.current_highlighter = None
        self.is_file_opened = False
        self.dark_mode = False
        self.plugin = None
        self.startup()

    def startup(self):
        if os.path.exists("beagleeditor_settings.json"):
            with open("beagleeditor_settings.json", "r") as json_file:
                json_load = json.load(json_file)
                be_settings = json_load['settings']
                theme = be_settings['theme']
                if theme == "dark":
                    MainWindow.setStyleSheet("QMainWindow { background-color: black; color: white; } QFontComboBox { background-color: white; color: black; } QMenuBar { color: white; } QPlainTextEdit { background-color: #2e2e2e; color: white; }")
        else:
            run_from_main_app()

        self.load_plugins()

    def load_plugins(self):
        plugin_dir = "plugins"
        plugin_modules = []  # List to store loaded plugin modules

        if os.path.exists(plugin_dir):
            self.menuPlugins = QtWidgets.QMenu(parent=self.menubar)
            self.menuPlugins.setObjectName("menuPlugins")
            self.menuPlugins.setTitle("Plugins")

            for filename in os.listdir(plugin_dir):
                if filename.endswith(".py"):
                    module_name = filename[:-3]  # Remove ".py" extension
                    try:
                        plugin_module = importlib.import_module(f"{plugin_dir}.{module_name}")
                        plugin_modules.append(plugin_module)  # Add the loaded module to the list
                    except ImportError:
                        print(f"Error importing plugin: {module_name}")

            # Add actions to the plugins menu
            for module in plugin_modules:
                # Use module filename as action name
                action_name = module.__name__.split('.')[-1]
                action = QtGui.QAction(action_name, MainWindow)
                action.triggered.connect(lambda checked, m=module: self.run_plugin(m))
                self.menuPlugins.addAction(action)

            self.menubar.addAction(self.menuPlugins.menuAction())

    def run_plugin(self, module):
        # Call a specific function from the plugin module, e.g., `run`
        if hasattr(module, 'run_from_beagleeditor'):
            module.run_from_beagleeditor()
        else:
            QtWidgets.QMessageBox.critical(None, "Warning", f"Module {module.__name__} does not have a run_from_beagleeditor() function", QtWidgets.QMessageBox.StandardButton.Ok)

    def save_file(self):
        if self.is_file_opened:
            with open(self.filename, 'w') as f:
                f.write(self.plainTextEdit.toPlainText())
        else:
            self.filename, _ = QtWidgets.QFileDialog.getSaveFileName(None, "Save File", "", "All Files (*)")
            if self.filename:
                with open(self.filename, 'w') as f:
                    f.write(self.plainTextEdit.toPlainText())
                self.is_file_opened = True
        self.update_completions()
        self.apply_highlighter()
        self.add_run_action()

    def open_file(self):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(None, "Open File", "", "All Files (*)")
        if filename:
            with open(filename, 'r') as f:
                file_content = f.read()
                self.plainTextEdit.setPlainText(file_content)
            self.is_file_opened = True
            self.filename = filename
            self.update_completions()
            self.apply_highlighter()
            self.add_run_action()

    def add_run_action(self):
        if self.is_file_opened and self.filename.endswith('.py'):
            self.actionRunPythonFile = QtGui.QAction("Run Python File", parent=MainWindow)
            self.actionRunPythonFile.setObjectName("actionRunPythonFile")
            self.menuActions.addAction(self.actionRunPythonFile)
            self.actionRunPythonFile.triggered.connect(self.start_python_file)

    def start_python_file(self):
        if self.filename:
            subprocess.run([sys.executable, self.filename])

    def apply_highlighter(self):
        if self.current_highlighter:
            self.current_highlighter.setDocument(None)

        if self.filename.endswith('.py'):
            self.current_highlighter = PythonHighlighter(self.plainTextEdit.document())
        elif self.filename.endswith('.html'):
            self.current_highlighter = HTMLHighlighter(self.plainTextEdit.document())
        elif self.filename.endswith('.cpp') or self.filename.endswith('.h'):
            self.current_highlighter = CppHighlighter(self.plainTextEdit.document())
        elif self.filename.endswith('.css'):
            self.current_highlighter = CSSHighlighter(self.plainTextEdit.document())
        elif self.filename.endswith('.cs'):
            self.current_highlighter = CSharpHighlighter(self.plainTextEdit.document())
        elif self.filename.endswith('.c'):
            self.current_highlighter = CHighlighter(self.plainTextEdit.document())
        elif self.filename.endswith('.js'):
            self.current_highlighter = JavaScriptHighlighter(self.plainTextEdit.document())

    def update_completions(self):
        cursor = self.plainTextEdit.textCursor()
        cursor.select(QtGui.QTextCursor.SelectionType.WordUnderCursor)
        word_fragment = cursor.selectedText()

        if not word_fragment:
            return

        if self.filename and self.filename.endswith('.py'):
            suggestions = PythonSuggestions.get_suggestions
        elif self.filename and self.filename.endswith('.html'):
            suggestions = HTMLSuggestions.get_suggestions
        elif self.filename and (self.filename.endswith('.cpp') or self.filename.endswith('.h')):
            suggestions = CppSuggestions.get_suggestions
        elif self.filename and self.filename.endswith('.css'):
            suggestions = CSSSuggestions.get_suggestions
        elif self.filename and self.filename.endswith('.cs'):
            suggestions = CSharpSuggestions.get_suggestions
        elif self.filename and self.filename.endswith('.c'):
            suggestions = CSuggestions.get_suggestions
        elif self.filename and self.filename.endswith('.js'):
            suggestions = JavaScriptSuggestions.get_suggestions
        else:
            suggestions = lambda word_fragment: []

        suggestions_list = suggestions(word_fragment)
        self.model = QtGui.QStandardItemModel(self.completer)
        for suggestion in suggestions_list:
            item = QtGui.QStandardItem(suggestion)
            self.model.appendRow(item)
        self.completer.setModel(self.model)

        self.completer.setCompletionPrefix(word_fragment)
        cursor_rect = self.plainTextEdit.cursorRect()
        cursor_rect.setWidth(self.completer.popup().sizeHintForColumn(0) +
                             self.completer.popup().verticalScrollBar().sizeHint().width())
        self.completer.complete(cursor_rect)

    def insert_completion(self, completion):
        cursor = self.plainTextEdit.textCursor()
        cursor.select(QtGui.QTextCursor.SelectionType.WordUnderCursor)
        cursor.insertText(completion)
        self.plainTextEdit.setTextCursor(cursor)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "BeagleEditor"))
        self.menuActions.setTitle(_translate("MainWindow", "Actions"))
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.actionSave.setText(_translate("MainWindow", "Save"))
        self.actionOpen.setText(_translate("MainWindow", "Open"))

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec())
