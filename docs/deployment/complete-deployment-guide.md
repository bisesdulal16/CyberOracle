# CyberOracle Complete Deployment Guide

This document provides instructions for running the complete CyberOracle system with both backend and frontend components.

## System Overview

CyberOracle is a secure AI gateway that provides:
- FastAPI backend with JWT authentication
- React/Next.js frontend with dashboard and UI
- PostgreSQL database for logging
- Grafana dashboard for compliance monitoring
- DLP (Data Loss Prevention) capabilities

## Prerequisites

- Docker and Docker Compose
- Node.js 18+
- Python 3.10+
- Git

## Local Development Setup

### 1. Clone and Install

```bash
git clone <repository-url>
cd CyberOracle
```

### 2. Install Backend Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt
```

### 3. Set Up Environment Variables

```bash
# Copy the example .env file
cp .env.example .env
```

### 4. Start the Backend

```bash
# Start database and API services
docker-compose up -d db
docker-compose up -d api

# Or start everything together
docker-compose up -d
```

### 5. Start the Frontend

```bash
# Navigate to UI directory
cd ui/ui

# Install Node dependencies
npm install

# Start development server
npm run dev
```

### 6. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Grafana**: http://localhost:3000 (after starting the full stack)

## Production Deployment

### 1. Build the Frontend

```bash
cd ui/ui
npm install
npm run build
```

### 2. Configure Nginx Reverse Proxy

Create an Nginx configuration file for the production deployment:

```nginx
server {
    listen 80;
    server_name cyberoracle.eng.unt.edu;

    # Serve frontend (Next.js app)
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Proxy API requests to backend
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Proxy Grafana
    location /grafana/ {
        proxy_pass http://localhost:3000/grafana/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3. Deploy Backend Services

```bash
# Start all services in production
docker-compose up -d
```

## Authentication Credentials

The system comes with default test credentials:

- **Admin**: admin / changeme_admin
- **Developer**: developer / changeme_dev  
- **Auditor**: auditor / changeme_auditor

## Testing the System

### Backend API Tests

```bash
# Run backend tests
python -m pytest app/tests/ -v
```

### Frontend Tests

```bash
# Navigate to UI directory
cd ui/ui

# Run frontend tests (if any)
npm test
```

## Verification Commands

### 1. Test Backend Health

```bash
curl http://localhost:8000/health
```

### 2. Test Frontend Access

```bash
curl http://localhost:3000/
```

### 3. Test API Access Through Proxy

```bash
curl http://cyberoracle.eng.unt.edu/api/health
```

## Troubleshooting

### Common Issues

1. **Docker Connection Issues**:
   - Ensure Docker Desktop is running
   - Check that you have proper permissions

2. **CORS Errors**:
   - Verify CORS settings in `app/main.py`
   - Ensure the frontend is using the correct API base URL

3. **Authentication Failures**:
   - Check that the correct credentials are being used
   - Verify that JWT tokens are being stored in localStorage

4. **UI Not Loading**:
   - Ensure the Nginx reverse proxy is configured correctly
   - Check that the frontend build files are properly deployed

## Security Notes

- All API endpoints require valid JWT tokens
- Sensitive data is logged with proper masking
- Database encryption is enabled when configured
- HTTPS is implemented for production deployment

## System Architecture

```
[Browser] 
   ↓
[Nginx Reverse Proxy]
   ↓
[Frontend (Next.js)] ←→ [Backend (FastAPI)]
   ↑                           ↓
[Grafana] ←←←←←←←←←←←←←←← [Database (PostgreSQL)]
```

## File Structure

```
CyberOracle/
├── app/                 # FastAPI backend
│   ├── main.py          # Main application
│   ├── routes/          # API routes
│   ├── middleware/      # Security middleware
│   └── db/              # Database models
├── ui/                  # Frontend (Next.js)
│   └── ui/
│       ├── app/         # Next.js app pages
│       ├── components/  # UI components
│       └── lib/         # API clients and utilities
├── docker-compose.yml   # Docker orchestration
├── requirements.txt     # Python dependencies
└── docs/                # Documentation
    └── deployment/
        └── ui-api-production-wiring.md
```

## Final Checklist

Before submitting for demo or production:

- [ ] All backend tests pass
- [ ] Frontend loads correctly
- [ ] API endpoints are accessible
- [ ] Authentication works
- [ ] CORS settings allow both local and production origins
- [ ] Grafana dashboard is functional
- [ ] All environment variables are properly set
- [ ] Nginx reverse proxy is configured correctly
- [ ] Production deployment documentation is complete