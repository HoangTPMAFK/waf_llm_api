from flask import Blueprint, jsonify, request
from app.services.xgboost_detector import XGBoostDetector
from app.services.mcp_client import run_mcp_client
import threading

main = Blueprint('main', __name__)

@main.route('/api/detect', methods=['POST'])
def malicious_payload_detect():
    data = request.json
    result = data["request_data"]
    detector = XGBoostDetector()
    is_safe = detector.predict([result])
    if not is_safe:
        threading.Thread(target=run_mcp_client, args=([result],), daemon=True).start()
    