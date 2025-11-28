#!/bin/bash

echo "══════════════════════════════════════════════════════"
echo "  🧪 Testing Option 3: No More Duplicate IDs"
echo "══════════════════════════════════════════════════════"
echo ""

# Clear existing rules
echo "" > ./shared_rules/custom-rules.conf
echo "✅ Cleared existing rules"
echo ""

# Send 3 different malicious requests
echo "📤 Sending malicious request #1 (SQL Injection)..."
curl -s -X POST http://localhost:5000/api/detect \
  -H "Content-Type: application/json" \
  -d '{"request_data": {"uri": "/?id=1 OR 1=1", "method": "GET"}, "client_ip": "192.168.1.100"}' | python3 -m json.tool
echo ""

sleep 15
echo "📋 Rules after request #1:"
cat ./shared_rules/custom-rules.conf | grep -E "SecRule|^$" || echo "(no rules yet)"
echo ""
echo "---"
echo ""

echo "📤 Sending malicious request #2 (XSS)..."
curl -s -X POST http://localhost:5000/api/detect \
  -H "Content-Type: application/json" \
  -d '{"request_data": {"uri": "/?test=<script>alert(1)</script>", "method": "GET"}, "client_ip": "192.168.1.101"}' | python3 -m json.tool
echo ""

sleep 15
echo "📋 Rules after request #2:"
cat ./shared_rules/custom-rules.conf | grep -E "SecRule|^$" || echo "(no rules yet)"
echo ""
echo "---"
echo ""

echo "📤 Sending malicious request #3 (Command Injection)..."
curl -s -X POST http://localhost:5000/api/detect \
  -H "Content-Type: application/json" \
  -d '{"request_data": {"uri": "/?cmd=; cat /etc/passwd", "method": "GET"}, "client_ip": "192.168.1.102"}' | python3 -m json.tool
echo ""

sleep 15
echo "📋 Final rules after all requests:"
cat ./shared_rules/custom-rules.conf
echo ""

echo "══════════════════════════════════════════════════════"
echo "  🔍 Checking for Duplicate IDs..."
echo "══════════════════════════════════════════════════════"
echo ""

# Extract all IDs and check for duplicates
ids=$(grep -oP 'id:\K\d+' ./shared_rules/custom-rules.conf | sort)
duplicate_ids=$(echo "$ids" | uniq -d)

if [ -z "$duplicate_ids" ]; then
    echo "✅ SUCCESS: No duplicate IDs found!"
    echo ""
    echo "📊 Rule IDs generated:"
    echo "$ids" | tr '\n' ', ' | sed 's/,$/\n/'
else
    echo "❌ FAILURE: Duplicate IDs detected:"
    echo "$duplicate_ids"
fi

echo ""
echo "══════════════════════════════════════════════════════"
