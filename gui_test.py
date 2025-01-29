import json
import re
import sys
import os
from datetime import datetime, timedelta
from collections import Counter
import pickle
from PyQt6.QtCore import Qt, QTimer, QEvent
from PyQt6.QtGui import QFont, QPen, QBrush, QColor, QPainter
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QDialog, QVBoxLayout, QGraphicsView,
    QGraphicsScene, QGraphicsEllipseItem, QGraphicsTextItem,
    QFileDialog, QMessageBox, QMenu, QPushButton, QHBoxLayout, QInputDialog, QFrame, QLabel, QComboBox,
    QGraphicsRectItem, QTextEdit, QTabWidget, QSizePolicy, QScrollArea, QGraphicsProxyWidget, QWidget, QGridLayout,
    QGroupBox
)
from PyQt6 import uic

from advanced_compression_tool import (
    bwt_encode, bwt_decode,
    rle_encode, rle_decode,
    build_huffman_tree, generate_huffman_codes,
    huffman_encode, huffman_decode
)

class CompressionHistoryDialog(QDialog):
    def __init__(self, parent=None, compression_history=None):
        super().__init__(parent)
        self.compression_history = compression_history or []

        # Set window properties
        self.setWindowTitle("Compression History")
        screen = QApplication.primaryScreen()
        screen_size = screen.availableGeometry()
        self.resize(int(screen_size.width() * 0.8), int(screen_size.height() * 0.8))

        # Set size constraints
        self.setMinimumSize(800, 600)

        self.setup_ui()
        self.load_history()
        self.update_history_view()  # Ensure the history view is updated initially

    def setup_ui(self):
        self.setWindowTitle("Compression History")
        screen = QApplication.primaryScreen()
        screen_size = screen.availableGeometry()
        self.resize(int(screen_size.width() * 0.8), int(screen_size.height() * 0.8))

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header frame
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #1a1a2e;
                border-bottom: 2px solid #2d3436;
                padding: 10px;
            }
        """)

        # Create main header layout
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(10, 5, 10, 5)
        header_layout.setSpacing(10)

        # Filter group box
        filter_group = QGroupBox("Filters")
        filter_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #3a3a5a;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)

        # Grid layout for filters
        filter_grid = QGridLayout(filter_group)
        filter_grid.setSpacing(10)

        # Method filter
        method_label = QLabel("Method:")
        method_label.setStyleSheet("color: #ffffff;")
        self.method_filter = QComboBox()
        self.method_filter.addItems([
            "All Methods", "BWT", "RLE", "Huffman", "BWT and RLE and Huffman"
        ])

        # Operation filter
        operation_label = QLabel("Operation:")
        operation_label.setStyleSheet("color: #ffffff;")
        self.operation_filter = QComboBox()
        self.operation_filter.addItems([
            "All Operations", "Encode", "Decode", "Encode → Decode"
        ])

        # Date filter
        date_label = QLabel("Date Range:")
        date_label.setStyleSheet("color: #ffffff;")
        self.date_filter = QComboBox()
        self.date_filter.addItems([
            "All Time", "Today", "Last 7 Days", "Last 30 Days"
        ])

        # Common ComboBox style
        combo_style = """
            QComboBox {
                background-color: #262636;
                color: #ffffff;
                border: 1px solid #3a3a5a;
                border-radius: 8px;
                padding: 5px;
                min-width: 180px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #ffffff;
                margin-right: 5px;
            }
        """

        self.method_filter.setStyleSheet(combo_style)
        self.operation_filter.setStyleSheet(combo_style)
        self.date_filter.setStyleSheet(combo_style)

        # Add filters to grid layout
        filter_grid.addWidget(method_label, 0, 0)
        filter_grid.addWidget(self.method_filter, 0, 1)
        filter_grid.addWidget(operation_label, 0, 2)
        filter_grid.addWidget(self.operation_filter, 0, 3)
        filter_grid.addWidget(date_label, 0, 4)
        filter_grid.addWidget(self.date_filter, 0, 5)

        # Add stretching to prevent compression
        filter_grid.setColumnStretch(6, 1)

        # Button container
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)

        # Export and Clear buttons
        self.export_button = QPushButton("Export History")
        self.export_button.setStyleSheet("""
            QPushButton {
                background-color: #2d5a27;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 15px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #336633;
            }
        """)

        self.clear_button = QPushButton("Clear History")
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #8B0000;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 15px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #A00000;
            }
        """)

        button_layout.addStretch()
        button_layout.addWidget(self.export_button)
        button_layout.addSpacing(10)
        button_layout.addWidget(self.clear_button)

        # Add filter group and button container to header layout
        header_layout.addWidget(filter_group)
        header_layout.addWidget(button_container)

        # Graphics view
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setStyleSheet("""
            QGraphicsView {
                background-color: #111111;
                border: none;
            }
        """)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        # Set size policy to make the view expand properly
        self.view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Add widgets to main layout
        layout.addWidget(header_frame)
        layout.addWidget(self.view)

        # Connect signals
        self.method_filter.currentTextChanged.connect(self.update_history_view)
        self.operation_filter.currentTextChanged.connect(self.update_history_view)
        self.date_filter.currentTextChanged.connect(self.update_history_view)
        self.clear_button.clicked.connect(self.clear_history)
        self.export_button.clicked.connect(self.export_history)

    def update_scene_layout(self):
        """Update scene layout and card widths"""
        view_width = self.view.viewport().width()

        # Update all card widths
        for item in self.scene.items():
            if isinstance(item, QGraphicsRectItem):
                current_y = item.rect().y()
                current_height = item.rect().height()
                item.setRect(0, current_y, view_width, current_height)

                # Update positions of child items
                for child in self.scene.items():
                    if not isinstance(child, QGraphicsRectItem):
                        child_pos = child.pos()
                        if current_y < child_pos.y() < current_y + current_height:
                            if isinstance(child, QGraphicsProxyWidget):  # For buttons
                                child.setPos(10, child_pos.y())
                            else:  # For text items
                                if child_pos.x() > view_width / 2:  # Right aligned items
                                    child.setPos(view_width / 2, child_pos.y())
                                else:  # Left aligned items
                                    child.setPos(10, child_pos.y())

        # Update scene rect
        self.scene.setSceneRect(0, 0, view_width, self.scene.itemsBoundingRect().height())

    def update_history_view(self):
        self.scene.clear()
        filtered_history = self.filter_history()
        view_width = self.view.viewport().width()

        if not filtered_history:
            text_item = QGraphicsTextItem("No compression history available")
            text_item.setDefaultTextColor(Qt.GlobalColor.white)
            font = text_item.font()
            font.setPointSize(14)
            text_item.setFont(font)
            self.scene.addItem(text_item)
            text_item.setPos((view_width - text_item.boundingRect().width()) / 2, 20)
            self.scene.setSceneRect(0, 0, view_width, 60)
            return

        y_pos = 10

        for history_item in filtered_history:
            # Create card with exact width
            card_height = 200  # Adjust card height as needed
            card = QGraphicsRectItem(0, y_pos, view_width, card_height)
            card.setBrush(QBrush(QColor("#1a1a2e")))
            card.setPen(QPen(QColor("#2d3436")))
            self.scene.addItem(card)

            # Padding and dimensions
            padding = 20
            left_width = view_width * 0.3  # 30% of width for left column
            middle_width = view_width * 0.3  # 30% of width for middle column
            right_width = view_width * 0.3  # 30% of width for right column
            current_y = y_pos + padding  # Start position inside card

            # Date (Left column)
            date_info = QGraphicsTextItem()
            date_info.setHtml(
                f'<div style="color: #00BFFF; font-size: 12px;">'
                f'<b>Date:</b> {history_item.get("date", "N/A")}'
                f'</div>'
            )
            date_info.setPos(padding, current_y)
            date_info.setTextWidth(left_width - padding)
            self.scene.addItem(date_info)
            current_y += 15

            # Method (Middle column)
            method_info = QGraphicsTextItem()
            method_info.setHtml(
                f'<div style="color: #00BFFF; font-size: 12px;">'
                f'<b>Method:</b> {history_item.get("algorithm", "N/A")}'
                f'</div>'
            )
            method_info.setPos(padding, current_y)
            # method_info.setTextWidth(middle_width - padding)
            self.scene.addItem(method_info)
            current_y += 15

            # Operation and Time (Right column)
            operation_info = QGraphicsTextItem()
            operation_info.setHtml(
                f'<div style="color: #00BFFF; font-size: 12px;">'
                f'<b>Operation:</b> {history_item.get("operation_type", "N/A")}<br>'
                f'<b>Processing Time:</b> {history_item.get("time_taken", 0):.3f}s'
                f'</div>'
            )
            operation_info.setPos(padding, current_y)
            operation_info.setTextWidth(right_width - padding)
            self.scene.addItem(operation_info)
            current_y += 30  # Move to next line inside the card

            # Size information (Middle row)
            size_info = QGraphicsTextItem()
            size_info.setHtml(
                f'<div style="color: #00ff00; font-size: 12px;">'
                f'<b>Original Size:</b> {history_item.get("original_size", 0)} bytes | '
                f'<b>Compressed Size:</b> {history_item.get("compressed_size", 0)} bytes | '
                f'<b>Compression Ratio:</b> {history_item.get("compression_ratio", 0):.2f}%'
                f'</div>'
            )
            size_info.setPos(padding, current_y)
            size_info.setTextWidth(view_width - padding * 2)
            self.scene.addItem(size_info)
            current_y += 30  # Move to next line

            # Text preview (Bottom)
            def truncate_text(text, max_length=50):
                if not text:
                    return "N/A"
                return text if len(text) <= max_length else text[:max_length] + "..."

            text_info = QGraphicsTextItem()
            text_info.setHtml(
                f'<div style="color: #ffffff; font-size: 12px;">'
                f'<b>Input:</b> {truncate_text(history_item.get("original_text", ""))}<br>'
                f'<b>Output:</b> {truncate_text(history_item.get("processed_text", ""))}'
                f'</div>'
            )
            text_info.setPos(padding, current_y)
            text_info.setTextWidth(view_width - padding * 2)
            self.scene.addItem(text_info)
            current_y += 50  # Move to next section

            # Show Full Text button
            show_text_button = QPushButton("Show Full Text")
            show_text_button.setStyleSheet("""
                QPushButton {
                    background-color: #3a3af5;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 4px 8px;
                    min-width: 100px;
                }
                QPushButton:hover {
                    background-color: #4a4af5;
                }
            """)

            def create_button_handler(item_data):
                def button_handler():
                    self.show_full_text_dialog(item_data)

                return button_handler

            show_text_button.clicked.connect(create_button_handler(history_item))

            proxy = self.scene.addWidget(show_text_button)
            proxy.setPos(padding, current_y)
            current_y += show_text_button.sizeHint().height() + 10  # Account for button height and spacing

            # Update y_pos for the next card
            y_pos += max(current_y - y_pos, card_height) + 10  # Add spacing between cards

        # Set scene rect to fit content
        self.scene.setSceneRect(0, 0, view_width, y_pos)
        self.update_scene_layout()

        # Enable scrolling if needed
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

    def show_full_text_dialog(self, item):
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("Full Text View")
            dialog.resize(600, 400)

            layout = QVBoxLayout(dialog)

            # Create tabs for input and output text
            tabs = QTabWidget()
            tabs.setStyleSheet("""
                QTabWidget {
                    background-color: #1a1a2e;
                }
                QTabWidget::pane {
                    border: 1px solid #2d3436;
                }
                QTabBar::tab {
                    background-color: #262636;
                    color: white;
                    padding: 8px 12px;
                    margin: 2px;
                }
                QTabBar::tab:selected {
                    background-color: #3a3af5;
                }
            """)

            # Input text tab
            input_tab = QTextEdit()
            input_tab.setPlainText(item["original_text"])
            input_tab.setReadOnly(True)
            input_tab.setStyleSheet("""
                QTextEdit {
                    background-color: #262636;
                    color: white;
                    border: none;
                    padding: 5px;
                }
            """)
            tabs.addTab(input_tab, "Input Text")

            # Output text tab
            output_tab = QTextEdit()
            output_tab.setPlainText(item["processed_text"])
            output_tab.setReadOnly(True)
            output_tab.setStyleSheet(input_tab.styleSheet())
            tabs.addTab(output_tab, "Processed Text")

            layout.addWidget(tabs)

            # Add close button
            close_button = QPushButton("Close")
            close_button.setStyleSheet("""
                QPushButton {
                    background-color: #3a3af5;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 6px 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #4a4af5;
                }
            """)
            close_button.clicked.connect(dialog.close)
            layout.addWidget(close_button)

            dialog.setStyleSheet("""
                QDialog {
                    background-color: #1a1a2e;
                }
            """)

            dialog.exec()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to show text dialog: {str(e)}"
            )

    def showEvent(self, event):
        """Handle initial show event"""
        super().showEvent(event)
        # Force layout update when dialog is first shown
        QTimer.singleShot(0, self.update_scene_layout)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Update view width to match window width
        self.view.setFixedWidth(self.width())
        # Force scene update
        self.update_scene_layout()

    def filter_history(self):
        filtered = self.compression_history[:]

        try:
            # Filter by method
            method = self.method_filter.currentText()
            if method != "All Methods":
                filtered = [item for item in filtered if item.get('algorithm') == method]

            # Filter by operation
            operation = self.operation_filter.currentText()
            if operation != "All Operations":
                filtered = [item for item in filtered if item.get('operation_type') == operation]

            # Filter by date
            date_filter = self.date_filter.currentText()
            now = datetime.now()
            if date_filter == "Today":
                filtered = [
                    item for item in filtered
                    if datetime.strptime(item.get('date', ''), '%Y-%m-%d %H:%M:%S').date() == now.date()
                ]
            elif date_filter == "Last 7 Days":
                seven_days_ago = now - timedelta(days=7)
                filtered = [
                    item for item in filtered
                    if datetime.strptime(item.get('date', ''), '%Y-%m-%d %H:%M:%S') >= seven_days_ago
                ]
            elif date_filter == "Last 30 Days":
                thirty_days_ago = now - timedelta(days=30)
                filtered = [
                    item for item in filtered
                    if datetime.strptime(item.get('date', ''), '%Y-%m-%d %H:%M:%S') >= thirty_days_ago
                ]
        except Exception as e:
            QMessageBox.warning(self, "Filter Error", f"Error filtering history: {str(e)}")
            return []

        return filtered

    def showEvent(self, event):
        """Handle initial show event"""
        super().showEvent(event)
        # Force layout update when dialog is first shown
        QTimer.singleShot(0, self.update_scene_layout)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Update view width to match window width
        self.view.setFixedWidth(self.width())
        # Force scene update
        self.update_scene_layout()

    def filter_history(self):
        filtered = self.compression_history[:]

        try:
            # Filter by method
            method = self.method_filter.currentText()
            if method != "All Methods":
                filtered = [item for item in filtered if item.get('algorithm') == method]

            # Filter by operation
            operation = self.operation_filter.currentText()
            if operation != "All Operations":
                filtered = [item for item in filtered if item.get('operation_type') == operation]

            # Filter by date
            date_filter = self.date_filter.currentText()
            now = datetime.now()
            if date_filter == "Today":
                filtered = [
                    item for item in filtered
                    if datetime.strptime(item.get('date', ''), '%Y-%m-%d %H:%M:%S').date() == now.date()
                ]
            elif date_filter == "Last 7 Days":
                seven_days_ago = now - timedelta(days=7)
                filtered = [
                    item for item in filtered
                    if datetime.strptime(item.get('date', ''), '%Y-%m-%d %H:%M:%S') >= seven_days_ago
                ]
            elif date_filter == "Last 30 Days":
                thirty_days_ago = now - timedelta(days=30)
                filtered = [
                    item for item in filtered
                    if datetime.strptime(item.get('date', ''), '%Y-%m-%d %H:%M:%S') >= thirty_days_ago
                ]
        except Exception as e:
            QMessageBox.warning(self, "Filter Error", f"Error filtering history: {str(e)}")
            return []

        return filtered

    def export_history(self):
        """Export compression history to a file"""
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Export History",
                "",
                "CSV Files (*.csv);;JSON Files (*.json);;All Files (*.*)"
            )

            if filename:
                if filename.endswith('.csv'):
                    self.export_to_csv(filename)
                elif filename.endswith('.json'):
                    self.export_to_json(filename)
                else:
                    # Default to JSON if no extension specified
                    filename += '.json'
                    self.export_to_json(filename)

                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"History exported to {filename}"
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to export history: {str(e)}"
            )

    def export_to_csv(self, filename):
        """Export history to CSV format"""
        import csv

        fieldnames = [
            'date', 'algorithm', 'operation_type', 'original_text',
            'processed_text', 'original_size', 'compressed_size',
            'compression_ratio', 'time_taken'
        ]

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for item in self.compression_history:
                row = {field: item.get(field, '') for field in fieldnames}
                writer.writerow(row)

    def export_to_json(self, filename):
        """Export history to JSON format"""
        import json

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.compression_history, f, indent=4, ensure_ascii=False)

    def clear_history(self):
        reply = QMessageBox.question(
            self,
            'Clear History',
            'Are you sure you want to clear all compression history?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.compression_history.clear()
            self.update_history_view()
            return True
        return False

    def load_history(self):
        """Load and validate history data"""
        try:
            # Validate required fields
            required_fields = {'date', 'algorithm', 'operation_type', 'original_text',
                               'processed_text', 'original_size', 'compressed_size',
                               'compression_ratio', 'time_taken'}

            valid_history = []
            for item in self.compression_history:
                # Check if all required fields exist
                if all(field in item for field in required_fields):
                    valid_history.append(item)
                # else:
                #     print(f"Warning: Skipping invalid history item: {item}")

            self.compression_history = valid_history
            self.update_history_view()
        except Exception as e:
            QMessageBox.warning(self, "Load Error", f"Error loading history: {str(e)}")

class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # Load the UI file
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
        self.show_huffman_tree_button.clicked.connect(lambda : self.open_huffman_tree(self.current_huffman_tree))
        self.method.currentTextChanged.connect(self.update_huffman_button_state)
        self.operation.currentTextChanged.connect(self.update_huffman_button_state)

        # Connect menu actions
        self.actionOpen.triggered.connect(self.open_file)
        self.actionSave.triggered.connect(self.save_output)
        self.actionExit.triggered.connect(self.close)
        self.actionAbout.triggered.connect(self.show_about)
        self.actionDocumentation.triggered.connect(self.show_documentation)
        self.actionShowHistory.triggered.connect(self.show_compression_history)

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
        self.codes = None
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
            if "Encode" in operation:
                encoded, rotations = bwt_encode(text)
                self.add_text_to_scene("BWT Encoding Steps:", x=0, y=self.y_offset, is_title=True)
                self.add_text_to_scene(f"All Rotations: {rotations}", x=0, y=self.y_offset)
                self.add_text_to_scene(f"BWT Encoded Result: {encoded}", x=0, y=self.y_offset)
                text = encoded
            if 'Decode' in operation:
                decoded, iterations = bwt_decode(text)
                self.add_text_to_scene("BWT Decoding Steps:", x=0, y=self.y_offset, is_title=True)
                for i, iteration in enumerate(iterations):
                    self.add_text_to_scene(f"Iteration {i + 1}: {iteration}", x=0, y=self.y_offset)
                self.add_text_to_scene(f"BWT Decoded Result: {decoded}", x=0, y=self.y_offset)

            if 'Encode' in operation:
                return encoded
            else:
                return decoded
        except Exception as e:
            raise Exception(f"BWT Error: {str(e)}")

    def RLE(self, text, operation):
        """Handle RLE compression"""
        try:
            if "Encode" in operation:
                encoded = rle_encode(text)
                self.add_text_to_scene("RLE Encoding Steps:", x=0, y=self.y_offset, is_title=True)
                self.add_text_to_scene(f"RLE Encoded Result: {encoded}", x=0, y=self.y_offset)
                text = encoded
            if 'Decode' in operation:
                decoded = rle_decode(text)
                self.add_text_to_scene("RLE Decoding Steps:", x=0, y=self.y_offset, is_title=True)
                self.add_text_to_scene(f"RLE Decoded Result: {decoded}", x=0, y=self.y_offset)

            if 'Encode' in operation:
                return encoded
            else:
                return decoded
        except Exception as e:
            raise Exception(f"RLE Error: {str(e)}")

    def Huffman(self, text, operation):
        """Handle Huffman compression"""
        try:
            if "Encode" in operation:
                freq_dict = Counter(text)
                self.current_huffman_tree = build_huffman_tree(freq_dict)
                self.codes = generate_huffman_codes(self.current_huffman_tree)
                encoded = huffman_encode(text, self.codes)

                self.add_text_to_scene("Huffman Encoding Steps:", x=0, y=self.y_offset, is_title=True)
                self.add_text_to_scene(f"Frequency Table: {freq_dict}", x=0, y=self.y_offset)
                self.add_text_to_scene(f"Huffman Codes: {self.codes}", x=0, y=self.y_offset)
                self.add_text_to_scene(f"Huffman Encoded Result: {encoded}", x=0, y=self.y_offset)

                self.show_huffman_tree_button.setEnabled(True)
                text = encoded
            if 'Decode' in operation:
                if not self.codes:
                    self.codes = self.show_input_dialog()
                    # raise ValueError("No Huffman codes available for decoding")

                decoded = huffman_decode(text, self.codes)
                self.add_text_to_scene("Huffman Decoding Steps:", x=0, y=self.y_offset, is_title=True)
                self.add_text_to_scene(f"Huffman Decoded Result: {decoded}", x=0, y=self.y_offset)

            if 'Encode' in operation:
                return encoded
            else:
                return decoded
        except Exception as e:
            raise Exception(f"Huffman Error: {str(e)}")

    def calculate_tree_height(self, node):
        """Calculate the height of the tree"""
        if node is None:
            return 0
        return 1 + max(self.calculate_tree_height(node.left),
                       self.calculate_tree_height(node.right))

    def calculate_subtree_width(self, node, level=0, widths=None):
        """
        Calculate the width needed for each node considering its level.
        Returns a dictionary with level as key and total nodes at that level as value.
        """
        if widths is None:
            widths = {}

        if node is None:
            return widths

        # Initialize or increment the count at this level
        widths[level] = widths.get(level, 0) + 1

        # Recursively calculate for children
        self.calculate_subtree_width(node.left, level + 1, widths)
        self.calculate_subtree_width(node.right, level + 1, widths)

        return widths

    def get_node_horizontal_spacing(self, level, total_levels, window_width):
        """
        Calculate horizontal spacing between nodes at each level
        """
        # Base spacing that increases for lower levels
        min_spacing = 60  # Minimum spacing between nodes
        max_spacing = window_width / 4  # Maximum spacing

        # Calculate spacing based on level
        spacing = max_spacing / (2 ** level)
        return max(min_spacing, spacing)

    def draw_huffman_tree(self, node, x, y, level, total_levels, level_widths, window_width, drawn_positions=None):
        """
        Draws the Huffman tree with improved positioning to avoid overlaps.
        """
        if node is None:
            return

        if drawn_positions is None:
            drawn_positions = {i: [] for i in range(total_levels)}

        # Node properties
        radius = max(25, 30 - (total_levels // 4))

        # Calculate horizontal spacing for this level
        h_spacing = self.get_node_horizontal_spacing(level, total_levels, window_width)

        # Adjust x position if it conflicts with already drawn nodes
        while any(abs(pos - x) < h_spacing for pos in drawn_positions[level]):
            x += h_spacing

        drawn_positions[level].append(x)

        # Draw the current node
        ellipse = QGraphicsEllipseItem(x - radius, y - radius, 2 * radius, 2 * radius)
        ellipse.setPen(QPen(Qt.GlobalColor.black))
        ellipse.setBrush(QBrush(QColor(200, 200, 255)))
        self.huffman_scene.addItem(ellipse)

        # Add text
        text = f"{node.char}:{node.freq}" if node.char else f"{node.freq}"
        text_item = QGraphicsTextItem(text)
        font = text_item.font()
        font.setPointSize(int(max(8, radius * 0.5)))
        text_item.setFont(font)

        # Center text
        text_width = text_item.boundingRect().width()
        text_height = text_item.boundingRect().height()
        text_item.setPos(x - text_width / 2, y - text_height / 2)
        self.huffman_scene.addItem(text_item)

        # Calculate vertical spacing
        vertical_spacing = min(150, max(80, 400 / total_levels))

        # Draw children
        if node.left or node.right:
            next_y = y + vertical_spacing

            if node.left:
                left_x = x - h_spacing
                self.huffman_scene.addLine(x, y + radius, left_x, next_y - radius,
                                           QPen(Qt.GlobalColor.black, 2))
                self.draw_huffman_tree(node.left, left_x, next_y, level + 1,
                                       total_levels, level_widths, window_width,
                                       drawn_positions)

            if node.right:
                right_x = x + h_spacing
                self.huffman_scene.addLine(x, y + radius, right_x, next_y - radius,
                                           QPen(Qt.GlobalColor.black, 2))
                self.draw_huffman_tree(node.right, right_x, next_y, level + 1,
                                       total_levels, level_widths, window_width,
                                       drawn_positions)

    def open_huffman_tree(self, tree):
        self.tree_window = QDialog(self)
        self.tree_window.setWindowTitle("Huffman Tree")

        # Set window size
        screen = QApplication.primaryScreen()
        screen_size = screen.availableGeometry()
        window_width = int(screen_size.width() * 0.8)
        window_height = int(screen_size.height() * 0.8)
        self.tree_window.setGeometry(100, 100, window_width, window_height)

        # Setup scene and view
        self.huffman_scene = QGraphicsScene()
        self.view = QGraphicsView(self.huffman_scene, self.tree_window)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.view.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.view.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)

        # Create zoom buttons
        zoom_in_btn = QPushButton("Zoom In (+)", self.tree_window)
        zoom_out_btn = QPushButton("Zoom Out (-)", self.tree_window)
        reset_zoom_btn = QPushButton("Reset Zoom", self.tree_window)

        button_layout = QHBoxLayout()
        button_layout.addWidget(zoom_in_btn)
        button_layout.addWidget(zoom_out_btn)
        button_layout.addWidget(reset_zoom_btn)
        button_layout.addStretch()

        layout = QVBoxLayout()
        layout.addLayout(button_layout)
        layout.addWidget(self.view)
        self.tree_window.setLayout(layout)

        # Calculate tree properties
        total_levels = self.calculate_tree_height(tree)
        level_widths = self.calculate_subtree_width(tree)

        # Draw tree
        self.huffman_scene.clear()
        start_x = window_width / 2
        start_y = 50

        self.draw_huffman_tree(tree, start_x, start_y, 0, total_levels,
                               level_widths, window_width)

        # Set scene rect with padding
        scene_rect = self.huffman_scene.itemsBoundingRect()
        padding = 100
        scene_rect.adjust(-padding, -padding, padding, padding)
        self.huffman_scene.setSceneRect(scene_rect)

        # Zoom functions
        def zoom_in():
            self.view.scale(1.2, 1.2)

        def zoom_out():
            self.view.scale(1 / 1.2, 1 / 1.2)

        def reset_zoom():
            self.view.fitInView(scene_rect, Qt.AspectRatioMode.KeepAspectRatio)

        zoom_in_btn.clicked.connect(zoom_in)
        zoom_out_btn.clicked.connect(zoom_out)
        reset_zoom_btn.clicked.connect(reset_zoom)

        # Wheel zoom
        def wheelEvent(event):
            if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                if event.angleDelta().y() > 0:
                    zoom_in()
                else:
                    zoom_out()
            else:
                QGraphicsView.wheelEvent(self.view, event)

        self.view.wheelEvent = wheelEvent

        # Show and fit view
        self.tree_window.show()
        QTimer.singleShot(100, lambda: reset_zoom())

        self.tree_window.exec()

    def update_huffman_button_state(self, text):
        """Update Huffman tree button state"""
        self.show_huffman_tree_button.setEnabled(
            text in ["Huffman", "BWT and RLE and Huffman"] and
            "Encode" in self.operation.currentText()
        )

    def save_compression_result(self, original, compressed, method, operation, time_taken):
        """Save compression results with input and output text"""
        result = {
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'algorithm': method,  # This key needs to match
            'operation_type': operation,  # Changed from 'operation' to 'operation_type'
            'original_text': original,
            'processed_text': compressed,
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

    def show_input_dialog(self):
        """Displays an input dialog for the Huffman code table and validates the input."""
        question = "Please enter your Huffman code table in the format:\n{'A': '0', 'B': '10', 'C': '11'}"

        while True:
            # Show the input dialog
            text, ok = QInputDialog.getText(self, 'Input Huffman Code Table', question)

            # Check if the user clicked OK and provided input
            if ok:
                if text.strip():  # Validate that input is not empty
                    try:
                        # Attempt to parse the input as a dictionary
                        code_table = eval(re.search(r'({.*?})', text).group(1))
                        if isinstance(code_table, dict):  # Ensure it's a dictionary
                            return code_table
                        else:
                            raise ValueError("Input is not a valid dictionary.")
                    except Exception as e:
                        QMessageBox.critical(self, "Invalid Input", str(e))
                else:
                    QMessageBox.critical(self, "Input Error", "The input cannot be empty. Please try again.")
            else:
                # User pressed cancel or closed the dialog
                raise ValueError("User cancelled the input.")

    def show_compression_history(self):
        """Show compression history dialog"""
        dialog = CompressionHistoryDialog(self, self.compression_history)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # If history was cleared, save the empty history
            self.save_compression_history()

def load_stylesheet(app, stylesheet_path="styles.qss"):
    """Load application stylesheet"""
    try:
        with open(stylesheet_path, "r") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print(f"Warning: Stylesheet file '{stylesheet_path}' not found!")
    except Exception as e:
        print(f"Error loading stylesheet: {str(e)}")

# Run the application
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