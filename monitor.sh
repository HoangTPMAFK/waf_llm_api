#!/bin/bash

echo "═══════════════════════════════════════════════════════════"
echo "          WAF + ML Detector Live Monitor"
echo "═══════════════════════════════════════════════════════════"
echo ""

while true; do
    clear
    echo "═══════════════════════════════════════════════════════════"
    echo "          WAF + ML Detector Live Monitor"
    echo "═══════════════════════════════════════════════════════════"
    echo "🕐 $(date '+%Y-%m-%d %H:%M:%S')"
    echo "───────────────────────────────────────────────────────────"
    
    # Check if ml_detector is running
    if ! docker ps | grep -q ml_detector; then
        echo "❌ ML Detector container is not running!"
        echo "   Run: docker compose up -d"
        sleep 5
        continue
    fi
    
    # Get dashboard data
    dashboard=$(curl -s http://localhost:5000/api/dashboard 2>/dev/null)
    
    if [ -z "$dashboard" ]; then
        echo "⚠️  Waiting for ML Detector to be ready..."
        sleep 5
        continue
    fi
    
    echo "📊 Statistics:"
    echo "$dashboard" | jq -r '.stats | "  Total Requests: \(.total_requests)\n  Malicious: \(.malicious)\n  Safe: \(.safe)\n  Rules Generated: \(.rules_generated)"' 2>/dev/null || echo "  No data yet"
    
    echo ""
    echo "🚨 Recent Malicious Detections:"
    recent=$(echo "$dashboard" | jq -r '.recent_detections[] | select(.result == "MALICIOUS") | "  [\(.timestamp)] \(.ip) - \(.payload[:80])"' 2>/dev/null)
    if [ -z "$recent" ]; then
        echo "  None yet"
    else
        echo "$recent"
    fi
    
    echo ""
    echo "📋 Latest Generated Rules:"
    rules=$(curl -s http://localhost:5000/api/rules 2>/dev/null | jq -r '.rules' 2>/dev/null)
    if [ -z "$rules" ] || [ "$rules" == "null" ]; then
        echo "  No rules generated yet"
    else
        echo "$rules" | tail -5 | sed 's/^/  /'
    fi
    
    echo ""
    echo "───────────────────────────────────────────────────────────"
    echo "Refreshing every 5 seconds... Press Ctrl+C to stop"
    
    sleep 5
done

