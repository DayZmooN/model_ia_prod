"""
Barrière qualité : vérifie que model/metrics.json respecte config.yaml.

Usage :
    python scripts/check_quality.py

Code de sortie :
    0 → modèle accepté
    1 → modèle rejeté (fichier manquant, seuil non atteint, métrique absente)
"""
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config.yaml"
METRICS_PATH = ROOT / "model" / "metrics.json"


def load_yaml(path: Path) -> dict:
    if not path.exists():
        print(f"❌ Fichier de configuration introuvable : {path}")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_json(path: Path) -> dict:
    if not path.exists():
        print(f"❌ Fichier de métriques introuvable : {path}")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    print("🔍 Barrière qualité — vérification du modèle\n")

    config = load_yaml(CONFIG_PATH)
    metrics = load_json(METRICS_PATH)

    f1_min = config["f1_min"]
    size_min = config["test_size_min"]

    print(f"   Config  : F1 ≥ {f1_min}  |  test_size ≥ {size_min}")
    print(f"   Metrics : {METRICS_PATH.name}")
    print()

    errors = []

    # --- Seuil F1 ---
    f1 = metrics.get("f1_test")
    if f1 is None:
        errors.append("❌ 'f1_test' absent de metrics.json")
    elif f1 < f1_min:
        errors.append(f"❌ F1 insuffisant : {f1:.4f} < {f1_min:.4f}")
    else:
        print(f"✅ F1 OK : {f1:.4f} ≥ {f1_min:.4f}")

    # --- Taille du test ---
    n = metrics.get("test_size")
    if n is None:
        errors.append("❌ 'test_size' absent de metrics.json")
    elif n < size_min:
        errors.append(f"❌ Taille de test insuffisante : {n} < {size_min}")
    else:
        print(f"✅ Taille de test OK : {n} ≥ {size_min}")

    print()

    if errors:
        for e in errors:
            print(e)
        print("\n❌ BARRIÈRE QUALITÉ : ÉCHEC — modèle refusé")
        return 1

    print("✅ BARRIÈRE QUALITÉ : SUCCÈS — modèle accepté")
    return 0


if __name__ == "__main__":
    sys.exit(main())