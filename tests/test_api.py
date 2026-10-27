"""
Tests fonctionnels de l'API /predict.

Couvre :
- l'API répond (health, root)
- un cas valide fonctionne (horreur + comédie)
- un cas invalide est refusé (texte trop court, champ manquant, mauvais type)
"""
import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture(scope="session")
def client():
    """Un seul client pour toute la session → le modèle se charge une seule fois."""
    with TestClient(app) as c:
        yield c


# --- 1) L'API répond ---

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.json() == {"Hello": "World"}


# --- 2) Cas valide : le modèle prédit correctement ---

def test_predict_horror(client):
    r = client.post("/predict", json={
        "text": "A serial killer stalks and murders entire families in a haunted house at night. Blood everywhere."
    })
    assert r.status_code == 200
    data = r.json()
    assert data["classe"] == "Horreur"
    assert 0.0 <= data["probabilite"] <= 1.0
    assert data["version"] == "1.0.0"


def test_predict_comedy(client):
    r = client.post("/predict", json={
        "text": "A clumsy man keeps making hilarious mistakes at a disastrous wedding. Everyone laughs at his jokes."
    })
    assert r.status_code == 200
    assert r.json()["classe"] == "Comédie"


# --- 3) Cas invalides : l'API refuse proprement ---

def test_text_too_short(client):
    """Texte < 10 caractères → Pydantic renvoie 422 avant d'appeler le modèle."""
    r = client.post("/predict", json={"text": "court"})
    assert r.status_code == 422


def test_missing_field(client):
    """Body vide → 422 (champ 'text' requis)."""
    r = client.post("/predict", json={})
    assert r.status_code == 422


def test_wrong_type(client):
    """text = entier au lieu de string → 422."""
    r = client.post("/predict", json={"text": 12345})
    assert r.status_code == 422