# EIS Admin Portal

Administration portal for the EIS Pet Insurance Platform. Provides configuration management, cost monitoring, and audit logging for platform administrators.

## Architecture

```
ws8_admin_portal/
├── backend/           # FastAPI (Port 3001)
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── models/
│   │   ├── routers/
│   │   ├── services/
│   │   └── middleware/
│   ├── requirements.txt
│   └── .env
│
└── frontend/          # Next.js 14 (Port 3000)
    ├── app/
    ├── components/
    ├── lib/
    └── .env.local
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Azure CLI (`az login` for cost data)
- AWS credentials (for AWS cost data)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp ../.env.example .env
# Edit .env with your settings

# Start server
uvicorn app.main:app --host 0.0.0.0 --port 3001 --reload
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
echo "NEXT_PUBLIC_API_URL=http://localhost:3001" > .env.local

# Start development server
npm run dev
```

### Using Docker

```bash
docker-compose up --build
```

## Configuration

### Environment Variables

#### Backend (.env)

| Variable | Description | Required |
|----------|-------------|----------|
| `BACKEND_PORT` | Backend API port (default: 3001) | No |
| `FRONTEND_PORT` | Frontend port for CORS (default: 3000) | No |
| `DEBUG` | Enable debug mode | No |
| `DEV_MODE` | Enable development features | No |
| `AZURE_SUBSCRIPTION_ID` | Azure subscription for cost data | Yes* |
| `AZURE_RESOURCE_GROUP_FILTER` | Comma-separated RG name patterns | No |
| `AWS_ACCESS_KEY_ID` | AWS access key for Cost Explorer | Yes* |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | Yes* |
| `AWS_REGION` | AWS region (default: us-east-1) | No |
| `AWS_SERVICE_FILTER` | Comma-separated AWS service names | No |

*Required for real cost data. Without these, cost sections show zeros.

#### Frontend (.env.local)

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Backend API URL |
| `PORT` | Frontend port (default: 3000) |

## Features

### Dashboard
- Monthly spend overview (Azure + AWS combined)
- Pending approvals count
- AI/ML costs summary
- Audit activity metrics
- Cost trend chart
- Top services by cost

### Cost Monitor
Real-time cost tracking from cloud providers:

- **Overview Tab**: Combined Azure + AWS costs, forecasts, top services
- **Azure Tab**: Azure-specific cost breakdown by service
- **AWS Tab**: AWS-specific cost breakdown by service
- **AI Usage Tab**: AI/LLM token usage and costs (Azure OpenAI, AWS Bedrock)
- **Budget Alerts Tab**: User-created budget alerts with thresholds

#### Data Sources

| Provider | API | Authentication |
|----------|-----|----------------|
| Azure | Cost Management API | DefaultAzureCredential (`az login`) |
| AWS | Cost Explorer API | IAM credentials or role |
| Azure OpenAI | Azure Monitor Metrics | DefaultAzureCredential |
| AWS Bedrock | CloudWatch Metrics | IAM credentials |

### Configuration Management
- AI/ML model configuration
- Claims processing rules
- Policy configuration
- Rating factors

### Audit Logs
- All admin actions tracked
- Filterable by date, user, action type
- Exportable reports

### Approvals (Maker-Checker)
- Configuration changes require approval
- Review pending changes with diff view
- Approve/reject with comments

### User Management
- Role-based access control
- Permission management

## API Endpoints

### Health
- `GET /health` - Health check
- `GET /` - API info

### Costs
- `GET /api/v1/costs/dashboard` - Aggregated cost dashboard
- `GET /api/v1/costs/azure/summary` - Azure cost summary
- `GET /api/v1/costs/aws/summary` - AWS cost summary
- `GET /api/v1/costs/forecast` - Cost forecast
- `GET /api/v1/costs/ai-usage` - AI/LLM token usage
- `GET /api/v1/costs/platform-usage` - Full platform usage
- `GET /api/v1/costs/budgets` - Budget alerts
- `POST /api/v1/costs/budgets` - Create budget alert

### Configuration
- `GET/PUT /api/v1/config/ai` - AI configuration
- `GET/PUT /api/v1/config/claims` - Claims rules
- `GET/PUT /api/v1/config/policies` - Policy config
- `GET/PUT /api/v1/config/rating` - Rating factors

### Audit
- `GET /api/v1/audit` - Query audit logs
- `GET /api/v1/audit/stats` - Audit statistics

### Users
- `GET/POST /api/v1/users` - List/create users
- `GET/PUT/DELETE /api/v1/users/{id}` - User management

### Approvals
- `GET /api/v1/approvals` - List approvals
- `GET /api/v1/approvals/pending` - Pending approvals
- `POST /api/v1/approvals/{id}/approve` - Approve change
- `POST /api/v1/approvals/{id}/reject` - Reject change

## Authentication

The portal uses JWT-based authentication:

1. Login with email/password at `/api/v1/auth/login`
2. Include token in `Authorization: Bearer <token>` header
3. Token refresh at `/api/v1/auth/refresh`

### Default Dev User
- Email: `admin@example.com`
- Password: `admin123`

## Cost Data Integration

### Azure Setup

1. Login to Azure CLI:
   ```bash
   az login
   ```

2. Set subscription ID in `.env`:
   ```
   AZURE_SUBSCRIPTION_ID=your-subscription-id
   ```

3. (Optional) Filter by resource groups:
   ```
   AZURE_RESOURCE_GROUP_FILTER=eis,dynamics,prod
   ```

The portal uses `DefaultAzureCredential` which works with:
- Local: Azure CLI login (`az login`)
- Cloud: Managed Identity

### AWS Setup

1. Add credentials to `.env`:
   ```
   AWS_ACCESS_KEY_ID=your-access-key
   AWS_SECRET_ACCESS_KEY=your-secret-key
   AWS_REGION=us-east-1
   ```

2. (Optional) Filter by services:
   ```
   AWS_SERVICE_FILTER=Bedrock,Lambda,S3,API Gateway
   ```

Required IAM permissions:
- `ce:GetCostAndUsage`
- `ce:GetCostForecast`
- `cloudwatch:GetMetricStatistics` (for Bedrock usage)

## Development

### Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Settings (Pydantic)
│   ├── models/              # Pydantic models
│   │   ├── users.py
│   │   ├── costs.py
│   │   ├── ai_usage.py
│   │   └── ...
│   ├── routers/             # API endpoints
│   │   ├── costs.py
│   │   ├── ai_config.py
│   │   └── ...
│   ├── services/            # Business logic
│   │   ├── azure_cost_service.py
│   │   ├── aws_cost_service.py
│   │   ├── ai_usage_service.py
│   │   └── ...
│   └── middleware/          # Auth, logging
│       └── auth.py

frontend/
├── app/                     # Next.js App Router
│   ├── page.tsx             # Dashboard
│   ├── costs/page.tsx       # Cost Monitor
│   ├── audit/page.tsx       # Audit Logs
│   └── ...
├── components/              # React components
│   ├── layout/
│   ├── costs/
│   └── ...
└── lib/
    ├── api.ts               # API client
    └── utils.ts             # Utilities
```

### Adding New Features

1. **Backend**: Add model in `models/`, service in `services/`, router in `routers/`
2. **Frontend**: Add API function in `lib/api.ts`, create page in `app/`

### Testing

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

## Deployment

### Docker

```bash
docker-compose -f docker-compose.yml up -d
```

### Azure Container Apps

See deployment scripts in `/deploy/azure/`

### AWS ECS

See deployment scripts in `/deploy/aws/`

## Troubleshooting

### Cost data shows $0.00

1. Verify Azure CLI login: `az account show`
2. Check subscription ID matches in `.env`
3. Verify AWS credentials are valid
4. Check service filters aren't too restrictive

### CORS errors

1. Ensure `FRONTEND_PORT` in backend `.env` matches actual frontend port
2. Check `NEXT_PUBLIC_API_URL` points to correct backend URL

### Authentication issues

1. Clear browser localStorage
2. Check JWT secret configuration
3. Verify user exists in system

## License

Proprietary - Sunware Technologies
