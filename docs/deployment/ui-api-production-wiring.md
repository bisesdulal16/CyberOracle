# CyberOracle UI-Backend Production Wiring

This document explains how to properly wire up the CyberOracle frontend with the backend in production.

## Local Development Setup

### Prerequisites
- Node.js 18+ installed
- Docker and Docker Compose installed
- Python 3.10+ installed

### Running Locally

1. **Start the backend API**:
   ```bash
   # From the root directory
   docker-compose up -d db
   docker-compose up -d api
   ```

2. **Start the frontend**:
   ```bash
   # From ui/ui directory
   npm install
   npm run dev
   ```

3. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - Grafana: http://localhost:3000 (after starting the full stack)

## Production Deployment

### Nginx Reverse Proxy Configuration

The production deployment uses an Nginx reverse proxy to serve both the frontend and backend under the same domain:

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

### Environment Variables

In production, the UI should use the following environment variables:

```bash
# .env file for production
NEXT_PUBLIC_API_BASE_URL=/api
NEXT_PUBLIC_GRAFANA_URL=https://cyberoracle.eng.unt.edu/grafana
```

### Production Deployment Steps

1. **Build the frontend**:
   ```bash
   cd ui/ui
   npm install
   npm run build
   ```

2. **Deploy the frontend**:
   - Copy the `out` directory to your web server
   - Configure Nginx to serve the static files from the `out` directory

3. **Deploy the backend**:
   - Run `docker-compose up -d` on the server
   - Ensure the Nginx reverse proxy is configured

4. **Final Verification**:
   ```bash
   # Test API health
   curl http://cyberoracle.eng.unt.edu/api/health
   
   # Test UI access
   curl http://cyberoracle.eng.unt.edu/
   ```

## Final Verification Checklist

- [ ] Backend API is running on port 8000
- [ ] Frontend is running on port 3000
- [ ] Nginx reverse proxy is configured
- [ ] API base URL is set to `/api` in production
- [ ] Grafana URL is set to the correct production path
- [ ] CORS allows both local and production origins
- [ ] All protected routes require valid JWT tokens
- [ ] Authentication works correctly with local storage
- [ ] All API endpoints are accessible through the reverse proxy

## Troubleshooting

### Common Issues

1. **401 Unauthorized**: Check that JWT tokens are stored in localStorage and sent with requests
2. **CORS Errors**: Ensure the `allow_origin_regex` in `app/main.py` includes the production domain
3. **API Not Found**: Verify that the reverse proxy correctly routes `/api/` requests to the backend
4. **Frontend Not Loading**: Check that the Nginx configuration properly serves the static files

### Testing Commands

```bash
# Test backend API
curl http://localhost:8000/health

# Test frontend (if running separately)
curl http://localhost:3000/

# Test reverse proxy setup
curl http://cyberoracle.eng.unt.edu/api/health
```