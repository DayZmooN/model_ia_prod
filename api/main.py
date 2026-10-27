from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
from pathlib import Path
import joblib
import keras
from langdetect import detect, LangDetectException



MODEL_DIR = Path("model")
MODEL_PATH = MODEL_DIR / "model.keras"
VECTORIZER_PATH = MODEL_DIR / "vectoriseur.joblib"

model = None
vectorizer = None
model_version = "1.0.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    global model, vectorizer
    print("⏳ Chargement du modèle...")
    model = keras.models.load_model(MODEL_PATH)
    vectorizer = joblib.load(VECTORIZER_PATH)
    print(f"✅ Modèle chargé : {MODEL_PATH}")
    print(f"✅ Vectoriseur chargé : {VECTORIZER_PATH}")
    yield



app = FastAPI(
    title="Classifieur de résumés de films",
    description=(
        "API de classification Horreur vs Comédie basée sur un réseau Keras + TF-IDF. "
        "⚠️ Le modèle accepte uniquement des résumés **en anglais**."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


class MovieInput(BaseModel):
    text: str = Field(
        ...,
        min_length=10,
        description="Résumé de film **en anglais** (le modèle est entraîné sur des textes anglais).",
        examples=["A serial killer stalks families in a haunted house at night."]
    )


@app.get("/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/predict")
def predict_movie(input_data: MovieInput):
    """Reçoit un résumé, renvoie la classe, la probabilité et la version du modèle."""
    if model is None or vectorizer is None:
        raise HTTPException(status_code=500, detail="Modèle ou vectoriseur non chargé.")

    clean_text = input_data.text.strip()
    if len(clean_text) < 10:
        raise HTTPException(
            status_code=400,
            detail="Le texte du résumé est trop court ou invalide (minimum 10 caractères requis)."
        )
    
    try:
        if detect(clean_text) != "en":
            raise HTTPException(
                status_code=400,
                detail="Le modèle accepte uniquement des textes en anglais."
            )
    except LangDetectException:
        pass
    try:
        features = vectorizer.transform([clean_text])
        if hasattr(features, "toarray"):
            features = features.toarray()

        prediction_prob = float(model.predict(features)[0][0])
        predicted_class = "Horreur" if prediction_prob >= 0.5 else "Comédie"
        confidence = prediction_prob if prediction_prob >= 0.5 else (1 - prediction_prob)

        return {
            "classe": predicted_class,
            "probabilite": round(confidence, 4),
            "version": model_version
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne lors de la prédiction : {str(e)}")