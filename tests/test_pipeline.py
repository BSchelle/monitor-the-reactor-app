import pytest
from src.preprocesspredict import PredictionPipeline

def test_pipeline_no_model():
    pipeline = PredictionPipeline()
    assert pipeline.model is None
    assert pipeline.scaler is None

def test_predict_no_model():
    pipeline = PredictionPipeline()
    result = pipeline.predict_with_alert({"temperature":100,"pressure":5,"flowrate":10,"vibration":0.3})
    assert result["probability"] == 0.0
    assert result["alert"] == False
