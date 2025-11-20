from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

from APG.Headers import Headers


class HeadlessBrowser:

    def fetch_page_headless(self, url):
        content = None
        options = Options()
        # options.headless = True  # Runs Chrome in headless mode.
        options.add_argument("--headless=new")  # modern headless mode
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        user_agent = Headers.Headers().get_rand_header_modern()["User-Agent"]
        options.add_argument(f"user-agent={user_agent}")

        # Optional: reduce detection
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        # Optional stealth tweaks (minimize detection)
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                """
        })

        try:
            driver.get(url)
            time.sleep(3)  # Let JS load if needed
            content = driver.page_source
        finally:
            driver.quit()
            return content
