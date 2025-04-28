import os
import json
import time
import pandas as pd
from bs4 import BeautifulSoup
from datetime import timedelta
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
    
    def navigation_process(self, debug=False):
        """
        Automates the navigation process on the JEPX spot market page.
        This includes selecting default options, opening the date picker, 
        and selecting tomorrow's date.
        """
        self.playwright = sync_playwright().start()
        self.browser = self._launch_browser(self.playwright, debug)
        context = self.browser.new_context()
        self.page = context.new_page()

        # Open the target page
        self.page.goto(f"{self.base_url}electricpower/market-data/spot/")

        # Ensure "約定価格　入札・約定量" is selected (default option)
        assert self.page.locator("span.active").inner_text() == "約定価格　入札・約定量"

        # Ensure "30分コマ" is selected (default option)
        assert self.page.locator("label.filter-label.active").inner_text() == "30分コマ"

        # Open the date picker
        self.page.click("#button--calender-show")

        # Calculate tomorrow's date
        tomorrow = datetime.now() + timedelta(days=1)
        year = tomorrow.year
        month = tomorrow.month - 1  # Playwright uses zero-based months
        day = tomorrow.day

        # Select the year in the date picker
        self.page.select_option(".ui-datepicker-year", str(year))

        # Select the month in the date picker
        self.page.select_option(".ui-datepicker-month", str(month))

        # Click on tomorrow's date
        self.page.click(f"a.ui-state-default[data-date='{day}']")

        # Wait for the page to load or perform additional actions
        self.page.wait_for_timeout(2000)

        # Select the "全エリア" checkbox
        checkbox_graph_section = self.page.locator("#checkbox-area--graph")
        checkbox_graph_section.locator("#area_all").check()

        # Wait for the page to load or perform additional actions
        self.page.wait_for_timeout(2000)

        # Example: Perform additional actions, such as clicking the download button
        # self.page.click("button[data-dl='spot_summary']")

    def _generate_timestamp(self):
        """
        Generate a timestamp string in the format YYYYMMDD_HHMMSS.
        """
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def _save_downloaded_file(self, download, filename_prefix: str, save_dir: str = "csv"):
        """
        Save the downloaded file to the specified directory with a timestamped filename.

        :param download: Playwright Download object
        :param filename_prefix: filename prefix (e.g., 'unit', 'outages')
        :param save_dir: directory to save the file (default 'csv')
        """
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        timestamp = self._generate_timestamp()
        filename = f"{filename_prefix}_{timestamp}.csv"
        save_path = os.path.join(save_dir, filename)

        download.save_as(save_path)
        print(f"CSV file saved as: {save_path}")

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

    def _fetch_csrf_token(self, page_id):
        """
        Fetch CSRF token from a given page using Playwright request.
        """
        try:
            response = self.page.request.get(self.base_url + page_id)
            content = response.text()
            soup = BeautifulSoup(content, 'html.parser')
            csrf_token = soup.find('input', {'name': '_csrf'}).get('value')
            return csrf_token
        except Exception as e:
            print(f"Error fetching CSRF token: {e}")
            return None

    def _get_unit_status_data(self, from_date, area):
        """
        Request unit_status and follow-up unit_status_ajax using Playwright.
        """
        csrf_token = self._fetch_csrf_token("unit_status")
        if not csrf_token:
            return None

        # Step 1: Access unit_status page with parameters
        params = {
            'from': from_date,
            'to': '',
            'area': area,
            'format': '1',
            '_csrf': csrf_token
        }
        response = self.page.request.get(
            self.base_url + "unit_status",
            params=params,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        if response.status != 200:
            print(f"Failed to fetch unit_status: {response.status}")
            return None

        # Step 2: Request unit_status_ajax to get JSON data
        ajax_response = self.page.request.get(
            self.base_url + "unit_status_ajax",
            params={'_': int(time.time() * 1000)}
        )
        return ajax_response

    def _process_unit_status_data(self, response):
        """
        Process JSON response and return two DataFrames (operation and stop).
        """
        try:
            data = json.loads(response.text())
            if data.get('status') == 'success':
                df_opr = pd.DataFrame(data['startdtList'], columns=['Date'])
                df_opr.set_index('Date', inplace=True)
                for series in data['unitStatusSeriesList']:
                    df_opr[series['name']] = series['data']

                df_stop = pd.DataFrame(data['startdtList'], columns=['Date'])
                df_stop.set_index('Date', inplace=True)
                for series in data['unitStopStatusSeriesList']:
                    df_stop[series['name']] = series['data']

                return df_opr / 1000, df_stop / 1000  # Convert kW to MW
        except Exception as e:
            print(f"Error processing unit_status data: {e}")
        return None, None

    def get_unit_status(self, from_date, area):
        """
        Input date and area, return two DataFrames (operation and stop).
        """
        response = self._get_unit_status_data(from_date, area)
        if response:
            return self._process_unit_status_data(response)
        else:
            return None, None

    def download_unit_csv(self):
        """
        Download unit CSV by calling the generic download_csv method.
        """
        self.download_csv(page_name="unit", filename_prefix="unit")

    def download_outages_csv(self):
        """
        Download outages CSV by calling the generic download_csv method.
        """
        self.download_csv(page_name="outages", filename_prefix="outages")

    def download_csv(self, page_name: str, filename_prefix: str, save_dir: str = "csv"):
        """
        Download CSV from the specified page by simulating button click using Playwright.
        Save the file into the specified directory with a timestamped filename.
        """
        try:
            url = self.base_url + page_name
            self.page.goto(url, wait_until="networkidle")
            time.sleep(1)

            self.page.eval_on_selector("#csv", "el => el.value = 'csv'")

            with self.page.expect_download() as download_info:
                self.page.click("input[type='submit'][value='CSVダウンロード']")

            download = download_info.value

            self._save_downloaded_file(download, filename_prefix, save_dir)

        except Exception as e:
            print(f"Error downloading CSV from page {page_name}: {e}")

    def close_session(self):
        """
        Properly close browser and Playwright instance.
        """
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

if __name__ == '__main__':
    from datetime import datetime

    today_date = datetime.now().strftime("%Y/%m/%d")
    print(today_date)

    jepx = JEPX()
    # jepx.open_session(debug=True)
    jepx.navigation_process(debug=True)
    # jepx.open_session(debug=True)  # Open Playwright browser and page
    # df_oprt, df_stop = jepx.get_unit_status(today_date, '9')  # Fetch data for Kyushu (area 9)
    # jepx.download_outages_csv()
    # jepx.download_unit_csv()
    jepx.download_csv("unit", "unit")
    jepx.download_csv("outages", "outages")

    jepx.close_session()  # Clean up Playwright resources

