# ✅ LLM Prompts Updated - Rule Generation Improved

## Changes Made to `mcp_client.py`

### Updated Areas:
1. **SYSTEM_PROMT** - System instructions for the LLM
2. **run_mcp_client prompt** - User prompt with examples

---

## Key Improvements

### 1. **Flexible Regex Patterns**

**Added instructions for whitespace handling:**
```
- \s* = zero or more spaces (optional whitespace)
- \s+ = one or more spaces (required whitespace)
- ['"] = match both single and double quotes
- (?i) = case insensitive matching
```

**Why:** Attackers use variable spacing to evade detection. Rules must handle:
- `admin'or1=1` (no spaces)
- `admin' or 1=1` (with spaces)
- `admin'  or  1 = 1` (multiple spaces)

---

### 2. **Multiple Rule Variations**

**New requirement:**
```
Generate 2-3 rule variations for better detection:
1. Specific pattern with @rx operator
2. Generic variant pattern
3. Simple substring match with @contains operator
```

**Example output expected:**
```nginx
SecRule ARGS "@rx (?i)admin['\"]\s*or\s+1\s*=\s*1" "id:1001,phase:2,deny,status:403,log,msg:'SQL Injection: OR 1=1 attack detected'"
SecRule ARGS "@rx (?i)'\s*or\s+['\"]\s*1\s*['\"]\s*=\s*['\"]\s*1" "id:1002,phase:2,deny,status:403,log,msg:'SQL Injection: OR variant detected'"
SecRule ARGS "@contains ' or 1=1" "id:1003,phase:2,deny,status:403,log,msg:'SQL Injection: Simple OR 1=1 pattern'"
```

---

### 3. **Strict Requirements**

**CRITICAL RULE WRITING REQUIREMENTS:**
- ✅ Variable: `ARGS` (REQUIRED)
- ✅ Phase: `2` (REQUIRED)
- ✅ Action: `deny,status:403,log` (REQUIRED)

**Before:** Rules might use wrong phase or variable
**After:** Explicit requirements prevent mistakes

---

### 4. **Concrete Examples**

**Added real-world rule examples matching current rules:**

```nginx
# Example 1: Specific attack pattern
SecRule ARGS "@rx (?i)admin['\"]\s*or\s+1\s*=\s*1" "id:1001,phase:2,deny,status:403,log,msg:'SQL Injection: OR 1=1 attack detected'"

# Example 2: Generic variant
SecRule ARGS "@rx (?i)'\s*or\s+['\"]\s*1\s*['\"]\s*=\s*['\"]\s*1" "id:1002,phase:2,deny,status:403,log,msg:'SQL Injection: OR variant detected'"

# Example 3: Simple substring
SecRule ARGS "@contains ' or 1=1" "id:1003,phase:2,deny,status:403,log,msg:'SQL Injection: Simple OR 1=1 pattern'"
```

---

## Before vs After

### Before (Old Prompt):
```
Rule Syntax Example:
SecRule ARGS "@rx (?i)(pattern)" "id:1005,phase:2,deny,status:403,log,msg:'Attack description'"
```

**Issues:**
- ❌ No whitespace handling guidance
- ❌ No multiple rule variations
- ❌ Single generic example
- ❌ No quote variation handling

---

### After (New Prompt):
```
CRITICAL RULE WRITING REQUIREMENTS:
- Variable: ARGS (REQUIRED)
- Phase: 2 (REQUIRED)
- Use flexible regex with \s*, \s+, ['"], (?i)
- Generate 2-3 rule variations per attack

Rule Syntax Examples:
SecRule ARGS "@rx (?i)admin['\"]\s*or\s+1\s*=\s*1" "id:1001,phase:2,deny,status:403,log,msg:'SQL Injection: OR 1=1 attack detected'"
SecRule ARGS "@rx (?i)'\s*or\s+['\"]\s*1\s*['\"]\s*=\s*['\"]\s*1" "id:1002,phase:2,deny,status:403,log,msg:'SQL Injection: OR variant detected'"
SecRule ARGS "@contains ' or 1=1" "id:1003,phase:2,deny,status:403,log,msg:'SQL Injection: Simple OR 1=1 pattern'"
```

**Benefits:**
- ✅ Explicit whitespace handling
- ✅ Multiple rule variations
- ✅ Real-world examples
- ✅ Quote variation handling
- ✅ Both @rx and @contains operators

---

## Expected Behavior

When LLM detects SQL injection attack like `admin' or 1=1--`, it will now generate:

**Rule 1 - Specific Pattern:**
```nginx
SecRule ARGS "@rx (?i)admin['\"]\s*or\s+1\s*=\s*1" "id:XXXX,phase:2,deny,status:403,log,msg:'SQL Injection: OR 1=1 attack detected'"
```

**Rule 2 - Generic Variant:**
```nginx
SecRule ARGS "@rx (?i)'\s*or\s+['\"]\s*1\s*['\"]\s*=\s*['\"]\s*1" "id:YYYY,phase:2,deny,status:403,log,msg:'SQL Injection: OR variant detected'"
```

**Rule 3 - Simple Substring:**
```nginx
SecRule ARGS "@contains ' or 1=1" "id:ZZZZ,phase:2,deny,status:403,log,msg:'SQL Injection: Simple OR 1=1 pattern'"
```

---

## Testing the Updated Prompts

### 1. **Send a malicious request:**
```bash
curl -X POST http://localhost:8080/login -d "username=test' or 1=1--&password=test"
```

### 2. **Check ML detector logs:**
```bash
docker logs ml_detector --tail 50 | grep -A 5 "MALICIOUS"
```

### 3. **Wait 15-20 seconds for LLM to generate rules**

### 4. **Check generated rules:**
```bash
cat shared_rules/custom-rules.conf
```

**Expected:** Multiple rule variations with proper regex patterns

---

## Summary

✅ **Prompts updated to match current best practices**
✅ **LLM will now generate flexible, robust rules**
✅ **Multiple rule variations for better detection**
✅ **Proper whitespace and quote handling**
✅ **Explicit requirements prevent mistakes**

**The LLM will now generate high-quality ModSecurity rules like the ones in custom-rules.conf!** 🎯
