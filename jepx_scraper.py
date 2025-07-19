import os
import time
import pandas as pd
import requests
import warnings
import urllib3
from playwright.sync_api import sync_playwright

class JEPX:
    def __init__(self):
        self.base_url = "https://www.jepx.jp/"
        self.page = None
        self.browser = None
        self.playwright = None

    def _launch_browser(self, playwright, debug=False):
        browser = playwright.chromium.launch(
            headless=not debug,
            slow_mo=50 if debug else 0,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--start-maximized' if debug else '--disable-gpu',
            ]
        )
        return browser

    def _download_csv(self, dir_name: str, date: str, out_path: str):
        # Remove slashes
        date_str = date.replace("/", "")
        file_name = f"{dir_name}_{date_str}.csv"
        url = f"https://www.jepx.jp/js/csv_read.php?dir={dir_name}&file={file_name}"

        headers = {
            "Referer": self.page.url,  # Use the current loaded page as referer
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
            "Accept": "*/*",
        }

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        r = requests.get(url, headers=headers, verify=False)
        if r.ok and len(r.content) > 100:
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, "wb") as f:
                f.write(r.content)
            print(f"Downloaded: {out_path}")
        else:
            print(f"Failed to download CSV: {url}")

    def _navigate_spot_page(self, date: str, debug=False, accept_downloads=False, item: str = "spot"):
        """
        Navigate to the JEPX spot market page, set a specific date, and select 'All Areas'.

        Args:
            date (str): Date in "YYYY/MM/DD" format.
            debug (bool): If True, browser opens visibly.
            accept_downloads (bool): If True, allow browser downloads (for download operations).
        """
        from datetime import datetime

        dt = datetime.strptime(date, "%Y/%m/%d")
        year = dt.year
        month = dt.month - 1
        day = dt.day

        self.playwright = sync_playwright().start()
        self.browser = self._launch_browser(self.playwright, debug)
        context = self.browser.new_context(accept_downloads=accept_downloads)
        self.page = context.new_page()

        if item.lower() == "spot":
            self.page.goto(f"{self.base_url}electricpower/market-data/spot/")
            try:
                assert self.page.locator("span.active").inner_text() == "約定価格　入札・約定量"
                assert self.page.locator("label.filter-label.active").inner_text() == "30分コマ"
            except Exception as e:
                print(f"Warning: default spot page layout check failed: {e}")
        elif item.lower() in {"bid_curves", "virtualprice"}:
            self.page.goto(f"{self.base_url}electricpower/market-data/spot/{item}.html")
            print(f"Info: Skipping layout assertions for item: {item}")
        else:
            print(f"Warning: Unrecognized item '{item}', skipping default checks.")

        self.page.click("#button--calender-show")
        self.page.select_option(".ui-datepicker-year", str(year))
        self.page.select_option(".ui-datepicker-month", str(month))
        self.page.click(f"a.ui-state-default[data-date='{day}']")

        self.page.wait_for_timeout(8000)

        if item.lower() == "spot":
            try:
                label = self.page.locator("#checkbox-area--graph label[for='area_all']")
                label.click()
                print("Successfully clicked 'All Areas' checkbox")
            except Exception as e:
                print(f"Failed to click 'All Areas' checkbox: {e}")
        elif item.lower() == "bid_curves":
            pass
        else:
            print(f"Warning: Unrecognized item '{item}', skipping default checks.")


    def spot_table(self, date: str, debug=False):
        """
        Navigate to JEPX spot market page, set a specific date,
        select '全エリア', switch to 'テーブル' view, and extract tables.

        Args:
            date (str): Date in "YYYY/MM/DD" format.
            debug (bool): If True, browser opens visibly.

        Returns:
            (price_df, amount_df): Two pandas DataFrames
        """
        self._navigate_spot_page(date, debug, accept_downloads=False)

        try:
            self.page.locator("button[data-type='table']").click()
            self.page.wait_for_timeout(2000)
            print("Switched to 'Table' view")
        except Exception as e:
            print(f"Failed to switch to 'Table' view: {e}")

        # --- Extract price table
        try:
            table1_locator = self.page.locator("#spotGraph1-table table")
            table1_html = table1_locator.inner_html()
            price_df = pd.read_html(f"<table>{table1_html}</table>")[0]
            price_df["Date"] = date
            print(f"Extracted price table: {price_df.shape[0]} rows, {price_df.shape[1]} columns")
        except Exception as e:
            print(f"Failed to extract price table: {e}")
            price_df = None

        # --- Extract amount table
        try:
            table2_locator = self.page.locator("#spotGraph2-table table")
            table2_html = table2_locator.inner_html()
            amount_df = pd.read_html(f"<table>{table2_html}</table>")[0]
            amount_df["Date"] = date
            print(f"Extracted amount table: {amount_df.shape[0]} rows, {amount_df.shape[1]} columns")
        except Exception as e:
            print(f"Failed to extract amount table: {e}")
            amount_df = None

        return price_df, amount_df

    def spot_curve(self, date: str, debug=False):
        """
        Navigate to JEPX spot market page, set a specific date,
        select '全エリア', switch to 'テーブル' view, and extract tables.

        Args:
            date (str): Date in "YYYY/MM/DD" format.
            debug (bool): If True, browser opens visibly.

        Returns:
            (price_df, amount_df): Two pandas DataFrames
        """
        self._navigate_spot_page(date, debug, accept_downloads=False, item="bid_curves")
        try:
            year = date.split("/")[0]
            date_no_slash = date.replace("/", "")
            bid_path = os.path.join("csv", year, f"spot_bid_curves_{date_no_slash}.csv")
            split_path = os.path.join("csv", year, f"spot_splitting_areas_{date_no_slash}.csv")
            self._download_csv("spot_bid_curves", date, bid_path)
            self._download_csv("spot_splitting_areas", date, split_path)
            print("Extracted")
        except Exception as e:
            print(f"Failed to extract amount table: {e}")

    def open_session(self, debug=False):
        """
        Open browser session using Playwright and navigate to HJKS unit page.
        """
        self.playwright = sync_playwright().start()
        self.browser = self._launch_browser(self.playwright, debug=debug)
        context = self.browser.new_context()
        self.page = context.new_page()
        self.page.goto(self.base_url + "/electricpower/market-data/spot/", wait_until="networkidle")
        time.sleep(2)

    def close_session(self):
        """
        Properly close browser and Playwright instance.
        """
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

if __name__ == '__main__':

    from datetime import datetime, timedelta

    # # today_date = datetime.now().strftime("%Y/%m/%d")
    # # print(today_date)

    jepx = JEPX()
    jepx.spot_curve(date="2025/04/24", debug=True)
    jepx.close_session()

    print()
    # # jepx.batch_spot_curve(start_date_str="2025/05/26", end_date_str="2025/05/23", debug=False)

    # # # price_df, amount_df = jepx.spot_table(date="2024/04/25", debug=True)
    # jepx.spot_curve(date="2025/05/19", debug=False)
    # # # jepx.download_spot_summary_csv(date="2020/04/25", debug=True, save_dir="spot_summary")
    # # #
    # jepx.close_session()  # Clean up Playwright resources
