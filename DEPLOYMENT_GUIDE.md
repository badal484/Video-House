# Production Deployment Guide & Infrastructure Setup
**Project:** Universal AI Video Production Studio  
**Document Version:** 1.0.0  
**Status:** Approved Production Deployment Guide  

---

## 1. Single-Node Production Deployment (Docker Compose)

### 1.1 Server Provisioning
- **OS:** Ubuntu 22.04 LTS / Debian 12 Bookworm / macOS Monterey+
- **CPU:** 4+ Cores (ARM64 Apple Silicon or x86_64)
- **RAM:** 8 GB Minimum (16 GB Recommended)
- **Storage:** NVMe SSD with minimum 100 GB available space

### 1.2 Deployment Steps
```bash
# 1. Clone repository on production host
git clone https://github.com/badal484/Video-House.git /opt/video-house
cd /opt/video-house

# 2. Configure production environment
cp .env.example .env
nano .env  # Set STUDIO_ENV=production, CORS_ORIGINS, and custom keys

# 3. Build & start container cluster
docker compose up -d --build

# 4. Verify running health status
docker compose ps
curl -f http://localhost:8000/api/v1/system/telemetry
```

---

## 2. Reverse Proxy Configuration (Nginx with HTTPS)

Place the following configuration in `/etc/nginx/sites-available/video-house.conf`:

```nginx
server {
    listen 80;
    server_name studio.yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name studio.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/studio.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/studio.yourdomain.com/privkey.pem;

    client_max_body_size 5000M;  # Allow large 4K video uploads

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Media streaming optimizations
        proxy_buffering off;
        proxy_read_timeout 600s;
        proxy_send_timeout 600s;
    }
}
```

---

## 3. Rollback Procedures
```bash
# In case of bad deployment:
git checkout <PREVIOUS_TAG>
docker compose up -d --build
```
