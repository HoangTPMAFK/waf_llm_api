#!/bin/bash

# WAF Log Viewer Script
echo "═══════════════════════════════════════════════════════════"
echo "          WAF Log Viewer - Press Ctrl+C to stop"
echo "═══════════════════════════════════════════════════════════"
echo ""

case "${1:-all}" in
    audit)
        echo "📋 Viewing ModSecurity Audit Log (Full Requests/Responses)"
        echo "───────────────────────────────────────────────────────────"
        tail -f waf_firewall/logs/modsec_audit.log
        ;;
    debug)
        echo "🔍 Viewing ModSecurity Debug Log"
        echo "───────────────────────────────────────────────────────────"
        tail -f waf_firewall/logs/modsec_debug.log
        ;;
    access)
        echo "📊 Viewing Nginx Access Log"
        echo "───────────────────────────────────────────────────────────"
        tail -f waf_firewall/logs/nginx_access.log
        ;;
    error)
        echo "❌ Viewing Nginx Error Log"
        echo "───────────────────────────────────────────────────────────"
        tail -f waf_firewall/logs/nginx_error.log
        ;;
    all)
        echo "📚 Viewing All Logs"
        echo "───────────────────────────────────────────────────────────"
        tail -f waf_firewall/logs/*.log
        ;;
    *)
        echo "Usage: $0 [audit|debug|access|error|all]"
        echo ""
        echo "Options:"
        echo "  audit   - ModSecurity audit log (full request/response)"
        echo "  debug   - ModSecurity debug log (detailed processing)"
        echo "  access  - Nginx access log (one-line per request)"
        echo "  error   - Nginx error log (errors only)"
        echo "  all     - All logs combined (default)"
        exit 1
        ;;
esac

