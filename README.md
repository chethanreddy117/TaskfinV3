# TaskFin - AI-Powered Bill Payment System

> **Agent-based bill payment system** with AI orchestration, risk controls, and comprehensive audit logging.

![Version](https://img.shields.io/badge/version-3.0-blue) ![Status](https://img.shields.io/badge/status-production--ready-green) ![License](https://img.shields.io/badge/license-MIT-blue)

---

## 🎯 Overview

TaskFin is an intelligent bill payment assistant that uses AI agents to help users manage and pay their bills through natural language conversations. It demonstrates modern software architecture with clean separation of concerns, payment correctness, risk controls, and full auditability.

### Key Capabilities

- 💬 **Natural Language Interface**: Chat with AI to manage bills
- 💰 **Smart Bill Payment**: Fuzzy matching, confirmation flow, balance checks
- 🛡️ **Risk Controls**: Daily spending limits (₹5,000) and payment count limits (5/day)
- 📊 **Complete Audit Trail**: Immutable logging of all financial activities
- 🎯 **Agent Architecture**: Specialized agents for different responsibilities
- 🔒 **Secure**: JWT authentication, encrypted passwords, secure transactions

---

## ✨ Features

### For Users
- ✅ View unpaid bills
- ✅ Check account balance
- ✅ Pay bills with 2-step confirmation
- ✅ View transaction history
- ✅ Check spending limits
- ✅ Fuzzy bill name matching ("electric" → "Electricity")

### For Developers
- ✅ Docker Compose setup (one command to run)
- ✅ Agent-based architecture (easy to extend)
- ✅ Comprehensive error handling
- ✅ Redis-based session management
- ✅ PostgreSQL for data persistence
- ✅ LangChain + Anthropic Claude for AI

---

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│    Next.js Frontend (Port 3000)    │
│   Modern Chat UI + Quick Actions    │
└──────────────┬──────────────────────┘
               │ REST API
               ▼
┌─────────────────────────────────────┐
│   FastAPI Backend (Port 8000)       │
│         Orchestrator Agent          │
└──┬────────┬──────────┬──────────┬───┘
   │        │          │          │
   ▼        ▼          ▼          ▼
┌─────┐ ┌──────┐  ┌──────┐   ┌──────┐
│Auth │ │Financial│ │Risk │  │Audit│
│Agent│ │ Agent  │ │Agent│  │Agent│
└──┬──┘ └───┬───┘ └───┬──┘  └───┬──┘
   └────────┴─────────┴─────────┘
              │
   ┌──────────┴───────────┐
   ▼                      ▼
┌──────────┐         ┌──────────┐
│PostgreSQL│         │  Redis   │
│  (5432)  │         │  (6379)  │
└──────────┘         └──────────┘
```

### Agent Responsibilities

| Agent | Responsibility |
|-------|---------------|
| **Orchestrator** | Intent detection, routing, conversation flow |
| **Financial** | Bill management, payments, balance, history |
| **Risk** | Daily limits enforcement, fraud prevention |
| **Audit** | Immutable event logging for compliance |
| **Auth** | User authentication and authorization |

---

## 🚀 Quick Start

### Prerequisites

- Docker Desktop (running)
- Anthropic API key (Claude)

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd "Taskfin V3"
   ```

2. **Set up environment variables**
   ```bash
   # Create .env file in project root
   cp .env.example .env
   ```

   Edit `.env` and add your API key:
   ```env
   ANTHROPIC_API_KEY=your_api_key_here
   ```

3. **Start all services**
   ```bash
   docker-compose up --build
   ```

   Wait for seed completion:
   ```
   ✓ Created demo user: chethan
   ✓ Created account with balance: ₹15,000
   ✓ Created 5 demo bills
   🎉 Seed completed successfully!
   ```

4. **Open the app**
   ```
   http://localhost:3000
   ```

5. **Login**
   ```
   Username: chethan
   Password: 1234
   ```

---

## 💬 Usage Examples

### List Bills
```
You: show my bills

TaskFin: 📋 Your Unpaid Bills:
• Electricity: ₹1200
• Water: ₹450
• Internet: ₹899
• Mobile: ₹599
• Gas: ₹850

Total: ₹3998
```

### Pay a Bill
```
You: pay electricity bill

TaskFin: 💳 Payment Confirmation
Electricity: ₹1200
Confirm payment? (yes/no)

You: yes

TaskFin: ✓ Payment successful!
Electricity bill of ₹1200 has been paid.
Your updated balance: ₹13800
```

### Check Balance
```
You: show balance

TaskFin: 💰 Account Balance
Current Balance: ₹15000
Account Type: Savings
```

### View History
```
You: show history

TaskFin: 📜 Recent Transactions:
✓ 2026-02-14 16:45 | Electricity | ₹1200
✓ 2026-02-14 16:43 | Internet | ₹899
```

### Check Limits
```
You: show my limits

TaskFin: 📊 Daily Spending Limits
Amount:
• Used: ₹2500
• Limit: ₹5000
• Remaining: ₹2500

Payments:
• Made: 2
• Limit: 5
• Remaining: 3
```

---

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM for database operations
- **PostgreSQL** - Primary data store
- **Redis** - Session state, risk tracking, locks
- **LangChain** - Agent orchestration framework
- **Anthropic Claude** - LLM for intent detection

### Frontend
- **Next.js 14** - React framework (App Router)
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Axios** - HTTP client

### Infrastructure
- **Docker Compose** - Multi-container orchestration
- **JWT** - Authentication tokens
- **bcrypt** - Password hashing

---

## 📊 Database Schema

```sql
users
  ├─ id (PK)
  ├─ username (UNIQUE)
  └─ password (hashed)

accounts
  ├─ id (PK)
  ├─ user_id (FK)
  ├─ balance
  └─ type

bills
  ├─ id (PK)
  ├─ user_id (FK)
  ├─ name
  ├─ amount
  └─ status (PAID/UNPAID)

transactions
  ├─ id (PK)
  ├─ user_id (FK)
  ├─ bill_name
  ├─ amount
  ├─ status (SUCCESS/FAILED)
  └─ created_at

audit_logs
  ├─ id (PK)
  ├─ user_id (FK)
  ├─ action
  ├─ status
  ├─ message
  └─ created_at
```

---

## 🔧 Development

### Run Backend Only
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Run Frontend Only
```bash
cd frontend
npm install
npm run dev
```

### Access Services
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

### Database Access
```bash
docker exec -it <postgres-container> psql -U taskfin_user -d taskfin_db
```

### Redis Access
```bash
docker exec -it <redis-container> redis-cli
```

---

## 🧪 Testing

See [DEMO_SCRIPT.md](./DEMO_SCRIPT.md) for step-by-step testing guide.

### Quick Test
```bash
# Health check
curl http://localhost:8000/api/v1/health

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"chethan","password":"1234"}'
```

---

## 🐛 Troubleshooting

See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for common issues.

**Quick fixes**:
- **Containers won't start**: `docker-compose down -v && docker-compose up --build`
- **Backend errors**: Check `ANTHROPIC_API_KEY` in `.env`
- **Login fails**: Ensure database seed completed (check logs)

---

## 📝 API Documentation

### Authentication
```http
POST /api/v1/auth/login
POST /api/v1/auth/register
```

### Chat
```http
POST /api/v1/agent/chat
Headers: Authorization: Bearer <token>
Body: { "message": "string" }
```

### Health
```http
GET /api/v1/health
```

---

## 🔒 Security Features

- ✅ JWT-based authentication
- ✅ bcrypt password hashing
- ✅ Environment variable configuration
- ✅ SQL injection protection (SQLAlchemy ORM)
- ✅ CORS configuration
- ✅ Rate limiting via risk controls
- ✅ Transaction idempotency

---

## 🎯 Risk Controls

### Daily Limits
- **Amount**: ₹5,000 per day
- **Count**: 5 payments per day
- **Reset**: Automatic at midnight
- **Storage**: Redis with TTL

### Enforcement
Payments are blocked when:
1. Total daily amount would exceed ₹5,000
2. Daily payment count would exceed 5
3. Insufficient account balance

---

## 📋 Project Structure

```
taskfin/
├── backend/
│   ├── app/
│   │   ├── agents/          # Agent implementations
│   │   ├── services/        # Business logic
│   │   ├── models.py        # Database models
│   │   ├── main.py          # FastAPI app
│   │   └── seed.py          # Demo data
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   └── app/
│   │       └── page.tsx     # Main chat UI
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── .env
└── README.md
```

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

---

## 📄 License

MIT License - see LICENSE file for details

---

## 🙏 Acknowledgments

- **Anthropic** for Claude AI
- **LangChain** for agent framework
- **FastAPI** community
- **Next.js** team

---

## 📞 Support

For issues and questions:
- Create an issue on GitHub
- Check [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
- Review [DEMO_SCRIPT.md](./DEMO_SCRIPT.md)

---

**Built with ❤️ using AI agents**
