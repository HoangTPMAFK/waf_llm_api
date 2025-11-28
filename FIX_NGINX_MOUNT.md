# ✅ FIXED: nginx.conf Mount Path Issue

## 🔴 Problem Found

The `nginx.conf` was mounted to the **WRONG PATH** in `compose.yaml`:

**Before (Wrong):**
```yaml
- ./waf_firewall/nginx.conf:/etc/nginx/nginx.conf:ro  ❌
```

**After (Correct):**
```yaml
- ./waf_firewall/nginx.conf:/usr/local/openresty/nginx/conf/nginx.conf:ro  ✅
```

OpenResty uses `/usr/local/openresty/nginx/conf/nginx.conf`, NOT `/etc/nginx/nginx.conf`!

---

## 🛠️ How to Apply the Fix

Since I updated `compose.yaml`, you need to **recreate** the WAF container:

```bash
cd /home/lsquare/5th_semester/NCKH/waf_llm_api

# Stop and remove old container
docker stop waf_firewall
docker rm waf_firewall

# Recreate with new mount path
docker-compose up -d waf

# Wait for startup
sleep 5

# Verify config is loaded
docker exec waf_firewall grep "Sending to ML detector" /usr/local/openresty/nginx/conf/nginx.conf
```

**Expected output:** Should find the line with "Sending to ML detector"

---

## 🧪 Test After Fix

Once recreated, test with:

```bash
# Send test request
curl -X POST "http://localhost:8080/login?test=123" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=test" && sleep 2

# Check WAF logs
docker logs waf_firewall --tail 20 | grep "WAF:"

# Check ML detector logs  
docker logs ml_detector --tail 20 | grep "Received"
```

**Expected:**
- WAF logs show: "🔍 WAF: Captured POST /login..."
- ML detector logs show: "🔍 Received data: {...}"

---

## 📝 Summary of All Changes

1. ✅ Fixed `log_by_lua_block` to capture ALL request data BEFORE timer
2. ✅ Moved all `ngx.var` and `ngx.req` calls outside timer context
3. ✅ Fixed `compose.yaml` to mount nginx.conf to correct OpenResty path
4. ⏳ **Next: Recreate container to apply changes**

---

## 🚀 Quick Command (Run This)

```bash
docker stop waf_firewall && docker rm waf_firewall && docker-compose up -d waf && sleep 5 && docker exec waf_firewall grep -c "Sending to ML detector" /usr/local/openresty/nginx/conf/nginx.conf && echo "✅ Config loaded!" || echo "❌ Config not loaded"
```

This will stop, remove, recreate the container, and verify the config is loaded correctly.
