"""
Test d'intégration de la barrière qualité.

Vérifie que model/metrics.json respecte les seuils de config.yaml.
Doublonne volontairement scripts/check_quality.py : ainsi, un `pytest` seul
suffit à détecter un modèle dégradé, sans dépendre d'un script externe.
"""
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config.yaml"
METRICS_PATH = ROOT / "model" / "metrics.json"


def test_metrics_file_exists():
    assert METRICS_PATH.exists(), f"Fichier absent : {METRICS_PATH}"


def test_config_file_exists():
    assert CONFIG_PATH.exists(), f"Fichier absent : {CONFIG_PATH}"


def test_model_meets_quality_bar():
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))

    f1 = metrics["f1_test"]
    n = metrics["test_size"]

    assert f1 >= config["f1_min"], (
        f"F1 insuffisant : {f1} < {config['f1_min']}"
    )
    assert n >= config["test_size_min"], (
        f"Taille de test insuffisante : {n} < {config['test_size_min']}"
    )