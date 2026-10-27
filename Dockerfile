# ============================================================
# API Classifieur Horreur vs Comédie — Image de production
# ============================================================
# Multi-stage build :
#   - stage "quality-gate" : vérifie que le modèle passe la barrière qualité
#   - stage final          : image runtime minimale, non-root
# ============================================================


# ---------- Étape 1 : barrière qualité ----------
FROM python:3.14-slim AS quality-gate

WORKDIR /check

# Installer uniquement ce que le script de vérification nécessite
RUN pip install --no-cache-dir PyYAML

# Copier strictement les fichiers nécessaires
COPY config.yaml .
COPY model/metrics.json ./model/metrics.json
COPY check_quality.py .

# Si le modèle ne respecte pas les seuils, le build ÉCHOUE ici
RUN python check_quality.py && touch /quality-gate-passed


# ---------- Étape 2 : image runtime ----------
FROM python:3.14-slim

# 🔑 Force la construction du stage quality-gate AVANT celui-ci :
#    si quality-gate échoue, ce COPY --from échoue → le build s'arrête.
COPY --from=quality-gate /quality-gate-passed /quality-gate-passed

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TF_CPP_MIN_LOG_LEVEL=2 \
    TF_ENABLE_ONEDNN_OPTS=1\
    CUDA_VISIBLE_DEVICES=""  

WORKDIR /app

# Dépendances système minimales
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Dépendances Python (couche cachée tant que requirements-api.txt ne change pas)
COPY requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt

# Code applicatif
COPY api/ ./api/
COPY model/model.keras ./model/model.keras
COPY model/vectoriseur.joblib ./model/vectoriseur.joblib
COPY model/metrics.json ./model/metrics.json
COPY config.yaml .

# Utilisateur non-root
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Healthcheck Docker (marque le conteneur "healthy")
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request,sys; \
    sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health', timeout=3).status==200 else 1)"

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]