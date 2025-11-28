# Option 3 Implementation: Always Rewrite Rules File

## Problem
The LLM was generating duplicate rule IDs because it used **append mode** (`write_to_file`), which added new rules without properly tracking existing IDs.

## Solution
Modified the system to **ALWAYS rewrite the entire rules file** (`rewrite_rule_file`) with all rules (existing + new), ensuring unique, sequential IDs.

---

## Changes Made

### 1. `ml_detector/app/services/mcp_client.py`

#### System Prompt (Line 10)
**Before:**
```python
SYSTEM_PROMT = "You are an ModSecurity firewall rule generator. Check old rules before writing new rules to avoid conflict..."
```

**After:**
```python
SYSTEM_PROMT = """You are a ModSecurity firewall rule generator.

IMPORTANT INSTRUCTIONS:
1. ALWAYS call read_rule_file FIRST to read existing rules
2. Parse all existing rule IDs (format: id:XXXX)
3. Find the highest ID number in existing rules
4. Generate NEW rules starting from (highest_id + 1)
5. Use rewrite_rule_file to write ALL rules (existing + new) together
6. NEVER use write_to_file (append mode) - always rewrite the entire file
7. Maintain sequential, unique IDs for all rules"""
```

#### User Prompt (Line 100-112)
**Before:**
```python
prompt = f"Check if this payload is malicious: {json_string}. If malicious, generate rules..."
```

**After:**
```python
prompt = f"""Analyze this payload: {json_string}

If this payload is MALICIOUS:
1. Call read_rule_file to get existing rules
2. Parse existing IDs and find the highest ID
3. Generate NEW ModSecurity rules (starting from highest_id + 1)
4. Call rewrite_rule_file with ALL rules (existing + new)
5. Ensure all IDs are unique and sequential"""
```

#### Tool Call Logic (Lines 62-92)
- Added better handling for `read_rule_file`
- Prioritizes `rewrite_rule_file` over `write_to_file`
- Redirects `write_to_file` calls to `rewrite_rule_file`

### 2. `ml_detector/app/services/mcp_server.py`

**Tool Descriptions Updated:**
```python
@mcp.tool(name="write_to_file", description="[DEPRECATED] Use rewrite_rule_file instead...")
@mcp.tool(name="rewrite_rule_file", description="[PREFERRED] Rewrite the entire rules file...")
```

---

## How It Works Now

```
┌─────────────────────────────────────────────────────────────┐
│  Request 1 (SQLi)                                           │
├─────────────────────────────────────────────────────────────┤
│  1. ML Detector: Malicious → Trigger LLM                    │
│  2. LLM: read_rule_file → (empty)                           │
│  3. LLM: Generate rules with id:1001, 1002                  │
│  4. LLM: rewrite_rule_file(all rules: 1001, 1002)          │
│  ✅ File now contains: 1001, 1002                           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Request 2 (XSS)                                            │
├─────────────────────────────────────────────────────────────┤
│  1. ML Detector: Malicious → Trigger LLM                    │
│  2. LLM: read_rule_file → "id:1001... id:1002..."          │
│  3. LLM: Parse highest ID = 1002                            │
│  4. LLM: Generate new rules with id:1003, 1004              │
│  5. LLM: rewrite_rule_file(all: 1001,1002,1003,1004)       │
│  ✅ File now contains: 1001, 1002, 1003, 1004               │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Request 3 (RCE)                                            │
├─────────────────────────────────────────────────────────────┤
│  1. ML Detector: Malicious → Trigger LLM                    │
│  2. LLM: read_rule_file → "id:1001... id:1004..."          │
│  3. LLM: Parse highest ID = 1004                            │
│  4. LLM: Generate new rule with id:1005                     │
│  5. LLM: rewrite_rule_file(all: 1001-1005)                 │
│  ✅ File now contains: 1001, 1002, 1003, 1004, 1005         │
└─────────────────────────────────────────────────────────────┘
```

---

## Testing

### Quick Test
```bash
./test_duplicate_fix.sh
```

### Manual Test
```bash
# 1. Clear rules
echo "" > ./shared_rules/custom-rules.conf

# 2. Send malicious request
curl -X POST http://localhost:5000/api/detect \
  -H "Content-Type: application/json" \
  -d '{"request_data": {"uri": "/?id=1 OR 1=1"}, "client_ip": "test"}'

# 3. Wait for LLM to generate rules
sleep 15

# 4. Check for duplicates
grep -oP 'id:\K\d+' ./shared_rules/custom-rules.conf | sort | uniq -d
# (Should be empty = no duplicates!)
```

---

## Benefits

✅ **No More Duplicates**: LLM always maintains unique IDs
✅ **Sequential IDs**: Rules are numbered in order (1001, 1002, 1003...)
✅ **Context-Aware**: LLM reads existing rules before generating new ones
✅ **Atomic Updates**: Entire file is rewritten, preventing partial updates
✅ **Self-Healing**: If rules get messy, LLM can reorganize them

---

## Verification

After applying changes, verify:
1. ✅ All containers running: `docker ps`
2. ✅ ML Detector healthy: `curl http://localhost:5000/api/health`
3. ✅ No duplicate IDs: Run test script above
4. ✅ WAF blocking: `./test_blocking.sh`

---

## Rollback (if needed)

If issues occur, revert to append mode:
1. Change system prompt back to less strict instructions
2. Use `write_to_file` instead of `rewrite_rule_file`
3. Rebuild: `docker compose up -d --build ml_detector`
