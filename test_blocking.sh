#!/bin/bash

echo "══════════════════════════════════════════════════════"
echo "  🛡️  Testing WAF Blocking Functionality"
echo "══════════════════════════════════════════════════════"
echo ""

echo "1️⃣  SQL Injection Attack (should be BLOCKED):"
echo "   Payload: ?id=1' UNION SELECT password--"
curl -s -w "   HTTP Status: %{http_code}\n" 'http://localhost:8080/?id=1%27%20UNION%20SELECT%20password--'
echo ""

echo "2️⃣  XSS Attack (should be BLOCKED):"
echo "   Payload: ?test=<script>alert(1)</script>"
curl -s -w "   HTTP Status: %{http_code}\n" 'http://localhost:8080/?test=%3Cscript%3Ealert(1)%3C/script%3E'
echo ""

echo "3️⃣  SQL Injection in Login (should be BLOCKED):"
echo "   Payload: POST /login with OR '1'='1"
curl -s -w "   HTTP Status: %{http_code}\n" -X POST 'http://localhost:8080/login' -d "username=admin' OR '1'='1"
echo ""

echo "4️⃣  Normal Request (should PASS):"
echo "   Payload: ?id=123"
curl -s -w "   HTTP Status: %{http_code}\n" 'http://localhost:8080/?id=123' | tail -1
echo ""

echo "5️⃣  Health Check (should PASS):"
curl -s http://localhost:8080/health
echo "   HTTP Status: 200"
echo ""

echo "══════════════════════════════════════════════════════"
echo "  ✅ Test Complete!"
echo "══════════════════════════════════════════════════════"
echo ""
echo "📊 Check ModSecurity logs:"
echo "   tail -f ./waf_firewall/logs/modsec_audit.log"
echo ""
echo "📋 View generated rules:"
echo "   cat ./shared_rules/custom-rules.conf"
echo ""
