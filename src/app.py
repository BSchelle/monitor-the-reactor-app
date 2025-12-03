from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from src.preprocesspredict import PredictionPipeline

app = FastAPI(title="Monitor the Reactor API", version="1.0.0")
pipeline = PredictionPipeline()

class InputData(BaseModel):
    temperature: float = Field(..., ge=-50, le=200)
    pressure: float = Field(..., ge=0, le=50)
    flowrate: float = Field(..., ge=0, le=1000)
    vibration: float = Field(..., ge=0, le=50)
    threshold: Optional[float] = Field(default=0.8, ge=0.0, le=1.0)

@app.get("/")
def root() -> Dict[str, Any]:
    return {"greeting": "Monitor the Reactor API is running"}

@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "modelloaded": pipeline.model is not None,
        "preprocessorloaded": pipeline.scaler is not None,
    }

@app.post("/predict")
def predict(data: InputData) -> Dict[str, Any]:
    payload = data.dict()
    thresh = payload.pop("threshold", 0.8)
    try:
        res = pipeline.predict_with_alert(payload, threshold=thresh)
        res["modelready"] = pipeline.model is not None and pipeline.scaler is not None
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
