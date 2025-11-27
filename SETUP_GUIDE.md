# WAF + ML Detector + Web Interface Setup Guide

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Network (waf_network)             │
│                                                             │
│  ┌──────────────┐      ┌──────────────┐                   │
│  │   User       │      │              │                   │
│  │   Browser    │──────▶    WAF       │                   │
│  └──────────────┘      │ ModSecurity  │                   │
│                        │  Port: 8080  │                   │
│                        └──────┬───────┘                   │
│                               │                            │
│                               │ proxy_pass                 │
│                               ↓                            │
│                        ┌──────────────┐                   │
│                        │      Web     │                   │
│                        │   Interface  │                   │
│                        │  Port: 8080  │                   │
│                        └──────────────┘                   │
│                                                             │
│                        ┌──────────────┐                   │
│                        │      ML      │                   │
│                        │   Detector   │◀──── API calls    │
│                        │  Port: 5000  │                   │
│                        └──────┬───────┘                   │
│                               │                            │
│                               │ LLM (Groq)                 │
│                               ↓                            │
│                        Generates ModSecurity Rules         │
│                               ↓                            │
│         Shared Volume: /etc/modsec/rules/ ◀───┘           │
│                               │                            │
│                        watch_rules.sh → Nginx reload       │
└─────────────────────────────────────────────────────────────┘
```

## 📦 Components

1. **WAF Firewall** (Port 8080)
   - Nginx with ModSecurity
   - OWASP Core Rule Set
   - Custom LLM-generated rules
   - Auto-reload on rule changes

2. **ML Detector** (Port 5000)
   - XGBoost + SecBERT model
   - Groq LLM integration
   - MCP server for rule generation

3. **Web Interface** (Port 8888 - direct, 8080 via WAF)
   - Vulnerable web application for testing
   - Flask-based authentication system

## 🚀 Quick Start

### 1. Set up environment variables

Edit `.env` file:
```bash
GROQ_API_KEY=your_actual_groq_api_key_here
```

### 2. Build and start all services

```bash
docker compose up -d --build
```

This will take several minutes on first build (ML dependencies are large).

### 3. Verify services are running

```bash
docker ps
```

You should see:
- `waf_firewall` (port 8080)
- `ml_detector` (port 5000)
- `web_interface` (port 8888)

### 4. Test the setup

**Access through WAF (protected):**
```bash
curl http://localhost:8080/
```

**Test XSS blocking:**
```bash
curl "http://localhost:8080/?test=<script>alert(1)</script>"
# Should return: 403 - Request blocked by WAF
```

**Test SQL injection blocking:**
```bash
curl "http://localhost:8080/?test=union+select+1,2,3"
# Should return: 403 - Request blocked by WAF
```

**Direct access (bypass WAF - for debugging only):**
```bash
curl http://localhost:8888/
```

## 🔄 Request Flow

### Normal Request Flow:
1. User sends request to http://localhost:8080
2. WAF checks ModSecurity rules
3. If clean → proxy to web_interface
4. Response returned to user

### Malicious Request Flow:
1. User sends malicious request to http://localhost:8080
2. WAF blocks with existing rules (if matched)
3. OR request reaches web_interface
4. Later: Logs analyzed by ML detector (manual trigger via API)
5. ML detector classifies as malicious
6. Sends payload to LLM via MCP
7. LLM generates ModSecurity rule
8. Rule written to shared volume
9. watch_rules.sh detects change → nginx reload
10. Future similar requests blocked at WAF

## 🧪 Testing ML Detection

Send a test request to ML detector:
```bash
curl -X POST http://localhost:5000/api/detect \
  -H "Content-Type: application/json" \
  -d '{"request_data": "/?id=1 union select * from users--"}'
```

Response:
```json
{
  "is_safe": false,
  "status": "processed"
}
```

When `is_safe` is false, the system automatically triggers LLM rule generation.

## 📊 Monitoring

### View WAF logs:
```bash
docker logs waf_firewall
```

### View ModSecurity audit log:
```bash
docker exec waf_firewall tail -f /var/log/modsec_audit.log
```

### View ML detector logs:
```bash
docker logs ml_detector
```

### View generated rules:
```bash
docker exec ml_detector cat /app/modsec_rules/custom-rules.conf
```

Or from WAF:
```bash
docker exec waf_firewall cat /etc/modsec/rules/custom-rules.conf
```

## 🔧 Troubleshooting

### WAF not starting:
```bash
docker logs waf_firewall
# Check for ModSecurity compilation errors
```

### Rules not reloading:
```bash
docker exec waf_firewall ps aux | grep watch_rules
# Check if watch_rules.sh is running
```

### ML detector failing:
```bash
docker logs ml_detector
# Check if model file exists and GROQ_API_KEY is set
```

### Web interface not accessible:
```bash
docker exec web_interface ps aux | grep gunicorn
# Check if gunicorn is running
```

## 🛠️ Development Commands

### Restart specific service:
```bash
docker compose restart waf
docker compose restart ml_detector
docker compose restart web_interface
```

### Rebuild after code changes:
```bash
docker compose up -d --build <service_name>
```

### View all logs:
```bash
docker compose logs -f
```

### Stop all services:
```bash
docker compose down
```

### Remove volumes (reset rules):
```bash
docker compose down -v
```

## 📝 Next Steps

1. **Test the complete flow:**
   - Send malicious requests
   - Verify ML detection
   - Check rule generation
   - Confirm blocking

2. **Integrate automatic request logging:**
   - Modify WAF to log all requests to ML detector
   - Implement background analysis

3. **Add admin dashboard:**
   - View generated rules
   - Manually trigger scans
   - See blocked request statistics

## 🔐 Security Notes

- Port 8888 (direct web interface) should be closed in production
- Only expose port 8080 (WAF) to the internet
- Set strong GROQ_API_KEY
- Regularly update OWASP Core Rule Set
- Monitor ModSecurity logs for false positives

## 📚 File Structure

```
waf_llm_api/
├── compose.yaml                    # Docker orchestration
├── .env                            # Environment variables
│
├── waf_firewall/                   # WAF container
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── modsecurity.conf
│   ├── modsec/main.conf
│   └── scripts/watch_rules.sh
│
├── ml_detector/                    # ML + LLM backend
│   ├── app/
│   │   ├── routes.py
│   │   └── services/
│   │       ├── xgboost_detector.py
│   │       ├── mcp_client.py
│   │       └── mcp_server.py
│   └── requirements.txt
│
└── web-interface/                  # Test application
    └── src/app.py
```

