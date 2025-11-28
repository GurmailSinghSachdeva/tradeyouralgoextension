# Trade Your Algo Extension

Automated login to 5paisa trading website using Playwright and send access token to backend API for automated trading.

## Features

- 🔐 Automated login to 5paisa trading website using Playwright
- 🎫 Extract access token from browser storage (localStorage, sessionStorage, cookies)
- 📡 Send access token to backend API for automated trading
- ⚙️ Configurable via environment variables
- 📝 Comprehensive logging

## Setup

1. **Create a virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Install Playwright browsers:**
```bash
playwright install chromium
```

4. **Configure environment variables:**
```bash
cp .env.example .env
```

Edit `.env` file with your credentials:
```env
# 5paisa Login Credentials
FIVEPAISA_USERNAME=your_username_or_email
FIVEPAISA_PASSWORD=your_password
FIVEPAISA_PIN=your_pin_if_required

# Backend API Configuration
BACKEND_API_URL=http://localhost:8000

# Playwright Settings
HEADLESS=false  # Set to true to run browser in background
TIMEOUT=30000
```

## Usage

### Run the application:
```bash
python -m tradeyouralgoextension
```

Or if installed in development mode:
```bash
pip install -e .
tradeyouralgoextension
```

## Project Structure

```
tradeyouralgoextension/
├── tradeyouralgoextension/
│   ├── __init__.py           # Package initialization
│   ├── main.py               # Main entry point
│   ├── config.py             # Configuration management
│   ├── fivepaisa_login.py   # Playwright login automation
│   └── backend_client.py     # Backend API client
├── requirements.txt          # Python dependencies
├── setup.py                  # Package setup
├── .env.example              # Environment variables template
└── README.md                 # This file
```

## How It Works

1. **Login Automation**: Uses Playwright to automate browser login to 5paisa website
2. **Token Extraction**: Extracts access token from browser storage (localStorage, sessionStorage, or cookies)
3. **Backend Communication**: Sends the access token to your backend API endpoint
4. **Automated Trading**: Your backend can now use the token for automated trading

## Backend API Expected Format

The application sends a POST request to `{BACKEND_API_URL}/api/auth/token` with:

```json
{
  "access_token": "your_token_here",
  "source": "5paisa",
  "timestamp": null
}
```

## Customization

### Updating Login Selectors

If 5paisa website structure changes, update selectors in `fivepaisa_login.py`:
- `username_selector`: Input field for username/email
- `password_selector`: Input field for password
- `login_button_selector`: Login button
- `pin_selector`: PIN input field (if required)

### Token Extraction

The application automatically searches for tokens in:
1. localStorage (keys containing "token", "auth", or "access")
2. sessionStorage (same pattern)
3. Cookies (same pattern)

If your token is stored differently, modify the `_extract_access_token()` method in `fivepaisa_login.py`.

## Troubleshooting

- **Login fails**: Check if selectors match the current 5paisa website structure. A screenshot will be saved as `login_error.png` on failure.
- **Token not found**: Verify token storage location and update extraction logic if needed.
- **Backend connection fails**: Check `BACKEND_API_URL` in `.env` and ensure backend is running.

## Security Notes

- Never commit `.env` file to version control (already in `.gitignore`)
- Keep credentials secure
- Consider using encrypted storage for production deployments

