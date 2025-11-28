from flask import Blueprint, jsonify, request
from app.services.xgboost_detector import XGBoostDetector
from app.services.mcp_client import run_mcp_client
import threading
import logging
from datetime import datetime
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

main = Blueprint('main', __name__)

detector = XGBoostDetector("app/resources/xgboost_httpParams.json")

detection_log = []

@main.route('/api/detect', methods=['POST'])
def malicious_payload_detect():
    try:
        data = request.json
        result = data.get("request_data", "")
        client_ip = data.get("client_ip", request.remote_addr)
        timestamp = datetime.now().isoformat()
        
        # Convert dict to JSON string if needed for detector
        if isinstance(result, dict):
            result = json.dumps(result)
        
        logger.info(f"🔍 Analyzing request from {client_ip}")
        logger.info(f"📦 Payload preview: {str(result)[:200]}...")
        
        is_safe = detector.predict([result])
        
        if is_safe:
            logger.info(f"✅ Request is SAFE")
            detection_log.append({
                "timestamp": timestamp,
                "ip": client_ip,
                "result": "SAFE",
                "payload": str(result)[:100]
            })
        else:
            logger.warning(f"🚨 MALICIOUS REQUEST DETECTED!")
            logger.warning(f"🎯 Payload: {result}")
            logger.info(f"🤖 Triggering LLM rule generation...")
            
            detection_log.append({
                "timestamp": timestamp,
                "ip": client_ip,
                "result": "MALICIOUS",
                "payload": str(result)
            })
            
            threading.Thread(
                target=run_mcp_client, 
                args=([result],), 
                daemon=True
            ).start()
        
        return jsonify({
            "is_safe": is_safe,
            "status": "processed",
            "timestamp": timestamp
        })
    
    except Exception as e:
        logger.error(f"❌ Error in detection: {str(e)}")
        return jsonify({"error": str(e)}), 500

@main.route('/api/history', methods=['GET'])
def get_history():
    """View detection history"""
    return jsonify({
        "total": len(detection_log),
        "history": detection_log[-50:]
    })

@main.route('/api/rules', methods=['GET'])
def get_generated_rules():
    """View generated ModSecurity rules"""
    try:
        with open("/app/modsec_rules/custom-rules.conf", "r") as f:
            rules = f.read()
        rule_count = len([line for line in rules.split('\n') if 'SecRule' in line])
        return jsonify({
            "rules": rules,
            "count": rule_count
        })
    except FileNotFoundError:
        return jsonify({"rules": "", "count": 0})

@main.route('/api/dashboard', methods=['GET'])
def dashboard():
    """Real-time dashboard data"""
    try:
        with open("/app/modsec_rules/custom-rules.conf", "r") as f:
            rules = f.read()
    except FileNotFoundError:
        rules = ""
    
    total_detections = len(detection_log)
    malicious_count = sum(1 for d in detection_log if d['result'] == 'MALICIOUS')
    safe_count = total_detections - malicious_count
    
    return jsonify({
        "stats": {
            "total_requests": total_detections,
            "malicious": malicious_count,
            "safe": safe_count,
            "rules_generated": len([l for l in rules.split('\n') if 'SecRule' in l])
        },
        "recent_detections": detection_log[-10:],
        "latest_rules": [r for r in rules.split('\n') if r.strip()][-5:] if rules else []
    })

@main.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "ml_detector",
        "detections": len(detection_log)
    })
