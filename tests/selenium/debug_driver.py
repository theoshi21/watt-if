"""Minimal debug script to test Chrome headless connectivity."""
import sys
import time

print("Starting debug script...", flush=True)

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

print("Imports OK", flush=True)

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-software-rasterizer")
chrome_options.add_argument("--remote-debugging-port=0")

print("Options set, creating service...", flush=True)

try:
    service = Service(ChromeDriverManager().install())
    print(f"Service created: {service.path}", flush=True)
    
    print("Creating Chrome driver...", flush=True)
    browser = webdriver.Chrome(service=service, options=chrome_options)
    print("Driver created!", flush=True)
    
    print("Navigating to localhost:5173...", flush=True)
    browser.set_page_load_timeout(15)
    browser.get("http://localhost:5173")
    print(f"Page title: {browser.title}", flush=True)
    print(f"Current URL: {browser.current_url}", flush=True)
    
    browser.quit()
    print("SUCCESS - driver works correctly!", flush=True)
    
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}", flush=True)
    sys.exit(1)
