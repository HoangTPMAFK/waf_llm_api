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
        logger.info(f"🔍 Received data: {data}")
        
        request_data = data.get("request_data", "")
        client_ip = data.get("client_ip", request.remote_addr)
        timestamp = datetime.now().isoformat()
        
        if isinstance(request_data, str):
            try:
                request_data = json.loads(request_data)
            except:
                pass
        
        static_file_extensions = ['.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.woff2', '.ttf', '.eot', '.map']
        
        uri = ""
        if isinstance(request_data, dict) and "uri" in request_data:
            uri = str(request_data["uri"]).lower()
        
        if any(uri.endswith(ext) for ext in static_file_extensions):
            logger.info(f"⚡ Skipping static file: {uri}")
            return jsonify({
                "is_safe": True,
                "status": "skipped_static_file",
                "timestamp": timestamp
            })
        
        payload_list = []
        
        if isinstance(request_data, dict):
            if "body" in request_data and request_data["body"]:
                body_str = str(request_data["body"])
                
                try:
                    body_json = json.loads(body_str)
                    if isinstance(body_json, dict):
                        for key, value in body_json.items():
                            payload_list.append(str(value))
                    else:
                        payload_list.append(body_str)
                except:
                    if "&" in body_str or "=" in body_str:
                        for pair in body_str.split("&"):
                            if "=" in pair:
                                key, value = pair.split("=", 1)
                                payload_list.append(str(value))
                            else:
                                payload_list.append(str(pair))
                    else:
                        payload_list.append(body_str)
            
            if "query" in request_data and isinstance(request_data["query"], dict):
                for key, value in request_data["query"].items():
                    payload_list.append(str(value))
        else:
            payload_list.append(str(request_data))
        
        request_data_str = json.dumps(request_data) if isinstance(request_data, dict) else str(request_data)
        
        logger.info(f"🔍 Analyzing request from {client_ip}")
        logger.info(f"📦 Extracted {len(payload_list)} values from request")
        
        if len(payload_list) == 0:
            logger.info(f"⚠️  No payload data to analyze, marking as SAFE")
            is_safe = True
        else:
            logger.info(f"📦 Payload list preview: {payload_list[:3]}...")
            is_safe = detector.predict(payload_list, logger)
        
        if is_safe:
            logger.info(f"✅ Request is SAFE")
            detection_log.append({
                "timestamp": timestamp,
                "ip": client_ip,
                "result": "SAFE",
                "payload": request_data_str[:100]
            })
        else:
            logger.warning(f"🚨 MALICIOUS REQUEST DETECTED!")
            logger.warning(f"🎯 Payload: {request_data_str}")
            logger.info(f"🤖 Triggering LLM rule generation...")
            
            detection_log.append({
                "timestamp": timestamp,
                "ip": client_ip,
                "result": "MALICIOUS",
                "payload": request_data_str
            })
            
            threading.Thread(
                target=run_mcp_client, 
                args=(payload_list,), 
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
