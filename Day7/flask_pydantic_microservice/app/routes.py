from flask import Blueprint, request, jsonify, g
from pydantic import ValidationError
from app.schemas import PredictionRequest, PredictionResponse
from app.logging_config import logger
import uuid
import time


prediction_bp = Blueprint("prediction_bp", __name__)

predictions_db = {}

@prediction_bp.route("/", methods=["GET"])
def home():
    return {
        "message": "Flask Microservice is running"
    }, 200

@prediction_bp.before_request
def before_request():
    g.start_time = time.time()
    g.correlation_id = str(uuid.uuid4())


@prediction_bp.after_request
def after_request(response):
    duration = round(time.time() - g.start_time, 4)

    logger.info(
        "request_log",
        correlation_id=g.correlation_id,
        method=request.method,
        path=request.path,
        status=response.status_code,
        duration=duration
    )

    response.headers["X-Correlation-ID"] = g.correlation_id
    return response


@prediction_bp.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "success",
        "message": "Service is running"
    }), 200


@prediction_bp.route("/predictions", methods=["POST"])
def create_prediction():
    try:
        payload = PredictionRequest(**request.get_json())

        prediction_id = str(uuid.uuid4())

        result = "Approved" if payload.salary >= 50000 else "Rejected"

        response_data = PredictionResponse(
            prediction_id=prediction_id,
            result=result,
            message=f"Prediction created successfully for {payload.name}"
        )

        predictions_db[prediction_id] = response_data.model_dump()

        return jsonify(response_data.model_dump()), 201

    except ValidationError as e:
        return jsonify({
            "error": "Validation Error",
            "details": e.errors()
        }), 422

    except Exception as e:
        return jsonify({
            "error": "Internal Server Error",
            "message": str(e)
        }), 500


@prediction_bp.route("/predictions/<prediction_id>", methods=["GET"])
def get_prediction(prediction_id):
    prediction = predictions_db.get(prediction_id)

    if not prediction:
        return jsonify({
            "error": "Not Found",
            "message": "Prediction ID not found"
        }), 404

    return jsonify(prediction), 200