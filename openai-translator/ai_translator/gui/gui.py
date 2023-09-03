import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, 
                             QFileDialog, QTextEdit, QLabel)
from PyQt5.QtCore import Qt
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

        self.setLayout(layout)

    def on_select_file(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Select File", "", "All Files (*);;Text Files (*.txt)", options=options)
        if file_name:
            self.file_name = file_name
            self.file_path_label.setText('Selected File: ' + file_name)
            # TODO: add parameter pages
            self.book = self.pdf_parser.parse_pdf(file_name)
            content = self.book.pages[0].contents[0]
            LOG.debug(f"content type: {content.content_type}")
            if content.content_type == ContentType.TEXT:
                self.file_preview.setText(content.original)
            elif content.content_type == ContentType.TABLE:
                self.file_preview.setText(str(content.original))
            else:
                self.file_preview.setText('first page content is not text or table')

    def on_translate(self):
        file_format = self.config['common']['file_format']
        if self.file_name:
            self.book = self.pdf_translator.translate_pdf(self.file_name, file_format=file_format, save=False)
            translated_content = self.book.pages[0].contents[0].translation
            LOG.debug(f"translated content type: {type(translated_content)}")
            self.translation_result.setText(translated_content)
        else:
            self.file_preview.setText('Please select a file first.')

    def on_save(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Translation", "", f"{self.get_save_file_format()};;All Files (*)", options=options)
        if file_name is None:
            file_name = self.file_name.replace('.pdf', f'_translated.{self.config["common"]["file_format"].lower()}')
        self.writer.save_translated_book(self.book, file_name, self.config['common']['file_format'])

