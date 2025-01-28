import sys
import os
from datetime import datetime
from collections import Counter
import pickle
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPen, QBrush, QColor, QPainter
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QDialog, QVBoxLayout, QGraphicsView,
    QGraphicsScene, QGraphicsEllipseItem, QGraphicsTextItem,
    QFileDialog, QMessageBox, QMenu
)
from PyQt6 import uic

from advanced_compression_tool import (
    bwt_encode, bwt_decode,
    rle_encode, rle_decode,
    build_huffman_tree, generate_huffman_codes,
    huffman_encode, huffman_decode
)


class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("main_window.ui", self)
        self.setup_ui()
        self.initialize_variables()
        self.load_compression_history()
        self.update_info_labels()
        self.setup_context_menu()

    def setup_context_menu(self):
        """Setup context menu for GraphicsView"""
        self.graphicsView.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.graphicsView.customContextMenuRequested.connect(self.show_graphics_context_menu)

    def wheelEvent(self, event):
        """Handle mouse wheel events for zooming"""
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            factor = 1.2
            if event.angleDelta().y() < 0:
                factor = 1.0 / factor
            self.graphicsView.scale(factor, factor)
        else:
            super().wheelEvent(event)

    def show_graphics_context_menu(self, position):
        """Show context menu for GraphicsView"""
        menu = QMenu()

        copy_action = menu.addAction("Copy")
        select_all_action = menu.addAction("Select All")

        action = menu.exec(self.graphicsView.mapToGlobal(position))

        if action == copy_action:
            focused_item = self.scene.focusItem()
            if isinstance(focused_item, QGraphicsTextItem):
                if focused_item.textCursor().hasSelection():
                    QApplication.clipboard().setText(focused_item.textCursor().selectedText())

        elif action == select_all_action:
            focused_item = self.scene.focusItem()
            if isinstance(focused_item, QGraphicsTextItem):
                cursor = focused_item.textCursor()
                cursor.select(cursor.SelectionType.Document)
                focused_item.setTextCursor(cursor)

    def setup_ui(self):
        """Initialize and setup UI elements"""
        self.scene = QGraphicsScene()
        self.graphicsView.setScene(self.scene)

        self.graphicsView.setInteractive(True)
        self.graphicsView.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.graphicsView.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.graphicsView.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.graphicsView.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)

        # Connect signals
        self.process_button.clicked.connect(self.process)
        self.open_file_button.clicked.connect(self.open_file)
        self.show_huffman_tree_button.clicked.connect(self.show_huffman_tree)
        self.method.currentTextChanged.connect(self.update_huffman_button_state)

        # Connect menu actions
        self.actionOpen.triggered.connect(self.open_file)
        self.actionSave.triggered.connect(self.save_output)
        self.actionExit.triggered.connect(self.close)
        self.actionAbout.triggered.connect(self.show_about)
        self.actionDocumentation.triggered.connect(self.show_documentation)

        self.show_huffman_tree_button.setEnabled(False)

        # Set text interaction flags for output
        self.output.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse |
            Qt.TextInteractionFlag.TextSelectableByKeyboard
        )

    def initialize_variables(self):
        """Initialize class variables"""
        self.current_huffman_tree = None
        self.compression_history = []
        self.codes = None
        self.y_offset = 0

    def update_info_labels(self):
        """Update datetime and user information labels"""
        self.datetime_label.setText(
            f"Current Date and Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        self.user_label.setText(f"User: {os.getlogin()}")
        QTimer.singleShot(1000, self.update_info_labels)

    def add_text_to_scene(self, text, x=0, y=0, is_title=False):
        """Add text to the graphics scene"""
        text_item = QGraphicsTextItem(text)
        text_item.setPos(x, y)
        text_item.setTextWidth(self.graphicsView.viewport().width() - 20)

        text_item.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse |
            Qt.TextInteractionFlag.TextSelectableByKeyboard
        )

        if is_title:
            text_item.setDefaultTextColor(QColor("#00BFFF"))
            text_item.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        else:
            text_item.setDefaultTextColor(Qt.GlobalColor.white)
            text_item.setFont(QFont("Consolas", 10))

        self.scene.addItem(text_item)
        self.y_offset += text_item.boundingRect().height() + 5
        return text_item.boundingRect().height()

    def process(self):
        """Process the input text"""
        try:
            self.scene.clear()
            text = self.input.toPlainText()
            if not text:
                QMessageBox.warning(self, "Warning", "Please enter text to process.")
                return

            algorithm = self.method.currentText()
            operation = self.operation.currentText()
            self.y_offset = 0

            result = self.process_text(text, algorithm, operation)
            if result:
                self.output.setPlainText(result)
                self.statusbar.showMessage("Processing completed successfully!", 3000)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def process_text(self, text, algorithm, operation):
        """Process text using selected algorithm"""
        start_time = datetime.now()
        algorithm_functions = {
            "BWT": self.BWT,
            "RLE": self.RLE,
            "Huffman": self.Huffman,
        }

        if algorithm == 'BWT and RLE and Huffman':
            if "Encode" in operation:
                for algo in ["BWT", "RLE", "Huffman"]:
                    text = algorithm_functions[algo](text, "Encode")
            if "Decode" in operation:
                for algo in reversed(["BWT", "RLE", "Huffman"]):
                    text = algorithm_functions[algo](text, "Decode")
        else:
            text = algorithm_functions[algorithm](text, operation)

        self.save_compression_result(
            self.input.toPlainText(), text, algorithm, operation,
            (datetime.now() - start_time).total_seconds()
        )
        return text

    def BWT(self, text, operation):
        """Handle BWT compression"""
        try:
            if operation == "Encode":
                encoded, rotations = bwt_encode(text)
                self.add_text_to_scene("BWT Encoding Steps:", x=0, y=self.y_offset, is_title=True)
                self.add_text_to_scene(f"All Rotations: {rotations}", x=0, y=self.y_offset)
                self.add_text_to_scene(f"BWT Encoded Result: {encoded}", x=0, y=self.y_offset)
                return encoded
            else:
                decoded, iterations = bwt_decode(text)
                self.add_text_to_scene("BWT Decoding Steps:", x=0, y=self.y_offset, is_title=True)
                for i, iteration in enumerate(iterations):
                    self.add_text_to_scene(f"Iteration {i + 1}: {iteration}", x=0, y=self.y_offset)
                self.add_text_to_scene(f"BWT Decoded Result: {decoded}", x=0, y=self.y_offset)
                return decoded
        except Exception as e:
            raise Exception(f"BWT Error: {str(e)}")

    def RLE(self, text, operation):
        """Handle RLE compression"""
        try:
            if operation == "Encode":
                encoded = rle_encode(text)
                self.add_text_to_scene("RLE Encoding Steps:", x=0, y=self.y_offset, is_title=True)
                self.add_text_to_scene(f"RLE Encoded Result: {encoded}", x=0, y=self.y_offset)
                return encoded
            else:
                decoded = rle_decode(text)
                self.add_text_to_scene("RLE Decoding Steps:", x=0, y=self.y_offset, is_title=True)
                self.add_text_to_scene(f"RLE Decoded Result: {decoded}", x=0, y=self.y_offset)
                return decoded
        except Exception as e:
            raise Exception(f"RLE Error: {str(e)}")

    def Huffman(self, text, operation):
        """Handle Huffman compression"""
        try:
            if operation == "Encode":
                freq_dict = Counter(text)
                self.current_huffman_tree = build_huffman_tree(freq_dict)
                self.codes = generate_huffman_codes(self.current_huffman_tree)
                encoded = huffman_encode(text, self.codes)

                self.add_text_to_scene("Huffman Encoding Steps:", x=0, y=self.y_offset, is_title=True)
                self.add_text_to_scene(f"Frequency Table: {freq_dict}", x=0, y=self.y_offset)
                self.add_text_to_scene(f"Huffman Codes: {self.codes}", x=0, y=self.y_offset)
                self.add_text_to_scene(f"Huffman Encoded Result: {encoded}", x=0, y=self.y_offset)

                self.show_huffman_tree_button.setEnabled(True)
                return encoded
            else:
                if not self.codes:
                    raise ValueError("No Huffman codes available for decoding")
                decoded = huffman_decode(text, self.codes)
                self.add_text_to_scene("Huffman Decoding Steps:", x=0, y=self.y_offset, is_title=True)
                self.add_text_to_scene(f"Huffman Decoded Result: {decoded}", x=0, y=self.y_offset)
                return decoded
        except Exception as e:
            raise Exception(f"Huffman Error: {str(e)}")

    def show_huffman_tree(self):
        """Show Huffman tree visualization with zoom and pan capabilities"""
        if not self.current_huffman_tree:
            QMessageBox.warning(self, "Warning", "Please encode text using Huffman method first.")
            return

        class ZoomableGraphicsView(QGraphicsView):
            def __init__(self, scene):
                super().__init__(scene)
                self.setRenderHint(QPainter.RenderHint.Antialiasing)
                self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
                self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
                self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
                self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
                self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
                self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)  # Enable pan
                self.zoom_factor = 1.15
                self.current_zoom = 1.0
                self.min_zoom = 0.1
                self.max_zoom = 10.0

            def wheelEvent(self, event):
                """Handle mouse wheel for zooming"""
                if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                    # Zoom Factor
                    if event.angleDelta().y() > 0:
                        factor = self.zoom_factor
                    else:
                        factor = 1 / self.zoom_factor

                    new_zoom = self.current_zoom * factor
                    if self.min_zoom <= new_zoom <= self.max_zoom:
                        self.current_zoom = new_zoom
                        self.scale(factor, factor)
                else:
                    super().wheelEvent(event)

            def resetZoom(self):
                """Reset zoom level"""
                self.resetTransform()
                self.current_zoom = 1.0

        dialog = QDialog(self)
        dialog.setWindowTitle("Huffman Tree Visualization")
        dialog.setMinimumSize(800, 600)

        layout = QVBoxLayout()

        # Create toolbar for zoom controls
        from PyQt6.QtWidgets import QToolBar, QLabel
        toolbar = QToolBar()

        zoom_label = QLabel("Zoom: 100%")
        toolbar.addWidget(zoom_label)

        scene = QGraphicsScene()
        view = ZoomableGraphicsView(scene)

        total_width = self.calculate_subtree_widths(self.current_huffman_tree) * 50

        # Draw tree
        self.draw_huffman_tree(
            self.current_huffman_tree,
            400,
            50,
            total_width / 4,
            scene
        )

        help_text = """
        Controls:
        - Zoom: Ctrl + Mouse Wheel
        - Pan: Click and Drag
        - Reset: Double Click
        """
        help_item = scene.addText(help_text)
        help_item.setDefaultTextColor(Qt.GlobalColor.white)
        help_item.setPos(10, 10)

        def update_zoom_label():
            zoom_percent = int(view.current_zoom * 100)
            zoom_label.setText(f"Zoom: {zoom_percent}%")

        view.scale_changed = update_zoom_label

        # Add double-click event to reset zoom
        def mouseDoubleClickEvent(event):
            view.resetZoom()
            update_zoom_label()

        view.mouseDoubleClickEvent = mouseDoubleClickEvent

        layout.addWidget(toolbar)
        layout.addWidget(view)
        dialog.setLayout(layout)

        view.fitInView(scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        view.current_zoom = 1.0
        update_zoom_label()

        dialog.exec()

    def draw_huffman_tree(self, node, x, y, x_offset, scene):
        """Draw Huffman tree node"""
        if not node:
            return

        radius = 20
        ellipse = QGraphicsEllipseItem(x - radius, y - radius, 2 * radius, 2 * radius)
        ellipse.setPen(QPen(Qt.GlobalColor.white))
        ellipse.setBrush(QBrush(QColor("#3a3af5")))
        scene.addItem(ellipse)

        text = f"{node.char}:{node.freq}" if node.char else f"{node.freq}"
        text_item = QGraphicsTextItem(text)
        text_item.setDefaultTextColor(Qt.GlobalColor.white)
        text_item.setFont(QFont("Consolas", 8))

        text_rect = text_item.boundingRect()
        text_item.setPos(x - text_rect.width() / 2, y - text_rect.height() / 2)
        scene.addItem(text_item)

        if node.left:
            left_x = x - x_offset * self.calculate_subtree_widths(node.left)
            left_y = y + 60
            scene.addLine(x, y + radius, left_x, left_y - radius, QPen(Qt.GlobalColor.white))
            self.draw_huffman_tree(node.left, left_x, left_y, x_offset / 2, scene)

        if node.right:
            right_x = x + x_offset * self.calculate_subtree_widths(node.right)
            right_y = y + 60
            scene.addLine(x, y + radius, right_x, right_y - radius, QPen(Qt.GlobalColor.white))
            self.draw_huffman_tree(node.right, right_x, right_y, x_offset / 2, scene)

    def calculate_subtree_widths(self, node):
        """Calculate width needed for Huffman subtree"""
        if not node or (not node.left and not node.right):
            return 1
        return self.calculate_subtree_widths(node.left) + self.calculate_subtree_widths(node.right)

    def update_huffman_button_state(self, text):
        """Update Huffman tree button state"""
        self.show_huffman_tree_button.setEnabled(
            text in ["Huffman", "BWT and RLE and Huffman"] and
            "Encode" in self.operation.currentText()
        )

    def save_compression_result(self, original, compressed, method, operation, time_taken):
        """Save compression results"""
        result = {
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'method': method,
            'operation': operation,
            'original_size': len(original),
            'compressed_size': len(compressed),
            'compression_ratio': ((len(original) - len(compressed)) / len(original) * 100)
            if operation == "Encode" else 0,
            'time_taken': time_taken
        }
        self.compression_history.append(result)
        self.save_compression_history()

    def save_compression_history(self):
        """Save compression history to file"""
        try:
            with open('compression_history.pkl', 'wb') as f:
                pickle.dump(self.compression_history, f)
        except Exception as e:
            self.statusbar.showMessage(f"Failed to save history: {str(e)}", 3000)

    def load_compression_history(self):
        """Load compression history from file"""
        try:
            with open('compression_history.pkl', 'rb') as f:
                self.compression_history = pickle.load(f)
        except FileNotFoundError:
            self.compression_history = []
        except Exception as e:
            self.statusbar.showMessage(f"Failed to load history: {str(e)}", 3000)
            self.compression_history = []

    def open_file(self):
        """Open and load file"""
        try:
            filename, _ = QFileDialog.getOpenFileName(
                self, "Open File", "",
                "Text Files (*.txt);;All Files (*.*)"
            )
            if filename:
                with open(filename, 'r', encoding='utf-8') as f:
                    self.input.setPlainText(f.read())
                self.statusbar.showMessage(f"File loaded: {filename}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open file: {str(e)}")

    def save_output(self):
        """Save output to file"""
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self, "Save Output", "",
                "Text Files (*.txt);;All Files (*.*)"
            )
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.output.toPlainText())
                self.statusbar.showMessage(f"Output saved to: {filename}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save file: {str(e)}")

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About Advanced Text Compression Tool",
            """<h3>Advanced Text Compression Tool v1.0.0</h3>
            <p>A powerful tool for text compression using various algorithms:</p>
            <ul>
                <li>Burrows-Wheeler Transform (BWT)</li>
                <li>Run-Length Encoding (RLE)</li>
                <li>Huffman Coding</li>
            </ul>
            <p>Created for Data Structures and Algorithms course project.</p>
            <p>Features:</p>
            <ul>
                <li>Multiple compression algorithms</li>
                <li>Visual Huffman tree representation</li>
                <li>Compression history tracking</li>
                <li>File import/export support</li>
            </ul>"""
        )

    def show_documentation(self):
        """Show documentation dialog"""
        QMessageBox.information(
            self,
            "Documentation",
            """<h3>How to Use:</h3>
            <ol>
                <li>Enter or load text in the input area</li>
                <li>Select compression method:
                    <ul>
                        <li>BWT - Burrows-Wheeler Transform</li>
                        <li>RLE - Run-Length Encoding</li>
                        <li>Huffman - Huffman Coding</li>
                        <li>BWT and RLE and Huffman - Combined compression</li>
                    </ul>
                </li>
                <li>Choose operation:
                    <ul>
                        <li>Encode - Compress the text</li>
                        <li>Decode - Decompress the text</li>
                        <li>Encode → Decode - Test both operations</li>
                    </ul>
                </li>
                <li>Click Process to start compression</li>
                <li>View results in the output area</li>
                <li>For Huffman compression, you can view the Huffman tree 
                by clicking the 'Show Huffman Tree' button</li>
            </ol>
            <p><b>Tips:</b></p>
            <ul>
                <li>You can load text from a file using the 'Open File' button</li>
                <li>Results can be saved using the 'Save' option in the File menu</li>
                <li>Compression history is automatically saved</li>
            </ul>"""
        )

    def closeEvent(self, event):
        """Handle application close event"""
        reply = QMessageBox.question(
            self,
            'Confirm Exit',
            'Are you sure you want to exit?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.save_compression_history()
            event.accept()
        else:
            event.ignore()


def load_stylesheet(app, stylesheet_path="styles.qss"):
    """Load application stylesheet"""
    try:
        with open(stylesheet_path, "r") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print(f"Warning: Stylesheet file '{stylesheet_path}' not found!")
    except Exception as e:
        print(f"Error loading stylesheet: {str(e)}")


if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        load_stylesheet(app, "styles.qss")

        window = MyApp()
        window.show()
        window.statusbar.showMessage("Welcome to Advanced Text Compression Tool!", 5000)

        sys.exit(app.exec())
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        sys.exit(1)