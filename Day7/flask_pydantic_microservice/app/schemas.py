from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    name: str = Field(..., min_length=2)
    age: int = Field(..., gt=0)
    salary: float = Field(..., gt=0)


class PredictionResponse(BaseModel):
    prediction_id: str
    result: str
    message: str