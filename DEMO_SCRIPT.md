# TaskFin Demo Script

## Purpose
Step-by-step guide for demonstrating TaskFin's capabilities to stakeholders, clients, or during presentations.

**Total Time**: ~15 minutes

---

## Prerequisites (5 minutes)

1. **Start Docker Desktop**
   
2. **Launch Services**
   ```bash
   cd "C:/Users/Damodher/Desktop/Taskfin V2/Taskfin V3"
   docker-compose up --build
   ```

3. **Wait for Seed Completion**
   Look for in terminal:
   ```
   ✓ Created demo user: chethan
   ✓ Created account with balance: ₹15,000
✓ Created 5 demo bills
   🎉 Seed completed successfully!
   ```

4. **Open Browser**
   Navigate to: http://localhost:3000

---

## Demo Flow (10 minutes)

### Part 1: Introduction & Login (1 min)

**Show**: Modern login page with gradient background

**Say**: *"TaskFin is an AI-powered bill payment system that uses intelligent agents to help users manage their finances through natural conversation."*

**Action**: Enter credentials
```
Username: chethan
Password: 1234
```

**Point Out**:
- Clean, modern UI
- Demo credentials shown on login page

---

### Part 2: First Interaction (1 min)

**Show**: Welcome screen with quick action buttons

**Say**: *"Users can interact via chat or use quick actions for common tasks."*

**Type**: `hello`

**Point Out**:
- Friendly greeting from AI
- Natural language understanding
- Quick action buttons at bottom

---

### Part 3: Bill Management (2 min)

#### Show Bills
**Click**: "📋 Show Bills" button (or type: `show my bills`)

**Point Out**:
- Lists all 5 unpaid bills
- Shows individual amounts
- Calculates total (₹3,998)
- Clean formatting with currency symbols

**Say**: *"The system fetches all unpaid bills from the database and presents them in a user-friendly format."*

---

### Part 4: Balance Check (1 min)

**Click**: "💰 Check Balance" button (or type: `show balance`)

**Point Out**:
- Current balance: ₹15,000
- Account type: Savings
- Instant response

**Say**: *"Users can check their balance anytime to ensure they have sufficient funds."*

---

### Part 5: Bill Payment Flow (3 min)

#### Initiate Payment
**Type**: `pay electricity bill`

**Point Out**:
- **Fuzzy Matching**: System found "Electricity" from "electricity bill"
- Confirmation request appears
- Shows exact amount (₹1,200)
- 60-second countdown timer starts

**Say**: *"The system uses fuzzy matching to understand user intent. Notice the 2-step confirmation process - a critical safety feature for financial transactions."*

#### Confirm Payment
**Type**: `yes`

**Point Out**:
- Loading indicator with animation ("Processing payment...")
- Success message appears
- **Updated balance shown**: ₹13,800 (was ₹15,000)
- Transaction details displayed

**Say**: *"Behind the scenes, the system:
1. Checks risk limits
2. Validates balance
3. Creates transaction record
4. Updates bill status
5. Logs to audit trail
All in a single atomic operation."*

---

### Part 6: Transaction History (1 min)

**Click**: "📜 History" button (or type: `show history`)

**Point Out**:
- Recent transaction appears (Electricity, ₹1,200)
- Timestamp shown
- Status indicator (✓)

**Say**: *"Complete transaction history is maintained for transparency and reconciliation."*

---

### Part 7: Risk Controls Demo (3 min)

#### Check Current Limits
**Click**: "📊 My Limits" button (or type: `show my limits`)

**Point Out**:
- Daily spending limit: ₹5,000
- Already used: ₹1,200 (from electricity payment)
- Remaining: ₹3,800
- Payment count: 1 of 5 used

**Say**: *"TaskFin enforces two types of daily limits:
1. Amount limit (₹5,000/day)
2. Payment count (5 payments/day)
This prevents fraud and accidental overspending."*

#### Make More Payments
**Action**: Pay 4 more bills
```
1. pay internet bill → yes (₹899)
2. pay gas → yes (₹850)
3. pay mobile → yes (₹599)
4. pay water → yes (₹450)
```

**Point Out** after each:
- Quick payment using fuzzy matching
- Balance decreasing
- Payment count increasing

**Current State**:
- Total spent: ₹1,200 + ₹899 + ₹850 + ₹599 + ₹450 = ₹3,998
- Payment count: 5/5 (LIMIT REACHED)

#### Demonstrate Risk Block
**Type**: `show my bills`  
*(All bills are now paid)*

**OR** (if you have more bills):
**Type**: `pay [any remaining bill]`

**Expected Response**:
```
Payment blocked: Daily payment limit reached.
You've made 5 payments today (limit: 5)
```

**Say**: *"The risk system automatically blocks the 6th payment. These limits reset daily at midnight."*

---

## Part 8: Technical Deep Dive (Optional, 5 min)

### Show Backend Logs
```bash
docker logs <backend-container-name>
```

**Point Out**:
- Agent orchestration
- Intent detection
- Database queries
- Risk evaluation logs

### Show Database
```bash
docker exec -it <postgres-container> psql -U taskfin_user -d taskfin_db

-- Show transactions
SELECT * FROM transactions ORDER BY created_at DESC LIMIT 5;

-- Show bill status
SELECT name, amount, status FROM bills WHERE user_id = 1;

-- Show audit logs
SELECT action, status, message FROM audit_logs 
ORDER BY created_at DESC LIMIT 10;
```

**Point Out**:
- Bills marked as PAID
- Transaction records with SUCCESS status
- Complete audit trail

### Show Redis
```bash
docker exec -it <redis-container> redis-cli

KEYS risk:*
GET risk:amount:1:2026-02-14
GET risk:count:1:2026-02-14
```

**Point Out**:
- Risk counters in Redis
- Fast, in-memory tracking
- TTL-based expiration

---

## Key Takeaways to Emphasize

1. **Natural Language**: Users don't need to learn commands
2. **Safety**: 2-step confirmation prevents accidents
3. **Risk Controls**: Automatic fraud prevention
4. **Auditability**: Complete transaction history
5. **Modern Tech**: AI + Microservices + Cloud-ready
6. **User Experience**: Clean UI, instant feedback, quick actions

---

## Common Questions & Answers

**Q**: What if the user types "electric" instead of "Electricity"?  
**A**: Fuzzy matching handles it! Demo by typing various spellings.

**Q**: What happens if they don't confirm within 60 seconds?  
**A**: Payment automatically cancels. Demo by waiting.

**Q**: Can they cancel a payment?  
**A**: Yes! Demo by typing "no" instead of "yes" during confirmation.

**Q**: What if they have insufficient balance?  
**A**: System blocks the payment and shows clear error message.

**Q**: Is this production-ready?  
**A**: Yes! Complete with error handling, security, audit logs, and risk controls.

---

## Troubleshooting During Demo

| Issue | Quick Fix |
|-------|-----------|
| Backend not responding | Check logs: `docker logs <backend-container>` |
| Login fails | Verify seed completed successfully |
| Limits already exceeded | Reset Redis: `docker exec -it <redis> redis-cli` → `KEYS risk:*` → `DEL <key>` |
| No bills showing | Check database: bills should be seeded |

---

**End of Demo**

**Closing Statement**: *"TaskFin demonstrates how AI agents can transform traditional banking interfaces into conversational experiences while maintaining the security and compliance required for financial transactions."*
