import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils import ArgumentParser, ConfigLoader, LOG
from model import GLMModel, OpenAIModel
from translator import PDFTranslator
from gui import TranslatorApp

if __name__ == "__main__":
    argument_parser = ArgumentParser()
    args = argument_parser.parse_arguments()
    config_loader = ConfigLoader(args.config)

    config = config_loader.load_config()

    model_name = args.openai_model if args.openai_model else config['OpenAIModel']['model']
    api_key = args.openai_api_key if args.openai_api_key else config['OpenAIModel']['api_key']
    model = OpenAIModel(model=model_name, api_key=api_key)


    pdf_file_path = args.book if args.book else config['common']['book']
    file_format = args.file_format if args.file_format else config['common']['file_format']

    # 实例化 PDFTranslator 类，并调用 translate_pdf() 方法
    translator = PDFTranslator(model)
    if args.gui:
        from PySide6.QtWidgets import QApplication
        app = QApplication(sys.argv)
        main_win = TranslatorApp(translator, config)
        main_win.show()
        sys.exit(app.exec_())
    elif args.api:
        from api import APIManager
        api_manager = APIManager(translator, config)
        api_manager.run()
    else:
        translator.translate_pdf(pdf_file_path, file_format)
