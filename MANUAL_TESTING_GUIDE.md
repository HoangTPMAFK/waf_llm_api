# 🧪 Manual Testing Guide - See Visual Feedback

## ✅ System is Ready!

**Changes Applied:**
- ✅ Rule 1006 commented out (was blocking ALL /login requests)
- ✅ Rule 1007 active (blocks UNION in ARGS)
- ✅ Groq API key configured
- ✅ WAF and ML detector restarted

**Current Active Rules:**
```
id:1005 - Blocks /style.css
id:1007 - Blocks ARGS containing "UNION"
```

---

## 🎯 Manual Test: SQL Injection Attack

### **Step 1: Open Your Browser**

Navigate to:
```
http://localhost:8080/login
```

You should see the **login page**.

---

### **Step 2: Submit SQL Injection - FIRST TIME**

**Enter in the form:**
- Username: `admin' or 1=1--`
- Password: `123`
- Click "Submit" or "Login"

**What You'll See:**
```
┌─────────────────────────────────────┐
│  Browser shows:                     │
│  ✓ Request goes through (200 OK)   │
│  ✓ Login page responds normally    │
│  ✓ No 403 error (YET!)             │
└─────────────────────────────────────┘
```

**What's Happening Behind the Scenes:**
```
1. Request → WAF → Passes (no rule for this yet)
2. Request → Web App → You see response
3. WAF → ML Detector (background analysis)
4. ML Detector → "🚨 MALICIOUS!"
5. ML Detector → LLM (generates rule)
6. LLM → Writes to ./shared_rules/custom-rules.conf
7. WAF → Auto-reloads (5 seconds)
```

---

### **Step 3: Watch the Magic Happen!**

**Open your file editor side-by-side with browser:**

**File to watch:** `./shared_rules/custom-rules.conf`

**Wait 15-20 seconds**, then refresh the file view.

**You'll see something like:**
```nginx
# NEW RULE APPEARS! 🎉
SecRule ARGS "@rx admin.*or.*1.*=.*1" \
    "id:1008,phase:2,deny,status:403,log,msg:'SQL injection detected'"
```

---

### **Step 4: Submit SAME Attack - SECOND TIME**

**Refresh the page and submit again:**
- Username: `admin' or 1=1--`
- Password: `123`
- Click "Submit"

**What You'll See NOW:**
```
┌─────────────────────────────────────┐
│  403 Forbidden                      │
│                                     │
│  Request blocked by WAF             │
│                                     │
│  nginx/1.21.4                       │
└─────────────────────────────────────┘
```

**🎉 SUCCESS! This is your visual proof it's blocked!**

---

## 🎨 Visual Indicators Cheat Sheet

### **✅ BLOCKED (What You Want to See):**

**Browser:**
- White/gray page with "403 Forbidden"
- "Request blocked by WAF" message
- Browser address bar stays at `/login`

**Browser DevTools (F12 → Network tab):**
- Status: `403` (in red)
- Request to `/login` shows red indicator

**In `./shared_rules/custom-rules.conf`:**
- New rule appeared matching your attack

---

### **❌ NOT BLOCKED (First Time is Normal):**

**Browser:**
- Login form responds normally
- "Invalid credentials" or redirects
- Status: `200 OK`

**Browser DevTools:**
- Status: `200` or `302` (in black/green)

---

## 🧪 More Test Cases You Can Try

### **Test 1: UNION Attack (Should be blocked immediately)**
```
http://localhost:8080/?id=1 UNION SELECT password
```
**Expected:** 403 Forbidden (Rule 1007 catches this)

### **Test 2: Normal Login (Should pass)**
```
Username: user
Password: password123
```
**Expected:** 200 OK (goes through)

### **Test 3: XSS Attack**
```
Username: <script>alert(1)</script>
Password: 123
```
**Expected:** 
- First time: Goes through → LLM generates rule
- Second time: 403 Blocked

---

## 📱 Using Postman (More Visual)**

**Step 1:** Open Postman

**Step 2:** Create POST request
- URL: `http://localhost:8080/login`
- Body type: `x-www-form-urlencoded`
- Add:
  - Key: `username`, Value: `admin' or 1=1--`
  - Key: `password`, Value: `123`

**Step 3:** Click "Send"

**Step 4:** See response
- **Green 200 OK** = Not blocked (first time)
- **Orange/Red 403** = BLOCKED! 🎉

**Step 5:** Wait 15 seconds, click "Send" again
- Should now show **403 Forbidden**

---

## 🎬 Complete Demo Flow

**Window 1: Browser**
```
http://localhost:8080/login
```

**Window 2: Text Editor**
```
Open: ./shared_rules/custom-rules.conf
```

**Window 3: Terminal (Optional)**
```bash
watch -n 1 'docker logs ml_detector --tail 5 | grep -E "MALICIOUS|Triggering"'
```

**Timeline:**
```
00:00 - Submit attack in Window 1
00:00 - See normal response (200 OK)
00:05 - Window 3 shows "🚨 MALICIOUS REQUEST DETECTED!"
00:15 - Window 2 shows NEW RULE appears!
00:20 - Submit again in Window 1
00:20 - See 403 FORBIDDEN! 🎉
```

---

## ✨ Summary

**First Attack:**
- ✅ Goes through (you see normal page)
- ✅ ML detects as malicious
- ✅ LLM generates rule (15-20 sec)
- ✅ Rule appears in ./shared_rules/

**Second Attack (Same Pattern):**
- ✅ **403 FORBIDDEN** in browser
- ✅ Visual confirmation it's blocked!

**The 403 page is your proof the WAF is working! 🛡️**

---

## 🆘 Troubleshooting

**Not seeing 403 on second try?**
```bash
# Check if rule was generated
cat ./shared_rules/custom-rules.conf

# Check ML detector logs
docker logs ml_detector --tail 50

# Check WAF loaded the rule
docker logs waf_firewall --tail 20 | grep "rules loaded"
```

**Rule not generating?**
- Check Groq API key is valid
- Check ML detector logs for errors
- Wait longer (some LLMs take 20-30 seconds)
