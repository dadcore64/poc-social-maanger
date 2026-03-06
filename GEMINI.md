# Socialease - Project Context

## Project Overview
Socialease is a centralized dashboard built for social media managers to monitor Meta, TikTok, YouTube, and Discord feeds from a single, unified, Discord-themed interface. It features secure JWT authentication (with real-time form validation and a password reset flow), dynamic platform connections, and AI-driven message summarization using the Gemini API. 

### Architecture & Tech Stack
*   **Backend:** Python, FastAPI, SQLAlchemy 2.0 (currently using SQLite for local development and testing).
*   **Security:** passlib (bcrypt), python-jose (JWT), cryptography (Fernet).
*   **AI:** Google GenAI SDK (`gemini-2.5-flash`) for automated summarization and prioritization.
*   **Frontend:** HTML, Tailwind CSS, Vanilla JS, rendered via Jinja2 Templates. Assets are optimized for Core Web Vitals and located in `app/static/`.
*   **Testing:** Pytest.

## Building and Running

### Prerequisites
*   Python 3 installed.

### Setup Instructions
1.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    # If 'python' is not recognized, try using 'python3' or 'py':
    # python3 -m venv venv
    # py -m venv venv
    ```
2.  **Activate the virtual environment:**
    *   On Windows: `venv\Scripts\activate`
    *   On macOS/Linux: `source venv/bin/activate`
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Running the Application
To start the FastAPI development server:
```bash
python main.py
```
*Note: The application will run on `http://localhost:8000`. On startup, it automatically seeds dummy data into the SQLite database for demonstration purposes.*

### Running Tests
The project uses Pytest for database stability and API reliability testing.
```bash
pytest test_main.py -v
```

## Development Conventions
*   **Database:** Currently utilizes SQLite (`socialease.db`) for easy local development, but is designed to be easily swappable to PostgreSQL.
*   **Testing (TDD):** A separate testing database (`test.db`) is used during test execution to ensure tests are isolated and do not affect the main development database.
*   **Logging & Debugging:** Centralized logging is configured in `app/logger.py`. It uses a global exception handler and HTTP middleware in `app/main.py` to trace request lifecycles. Logs are output to the console for local development and rotated into `logs/app.log` for persistent troubleshooting.
*   **Frontend Structure:** The frontend is a single-page application built with vanilla HTML/JS and Tailwind CSS. It is rendered using Jinja2 templates located in the `app/templates` directory.
*   **Application Structure:** The codebase follows an MVC (Model-View-Controller) pattern using FastAPI modular routers (`app/routers/`), separated database schemas (`app/models.py`), and dedicated configuration files.
*   **Frontend Modularity:** To minimize redundant logic in Vanilla JS, extract and reuse common utility functions across the application (e.g., sharing the alidatePasswordStrength and alidateConfirmPassword logic between the Registration and Reset Password forms).
