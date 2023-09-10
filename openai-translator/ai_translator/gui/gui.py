import sys
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton,
                             QFileDialog, QTextEdit, QLabel, QComboBox, QLineEdit)

from translator import PDFTranslator
from translator.pdf_parser import PDFParser
from translator.writer import Writer
from utils import LOG
from book import ContentType


class TranslatorApp(QWidget):
    def __init__(self, pdf_translator: PDFTranslator, config: dict):
        super().__init__()
        self.pdf_translator = pdf_translator
        self.config = config
        self.pdf_parser = PDFParser()
        self.writer = Writer()
        self.book = None

        # UI Initialization
        self.init_ui()

    def get_save_file_format(self):
        if self.config['common']['file_format'] == 'PDF':
            return 'PDF (*.pdf)'
        elif self.config['common']['file_format'] == 'markdown':
            return 'Markdown (*.md)'
        elif self.config['common']['file_format'] == 'TXT':
            return 'TXT (*.txt)'
        else:
            return 'All Files (*);;Text Files (*.txt)'

    def init_ui(self):
        self.setWindowTitle('File Translator')

        layout = QVBoxLayout()

        # File Selection
        self.file_path_label = QLabel('Selected File: None')
        self.select_file_btn = QPushButton('Select File')
        self.select_file_btn.clicked.connect(self.on_select_file)
        layout.addWidget(self.file_path_label)
        layout.addWidget(self.select_file_btn)

        # File Content Preview
        self.file_preview = QTextEdit()
        self.file_preview.setPlaceholderText("File content will be shown here...")
        self.file_preview.setReadOnly(True)
        layout.addWidget(self.file_preview)

        # Translate Button
        self.translate_btn = QPushButton('Translate')
        self.translate_btn.clicked.connect(self.on_translate)
        layout.addWidget(self.translate_btn)

        # Translation Result
        self.translation_result = QTextEdit()
        self.translation_result.setPlaceholderText("Translation result will be shown here...")
        self.translation_result.setReadOnly(True)
        layout.addWidget(self.translation_result)

        # Save Button
        self.save_btn = QPushButton('Save Translation')
        self.save_btn.clicked.connect(self.on_save)
        layout.addWidget(self.save_btn)

        # Create a label and dropdown for translation style
        self.style_label = QLabel("Translation Style:", self)
        self.style_dropdown = QComboBox(self)
        self.style_dropdown.addItems(["小说", "新闻稿", "作家风格", "Custom"])
        self.style_dropdown.currentIndexChanged.connect(self.style_changed)

        # Create a line edit for custom style input
        self.custom_style_input = QLineEdit(self)
        self.custom_style_input.setPlaceholderText("Enter custom style...")
        self.custom_style_input.setDisabled(True)  # Disabled by default

        # Add style dropdown and custom input to layout
        style_layout = QVBoxLayout()
        style_layout.addWidget(self.style_label)
        style_layout.addWidget(self.style_dropdown)
        style_layout.addWidget(self.custom_style_input)
        layout.addLayout(style_layout)

        # Select pages to translate
        self.pages_label = QLabel("Pages to Translate:", self)
        # add page selecter, has numbernual values
        self.pages_dropdown = QComboBox(self)
        self.pages_dropdown.addItems(["All Pages", "First Page Only", "First 5 Pages", "First 10 Pages", "First 20 Pages"])
        layout.addWidget(self.pages_label)
        layout.addWidget(self.pages_dropdown)

        self.setLayout(layout)

    def on_select_file(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Select File", "", "All Files (*);;Text Files (*.txt)",
                                                   options=options)
        if file_name:
            self.file_name = file_name
            self.file_path_label.setText('Selected File: ' + file_name)
            # TODO: add parameter pages
            self.book = self.pdf_parser.parse_pdf(file_name)
            # combine text only contents from book into preview
            for page in self.book.pages:
                for content in page.contents:
                    if content.content_type == ContentType.TEXT:
                        self.file_preview.append(content.original)
            # set pages by default to all pages
            self.pages_dropdown.setCurrentIndex(0)

    def on_translate(self):
        file_format = self.config['common']['file_format']
        # Retrieve the selected style
        style = self.style_dropdown.currentText()
        if style == "Custom":
            style = self.custom_style_input.text()

        if self.file_name:
            # get number values for pages
            # TODO: better page selection
            switch = {
                "All Pages": None,
                "First Page Only": 1,
                "First 5 Pages": 5,
                "First 10 Pages": 10,
                "First 20 Pages": 20
            }
            pages = switch.get(self.pages_dropdown.currentText(), None)
            LOG.debug(f"pages: {pages}")
            self.book = self.pdf_translator.translate_pdf(self.file_name, style=style, file_format=file_format,
                                                          pages=pages, save=False)
            # prepare the translated content
            translated_content = ''
            for page in self.book.pages:
                for content in page.contents:
                    if content.content_type == ContentType.TEXT:
                        translated_content += content.translation
            LOG.debug(f"translated content type: {type(translated_content)}")
            self.translation_result.setText(translated_content)
        else:
            self.file_preview.setText('Please select a file first.')

    def on_save(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Translation", "",
                                                   f"{self.get_save_file_format()};;All Files (*)", options=options)
        if file_name is None:
            file_name = self.file_name.replace('.pdf', f'_translated.{self.config["common"]["file_format"].lower()}')
        self.writer.save_translated_book(self.book, file_name, self.config['common']['file_format'])

    def style_changed(self, index):
        if self.style_dropdown.currentText() == "Custom":
            self.custom_style_input.setDisabled(False)
        else:
            self.custom_style_input.setDisabled(True)
            self.custom_style_input.clear()
