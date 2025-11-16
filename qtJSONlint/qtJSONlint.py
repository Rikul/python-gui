import sys
import json
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLabel, QSpinBox, QCheckBox, QGroupBox,
    QMessageBox, QFileDialog, QRadioButton, QButtonGroup
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QFont


class JSONLintWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("qtJSONlint - JSON Formatter and Validator")
        self.resize(1000, 700)
        
        # Create the menu bar
        self.create_menu_bar()
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Input section
        input_group = QGroupBox("Input JSON")
        input_layout = QVBoxLayout()
        
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("Paste JSON here or use File > Open to load from a file...")
        self.input_text.setFont(QFont("Courier", 10))
        input_layout.addWidget(self.input_text)
        
        input_group.setLayout(input_layout)
        main_layout.addWidget(input_group)
        
        # Options section
        options_group = QGroupBox("Format Options")
        options_layout = QHBoxLayout()
        
        # Format type
        format_label = QLabel("Format:")
        options_layout.addWidget(format_label)
        
        self.format_group = QButtonGroup(self)
        self.regular_radio = QRadioButton("Regular")
        self.compact_radio = QRadioButton("Compact")
        self.regular_radio.setChecked(True)
        
        self.format_group.addButton(self.regular_radio, 0)
        self.format_group.addButton(self.compact_radio, 1)
        
        options_layout.addWidget(self.regular_radio)
        options_layout.addWidget(self.compact_radio)
        
        options_layout.addSpacing(20)
        
        # Indent size
        indent_label = QLabel("Indent Size:")
        options_layout.addWidget(indent_label)
        
        self.indent_spinbox = QSpinBox()
        self.indent_spinbox.setMinimum(0)
        self.indent_spinbox.setMaximum(10)
        self.indent_spinbox.setValue(2)
        options_layout.addWidget(self.indent_spinbox)
        
        options_layout.addSpacing(20)
        
        # Sort keys checkbox
        self.sort_keys_checkbox = QCheckBox("Sort Keys")
        options_layout.addWidget(self.sort_keys_checkbox)
        
        options_layout.addSpacing(20)
        
        # Ensure ASCII checkbox
        self.ensure_ascii_checkbox = QCheckBox("Ensure ASCII")
        options_layout.addWidget(self.ensure_ascii_checkbox)
        
        options_layout.addStretch()
        
        # Format button
        self.format_button = QPushButton("Format JSON")
        self.format_button.clicked.connect(self.format_json)
        self.format_button.setFixedWidth(120)
        options_layout.addWidget(self.format_button)
        
        options_group.setLayout(options_layout)
        main_layout.addWidget(options_group)
        
        # Output section
        output_group = QGroupBox("Formatted Output")
        output_layout = QVBoxLayout()
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Courier", 10))
        output_layout.addWidget(self.output_text)
        
        output_group.setLayout(output_layout)
        main_layout.addWidget(output_group)
        
        # Error section
        error_group = QGroupBox("Errors")
        error_layout = QVBoxLayout()
        
        self.error_text = QTextEdit()
        self.error_text.setReadOnly(True)
        self.error_text.setMaximumHeight(100)
        self.error_text.setFont(QFont("Courier", 9))
        self.error_text.setStyleSheet("QTextEdit { color: red; }")
        error_layout.addWidget(self.error_text)
        
        error_group.setLayout(error_layout)
        main_layout.addWidget(error_group)
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
    def create_menu_bar(self):
        """Create the menu bar."""
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("File")
        
        open_action = QAction("Open...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        save_action = QAction("Save Output...", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        clear_action = QAction("Clear Input", self)
        clear_action.setShortcut("Ctrl+L")
        clear_action.triggered.connect(self.clear_input)
        file_menu.addAction(clear_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Help menu
        help_menu = menu_bar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def open_file(self):
        """Open a JSON file."""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Open JSON File",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_name:
            try:
                with open(file_name, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.input_text.setPlainText(content)
                self.statusBar().showMessage(f"Loaded: {file_name}")
                self.error_text.clear()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open file:\n{str(e)}")
                
    def save_file(self):
        """Save the formatted JSON output to a file."""
        if not self.output_text.toPlainText():
            QMessageBox.warning(self, "Warning", "No formatted output to save.")
            return
            
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Save JSON File",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_name:
            try:
                with open(file_name, 'w', encoding='utf-8') as f:
                    f.write(self.output_text.toPlainText())
                self.statusBar().showMessage(f"Saved: {file_name}")
                QMessageBox.information(self, "Success", f"File saved successfully:\n{file_name}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save file:\n{str(e)}")
                
    def clear_input(self):
        """Clear the input text area."""
        self.input_text.clear()
        self.output_text.clear()
        self.error_text.clear()
        self.statusBar().showMessage("Cleared")
        
    def format_json(self):
        """Format the JSON input."""
        self.error_text.clear()
        self.output_text.clear()
        
        input_json = self.input_text.toPlainText().strip()
        
        if not input_json:
            self.error_text.setPlainText("Error: No input provided")
            self.statusBar().showMessage("Error: No input")
            return
            
        try:
            # Parse the JSON
            data = json.loads(input_json)
            
            # Get format options
            is_compact = self.compact_radio.isChecked()
            indent = None if is_compact else self.indent_spinbox.value()
            sort_keys = self.sort_keys_checkbox.isChecked()
            ensure_ascii = self.ensure_ascii_checkbox.isChecked()
            
            # Format options for compact mode
            separators = (',', ':') if is_compact else (',', ': ')
            
            # Format the JSON
            formatted_json = json.dumps(
                data,
                indent=indent,
                sort_keys=sort_keys,
                ensure_ascii=ensure_ascii,
                separators=separators
            )
            
            # Display the formatted JSON
            self.output_text.setPlainText(formatted_json)
            self.statusBar().showMessage("JSON formatted successfully")
            
        except json.JSONDecodeError as e:
            error_msg = f"JSON Decode Error:\n"
            error_msg += f"  Message: {e.msg}\n"
            error_msg += f"  Line: {e.lineno}, Column: {e.colno}\n"
            error_msg += f"  Position: {e.pos}"
            self.error_text.setPlainText(error_msg)
            self.statusBar().showMessage("Error: Invalid JSON")
            
        except Exception as e:
            error_msg = f"Error: {type(e).__name__}\n{str(e)}"
            self.error_text.setPlainText(error_msg)
            self.statusBar().showMessage("Error occurred")
            
    def show_about(self):
        """Display the 'About' message box."""
        about_text = (
            "qtJSONlint\n\n"
            "A JSON formatter and validator built with PySide6.\n\n"
            "Features:\n"
            "• Format JSON in regular or compact mode\n"
            "• Customizable indent size\n"
            "• Sort keys alphabetically\n"
            "• Ensure ASCII output\n"
            "• Display detailed parsing errors\n"
        )
        QMessageBox.information(self, "About qtJSONlint", about_text)


def main():
    app = QApplication(sys.argv)
    window = JSONLintWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
