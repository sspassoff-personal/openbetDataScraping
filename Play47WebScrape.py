from tkinter import CURRENT
import requests
from bs4 import BeautifulSoup
import time
import asyncio
from dotenv import load_dotenv
import os
from asyncio import Lock

try:
    from telegram import Bot
except ImportError:
    print("Module 'telegram' not found. Install it using 'pip install python-telegram-bot'")
    exit()

load_dotenv()

# Telegram Bot Configuration
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

# Hardcoded Chat IDs (add as many as needed)
CHAT_IDS = {
    os.getenv('TELEGRAM_CHAT_ID_1'),   # Replace with actual Chat ID 1
    os.getenv('TELEGRAM_CHAT_ID_2'),   # Replace with actual Chat ID 2
    os.getenv('TELEGRAM_CHAT_ID_3'),   # Replace with actual Chat ID 3
}

# URL Configuration
LOGIN_URL = 'https://reports.play47.com/'
TARGET_URL = 'https://reports.play47.com/Report/OpenBets.aspx'
REFRESH_INTERVAL = 10  # seconds
RELOGIN_INTERVAL = 600  # 10 minutes

# Credentials
USERNAME = 'alanrodma'
PASSWORD = 'alanrod'

detectedTicketCount = 0
# Global ticket set to track previously detected tickets
previous_tickets = set()
notified_tickets = set()

tickets_lock = Lock()

# Initialize Telegram Bot
bot = Bot(token=TELEGRAM_TOKEN)

# Start a session
session = requests.Session()

# Send Telegram Notification to All Chat IDs
async def send_telegram_notification(message):
    try:
        if CHAT_IDS:
            for chat_id in CHAT_IDS:
                print(f"Sending message to {chat_id}: {message}")
               # await bot.send_message(chat_id=chat_id, text=message)
                detectedTicketCount = 0
        else:
            print("No registered users to notify.")
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
        player_name = extract_player_name()

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
                    bet_info = f"Player: {player_name} - STRAIGHT BET - {description}"
                else:
                    bet_info = f"Player: {player_name} - STRAIGHT BET - No description found"

                straight_bets.add(bet_info)

        return straight_bets
    except Exception as e:
        print(f"Error fetching STRAIGHT BETs: {e}")
        return set()

# Extract player name
def extract_player_name():
    player_name_extract = set()
    try:
        response = session.get(TARGET_URL)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Locate all <player> tags
        player_elements = soup.select('span.notation')

        for player_element in player_elements:
            # Extract the player name
            player_name = player_element.get_text(strip=True)

            # Construct the info
            bet_info = f"Player: {player_name}"
            player_name_extract.add(bet_info)

        return player_name_extract

    except Exception as e:
        print(f"Error fetching Player Name: {e}")
        return set()


# Check session status
async def session_check():
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

# Monitor for New Tickets
async def monitor_tickets():
    global detectedTicketCount
    global previous_tickets
    global notified_tickets
    global tickets_lock

    error_count = 0
    max_errors = 10
    retry_delay = 10  # seconds

    try:
        current_tickets = set(await get_ticket_numbers())

        async with tickets_lock:
            if detectedTicketCount == 0:
                print(f"Detected tickets: {current_tickets}")
                detectedTicketCount = 1
        
            new_tickets = current_tickets - previous_tickets

            for ticket in new_tickets:
                if ticket not in previous_tickets:
                    await send_telegram_notification(f"New Ticket Detected: {ticket}")
                    notified_tickets.add(ticket)

            # Update previous_tickets after processing
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

async def main():
    global previous_tickets

    RESTART_INTERVAL = 20 * 60 * 60  # 12 hours in seconds
    REFRESH_INTERVAL = 10  # 10 seconds

    while True:
        # Login before starting the main tasks
        await login_to_site()

        start_time = time.time()

        while time.time() - start_time < RESTART_INTERVAL:
            try:
                tasks = [
                    asyncio.create_task(session_check()),
                    asyncio.create_task(monitor_tickets())
                ]

                # Wait for tasks to complete
                await asyncio.gather(*tasks)
                await asyncio.sleep(REFRESH_INTERVAL)

            except Exception as e:
                print(f"Error in main loop: {e}")
                await send_telegram_notification(f"Error in main loop: {e}")

        # Reset the global ticket set after the 12-hour interval
        print(f"Restarting tasks after 12 hours. Resetting ticket set...")
        async with tickets_lock:
            previous_tickets.clear()
            notified_tickets.clear()
            detectedTicketCount = 0

if __name__ == '__main__':
    asyncio.run(main())



