import re
import os
import sys
import time
import uuid
import jdatetime
from pathlib import Path
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

SUPPORTER_PATH = "/nui/supporter"
# Data rows carry the `element-row` class; every other `tr[mat-row]` is an empty
# expansion-detail row that must be ignored.
ROW_XPATH = "//tr[@mat-row and contains(@class,'element-row')]"
# Popup fields are laid out as `<div><span class="label">…</span></div>` next to their control.
POPUP_FIELD_XPATH = (
    "//div[contains(@class,'cdk-overlay-pane')]"
    "//div[div/span[contains(@class,'label') and normalize-space()='{label}']]"
)
# `mat-select` keeps no text itself; the rendered value lives in this span.
SELECT_VALUE_XPATH = "//span[contains(@class,'select-selected-text')]"
POPUP_CLOSE_CSS = "div.cdk-overlay-pane button.modal-close"
EDITOR_IFRAME_CSS = "iframe.tox-edit-area__iframe"


class HamiScraper:
    def __init__(self,
                 LOGIN_URL: str,
                 USERNAME: str,
                 PASSWORD: str,
                 START_DATE: str,
                 END_DATE: str,
                 OUTPUT_DIR: str,
                 CHROMEPATH: str,
                 i_value: int,
                 name_value: str,
                 short_sleep_time: int = 2,
                 long_sleep_time: int = 5,
                 too_long_sleep_time: int = 10,
                 file_load_sleep: int = 3,
                 workflow_load_sleep: int = 5,
                 page_load_sleep: int = 5,
                 outdate_tolerance: int = 3,
                 progress_callback = None): 
        self.LOGIN_URL = LOGIN_URL
        self.USERNAME = USERNAME
        self.PASSWORD = PASSWORD
        self.START_DATE = jdatetime.datetime.strptime(START_DATE, "%Y/%m/%d")
        self.END_DATE = jdatetime.datetime.strptime(END_DATE, "%Y/%m/%d")
        self.OUTPUT_DIR = Path(OUTPUT_DIR)
        self.CHROMEPATH = CHROMEPATH
        self.i_value = i_value
        self.name_value = name_value
        self.short_sleep_time = short_sleep_time
        self.long_sleep_time = long_sleep_time
        self.too_long_sleep_time = too_long_sleep_time
        self.file_load_sleep = file_load_sleep
        self.workflow_load_sleep = workflow_load_sleep
        self.page_load_sleep = page_load_sleep
        self.outdate_tolerance = outdate_tolerance
        self.progress_callback = progress_callback
        self.driver = None
        self.wait = None
        self.START_MESSAGE_NUMBER = -1
        self.current_page = 1
        self.outdate_counter = 0  # Counter for consecutive out-of-date messages
    
    def report_progress(self, message_type, details=None):
        """Report progress to the callback if available"""
        if self.progress_callback:
            self.progress_callback(message_type, details or {})


    def clear_folder_and_create_it(self, folder_path: Path):
        if folder_path.exists():
            for file in folder_path.iterdir():
                if file.is_file():
                    file.unlink()
        else:
            os.makedirs(folder_path, exist_ok=True)

    def setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--incognito")
        chrome_options.add_argument("--force-device-scale-factor=0.60")
        # Add options for better stability
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        service = Service(executable_path=str(self.CHROMEPATH))
        driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver = driver
        # Increase wait timeout for slower connections
        self.wait = WebDriverWait(self.driver, 30)
        # Set page load timeout
        self.driver.set_page_load_timeout(60)
    

    def login(self):
        self.driver.get(self.LOGIN_URL)
        
        # Wait for login form to load
        username_input = self.wait.until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        password_input = self.wait.until(
            EC.presence_of_element_located((By.ID, "password"))
        )
        login_button = self.wait.until(
            EC.element_to_be_clickable((By.NAME, "_eventId"))
        )

        username_input.send_keys(self.USERNAME)
        password_input.send_keys(self.PASSWORD)
        time.sleep(2)
        login_button.click()
        
        # Wait for page to change after login (wait for URL change or specific element)
        time.sleep(20)  # Small buffer for redirect
        
    def open_supporter_app(self):
        # The app icon was renamed from `consultantApplicationButton` to `supporterApplicationButton`.
        for locator in ((By.ID, "supporterApplicationButton"), (By.ID, "consultantApplicationButton")):
            elements = self.driver.find_elements(*locator)
            if elements:
                self.driver.execute_script("arguments[0].click();", elements[0])
                break
        else:
            self.driver.get(self.LOGIN_URL.rstrip("/") + SUPPORTER_PATH)
        time.sleep(self.too_long_sleep_time)

    def click_tree_item(self, name: str):
        item = self.wait.until(EC.presence_of_element_located((
            By.XPATH,
            "//div[contains(@class,'tree-item')]"
            f"[.//span[contains(@class,'tree-item__name') and normalize-space()='{name}']]"
        )))
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", item)
        time.sleep(self.short_sleep_time)
        self.driver.execute_script("arguments[0].click();", item)
        time.sleep(self.long_sleep_time)

    def select_all_period_toggle(self):
        # "همه" is pre-selected by default now, so only click it when it is not checked.
        toggles = self.driver.find_elements(
            By.XPATH,
            "//mat-button-toggle[not(contains(@class,'mat-button-toggle-checked'))]"
            "//button[contains(@class,'mat-button-toggle-button')][.//span[normalize-space()='همه']]"
        )
        if toggles:
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", toggles[0])
            self.driver.execute_script("arguments[0].click();", toggles[0])
            time.sleep(self.too_long_sleep_time + 10)

    def main_process(self):
        self.open_supporter_app()
        self.click_tree_item("حامیان")

        def _norm(s: str) -> str:
            return " ".join(s.split())

        # Find the requested hami row. The name column is now `mat-column-supporter`.
        row = None
        for r in self.driver.find_elements(By.XPATH, ROW_XPATH):
            supporter_txt = r.find_element(By.XPATH, ".//td[contains(@class,'mat-column-supporter')]//span").text
            if _norm(supporter_txt) == _norm(self.name_value):
                row = r
                break
        if row is None:
            raise RuntimeError(f"Hami '{self.name_value}' was not found in the supporters table")

        # Go into one of the hami page.
        button = row.find_element(By.XPATH, ".//app-font-icon[@name='move_to_inbox']")
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", button)
        self.driver.execute_script("arguments[0].click();", button)
        time.sleep(self.long_sleep_time)

        self.click_tree_item("درخواست‌های دریافتی")
        self.select_all_period_toggle()

        j = 0
        skips = 0
        j, skips, should_stop = self.save_docs(i=self.i_value, 
                            j=j, 
                            skips=skips, 
                            start_date=self.START_DATE, 
                            end_date=self.END_DATE, 
                            start_message_number=self.START_MESSAGE_NUMBER,
                            driver=self.driver,
                            wait=self.wait,
                            OUTPUT_DIR=self.OUTPUT_DIR)
        
        # If outdate tolerance reached, stop completely
        if should_stop:
            return
        # logger.info(f"Processing i={i_value} | {j-skips} documents saved")

        while True:
            # Wait for next button to be present
            next_button = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "button.mat-mdc-paginator-navigation-next"))
            )
            is_disabled = next_button.get_attribute("aria-disabled") == "true"
            if not is_disabled:
                self.current_page += 1
                self.report_progress("page_change", {"page": self.current_page})
                self.driver.execute_script("arguments[0].click();", next_button)
                # Wait for new page to load with configurable wait time
                time.sleep(self.page_load_sleep)
                # Wait for rows to appear
                self.wait.until(
                    EC.presence_of_element_located((By.XPATH, ROW_XPATH))
                )
                time.sleep(1)  # Extra buffer
                j, skips, should_stop = self.save_docs(i=self.i_value, 
                                    j=j, 
                                    skips=skips, 
                                    start_date=self.START_DATE, 
                                    end_date=self.END_DATE, 
                                    start_message_number=self.START_MESSAGE_NUMBER,
                                    driver=self.driver,
                                    wait=self.wait,
                                    OUTPUT_DIR=self.OUTPUT_DIR)
                
                # If outdate tolerance reached, stop completely
                if should_stop:
                    return
            else:
                break
            
    def save_docs(self, i, j, skips, start_date=None, end_date=None, start_message_number=-1, driver=None, wait=None, OUTPUT_DIR=None):
        # Wait for rows to be present
        wait.until(EC.presence_of_element_located((By.XPATH, ROW_XPATH)))
        time.sleep(1)  # Small buffer for rendering
        
        # Get the number of rows first
        popup_rows = driver.find_elements(By.XPATH, ROW_XPATH)
        num_rows = len(popup_rows)
        
        # Use index-based iteration to avoid stale element references
        row_index = 0
        while row_index < num_rows:
            # Re-fetch rows each iteration to avoid stale element references
            time.sleep(0.5)  # Small buffer before re-fetching
            popup_rows = driver.find_elements(By.XPATH, ROW_XPATH)
            if row_index >= len(popup_rows):
                break
            row = popup_rows[row_index]
            
            # Extract date text from the row and convert to jdatetime
            try:
                date_el = row.find_element(
                    By.XPATH,
                    ".//td[contains(@class,'mat-column-date')]//*[contains(@class,'local-numbers')]"
                    " | .//td[contains(@class,'mat-column-date')]"
                )
                raw_date = date_el.text.strip()

                # Get the status text
                status_el = row.find_element(
                    By.XPATH,
                    ".//td[contains(@class,'mat-column-status')]//span"
                )
                status_text = status_el.text.strip()

                # Normalize Persian digits to ASCII
                trans = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
                normalized = raw_date.translate(trans)

                # Expected format: YY/MM/DD-HH:MM or YYYY/MM/DD-HH:MM
                ymd, hm = normalized.split('-', 1)
                yy_str, mm_str, dd_str = ymd.split('/')
                hh_str, mi_str = hm.split(':')

                yy = int(yy_str)
                year = yy + 1400 if yy < 100 else yy  # map 04 -> 1404
                month = int(mm_str)
                day = int(dd_str)
                hour = int(hh_str)
                minute = int(mi_str)

                row_date_jdt = jdatetime.datetime(year, month, day, hour, minute)
            except Exception:
                row_date_jdt = None
                status_text = None

            # Skip if status is not "بسته شده"
            if status_text != "بسته شده":
                skips += 1
                self.report_progress("skipped", {"status": status_text or "unknown"})
                row_index += 1
                continue

            if row_date_jdt > end_date:
                skips += 1
                row_index += 1
                continue
            elif row_date_jdt < end_date and row_date_jdt > start_date:
                # In-date message found - reset the outdate counter
                self.outdate_counter = 0
                pass
            elif row_date_jdt < start_date:
                # Out-of-date message - increment counter
                self.outdate_counter += 1
                self.report_progress("outdate_warning", {
                    "count": self.outdate_counter, 
                    "tolerance": self.outdate_tolerance,
                    "date": row_date_jdt.strftime("%Y/%m/%d")
                })
                
                # Check if we've exceeded tolerance
                if self.outdate_counter >= self.outdate_tolerance:
                    self.report_progress("outdate_stop", {"count": self.outdate_tolerance})
                    return j, skips, True  # Return True to signal complete stop
                
                # Otherwise, skip this message but continue checking
                skips += 1
                row_index += 1
                continue
                
            j += 1
            
            # Re-fetch the row right before clicking to ensure fresh reference
            popup_rows = driver.find_elements(By.XPATH, ROW_XPATH)
            row = popup_rows[row_index]
            cell = row.find_element(By.XPATH, ".//td[contains(@class, 'mat-column-sender')]")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", cell)
            time.sleep(0.5)  # Wait for scroll
            driver.execute_script("arguments[0].click();", cell)
            time.sleep(1)  # Wait for popup to start loading
            
            # Wait for popup form to load completely
            input_element = wait.until(EC.presence_of_element_located(
                (By.XPATH, POPUP_FIELD_XPATH.format(label="موضوع") + "//input")
            ))
            input_value = input_element.get_attribute("value")

            reference_code = wait.until(EC.presence_of_element_located(
                (By.XPATH, POPUP_FIELD_XPATH.format(label="کد پیگیری") + "//input")
            )).get_attribute("value")

            # "رشته محل" is a mat-select now, so its value has to be read as text.
            major = wait.until(EC.presence_of_element_located(
                (By.XPATH, POPUP_FIELD_XPATH.format(label="رشته محل") + SELECT_VALUE_XPATH)
            )).text.strip()

            pattern = re.compile(rf"^file_{i}_(\d+)\.txt$")
            indices = []
            for name in os.listdir(OUTPUT_DIR):
                m = pattern.match(name)
                if m:
                    indices.append(int(m.group(1)))
            next_index = (max(indices) + 1) if indices else 1
            file_path = os.path.join(OUTPUT_DIR, f"file_{i}_{next_index}.txt")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"Subject : {input_value}\nCode: {reference_code}\nMajor: {major}\n\n\n")

            # Get TinyMCE content
            iframe = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, EDITOR_IFRAME_CSS)))
            driver.switch_to.frame(iframe)
            # Wait for tinymce body to be present with configurable wait time
            time.sleep(self.file_load_sleep)
            tinymce_body = wait.until(EC.presence_of_element_located((By.ID, "tinymce")))
            popup_text = tinymce_body.text
            
            # Check if content is empty and report
            if not popup_text or popup_text.strip() == "":
                self.report_progress("file_empty", {"index": next_index, "subject": input_value})
            
            # Save to file
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(popup_text)
            driver.switch_to.default_content()
            
            # Report file saved
            self.report_progress("file_saved", {"index": next_index, "subject": input_value})

            # Close the message popup - wait for close button to be clickable
            time.sleep(0.5)
            close_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, POPUP_CLOSE_CSS)))
            driver.execute_script("arguments[0].click();", close_btn)
            time.sleep(1.0)  # Wait for popup to close completely

            # Re-fetch the row to get fresh reference for more_vert menu
            popup_rows = driver.find_elements(By.XPATH, ROW_XPATH)
            row = popup_rows[row_index]
            
            # Open workflow menu - find more_vert icon on the SPECIFIC row
            more_vert = row.find_element(By.XPATH, ".//app-font-icon[@name='more_vert']")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", more_vert)
            time.sleep(0.3)
            driver.execute_script("arguments[0].click();", more_vert)
            time.sleep(0.5)  # Wait for menu to appear
            
            # Wait for menu to appear and click workflow - use fresh lookup
            workflow_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'گردش کار')]/ancestor::button[@mat-menu-item]")))
            driver.execute_script("arguments[0].click();", workflow_button)
            
            # Wait for workflow popup to appear
            time.sleep(1)  # Wait for overlay to appear
            
            # Wait for workflow tree to fully load with configurable wait time
            time.sleep(self.workflow_load_sleep)
            
            # Get fresh reference to the overlay pane and extract HTML immediately
            overlay_panes = driver.find_elements(By.CSS_SELECTOR, "div.cdk-overlay-pane")
            if overlay_panes:
                # Get the last overlay pane (the topmost one)
                popup = overlay_panes[-1]
                html = popup.get_attribute("innerHTML")
            else:
                html = ""
            
            soup = BeautifulSoup(html, 'html.parser')

            # locate the main tree container
            tree_container = soup.find("mat-tree")
            if not tree_container:
                self.report_progress("workflow_empty", {"index": next_index})
                workflow_nodes = []
            else:
                # recursively extract nodes starting from this container
                def extract_node(node):
                    box_id = str(uuid.uuid4())
                    box_text = node.get_text(separator="\n", strip=True)

                    children = []
                    # get all groups directly under this node
                    for group in node.find_all("div", role="group", recursive=False):
                        # get all tree nodes inside the group (nested or simple)
                        for child in group.find_all(["mat-tree-node", "mat-nested-tree-node"], recursive=False):
                            children.append(extract_node(child))

                    return {
                        "id": box_id,
                        "text": box_text,
                        "children": children
                    }

                # top-level nodes inside this tree container
                top_nodes = tree_container.find_all("mat-nested-tree-node", recursive=False)
                workflow_nodes = [extract_node(node) for node in top_nodes]
                
                def write_workflow_node(f, node, parent_id=None):
                    date, personal, email = self.extract_info(node["text"])
                    f.write(f"parent_id: {parent_id}\n")
                    f.write(f"id: {node['id']}\n")
                    f.write(f"date: {date}\n") 
                    f.write(f"name: {personal}\n")
                    f.write(f"email: {email}\n")
                    f.write("-" * 50 + "\n")
                    
                    for child in node["children"]:
                        write_workflow_node(f, child, node["id"])

                workflow_file = os.path.join(OUTPUT_DIR, f"workflow_{i}_{next_index}.txt")
                with open(workflow_file, "w", encoding="utf-8") as f:
                    for node in workflow_nodes:
                        write_workflow_node(f, node)
                
                # Report workflow saved
                self.report_progress("workflow_saved", {"index": next_index})

            # Close workflow popup - use fresh element lookup
            time.sleep(0.3)
            close_buttons = driver.find_elements(By.XPATH, "//app-font-icon[@name='close']/parent::button")
            if close_buttons:
                close_btn = close_buttons[-1]  # Get the last (topmost) close button
                driver.execute_script("arguments[0].click();", close_btn)
            time.sleep(0.8)  # Wait for popup to close completely
            
            # Move to next row
            row_index += 1

        return j, skips, False  # Return False to indicate normal completion

    def extract_info(self, text):
        # Extract date (Persian date format)
        date_match = re.search(r'[\u0600-\u06FF]+، \d{1,2} [\u0600-\u06FF]+ \d{4} \d{2}:\d{2}', text)
        date = date_match.group(0) if date_match else None

        # Extract email
        email_match = re.search(r'[\w\.-]+@[\w\.-]+', text)
        email = email_match.group(0) if email_match else None

        # Extract name: the line immediately after the date
        name = None
        if date:
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if date in line:
                    # Name is the next non-empty line after date
                    for next_line in lines[i+1:]:
                        next_line = next_line.strip()
                        if next_line and not re.match(r'[\w\.-]+@[\w\.-]+', next_line):
                            name = next_line
                            break
                    break

        return date, name, email
    
    
if __name__ == "__main__":
    scraper = HamiScraper(
        LOGIN_URL="https://mail.iau.ac.ir",
        USERNAME="Manager105001@iau.ir",
        PASSWORD="@Hamiyazd110",
        START_DATE="1404/07/01",
        END_DATE="1404/08/01",
        OUTPUT_DIR="./output",
        CHROMEPATH="/home/keivan/drivers/chromedriver/chromedriver",
        i_value=105001,
        name_value="حامی 001 واحد یزد"
    )
    scraper.setup_driver()
    scraper.login()
    scraper.main_process()
    scraper.driver.quit()