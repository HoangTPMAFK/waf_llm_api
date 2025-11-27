# WAF Firewall Container

This directory contains the ModSecurity WAF (Web Application Firewall) configuration.

## Architecture

```
User Request → WAF (Port 8080) → ModSecurity Rules Check → Web Interface (Port 8080)
                                        ↓
                                  If malicious detected
                                        ↓
                                  ML Detector → LLM → Generate Rules
                                        ↓
                              Write to /etc/modsec/rules/custom-rules.conf
                                        ↓
                              watch_rules.sh detects change → Nginx reload
```

## Components

- **Dockerfile**: Builds Nginx with ModSecurity module
- **nginx.conf**: Nginx configuration with reverse proxy to web interface
- **modsecurity.conf**: ModSecurity core settings
- **modsec/main.conf**: Main ModSecurity rules file
- **scripts/watch_rules.sh**: Watches for rule changes and reloads nginx

## Ports

- **80**: Internal WAF port (mapped to 8080 on host)

## Volumes

- `modsec_rules`: Shared volume with ml_detector for rule synchronization

## Testing

### Test WAF is working:
```bash
curl http://localhost:8080/
```

### Test XSS blocking (should get 403):
```bash
curl "http://localhost:8080/?test=<script>alert(1)</script>"
```

### Test SQL injection blocking (should get 403):
```bash
curl "http://localhost:8080/?test=union+select+1,2,3"
```

### Check WAF logs:
```bash
docker exec waf_firewall tail -f /var/log/modsec_audit.log
```

## How Rules Are Applied

1. ML detector detects malicious request
2. LLM generates ModSecurity rule via MCP
3. Rule written to `/app/modsec_rules/custom-rules.conf` (shared volume)
4. `watch_rules.sh` detects file change
5. Nginx automatically reloads with new rules
6. Future matching requests are blocked immediately

