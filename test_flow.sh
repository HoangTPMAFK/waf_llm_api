#!/bin/bash

echo "═══════════════════════════════════════════════════════════"
echo "     Testing WAF → ML Detector → LLM → Rules Flow"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Check if services are running
echo "🔍 Checking services..."
if ! docker ps | grep -q ml_detector; then
    echo "❌ ML Detector is not running!"
    exit 1
fi

if ! docker ps | grep -q waf_firewall; then
    echo "❌ WAF is not running!"
    exit 1
fi

echo "✅ All services running"
echo ""

# Test 1: Send a safe request
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 1: Safe Request"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Sending: GET /"
response=$(curl -s -X POST http://localhost:5000/api/detect \
  -H "Content-Type: application/json" \
  -d '{"request_data": "GET / HTTP/1.1"}')
echo "Response: $response"
echo ""

sleep 2

# Test 2: XSS Attack
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 2: XSS Attack"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Sending: <script>alert('XSS')</script>"
response=$(curl -s -X POST http://localhost:5000/api/detect \
  -H "Content-Type: application/json" \
  -d '{"request_data": "<script>alert(\"XSS\")</script>", "client_ip": "192.168.1.100"}')
echo "Response: $response"
echo "⏳ Waiting for LLM processing (10 seconds)..."
sleep 10

# Test 3: SQL Injection
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 3: SQL Injection"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Sending: ' OR '1'='1"
response=$(curl -s -X POST http://localhost:5000/api/detect \
  -H "Content-Type: application/json" \
  -d '{"request_data": "\" OR \"1\"=\"1", "client_ip": "192.168.1.101"}')
echo "Response: $response"
echo "⏳ Waiting for LLM processing (10 seconds)..."
sleep 10

# Test 4: Path Traversal
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 4: Path Traversal"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Sending: ../../etc/passwd"
response=$(curl -s -X POST http://localhost:5000/api/detect \
  -H "Content-Type: application/json" \
  -d '{"request_data": "../../etc/passwd", "client_ip": "192.168.1.102"}')
echo "Response: $response"
echo "⏳ Waiting for LLM processing (10 seconds)..."
sleep 10

# Show results
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "                    Test Results"
echo "═══════════════════════════════════════════════════════════"
echo ""

echo "📊 Detection History:"
curl -s http://localhost:5000/api/history | jq '.history[-10:]'

echo ""
echo "📋 Generated ModSecurity Rules:"
curl -s http://localhost:5000/api/rules | jq -r '.rules'

echo ""
echo "📈 Dashboard Statistics:"
curl -s http://localhost:5000/api/dashboard | jq '.stats'

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "✅ Testing Complete!"
echo ""
echo "To view real-time monitoring, run: ./monitor.sh"
echo "To view ML detector logs: docker logs -f ml_detector"
echo "To view WAF logs: ./view_logs.sh"
echo "═══════════════════════════════════════════════════════════"

