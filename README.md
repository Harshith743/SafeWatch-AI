# SafeWatch AI - FDA Adverse Event Chatbot

SafeWatch AI is an intelligent, highly-optimized chatbot designed to help users query adverse drug events and report their own experiences seamlessly. It leverages the **openFDA API** to provide real-time pharmacological safety data and uses the state-of-the-art **Llama 3** LLM (via the blazing-fast **Groq API**) for Natural Language Understanding (NLU).

The application features a stunning, fully-animated **Glassmorphism UI** and is architected to run entirely on **Vercel Serverless Functions** with cloud database persistence.

## Features

- **Query Adverse Events**: Instantly retrieve reported adverse events and side effects for any drug using the openFDA database.
    - *Example:* "Show adverse events for Ibuprofen"
    - *Example:* "Are there any rare side effects of Ozempic?"
- **Report Adverse Events**: Users can report their own experiences in plain English. The AI engine automatically extracts:
    - **Drug Name**
    - **Reaction / Side Effect**
    - **Patient Age**
    - **Patient Gender**
    - *Example:* "My 64-year-old grandfather was taking 100mg of Losartan, but yesterday he woke up with severe facial swelling."
- **Interactive Follow-up**: If a report is missing critical medical details (like age or gender), the chatbot intelligently prompts the user to provide them before saving.
- **Serverless Cloud Persistence**: All valid reports and user data are securely preserved via a robust **Supabase PostgreSQL** database, ensuring data integrity beyond ephemeral serverless file systems.
- **Premium UI/UX**: Built with a dynamic, deep-space animated mesh gradient, frosted glass UI components (`backdrop-blur`), and fluid spring micro-animations via `framer-motion`.

## Tech Stack

### Frontend (Client)
- **React 18** & **Vite**: Next-generation frontend tooling for rapid rendering.
- **TailwindCSS**: Utility-first CSS framework (customized with Glassmorphism utilities).
- **Framer Motion**: Advanced physics-based spring animations and staggering.
- **Lucide Icons**: Beautiful, consistent SVG iconography.

### Backend (Serverless API)
- **Python 3.9+** & **FastAPI**: High-performance, highly concurrent web framework for building APIs.
- **Vercel Serverless Functions**: The backend is hosted as a serverless `/api` endpoint, automatically mapped via `vercel.json` monorepo routing.
- **Groq SDK**: Integrates the `llama3-8b-8192` model (and others) for instantaneous, accurate medical data extraction from unstructured patient text.
- **Supabase (PostgreSQL) / SQLAlchemy**: Robust cloud relational database to securely persist user accounts, adverse event records, and search histories.

---

## Local Development Setup

Follow these instructions to run the project locally.

### Prerequisites
- **Python 3.8+**
- **Node.js & npm**
- **Groq API Key** (Get one at [console.groq.com](https://console.groq.com/))
- **Supabase PostgreSQL URL** (Get one at [supabase.com](https://supabase.com/))

### 1. Backend Setup

1.  Navigate to the project root directory.
2.  Create and activate a virtual environment:
    ```bash
    python -m venv .venv
    # Windows:
    .\.venv\Scripts\activate
    # Mac/Linux:
    source .venv/bin/activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r api/requirements.txt
    ```
4.  Create a `.env` file in the root directory and add your keys:
    ```env
    GROQ_API_KEY="your_groq_api_key_here"
    DATABASE_URL="postgresql://user:password@your-supabase-db-url:5432/postgres"
    JWT_SECRET_KEY="generate_a_secure_random_string_here"
    ```
5.  Start the FastAPI server (it runs locally via `api/index.py`):
    ```bash
    python -m uvicorn api.index:app --reload
    ```
    The backend will be running at `http://127.0.0.1:8000`. *(Note: Locally, the app will fall back to using SQLite if `DATABASE_URL` is not provided).*

### 2. Frontend Setup

1.  Open a new terminal and navigate to the `frontend` directory:
    ```bash
    cd frontend
    ```
2.  Install Node.js dependencies:
    ```bash
    npm install
    ```
3.  Start the Vite development server:
    ```bash
    npm run dev
    ```
    The frontend will be running at `http://localhost:5173`. Proxies are configured in `vite.config.js` to automatically route `/api/chat` calls to your running FastAPI instance.

---

## Production Deployment (Vercel)

This project is meticulously configured to be deployed as a Monorepo on Vercel for free.

1. **Push your code to GitHub.**
2. **Import the repository into Vercel.**
3. **Environment Variables**: During setup, supply your `GROQ_API_KEY`, `DATABASE_URL`, and a highly secure `JWT_SECRET_KEY`.
4. **Build Settings**: Vercel will automatically detect the Vite frontend (`npm run build`). The `vercel.json` file ensures that all requests to `/api/*` are forcefully routed to the Python `api/index.py` serverless functions.
5. **Deploy!**

## Project Architecture

- `api/`: Contains the FastAPI application and backend logic.
  - `index.py`: Serverless endpoint configuration for Vercel.
  - `utils.py`: Core logic combining openFDA HTTP requests, Groq NLU parsing, and JSON generation.
  - `models.py`: SQLAlchemy database models (Users, Reports, History, Medications).
  - `database.py`: PostgreSQL/SQLite engine configuration.
  - `auth.py`: JWT token generation and authentication dependencies.
- `frontend/`: The React application source code containing the glassmorphism UI and Framer Motion logic.
- `vercel.json`: Critical routing configuration instructing Vercel how to serve a Monorepo containing both Static HTML (Vite) and Python Serverless Functions simultaneously.
