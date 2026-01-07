# Barber Shop Assistant Bot (Python Migration)

This project adapts the "Agente Barbería" n8n workflow to a Python application using `python-telegram-bot` and Google Gemini.

## Prerequisites

1.  **Python 3.9+** installed.
2.  **Telegram Bot Token**: Get it from @BotFather.
3.  **Google Gemini API Key**: Get it from AI Studio.
4.  **Google Cloud Project** with:
    *   Google Calendar API enabled.
    *   Google Sheets API enabled.
5.  **Service Account Credentials**:
    *   Create a Service Account in GCP.
    *   Download the JSON key and rename it to `credentials.json`.
    *   **Important**: Share your Google Calendar and Google Sheet with the `client_email` found inside `credentials.json` (Give "Editor" access).

## Setup

1.  Clone/Copy this folder.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Configure environment:
    *   Copy `.env.example` to `.env`.
    *   Fill in the values.
    *   `GOOGLE_CALENDAR_ID`: Usually `primary` (if using Service Account's calendar) OR the specific Calendar ID (email address) of the calendar you shared.
    *   `GOOGLE_SPREADSHEET_ID`: The long string in your Google Sheet URL.

## Running Locally

```bash
python bot.py
```

## Running on VPS (Linux/Ubuntu)

### Option 1: Systemd Service (Recommended)

1.  Upload files to the VPS (e.g., `/opt/barber-bot`).
2.  Create a virtual environment:
    ```bash
    cd /opt/barber-bot
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```
3.  Create a service file: `sudo nano /etc/systemd/system/barber-bot.service`
    ```ini
    [Unit]
    Description=Barber Bot Service
    After=network.target

    [Service]
    User=root
    WorkingDirectory=/opt/barber-bot
    ExecStart=/opt/barber-bot/venv/bin/python bot.py
    Restart=always

    [Install]
    WantedBy=multi-user.target
    ```
4.  Start the service:
    ```bash
    sudo systemctl enable barber-bot
    sudo systemctl start barber-bot
    ```

### Option 2: Docker

1.  Build the image:
    ```bash
    docker build -t barber-bot .
    ```
2.  Run conversation:
    ```bash
    docker run -d --env-file .env -v $(pwd)/credentials.json:/app/credentials.json --name barber-bot barber-bot
    ```
