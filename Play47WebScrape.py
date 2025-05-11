import requests
from bs4 import BeautifulSoup
import time
import asyncio
from dotenv import load_dotenv
import os

try:
    from telegram import Bot
except ImportError:
    print("Module 'telegram' not found. Install it using 'pip install python-telegram-bot'")
    exit()

load_dotenv()

# Telegram Bot Configuration
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# URL Configuration
LOGIN_URL = 'https://reports.play47.com/'
TARGET_URL = 'https://reports.play47.com/Report/OpenBets.aspx'
REFRESH_INTERVAL = 10  # seconds
RELOGIN_INTERVAL = 600  # 10 minutes

# Credentials
USERNAME = 'alanrodma'
PASSWORD = 'alanrod'

# Initialize Telegram Bot
bot = Bot(token=TELEGRAM_TOKEN)

# Start a session
session = requests.Session()

# Send Telegram Notification
async def send_telegram_notification(message):
    try:
        print(f"Sending message: {message}")
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception as e:
        print(f"Error sending message: {e}")

# Login to the site
async def login_to_site(retry_count=3):
    try:
        # Payload data based on login form
        payload = {
            'Account': USERNAME,
            'Password': PASSWORD
        }
        response = session.post(LOGIN_URL, data=payload)
        response.raise_for_status()

        if 'logout' in response.text.lower() or 'dashboard' in response.text.lower():
            print("Login successful")
            await send_telegram_notification("Login successful to Play47")
        else:
            print("Login failed. Check credentials or login payload.")
            await send_telegram_notification("Login attempt failed to Play47")
            if retry_count > 0:
                print("Retrying login...")
                await asyncio.sleep(5)
                await login_to_site(retry_count - 1)
            else:
                await send_telegram_notification("Login failed after multiple attempts")

    except Exception as e:
        print(f"Login error: {e}")
        await send_telegram_notification(f"Login error: {e}")

# Fetch Ticket Numbers
async def get_ticket_numbers():
    try:
        response = session.get(TARGET_URL)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        straight_bets = set()
        bet_elements = soup.select('td.define-height-td')

        for bet in bet_elements:
            text_content = bet.get_text(separator='|', strip=True)
            if 'STRAIGHT BET' in text_content:
                # Extract the description after STRAIGHT BET
                parts = text_content.split('|')
                if len(parts) > 1:
                    description = parts[1].strip()
                    bet_info = f"STRAIGHT BET - {description}"
                else:
                    bet_info = "STRAIGHT BET - No description found"

                straight_bets.add(bet_info)

        return straight_bets
    except Exception as e:
        print(f"Error fetching STRAIGHT BETs: {e}")
        return set()

# Check session status
async def session_check():
    while True:
        try:
            response = session.get(TARGET_URL)
            if "loginForm" in response.text.lower():
                print("Session expired. Re-logging in...")
                await send_telegram_notification("Session expired. Re-logging in...")
                await login_to_site()
            else:
                print("Session is still active.")

        except Exception as e:
            print(f"Error in session check: {e}")
            await send_telegram_notification(f"Error in session check: {e}")

        await asyncio.sleep(RELOGIN_INTERVAL)

# Monitor for New Tickets
async def monitor_tickets():
    error_count = 0
    max_errors = 10
    retry_delay = 10  # seconds
    previous_tickets = set()

    await login_to_site()

    while True:
        try:
            current_tickets = set(await get_ticket_numbers())
            print(f"Detected tickets: {current_tickets}")
            new_tickets = current_tickets - previous_tickets

            for ticket in new_tickets:
                if ticket not in previous_tickets:
                    await send_telegram_notification(f"New Ticket Detected: {ticket}")

            previous_tickets = current_tickets
            error_count = 0  # Reset error count after successful run

        except Exception as e:
            print(f"Error in ticket monitoring: {e}")
            error_count += 1
            if error_count <= max_errors:
                await send_telegram_notification("Error in ticket monitoring. Attempting re-login...")
            elif error_count > max_errors:
                print("Error notification limit reached. Not sending further error notifications.")

            await asyncio.sleep(retry_delay)
            await login_to_site()

        await asyncio.sleep(REFRESH_INTERVAL)

if __name__ == '__main__':
    asyncio.run(monitor_tickets())





