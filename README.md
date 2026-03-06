# Socialease - Unified Social Media Inbox

A centralized dashboard built for social media managers to monitor Meta, TikTok, YouTube, and Discord feeds from one secure, Discord-themed interface.

## Tech Stack

* **Backend:** Python, FastAPI, SQLAlchemy 2.0
* **Security:** passlib (bcrypt), python-jose (JWT), cryptography (Fernet)
* **Frontend:** HTML, Tailwind CSS, Vanilla JS, Jinja2 Templates (Optimized for Core Web Vitals)
* **AI & Summarization:** Google GenAI SDK (`gemini-2.5-flash`)
* **Testing:** Pytest

## Core Features

* **Unified Inbox:** View Discord webhooks, Meta API, and YouTube API incoming messages in one place.
* **Smart Summaries:** Uses Google Gemini API to summarize messages and provide priority scores.
* **Authentication:** Full JWT session management with a manual lock screen overlay. Includes secure registration, real-time password strength validation, and a mockable "Forgot Password" reset flow.
* **Platform Connections:** Add webhooks and access tokens securely using Fernet encryption. Dynamically switch between connected platform message feeds directly in the dashboard UI.

## Project Structure (MVC)
The application is structured using modular FastAPI best practices:
* `app/models.py` - Database schemas.
* `app/database.py` - SQLAlchemy configuration.
* `app/security.py` - Hashing, JWT, and Fernet encryption.
* `app/logger.py` - Centralized application logging configuration.
* `app/routers/` - API endpoints broken down by feature (`auth`, `messages`, `views`).
* `app/templates/` - Jinja2 HTML templates for the frontend.
* `main.py` - The entry point for Uvicorn.

## Troubleshooting & Logs

The application implements centralized logging to assist with debugging and monitoring. 

* **Console Logs:** While running `python main.py` locally, all requests and errors will print directly to your terminal.
* **File Logs:** Logs are automatically written to `logs/app.log` in the project root. This file captures detailed stack traces for unhandled exceptions and validation errors. The logger uses a rotating file handler (creating backups like `app.log.1` when it reaches 5MB) to prevent disk overflow.

If you encounter an "Internal Server Error" in the UI, check `logs/app.log` for the exact Python stack trace to diagnose the issue.

## Local Development Setup

1. **Clone the repository and navigate into it.**

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   # If 'python' is not recognized, try using 'python3' or 'py':
   # python3 -m venv venv
   # py -m venv venv
   ```

3. **Activate the virtual environment:**
   * On Windows use: `venv\Scripts\activate`
   * On macOS/Linux use: `source venv/bin/activate`

4. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

5. **Environment Variables:**
    Create a `.env` file in the root directory (or set it in your system environment) and add your Gemini API Key for AI summarization features:
    ```bash
    GEMINI_API_KEY="your_api_key_here"
    ```

6. **Run the Application:**
    ```bash
    python main.py
    ```

7. **View the Dashboard:**
    Open your browser and navigate to `http://localhost:8000`. You will be prompted to register/login. On startup, it automatically seeds dummy data into the SQLite database.

## Running Tests (TDD)
We utilize ``pytest`` to ensure database stability and API reliability.
To run the tests, simply execute:
    ```bash
    pytest test_main.py -v