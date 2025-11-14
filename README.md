# User Authentication & QR Code Microservice  
FastAPI + MongoDB Atlas + Render (Docker Deployment)

**Student:** Aizada  
**Course:** Software Architecture — Assignment 4  

---

## Project Overview

This microservice provides:

- User registration and authentication  
- JWT-based login  
- QR code generation  
- MongoDB Atlas cloud storage  
- Dockerized deployment on Render  

Architecture is designed for secure cloud deployment using TLS/SSL.

---

## Live Services

| Component | URL |
|----------|-----|
| **GitHub Repository** | https://github.com/aizada5/micro |
| **Live Render Deployment** | https://micro-0gg1.onrender.com |
| **Swagger UI** | https://micro-0gg1.onrender.com/docs#/default/health_check_health_db_get |

---

# Deployment Architecture


    "email": "admin@gmail.com",
    "full_name": "Admin Adminov",
    "role": "admin",
    "created_at": "2025-11-14T07:14:23.583000",
    "qr_code": null
  }
]
┌─────────────────┐
│ GitHub Repo │
│ (Source Code) │
└────────┬────────┘
│ (Git push triggers deployment)
▼
┌─────────────────┐
│ Render.com │
│ Docker Build │
│ - Dockerfile │
│ - Environment │
└────────┬────────┘
│ (Secure TLS)
▼
┌─────────────────┐
│ MongoDB Atlas │
│ M0 Cluster │
└─────────────────┘

---

# ⚠️ Issues Encountered & Solutions

## 1. TLS/SSL Certificate Errors with MongoDB Atlas

The Docker container couldn't verify the MongoDB Atlas SSL certificate, causing connection failures.

### ✔️ Solution  
Installed system certificates inside the Docker image:

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates openssl && \
    update-ca-certificates && \
    rm -rf /var/lib/apt/lists/*


