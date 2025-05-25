import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    """
    Cliente de pruebas reutilizable en todos los test.
    """
    return TestClient(app)
