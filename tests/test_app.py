import pytest
import os
from app import create_app
from config import get_config

@pytest.fixture(autouse=True)
def setup_test_env():
    """테스트 환경 설정"""
    os.environ["FLASK_ENV"] = "testing"
    yield
    os.environ.pop("FLASK_ENV", None)

@pytest.fixture
def app():
    """테스트 애플리케이션 픽스처"""
    app = create_app()
    return app

@pytest.fixture
def client(app):
    """테스트 클라이언트 픽스처"""
    return app.test_client()

def test_index_page(client):
    """인덱스 페이지 테스트"""
    response = client.get('/')
    assert response.status_code == 200

def test_config_loading():
    """설정 로딩 테스트"""
    config = get_config()
    assert config.ENV == "testing"
    assert config.TESTING == True
    assert config.DEBUG == True

def test_error_handling(client):
    """에러 핸들링 테스트"""
    response = client.get('/non-existent-path')
    assert response.status_code == 404
    
    data = response.get_json()
    assert data["error"] == True
    assert "message" in data 