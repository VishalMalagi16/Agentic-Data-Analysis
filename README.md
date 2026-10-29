# 📊 AutoStat: Agentic Data Analysis & Statistical Synthesis

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14-black?logo=next.js&logoColor=white)](https://nextjs.org/)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![Redis](https://img.shields.io/badge/Redis-Stack-DC382D?logo=redis&logoColor=white)](https://redis.io/)
[![Google Gemini](https://img.shields.io/badge/LLM-Gemini%202.0%20Flash-4285F4?logo=google&logoColor=white)](https://ai.google.dev/)

**AutoStat** is an intelligent, multi-agent AI system designed for automated data science, exploratory data analysis (EDA), statistical synthesis, and dynamic visualization. Powered by **Google Gemini** and built on **FastAPI** and **Next.js**, AutoStat autonomously formulates analysis plans, cleans datasets, executes secure code in isolated sandboxes, and delivers real-time streaming insights.

---

## 🌟 Key Features

- 🤖 **Multi-Agent Orchestration**: Specialized agents collaborate autonomously to analyze data, execute code, and synthesize findings.
- ⚡ **Real-Time SSE Streaming**: Live updates stream from agents directly to the UI via Server-Sent Events (SSE) backed by Redis Pub/Sub.
- 🛡️ **Sandboxed Code Execution**: Dynamically generated Python scripts execute inside an isolated Docker sandbox container (`python-datasci-sandbox`) with strict memory and CPU quotas.
- 📈 **Automated EDA & Visualization**: Automatically produces univariate and bivariate statistical metrics, distribution histograms, correlation heatmaps, and scatter plots.
- 🧹 **Intelligent Data Preprocessing**: Handles missing data, identifies outliers, standardizes column types, and provides downloadable cleaned datasets.
- 💬 **Interactive Conversational UI**: Ask questions about your data in natural language and receive executive summaries, statistical tables, and interactive dashboards.

---

## 🏗️ Multi-Agent Architecture

```
                       ┌─────────────────────────┐
                       │   Next.js Frontend      │
                       │   (Port 3000)           │
                       └────────────┬────────────┘
                                    │ Upload CSV / User Prompt
                                    │ SSE Stream Updates
                                    ▼
                       ┌─────────────────────────┐
                       │   FastAPI Backend       │
                       │   (Port 8000)           │
                       └────────────┬────────────┘
                                    │
                                    ▼
                       ┌─────────────────────────┐
                       │   Orchestrator Agent    │
                       └────────────┬────────────┘
         ┌──────────────────────────┼──────────────────────────┐
         ▼                          ▼                          ▼
┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│  Summary Agent   │       │ Preprocess Agent │       │ Univariate Agent │
└──────────────────┘       └──────────────────┘       └──────────────────┘
         │                          │                          │
         ▼                          ▼                          ▼
┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│ Bivariate Agent  │       │ Code Exec Agent  │       │ Synthesizer Agent│
│                  │       │ (Docker Sandbox) │       │ (Final Report)   │
└──────────────────┘       └──────────────────┘       └──────────────────┘
                                    │
                       ┌────────────┴────────────┐
                       │ Redis (State & Pub/Sub) │
                       │ (Port 6379)             │
                       └─────────────────────────┘
```

### Specialized Agents:
1. **Orchestrator Agent**: Breaks down user queries, manages conversation memory, and dynamically routes sub-tasks to specialized domain agents.
2. **Data Summary Agent**: Evaluates dataframe schema, missingness, numeric and categorical distributions, and shape.
3. **Preprocessing Agent**: Cleans anomalies, handles null values, imputes missing records, and saves clean datasets.
4. **Univariate Analysis Agent**: Conducts single-variable statistical testing, skewness, kurtosis, and distribution plots.
5. **Bivariate Analysis Agent**: Examines cross-variable relationships, correlation matrices, and comparative visualizations.
6. **Code Execution Agent**: Generates data science scripts and securely executes them inside an isolated Docker container with strict runtime resource bounds.
7. **Synthesizer Agent**: Compiles comprehensive reports, summarizing insights, statistical findings, and recommended next steps.

---

## 📁 Repository Structure

```
AutoStat/
├── backend/
│   ├── artifacts/                 # Generated plots and cleaned datasets
│   │   ├── datasets/
│   │   └── plots/
│   ├── bivariate_env/             # Bivariate statistical agent & prompts
│   ├── code_execution_env/        # Secure Docker sandbox execution agent
│   ├── preprocessing_env/         # Data cleaning & imputation agent
│   ├── summary_env/               # Data profiling & summary agent
│   ├── synthesizer_env/           # Report synthesis agent
│   ├── univariate_env/            # Single-variable analysis agent
│   ├── analysis_state.py          # Central session state data structure
│   ├── dockerfile                 # Dockerfile for python-datasci-sandbox
│   ├── Dockerfile.backend         # Dockerfile for FastAPI backend service
│   ├── example_data.csv           # Sample dataset for demonstration
│   ├── main.py                    # FastAPI entrypoint, SSE endpoints & routes
│   ├── orchestrator.py            # Main agent orchestrator logic
│   ├── orchestrator_agent_prompt.py
│   └── requirements.txt           # Python dependencies
│
├── frontend/
│   ├── src/
│   │   ├── app/                   # Next.js app directory (layout, globals, page)
│   │   └── components/
│   │       ├── chat/              # Chat interface, message bubble, input bar
│   │       ├── controls/          # File upload & download controls
│   │       └── dashboard/         # Visualization dashboard & plot cards
│   ├── Dockerfile.frontend        # Dockerfile for Next.js web application
│   ├── next.config.mjs            # Next.js build configuration
│   ├── package.json               # Node.js dependencies & scripts
│   ├── postcss.config.mjs         # PostCSS configuration
│   └── tailwind.config.js         # Tailwind CSS styling configuration
│
├── docker-compose.yml             # Orchestration for Redis, Backend & Frontend
├── .dockerignore                  # Docker build ignores
├── .gitignore                     # Git ignore rules
└── README.md                      # Project documentation
```

---

## 🚀 Getting Started

### Prerequisites

1. **Docker Desktop**: [Download and install Docker Desktop](https://www.docker.com/products/docker-desktop/) (ensure WSL 2 backend is enabled on Windows).
2. **Google Gemini API Key**: Obtain a key from [Google AI Studio](https://aistudio.google.com/).

---

### Method 1: Run with Docker Compose (Recommended)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/VishalMalagi16/Agentic-Data-Analysis.git
   cd Agentic-Data-Analysis
   ```

2. **Set your Google Gemini API Key:**
   - **PowerShell (Windows):**
     ```powershell
     $env:GOOGLE_API_KEY="your-google-api-key"
     ```
   - **Linux / macOS:**
     ```bash
     export GOOGLE_API_KEY="your-google-api-key"
     ```

3. **Pre-build the Data Science Sandbox Image:**
   ```bash
   docker build -t python-datasci-sandbox -f backend/dockerfile backend
   ```

4. **Launch all services:**
   ```bash
   docker-compose up --build
   ```

5. **Open the App:**
   - **Frontend UI**: [http://localhost:3000](http://localhost:3000)
   - **Backend API & Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
   - **Redis**: Port `6379`

---

### Method 2: Local Development Setup

#### 1. Start Redis Stack
```bash
docker run -d --name autostat-redis -p 6379:6379 redis/redis-stack-server:latest
```

#### 2. Build Sandbox Container
```bash
cd backend
docker build -t python-datasci-sandbox -f dockerfile .
```

#### 3. Run FastAPI Backend
```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate    # On Windows: .\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GOOGLE_API_KEY="your-google-api-key"   # Windows: $env:GOOGLE_API_KEY="your-key"
export REDIS_HOST="localhost"

# Start backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 4. Run Next.js Frontend
```bash
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev
```

Visit [http://localhost:3000](http://localhost:3000).

---

## 🧪 Usage Example

1. Open **[http://localhost:3000](http://localhost:3000)** in your browser.
2. Upload any CSV dataset (or use `backend/example_data.csv`).
3. Enter your prompt in the chat box, e.g.:
   - *"Perform a complete exploratory data analysis of this dataset."*
   - *"Check for missing values, impute them, and generate distribution plots."*
   - *"Analyze correlations between numerical features and highlight key patterns."*
4. Watch the agents stream live updates, generate plots, and deliver synthesized statistical reports!

---

## ⚙️ Environment Configuration

| Variable | Description | Default | Required |
| :--- | :--- | :--- | :--- |
| `GOOGLE_API_KEY` | Gemini API key for LLM agents | None | **Yes** |
| `REDIS_HOST` | Hostname of the Redis instance | `redis` / `localhost` | **Yes** |

---

## 🛠️ Tech Stack

- **Backend**: FastAPI, Python 3.10+, Pandas, NumPy, Scikit-learn, Matplotlib, Seaborn, Statsmodels, Missingno
- **Agents & LLM**: Google Gemini 2.0 Flash Lite via `google-generativeai`
- **Frontend**: Next.js 14, React 18, Tailwind CSS, React Markdown, React Icons
- **Cache & Pub/Sub**: Redis Stack (`redis/redis-stack-server`)
- **Containers**: Docker, Docker Compose

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
