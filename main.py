import time
import os
import sys

from random import random
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, expect
from pynput.keyboard import Key, Controller
from dotenv import load_dotenv, set_key

# 1. Set a persistent path for the browser
# If we don't do this, the .exe will download Chromium into a temporary folder
# and wipe it when the app closes, forcing a massive download on every launch.
browser_path = os.path.join(os.path.expanduser("~"), "MyAppBrowsers")
os.makedirs(browser_path, exist_ok=True)
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = browser_path

# 2. Programmatically invoke the Playwright installer
from playwright.__main__ import main as playwright_main

original_argv = sys.argv.copy()
try:
    # Spoof the command line arguments to run the installer
    sys.argv = ["", "install", "chromium"]
    playwright_main()
except SystemExit:
    # playwright_main() calls sys.exit() when it finishes.
    # We catch it here so it doesn't kill your entire application.
    pass
finally:
    # Restore the original arguments
    sys.argv = original_argv

#check if .env exists and if it is filled
if not load_dotenv():
    open(".env", "w").close()
    load_dotenv(".env")

if not os.getenv("EMAIL"):
    email = input("Write email: ")
    set_key(".env", "EMAIL", email)

if not os.getenv("PASSWORD"):
    password = input("Write password: ")
    set_key(".env", "PASSWORD", password)

keyboard = Controller()
playwright = sync_playwright().start()
browser = playwright.chromium.launch(headless=False, args=["--ozone-platform=x11"])
page = browser.new_page()

#login
page.goto("https://sberbank.solocorporate.com/co/sberbank")
page.locator("#form-email-email").first.fill(os.getenv("EMAIL"))
page.locator("#form-password-password").first.fill(os.getenv("PASSWORD"))
page.locator("#form-button-login").click()
page.wait_for_load_state("networkidle")

#go to tasks
page.get_by_text("Продолжить обучение").click()
page.wait_for_load_state("networkidle")


while True:
    # check if tasks are done and to go to the next page
    if page.locator('i.fa-thumb-tack:visible').count() == 0:
        number = 0
        index = 0
        url = page.url
        parts = url.split("/")
        for part in parts:
            if part.isdigit():
                number = int(part)
                index = parts.index(part)
        parts.pop(index)
        parts.insert(index, str(number+1))
        url = "/".join(parts)
        page.goto(url)

    #start doing task
    page.locator('button:has-text("Выполнить задание"):enabled').last.click()
    page.wait_for_timeout(1000)

    soup = BeautifulSoup(page.content(), 'html.parser')
    container = soup.find("div", {"class": "text-prompt-value"})
    texts = container.find_all("p")

    symbols = []
    for p_tag in texts:
        if p_tag.sup:
            p_tag.sup.decompose()
        clean_text = p_tag.get_text().replace('\xa0', ' ')
        symbols.extend(list(clean_text))

    print(f"Total characters to type: {len(symbols)}")
    print("WARNING: Switch your keyboard layout to RUSSIAN (RU) now!")
    print("Typing starts in 5 seconds...")
    time.sleep(5)

    print(symbols)

    for symbol in symbols:
        if symbol == ' ':
            keyboard.press(Key.space)
            time.sleep(0.07)
            keyboard.release(Key.space)
            time.sleep(0.08)
            continue

        char = symbol.lower()

        try:
            if symbol.isupper():
                with keyboard.pressed(Key.shift):
                    keyboard.press(char)
                    time.sleep(0.07)
                    keyboard.release(char)
                    print("Inputted " + symbol)
            else:
                keyboard.press(char)
                time.sleep(0.05)
                keyboard.release(char)
                print("Inputted " + symbol)

            time.sleep((random() + 0.1) % 0.3) #time between inputs

        except Exception as e:
            print(f"Не удалось нажать символ '{symbol}': {e}")

    time.sleep(2)
    page.get_by_role("button", name="Продолжить").click()
    time.sleep(2)


browser.close()
playwright.stop()
