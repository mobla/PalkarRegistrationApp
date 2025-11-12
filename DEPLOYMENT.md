# Deployment Guide for Render.com - Palkar Registration App

## Quick Start

1. **Push code to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Prepare for Render deployment"
   git remote add origin <your-github-repo-url>
   git push -u origin main
   ```

2. **Create Web Service on Render**
   - Go to https://dashboard.render.com
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select the repository and branch

3. **Configure Service Settings:**
   - **Name**: `palkar-registration-app` (or your choice)
   - **Root Directory**: Leave empty (root of repo)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Plan**: Free (or choose paid plan)

4. **Set Environment Variables:**
   - Go to "Environment" tab
   - Add the following:
     - `SECRET_KEY`: Generate with `python -c "import secrets; print(secrets.token_hex(32))"`
     - `SMTP_USER`: Your Gmail address (e.g., `palkardiwali@gmail.com`)
     - `SMTP_PASSWORD`: Your Gmail app password (not regular password)
     - `SMTP_SERVER`: (Optional) Defaults to `smtp.gmail.com`
     - `SMTP_PORT`: (Optional) Defaults to `587`
     - `DATABASE_URL`: (Optional) If using PostgreSQL, create a PostgreSQL database on Render and use its connection string

5. **Deploy**
   - Click "Create Web Service"
   - Wait for build to complete
   - Your app will be live at `https://palkar-registration-app.onrender.com` (or your custom domain)

## Gmail App Password Setup

Since the app uses Gmail for sending QR codes, you need to:

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate an App Password**:
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and "Other (Custom name)"
   - Enter "Palkar Registration App"
   - Copy the generated 16-character password
   - Use this as `SMTP_PASSWORD` in Render environment variables

## Using PostgreSQL (Recommended for Production)

1. **Create PostgreSQL Database:**
   - In Render dashboard, click "New +" → "PostgreSQL"
   - Name it (e.g., `palkar-db`)
   - Select Free plan
   - Click "Create Database"

2. **Link Database to Web Service:**
   - Go to your Web Service settings
   - In "Environment" tab, add:
     - Key: `DATABASE_URL`
     - Value: Copy from PostgreSQL service's "Internal Database URL"

3. **The app will automatically:**
   - Detect PostgreSQL connection string
   - Convert `postgres://` to `postgresql://` (required by SQLAlchemy)
   - Use PostgreSQL instead of SQLite

## Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `SECRET_KEY` | Yes | Flask session secret key | `your-secret-key-here` |
| `SMTP_USER` | Yes | Gmail address for sending emails | `palkardiwali@gmail.com` |
| `SMTP_PASSWORD` | Yes | Gmail app password | `your-16-char-app-password` |
| `SMTP_SERVER` | No | SMTP server (default: smtp.gmail.com) | `smtp.gmail.com` |
| `SMTP_PORT` | No | SMTP port (default: 587) | `587` |
| `DATABASE_URL` | No | PostgreSQL connection string | `postgres://user:pass@host/db` |
| `PORT` | No | Server port (auto-set by Render) | `10000` |

## Features

- ✅ QR Code generation for event attendees
- ✅ Email notifications with QR codes
- ✅ Real-time check-in scanning
- ✅ Admin dashboard with attendee management
- ✅ PDF export of attendee lists
- ✅ Headcount tracking

## Troubleshooting

### Build Fails
- Check that `requirements.txt` is in the root directory
- Verify Python version in `runtime.txt` (if specified)
- Check build logs for specific errors

### Email Not Sending
- Verify `SMTP_USER` and `SMTP_PASSWORD` are set correctly
- Ensure you're using Gmail App Password (not regular password)
- Check that 2FA is enabled on Gmail account
- Review Render logs for SMTP errors

### Database Connection Issues
- Ensure `DATABASE_URL` is set correctly if using PostgreSQL
- Verify PostgreSQL database is running
- Check that connection string uses `postgresql://` (not `postgres://`)

### App Crashes on Startup
- Check logs in Render dashboard
- Verify all required environment variables are set
- Ensure `gunicorn` is in requirements.txt
- Check that `Procfile` exists and is correct

### QR Codes Not Generating
- Verify `static/qr_codes/` directory has write permissions
- Check Render logs for file system errors
- Ensure static files are being served correctly

## Files Required for Deployment

- ✅ `requirements.txt` - Python dependencies
- ✅ `Procfile` - Start command for Render
- ✅ `app.py` - Main application file
- ✅ `.gitignore` - Excludes unnecessary files
- ✅ `runtime.txt` - (Optional) Python version specification
- ✅ `static/` - Static files (images, JS, CSS)
- ✅ `templates/` - HTML templates
- ✅ `utils/` - Utility modules

## Notes

- Free tier on Render spins down after 15 minutes of inactivity
- First request after spin-down may take 30-60 seconds
- Consider upgrading to paid plan for always-on service
- SQLite works but is not recommended for production (use PostgreSQL)
- QR codes are stored in `static/qr_codes/` directory
- Make sure to backup your database regularly

