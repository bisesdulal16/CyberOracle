# CyberOracle — TLS Setup Guide

CyberOracle supports TLS via two methods: **self-signed certificates** (development/testing)
and **Let's Encrypt** (production). Both terminate TLS at the Uvicorn layer.

---

## Method 1 — Self-Signed Certificate (Development)

### Step 1: Generate certificate and key

```bash
mkdir -p certs
openssl req -x509 -newkey rsa:4096 -keyout certs/server.key -out certs/server.crt \
  -days 365 -nodes \
  -subj "/C=US/ST=TX/L=Denton/O=CyberOracle/CN=localhost"
```

### Step 2: Start API with TLS

```bash
bash scripts/run_https.sh
```

This runs:
```bash
uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8443 \
  --ssl-keyfile certs/server.key \
  --ssl-certfile certs/server.crt
```

### Step 3: Verify TLS is active

```bash
curl -k https://localhost:8443/health
# Expected: {"status":"OK","service":"CyberOracle API"}
```

The `-k` flag skips self-signed certificate validation in curl.

---

## Method 2 — Let's Encrypt (Production)

### Prerequisites

- A domain pointing to your server (e.g. `cyberoracle.example.com`)
- Port 80 open for ACME challenge

### Step 1: Install Certbot

```bash
sudo apt update && sudo apt install -y certbot
```

### Step 2: Obtain certificate

```bash
sudo certbot certonly --standalone -d cyberoracle.example.com
```

Certificates are saved to:
- `/etc/letsencrypt/live/cyberoracle.example.com/fullchain.pem`
- `/etc/letsencrypt/live/cyberoracle.example.com/privkey.pem`

### Step 3: Start API with Let's Encrypt certs

```bash
uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 443 \
  --ssl-keyfile /etc/letsencrypt/live/cyberoracle.example.com/privkey.pem \
  --ssl-certfile /etc/letsencrypt/live/cyberoracle.example.com/fullchain.pem
```

### Step 4: Auto-renew

```bash
# Test renewal
sudo certbot renew --dry-run

# Add to cron (runs twice daily)
echo "0 0,12 * * * root certbot renew --quiet" | sudo tee /etc/cron.d/certbot-renew
```

---

## Method 3 — Docker Compose with TLS

Add certificate mounts to `docker-compose.yml` under the `api` service:

```yaml
volumes:
  - ./certs:/app/certs:ro
command: >
  uvicorn app.main:app
  --host 0.0.0.0
  --port 8443
  --ssl-keyfile /app/certs/server.key
  --ssl-certfile /app/certs/server.crt
```

---

## Verifying TLS

```bash
# Check certificate details
openssl s_client -connect localhost:8443 -showcerts 2>/dev/null | openssl x509 -noout -text | grep -E "Subject:|Issuer:|Not After"

# Test HTTPS endpoint
curl -k https://localhost:8443/health
curl -k https://localhost:8443/auth/me -H "Authorization: Bearer $TOKEN_ADMIN"
```

---

## Security Notes

- Never commit `certs/` to git — it is listed in `.gitignore`
- Use a minimum key size of 2048-bit RSA (4096 recommended for production)
- Self-signed certs are for development only — browsers will show a warning
- In production, always use Let's Encrypt or a CA-signed certificate
- Set `SECURE_COOKIES=true` in production to enforce HTTPS-only cookies
