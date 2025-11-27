# WAF Log Files

All WAF logs are mounted here from the container for easy access.

## Log Files

### 📋 `modsec_audit.log`
**ModSecurity Audit Log** - Full HTTP request/response details (like Burp Suite)
- Contains complete request headers, body, response headers, and body
- Shows which ModSecurity rules were triggered
- Format: Multi-part entries separated by `---ID---X--` markers

**View:**
```bash
tail -f modsec_audit.log
# or
../view_logs.sh audit
```

### 🔍 `modsec_debug.log`
**ModSecurity Debug Log** - Detailed processing information
- Shows ModSecurity processing steps
- Debug level: 3 (configurable in modsecurity.conf)
- Useful for troubleshooting rule matching

**View:**
```bash
tail -f modsec_debug.log
# or
../view_logs.sh debug
```

### 📊 `nginx_access.log`
**Nginx Access Log** - One-line summary per request
- Simple format: IP, timestamp, method, path, status code
- Easy to parse and analyze
- Good for quick overview

**View:**
```bash
tail -f nginx_access.log
# or
../view_logs.sh access
```

### ❌ `nginx_error.log`
**Nginx Error Log** - Server errors only
- Contains connection errors, upstream failures
- Empty if everything is working correctly

**View:**
```bash
tail -f nginx_error.log
# or
../view_logs.sh error
```

## Quick Commands

### View all logs simultaneously:
```bash
tail -f *.log
# or
./view_logs.sh all
```

### Search for specific IP:
```bash
grep "192.168.1.100" nginx_access.log
```

### Count requests:
```bash
wc -l nginx_access.log
```

### View only POST requests:
```bash
grep "POST" nginx_access.log
```

### Monitor for blocked requests:
```bash
grep -i "block\|deny\|403" nginx_access.log
```

## Log Rotation

Logs will grow over time. To clear them:

```bash
# Clear all logs
truncate -s 0 *.log

# Or use Docker logs rotation (recommended)
# Edit docker-compose.yaml:
#   logging:
#     driver: "json-file"
#     options:
#       max-size: "10m"
#       max-file: "3"
```

## Understanding ModSecurity Audit Log Format

```
---UNIQUE_ID---A--    Transaction header (timestamp, IPs, ports)
---UNIQUE_ID---B--    Request headers
---UNIQUE_ID---C--    Request body (POST data)
---UNIQUE_ID---D--    Reserved
---UNIQUE_ID---E--    Response body
---UNIQUE_ID---F--    Response headers
---UNIQUE_ID---H--    ModSecurity actions/rules matched
---UNIQUE_ID---I--    Request body (for multipart)
---UNIQUE_ID---J--    Reserved
---UNIQUE_ID---K--    Matched rules list
---UNIQUE_ID---Z--    End marker
```

Only enabled parts appear (configured by `SecAuditLogParts` in modsecurity.conf).

