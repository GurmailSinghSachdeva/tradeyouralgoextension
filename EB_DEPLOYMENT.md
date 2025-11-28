# AWS Elastic Beanstalk Deployment Guide

## Environment Variables Configuration

Set these environment variables in Elastic Beanstalk:

### Required Variables:
```bash
# 5paisa Credentials
FIVEPAISA_MOBILE_NUMBER=7838856179
FIVEPAISA_PIN=634863

# Backend API (your backend server)
BACKEND_API_URL=https://your-backend-api.com

# OTP API Configuration
OTP_API_URL=https://your-eb-domain.elasticbeanstalk.com
# OR Elastic Beanstalk will auto-detect from PORT env var

# Playwright Settings
HEADLESS=true  # Must be true for server deployment

# Logging Settings
USE_UTC=false  # Set to false for IST timezone (default: IST)
```

### Optional Variables:
```bash
# OTP API (auto-detected if not set)
OTP_API_PORT=5055  # Usually Elastic Beanstalk sets PORT automatically
OTP_API_HOST=0.0.0.0  # Default - accepts external connections
OTP_API_ENABLED=true

# 5paisa Vendor Configuration
FIVEPAISA_VENDOR_KEY=NgsvVsF61rnO6VAXASdlhvXqLnkZuKCT
FIVEPAISA_RESPONSE_URL=https://tradeyouralgo.com
```

## Important Notes:

1. **Logging Timezone**: By default, logs are displayed in IST (Indian Standard Time). Set `USE_UTC=true` if you want UTC timestamps instead.

2. **PORT Environment Variable**: Elastic Beanstalk automatically sets the `PORT` environment variable. The application will use this automatically.

3. **OTP_API_URL**: 
   - Set this to your Elastic Beanstalk domain (e.g., `https://your-app.elasticbeanstalk.com`)
   - Or leave empty and it will auto-detect from `PORT` env var
   - Make webhook should point to: `https://your-app.elasticbeanstalk.com/api/otp`

4. **HEADLESS Mode**: Must be `true` for server deployment (no display available)

5. **Playwright Browsers**: Make sure Playwright browsers are installed. You may need to add a `.ebextensions` config:

```yaml
# .ebextensions/01_install_playwright.config
container_commands:
  01_install_playwright:
    command: "source /var/app/venv/*/bin/activate && playwright install chromium"
```

## Make Webhook Configuration:

In Make, configure the webhook to send OTP to:
```
POST https://your-eb-domain.elasticbeanstalk.com/api/otp
Content-Type: application/json

Body:
{
  "otp": "123456"
}
```

## Health Check:

Elastic Beanstalk can use the health endpoint:
```
GET https://your-eb-domain.elasticbeanstalk.com/health
```

## Deployment Steps:

1. Create a `.ebextensions` folder in your project root
2. Add Playwright browser installation config (see above)
3. Set environment variables in EB console
4. Deploy your application
5. Update Make webhook URL to your EB domain

