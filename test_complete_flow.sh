#!/bin/bash

echo "══════════════════════════════════════════════════════"
echo "  🧪 Testing Complete WAF → ML → LLM Pipeline"
echo "══════════════════════════════════════════════════════"
echo ""

echo "1️⃣  Sending SQL Injection attack..."
curl -s -m 5 "http://localhost:8080/?id=1' UNION SELECT password FROM users--" > /dev/null 2>&1 &
echo "   ✅ Attack sent"
echo ""

echo "2️⃣  Waiting for LLM rule generation (25 seconds)..."
for i in {25..1}; do
    echo -ne "   ⏳ $i seconds...\r"
    sleep 1
done
echo ""
echo ""

echo "3️⃣  Generated ModSecurity Rules:"
echo "───────────────────────────────────────────────────────"
if [ -s ./shared_rules/custom-rules.conf ]; then
    cat ./shared_rules/custom-rules.conf
else
    echo "   (No rules generated yet)"
fi
echo "───────────────────────────────────────────────────────"
echo ""

echo "4️⃣  Detection History:"
curl -s http://localhost:5000/api/history 2>/dev/null | jq -r '.history[-3:] | .[] | "   \(.timestamp | split("T")[1] | split(".")[0]) - \(.result): \(.payload | .[0:60])"'
echo ""

echo "5️⃣  System Stats:"
curl -s http://localhost:5000/api/dashboard 2>/dev/null | jq '{status, total_requests, malicious, safe, rules_generated}'
echo ""

echo "══════════════════════════════════════════════════════"
echo "  ✅ Test Complete!"
echo "══════════════════════════════════════════════════════"
echo ""
echo "📁 Rules file location: ./shared_rules/custom-rules.conf"
echo "👀 Watch changes: watch -n 1 cat ./shared_rules/custom-rules.conf"
echo ""






