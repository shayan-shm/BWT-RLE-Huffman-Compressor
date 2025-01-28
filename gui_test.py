import sys
from advanced_compression_tool import *
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPen, QBrush, QColor, QPainter
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QTextEdit, QComboBox, QGraphicsView, \
    QGraphicsTextItem, QGraphicsScene, QInputDialog, QGraphicsEllipseItem, QDialog, QVBoxLayout, QFileDialog
from PyQt6 import uic
from collections import Counter
import json
import os


class ClickableTextItem(QGraphicsTextItem):
    clicked = pyqtSignal()  # Signal for handling clicks

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

    def mousePressEvent(self, event):
        self.clicked.emit()  # Emit signal when clicked
        super().mousePressEvent(event)


# Load the .ui file
class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # Load the UI file
        uic.loadUi("main_window.ui", self)

        self.process_button = self.findChild(QPushButton, 'process_button')
        self.open_file_button = self.findChild(QPushButton, 'open_file_button')
        self.input = self.findChild(QTextEdit, 'input')
        self.output = self.findChild(QTextEdit, 'output')
        self.output.setReadOnly(True)
        self.method = self.findChild(QComboBox, 'method')
        self.operation = self.findChild(QComboBox, 'operation')
        self.graphicsView = self.findChild(QGraphicsView, 'graphicsView')

        # Connect button click event to a method
        self.process_button.clicked.connect(self.process)
        self.open_file_button.clicked.connect(self.open_file)

        # Set up the graphics scene
        self.scene = QGraphicsScene()
        self.graphicsView.setScene(self.scene)

        self.font = QFont("Segoe UI", 10)

    def add_text_to_scene(self, text, x=0, y=0, color=Qt.GlobalColor.black, font=None):
        """
        Helper method to add text to the scene with customization options.
        """
        text_item = QGraphicsTextItem(text)
        text_item.setPos(x, y)
        text_item.setDefaultTextColor(color)
        text_item.setFont(font if font else self.font)
        text_item.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.scene.addItem(text_item)

    def process(self):
        # Reset the scene
        self.scene.clear()

        # Get input text and options
        text = self.input.toPlainText()
        algorithm = self.method.currentText()
        operation = self.operation.currentText()

        self.y_offset = 0  # Track the vertical position for text placement

        algorithm_functions = {
            "BWT": self.BWT,
            "RLE": self.RLE,
            "Huffman": self.Huffman,
        }
        self.codes = None

        if algorithm == 'BWT and RLE and Huffman':
            if "Encode" in operation:
                # Encode: BWT → RLE → Huffman
                for algo in algorithm_functions.keys():
                    text = algorithm_functions[algo](text, "Encode")
                self.output.setPlainText(text)
            if "Decode" in operation:
                # Decode: Huffman → RLE → BWT
                for algo in reversed(algorithm_functions.keys()):
                    text = algorithm_functions[algo](text, "Decode")
                if operation == 'Decode':
                    self.output.setPlainText(text)
        else:
            func = algorithm_functions[algorithm]
            if "Encode" in operation:
                text = func(text, "Encode")
                self.output.setPlainText(text)
            if "Decode" in operation:
                text = func(text, "Decode")
                if operation == 'Decode':
                    self.output.setPlainText(text)

    def BWT(self, text, operation):
        if operation == "Encode":
            encoded, rotations = bwt_encode(text)
            self.add_text_to_scene("BWT Encoding Steps:", x=0, y=self.y_offset, color=Qt.GlobalColor.blue,
                                   font=QFont("Segoe UI", 12, QFont.Weight.Bold))
            self.y_offset += 30
            self.add_text_to_scene(f"All Rotations: {rotations}", x=0, y=self.y_offset, color=Qt.GlobalColor.black)
            self.y_offset += 20
            self.add_text_to_scene(f"Sorted Rotations: {sorted(rotations)}", x=0, y=self.y_offset, color=Qt.GlobalColor.black)
            self.y_offset += 20
            self.add_text_to_scene(f"BWT Encoded Result: {encoded}", x=0, y=self.y_offset, color=Qt.GlobalColor.darkGreen)
            text = encoded
            self.y_offset += 40

        else:
            decoded, iteration = bwt_decode(text)
            self.add_text_to_scene("BWT Decoding Steps:", x=0, y=self.y_offset, color=Qt.GlobalColor.red,
                                   font=QFont("Segoe UI", 12, QFont.Weight.Bold))
            self.y_offset += 30
            for i, line in enumerate(iteration):
                self.add_text_to_scene(f"Iteration {i + 1}: {line}", x=0, y=self.y_offset, color=Qt.GlobalColor.darkBlue)
                self.y_offset += 20
            self.add_text_to_scene(f"BWT Decoded Result: {decoded}", x=0, y=self.y_offset, color=Qt.GlobalColor.darkGreen)
            text = decoded
            self.y_offset += 40

        return text

    def RLE(self, text, operation):
        if operation == "Encode":
            encoded = rle_encode(text)
            self.add_text_to_scene("RLE Encoding Steps:", x=0, y=self.y_offset, color=Qt.GlobalColor.blue,
                                   font=QFont("Segoe UI", 12, QFont.Weight.Bold))
            self.y_offset += 30
            self.add_text_to_scene(f"RLE Encoded Result: {encoded}", x=0, y=self.y_offset, color=Qt.GlobalColor.darkGreen)
            text = encoded
            self.y_offset += 40

        else:
            decoded = rle_decode(text)
            self.add_text_to_scene("RLE Decoding Steps:", x=0, y=self.y_offset, color=Qt.GlobalColor.red,
                                   font=QFont("Segoe UI", 12, QFont.Weight.Bold))
            self.y_offset += 30
            self.add_text_to_scene(f"RLE Decoded Result: {decoded}", x=0, y=self.y_offset, color=Qt.GlobalColor.darkGreen)
            text = decoded
            self.y_offset += 40

        return text

    def Huffman(self, text, operation):
        if operation == "Encode":
            freq_dict = Counter(text)
            tree = build_huffman_tree(freq_dict)
            self.codes = generate_huffman_codes(tree)
            encoded = huffman_encode(text, self.codes)

            self.add_text_to_scene("Huffman Encoding Steps:", x=0, y=self.y_offset, color=Qt.GlobalColor.blue, font=QFont("Segoe UI", 12, QFont.Weight.Bold))
            self.y_offset += 30
            self.add_text_to_scene(f"Frequency Table: {freq_dict}", x=0, y=self.y_offset, color=Qt.GlobalColor.black)
            self.y_offset += 20

            # Create clickable text item
            text_item = ClickableTextItem("Click here to open the Huffman Tree!")
            text_item.setPos(0, self.y_offset)
            text_item.setDefaultTextColor(Qt.GlobalColor.red)
            text_item.clicked.connect(lambda: self.open_huffman_tree(tree))  # Connect click to show tree
            self.scene.addItem(text_item)
            self.y_offset += 40

            self.add_text_to_scene(f"Huffman Codes: {self.codes}", x=0, y=self.y_offset, color=Qt.GlobalColor.black)
            self.y_offset += 20
            self.add_text_to_scene(f"Huffman Encoded Result: {encoded}", x=0, y=self.y_offset, color=Qt.GlobalColor.darkGreen)
            text = encoded
            self.y_offset += 40

        else:
            codes = json.loads(self.show_input_dialog().replace("'", '"')) if operation == "Decode" and self.codes is None else self.codes
            decoded = huffman_decode(text, codes)

            self.add_text_to_scene("Huffman Decoding Steps:", x=0, y=self.y_offset, color=Qt.GlobalColor.red, font=QFont("Segoe UI", 12, QFont.Weight.Bold))
            self.y_offset += 30
            self.add_text_to_scene(f"Huffman Decoded Result: {decoded}", x=0, y=self.y_offset, color=Qt.GlobalColor.darkGreen)
            text = decoded
            self.y_offset += 40

        return text

    def calculate_subtree_widths(self, node):
        """
        Calculate the width of each subtree based on the number of leaf nodes.
        """
        if node is None:
            return 0
        if node.left is None and node.right is None:  # Leaf node
            return 1
        return self.calculate_subtree_widths(node.left) + self.calculate_subtree_widths(node.right)

    def draw_huffman_tree(self, node, x, y, x_offset):
        """
        Draws the Huffman tree on the QGraphicsScene using calculated positions.

        Args:
            node: The current node of the Huffman tree.
            x: X-coordinate of the current node.
            y: Y-coordinate of the current node.
            x_offset: Horizontal offset for positioning child nodes.
        """
        if node is None:
            return

        # Node radius
        radius = 20

        # Draw the current node as a circle
        ellipse = QGraphicsEllipseItem(x - radius, y - radius, 2 * radius, 2 * radius)
        ellipse.setPen(QPen(Qt.GlobalColor.black))
        ellipse.setBrush(QBrush(QColor(200, 200, 255)))
        self.scene.addItem(ellipse)

        # Add text inside the node (character and frequency)
        text = f"{node.char}:{node.freq}" if node.char else f"{node.freq}"
        text_item = QGraphicsTextItem(text)
        text_item.setPos(x - radius / 2, y - radius / 2)
        self.scene.addItem(text_item)

        # Draw left child
        if node.left:
            left_width = self.calculate_subtree_widths(node.left)
            left_x = x - x_offset * left_width
            left_y = y + 100  # Vertical spacing
            self.scene.addLine(x, y + radius, left_x, left_y - radius, QPen(Qt.GlobalColor.black))
            self.draw_huffman_tree(node.left, left_x, left_y, x_offset / 2)

        # Draw right child
        if node.right:
            right_width = self.calculate_subtree_widths(node.right)
            right_x = x + x_offset * right_width
            right_y = y + 100
            self.scene.addLine(x, y + radius, right_x, right_y - radius, QPen(Qt.GlobalColor.black))
            self.draw_huffman_tree(node.right, right_x, right_y, x_offset / 2)

    def open_huffman_tree(self, tree):
        """
        Opens the Huffman tree visualization in a dialog window.
        """
        # Create a new dialog to display the Huffman tree
        self.tree_window = QDialog(self)
        self.tree_window.setWindowTitle("Huffman Tree")
        self.tree_window.setGeometry(200, 200, 1000, 800)

        # Create a QGraphicsView and QGraphicsScene for drawing the tree
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene, self.tree_window)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)  # Enable antialiasing for smooth edges

        # Set up the layout
        layout = QVBoxLayout()
        layout.addWidget(self.view)
        self.tree_window.setLayout(layout)

        # Reset the scene and draw the tree
        self.scene.clear()

        # Calculate the total width of the tree
        total_width = self.calculate_subtree_widths(tree) * 50  # Adjust scaling factor (50)
        x_offset = total_width / 2

        # Draw the tree starting from the root
        self.draw_huffman_tree(tree, x=500, y=50, x_offset=x_offset)

        # Show the tree window
        self.tree_window.exec()

    def open_file(self):
        file_dialog = QFileDialog.getOpenFileNames(
            self,
            "Open Files",
            os.path.join(os.path.expanduser('~'), 'Documents'),  # Default directory (optional)
        )

        # Get the list of selected file paths
        file_paths = file_dialog[0]

        with open(file_paths[0], "r") as file:
            self.input.setPlainText(file.read())

    def show_input_dialog(self):
        # Define the question
        question = "Please enter your code table:"

        # Show the input dialog
        text, ok = QInputDialog.getText(self, 'Input Dialog', question)

        # If the user pressed OK and entered text
        if ok and text:
            return text.strip()


# Run the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec())