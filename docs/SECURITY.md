# VARUNA — Security Policy, Configuration & Known Limitations

> **Document Status:** Operational Security Baseline  
> **Context:** Smart India Hackathon (SIH 2026) Demonstration & Research Evaluation

---

## 1. Executive Summary & Philosophy

This document outlines the security posture, operational configuration, and known limitations of the VARUNA platform in its current evaluation state. 

We maintain a policy of complete technical honesty: **no fabricated certifications (such as SOC 2, ISO 27001, or FedRAMP) are claimed**. The system is an open research and hackathon prototype engineered for evaluation by the Ministry of Earth Sciences (MoES) and hydrographic survey researchers.

---

## 2. Authentication & Authorization Status

### Deliberate Demo Configuration
- **Current State:** Authentication enforcement was **deliberately removed/bypassed from the user interface** during recent development milestones.
- **Rationale:** During evaluation sessions, judges and peer researchers require immediate, friction-free access to the acoustic inspection portal, Leaflet GIS swath viewer, and Explainable Sonar telemetry without navigating login friction, email OTP gates, or credential expiry walls.
- **Production Pre-Condition:** Before any deployment into active naval or commercial maritime networks, a strict identity and access management (IAM) layer (such as OAuth2 with JWT bearer tokens, or institutional SSO) **must be reinstated** across all API endpoints and UI routes.

---

## 3. Network & API Security

### FastAPI CORS Configuration
In [`backend/app/main.py`](../backend/app/main.py), Cross-Origin Resource Sharing (CORS) is currently configured with permissive defaults to facilitate local multi-port development (`localhost:3000` talking to `localhost:8000`):

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

> [!WARNING]
> **Production Hardening:** When deploying to production infrastructure or cloud servers, `allow_origins` must be restricted to explicit, trusted fully qualified domain names (FQDNs), and `allow_credentials` should only be enabled when paired with strict origin validation.

### File Upload & Path Traversal Safeguards
- SSS waterfall uploads are inspected for allowed file extensions (`.jpg`, `.jpeg`, `.png`, `.tif`, `.tiff`, `.bmp`, `.xtf`, `.jsf`, `.sdf`).
- File saves use generated unique identifiers (`srv_<uuid>`) combined with sanitized basenames to prevent path traversal attacks (`../`).
- Navigation metadata files are restricted to `.csv`, `.json`, and `.txt` extensions.

---

## 4. Secrets Management & Environment Variables

- **Git Exclusion:** Sensitive environment variables, local credentials, and API tokens are stored in `.env` or `.env.local` files, which are strictly excluded from version control via [`.gitignore`](../.gitignore):
  ```gitignore
  # environment & secrets
  .env*.local
  .env
  *.pem
  ```
- **External AI Providers:** If LLM features (such as tactical debrief generation) are enabled via Groq or OpenAI, API keys must be provided exclusively via runtime environment variables (`GROQ_API_KEY`) and never hardcoded in source files.

---

## 5. Docker & Container Security

In containerized deployments ([`docker-compose.yml`](../docker-compose.yml)):
- Backend and frontend containers run in an isolated Docker bridge network.
- Static file upload volumes are mapped locally (`./backend/data/uploads`), ensuring survey imagery persists across container restarts without exposing host root filesystems.
- Sensitive environment files must be injected via runtime environment flags rather than baked into container image layers.

---

## 6. Known Security Limitations & Roadmap

The following security constraints exist in the current evaluation prototype and are tracked for subsequent production hardening:

| Domain | Current State | Required Production Hardening |
| :--- | :--- | :--- |
| **Authentication** | Demo mode (bypassed in UI) | Reinstate JWT-based role authentication (Operator, Analyst, Admin) |
| **Rate Limiting** | No request throttling | Implement sliding-window rate limiting on `/surveys/upload` and inference APIs |
| **CORS** | Wildcard `*` allowed | Restrict to authorized hydrographic console origins |
| **Input Sanitization** | Basic extension & size validation | Comprehensive binary file parsing audit for XTF and TIFF formats |
| **Audit Logging** | Local console logging | Ship structured JSON audit logs to centralized SIEM or syslog |
| **Database Encryption** | Unencrypted SQLite at rest | Enable SQLCipher or migrate to encrypted PostgreSQL / RDS with TLS in transit |

---

## 7. Reporting Security Issues

If you identify a security vulnerability or credential leak within this codebase, please contact the development team directly:
- **Bodhisatwa Dutta:** [workwithbd18@gmail.com](mailto:workwithbd18@gmail.com)
- **Rupam Ghosh:** [rupamgh32@gmail.com](mailto:rupamgh32@gmail.com)
