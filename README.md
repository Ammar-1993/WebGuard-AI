# 🛡️ WebGuard AI - Intelligent Vulnerability Scanner

WebGuard AI is an advanced, automated Dynamic Application Security Testing (DAST) platform designed to detect vulnerabilities based on global standards (OWASP Top 10). The system innovates a solution to the notorious complexity of traditional security reports by seamlessly integrating a trusted cybersecurity engine (OWASP ZAP) with the analytical power of AI (via **LangChain & OpenAI**).

While the underlying ZAP engine conducts a rigorous, deep scan of the target web application to uncover security flaws, the platform's AI layer analyzes the raw technical outputs. It effectively eliminates false positives (False Positives) and translates dense security jargon into a highly readable report. By providing developers with actionable steps, ready-to-use remediation code, and a precise **Security Score**, WebGuard AI transforms raw vulnerability data into a clear, developer-friendly security posture evaluation.

---

## 🏗️ Microservices Architecture

The system is built using a microservices architecture to ensure security, scalability, and strict separation of concerns. The entire platform runs inside isolated containers managed seamlessly by **Docker Compose**.

| Service | Tech Stack | Port | Description |
| :--- | :--- | :--- | :--- |
| **Frontend UI** | Next.js, React, Tailwind CSS | `3030` | Interactive user interface and dashboard |
| **Backend API** | FastAPI, Python | `8010` | Central server and core system orchestrator |
| **AI Analyzer** | LangChain, OpenAI API, FastAPI | `8011` | Isolated AI service for analysis and remediation |
| **Security Scanner** | Python, ZAP API Wrapper | `8012` | Bridge and controller for the ZAP engine |
| **ZAP Engine** | OWASP ZAP (Daemon) | `8092` | The actual security engine extracting vulnerabilities |
| **Database** | MongoDB | `27017` | NoSQL storage for reports and security scoring |

---

## 🔄 Data Flow & Pipeline

1. **Discovery Stage:** The `OWASP ZAP` engine receives the target URL and executes a safe payload attack to detect vulnerabilities (OWASP Top 10).
2. **Routing Stage:** The `Security Scanner` wrapper retrieves the raw JSON report and forwards it to the central `FastAPI` server.
3. **AI Analysis Stage:** Data is securely passed to the `AI Analyzer` to filter false positives, translate technical jargon into readable insights, and generate specific framework-level remediation code.
4. **Scoring & Storage Stage:** The central server calculates the overall Security Score and securely stores the final structured report in `MongoDB`.
5. **Visualization Stage:** The `Next.js` frontend fetches the data, rendering it on an interactive dashboard with PDF export capabilities.

---

## ⚙️ Prerequisites

* **OS:** Windows 11 with **WSL2** enabled (Ubuntu 22.04 LTS recommended), or native Linux/macOS.
* **Docker Desktop** (with WSL integration enabled).
* **Git** & **VS Code** (or Antigravity IDE with Remote-WSL extension).
* An active **OpenAI API Key**.

---

## 🚀 Local Installation & Setup

**1. Clone the repository:**
```bash
git clone git@github.com:Ammar-1993/WebGuard-AI.git
cd WebGuard-AI

2. Configure Environment Variables:
Create a .env file in the root directory of the project and add your secure credentials:

 OPENAI_API_KEY=your_openai_api_key_here
 JWT_SECRET=your_super_secret_jwt_key

3. Build and Run the System:
Launch the entire microservices ecosystem with a single Docker command:

 docker-compose up --build -d

4. Access the Services:

 Frontend Dashboard: http://localhost:3030
 Backend API Docs (Swagger UI): http://localhost:8010/docs

Developed following Clean Architecture and modern DevOps best practices.