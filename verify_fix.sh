#!/bin/bash

echo "══════════════════════════════════════════════════════"
echo "  🧪 Verifying Complete System with Option 3"
echo "══════════════════════════════════════════════════════"
echo ""

echo "1️⃣  Testing ML Detector Health..."
ml_health=$(curl -s http://localhost:5000/api/health | grep -o "healthy")
if [ "$ml_health" = "healthy" ]; then
    echo "   ✅ ML Detector: Running"
else
    echo "   ❌ ML Detector: Failed"
fi
echo ""

echo "2️⃣  Testing WAF Health..."
waf_health=$(curl -s http://localhost:8080/health)
if [ "$waf_health" = "healthy" ]; then
    echo "   ✅ WAF: Running"
else
    echo "   ❌ WAF: Failed"
fi
echo ""

echo "3️⃣  Checking current rules..."
rule_count=$(docker exec waf_firewall grep -c "SecRule" /etc/modsec/rules/custom-rules.conf 2>/dev/null || echo "0")
echo "   Current rules: $rule_count"
echo ""

echo "4️⃣  Sending test malicious request (SQL Injection)..."
response=$(curl -s -X POST http://localhost:5000/api/detect \
  -H "Content-Type: application/json" \
  -d '{"request_data": {"uri": "/?test=1 UNION SELECT password FROM users", "method": "GET"}, "client_ip": "test-fix-verification"}')
echo "   Response: $(echo $response | python3 -m json.tool 2>/dev/null | head -3)"
echo ""

echo "5️⃣  Waiting 15 seconds for LLM to generate rules..."
for i in {15..1}; do
    echo -ne "   ⏳ $i seconds remaining...\r"
    sleep 1
done
echo "   ✅ Wait complete                    "
echo ""

echo "6️⃣  Checking generated rules..."
docker exec waf_firewall cat /etc/modsec/rules/custom-rules.conf > /tmp/current_rules.txt
new_rule_count=$(grep -c "SecRule" /tmp/current_rules.txt 2>/dev/null || echo "0")
echo "   New rule count: $new_rule_count"
echo ""

if [ "$new_rule_count" -gt "0" ]; then
    echo "7️⃣  Checking for duplicate IDs..."
    duplicate_check=$(grep -oP 'id:\K\d+' /tmp/current_rules.txt | sort | uniq -d)
    if [ -z "$duplicate_check" ]; then
        echo "   ✅ No duplicate IDs found!"
        echo ""
        echo "   📋 Generated rule IDs:"
        grep -oP 'id:\K\d+' /tmp/current_rules.txt | sort -n | tr '\n' ', ' | sed 's/,$/\n/'
    else
        echo "   ❌ Duplicate IDs found:"
        echo "   $duplicate_check"
    fi
else
    echo "7️⃣  ⚠️  No rules generated yet (LLM may need more time or check GROQ_API_KEY)"
fi
echo ""

echo "══════════════════════════════════════════════════════"
echo "  System Verification Complete!"
echo "══════════════════════════════════════════════════════"
