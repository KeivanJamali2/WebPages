import re
import os
import sys
import time
import uuid
import jdatetime
from pathlib import Path
from matplotlib import text
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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
                 too_long_sleep_time: int = 10): 
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
        self.driver = None


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
        service = Service(executable_path=str(self.CHROMEPATH))
        driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver = driver
    

    def login(self):
        self.driver.get(self.LOGIN_URL)
        time.sleep(self.too_long_sleep_time)

        username_input = self.driver.find_element(By.ID, "username")
        password_input = self.driver.find_element(By.ID, "password")
        login_button = self.driver.find_element(By.NAME, "_eventId")

        username_input.send_keys(self.USERNAME)
        password_input.send_keys(self.PASSWORD)
        login_button.click()
        time.sleep(self.long_sleep_time)
        
    def main_process(self):
        self.driver.find_element(By.ID, "consultantApplicationButton").click()
        time.sleep(self.too_long_sleep_time)

        supporters_btn = self.driver.find_element(By.XPATH, "//a[contains(@class,'tree-item')][.//span[contains(@class,'tree-item__name') and normalize-space()='حامیان']]")
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", supporters_btn)
        time.sleep(self.long_sleep_time)
        
        self.driver.execute_script("arguments[0].click();", supporters_btn)
        time.sleep(self.long_sleep_time)

        rows = self.driver.find_elements(By.XPATH, "//td[contains(@class, 'mat-column-action')]/ancestor::tr")
        
        # Find all rows info in the hami page.
        rows_info = []
        rows = self.driver.find_elements(By.XPATH, "//td[contains(@class, 'mat-column-action')]/ancestor::tr")
        for idx, row in enumerate(rows):
            sender = row.find_element(By.XPATH, ".//td[contains(@class, 'mat-column-sender')]").text
            date = row.find_element(By.XPATH, ".//td[contains(@class, 'mat-column-date')]").text
            rows_info.append({"sender": sender, "date": date, "index": idx + 1})

        def _norm(s: str) -> str:
            return " ".join(s.split())
        _target = None
        for r in rows:
            sender_txt = r.find_element(By.XPATH, ".//td[contains(@class,'mat-column-sender')]//span").text
            if _norm(sender_txt) == _norm(self.name_value):
                _target = r
                break       
        row = _target
        
        # Go into one of the hami page.
        button = row.find_element(By.XPATH, ".//app-font-icon[@name='move_to_inbox']")
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", button)
        self.driver.execute_script("arguments[0].click();", button)
        time.sleep(self.long_sleep_time)
        
        # Click the “همه” toggle
        button_all = self.driver.find_element(By.XPATH, "//button[@class='mat-button-toggle-button mat-focus-indicator' and .//span[text()='همه']]")
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", button_all)
        self.driver.execute_script("arguments[0].click();", button_all)
        time.sleep(self.too_long_sleep_time+10)
            
        j = 0
        skips = 0
        j, skips = self.save_docs(i=self.i_value, 
                            j=j, 
                            skips=skips, 
                            start_date=self.START_DATE, 
                            end_date=self.END_DATE, 
                            start_message_number=self.START_MESSAGE_NUMBER,
                            driver=self.driver,
                            wait=self.wait,
                            OUTPUT_DIR=self.OUTPUT_DIR)
        # logger.info(f"Processing i={i_value} | {j-skips} documents saved")

        while True:
            next_button = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "button.mat-mdc-paginator-navigation-next")))
            is_disabled = next_button.get_attribute("aria-disabled") == "true"
            if not is_disabled:
                self.driver.execute_script("arguments[0].click();", next_button)
                time.sleep(self.too_long_sleep_time)
                j, skips = self.save_docs(i=self.i_value, 
                                    j=j, 
                                    skips=skips, 
                                    start_date=self.START_DATE, 
                                    end_date=self.END_DATE, 
                                    start_message_number=self.START_MESSAGE_NUMBER,
                                    driver=self.driver,
                                    wait=self.wait,
                                    OUTPUT_DIR=self.OUTPUT_DIR)
            else:
                break
            
    def save_docs(self, i, j, skips, start_date=None, end_date=None, start_message_number=-1, driver=None, wait=None, OUTPUT_DIR=None):
        time.sleep(self.long_sleep_time)
        popup_rows = driver.find_elements(By.XPATH, "//tr[@mat-row]")
        for row in popup_rows:
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
                continue

            if row_date_jdt > end_date:
                skips += 1
                continue
            elif row_date_jdt < end_date and row_date_jdt > start_date:
                pass
            elif row_date_jdt < start_date:
                return j, skips
                
            time.sleep(self.long_sleep_time)
            j += 1
            cell = row.find_element(By.XPATH, ".//td[contains(@class, 'mat-column-sender')]")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", cell)
            driver.execute_script("arguments[0].click();", cell)
            time.sleep(self.short_sleep_time)
            
            input_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='موضوع']")))
            input_value = input_element.get_attribute("value")

            reference_code = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "input[readonly='true']")))
            reference_code = reference_code[1].get_attribute("value")

            major = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[readonly='true'].mat-mdc-input-element"))).get_attribute("value")

            type_select = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "mat-select")))

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
            iframe = wait.until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))
            driver.switch_to.frame(iframe)
            tinymce_body = driver.find_element(By.ID, "tinymce")
            popup_text = tinymce_body.text
            
            # Save to file
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(popup_text)
            driver.switch_to.default_content()

            time.sleep(self.short_sleep_time)
            button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//app-font-icon[@name='close']/parent::button")))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", button)
            driver.execute_script("arguments[0].click();", button)

            time.sleep(self.short_sleep_time)
            more_vert = row.find_element(By.CSS_SELECTOR, "app-font-icon[name='more_vert']")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", more_vert)
            driver.execute_script("arguments[0].click();", more_vert)
            time.sleep(self.short_sleep_time)
            workflow_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'گردش کار')]/ancestor::button[@mat-menu-item]")))
            driver.execute_script("arguments[0].click();", workflow_button)
            time.sleep(self.long_sleep_time)

            popup = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.cdk-overlay-pane")))

            # find all the details
            html = popup.get_attribute("innerHTML")
            soup = BeautifulSoup(html, 'html.parser')

            # locate the main tree container
            tree_container = soup.find("mat-tree")
            if not tree_container:
                print("No mat-tree found in popup!")
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


            close_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//app-font-icon[@name='close']/parent::button")))
            driver.execute_script("arguments[0].click();", close_button)
            time.sleep(self.short_sleep_time)

        return j, skips

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