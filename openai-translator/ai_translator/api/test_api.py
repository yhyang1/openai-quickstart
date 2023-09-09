from fastapi.testclient import TestClient
import pytest
from api import APIManager
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

import os

from utils import ArgumentParser, ConfigLoader, LOG
from model import GLMModel, OpenAIModel
from translator import PDFTranslator

@pytest.fixture(scope="session")
def openai_api_key(request):
    openai_api_key_value = request.config.option.openai_api_key
    if openai_api_key_value is None:
        pytest.skip()
    return openai_api_key_value

config_loader = ConfigLoader('config.yaml')
config_app = config_loader.load_config()
model_name = config_app['OpenAIModel']['model']
api_key = openai_api_key if openai_api_key else config_app['OpenAIModel']['api_key']
logger.debug(api_key)
model = OpenAIModel(model=model_name, api_key=api_key)
file_format_app = config_app['common']['file_format']
translator = PDFTranslator(model)

client = TestClient(APIManager(translator, config_app).app)

def test_upload_pdf():
    # Use a sample PDF for testing
    test_pdf_path = "tests/test.pdf"  # Replace with your test PDF's path

    with open(test_pdf_path, "rb") as f:
        response = client.post("/upload/", files={"file": f.read()})

    assert response.status_code == 200
    assert "file_id" in response.json()

    return response.json()["file_id"]  # for further use

def test_trigger_translation():
    file_id = test_upload_pdf()

    response = client.post(f"/translate/{file_id}", json={"target_language": "chinese", "file_format": "markdown"})
    assert response.status_code == 200
    assert response.json()["status"] == "Translation started"

def test_translation_status():
    file_id = test_upload_pdf()

    response = client.get(f"/status/{file_id}")
    assert response.status_code == 200
    assert response.json()["status"] in ["uploaded", "processing", "completed"]

def test_download_translated_file():
    file_id = test_upload_pdf()

    response = client.get(f"/download/{file_id}")
    if response.status_code == 404:
        assert "detail" in response.json()
    else:
        assert response.status_code == 200
        # Further checks can be added based on the content of the downloaded file

if __name__ == "__main__":
    pytest.main()
