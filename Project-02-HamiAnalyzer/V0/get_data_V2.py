from matplotlib import text
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re
import os
import time
import uuid
import sys
import jdatetime

def extract_info(text):
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

def save_docs(i, j, skips, start_date=None, end_date=None, start_message_number=-1, driver=None, wait=None, OUTPUT_DIR=None):
    time.sleep(5)
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
            
        print(row_date_jdt)
        time.sleep(10)
        j += 1
        cell = row.find_element(By.XPATH, ".//td[contains(@class, 'mat-column-sender')]")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", cell)
        driver.execute_script("arguments[0].click();", cell)
        time.sleep(2)
        
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

        time.sleep(1)
        button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//app-font-icon[@name='close']/parent::button")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", button)
        driver.execute_script("arguments[0].click();", button)

        time.sleep(2)
        more_vert = row.find_element(By.CSS_SELECTOR, "app-font-icon[name='more_vert']")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", more_vert)
        driver.execute_script("arguments[0].click();", more_vert)
        time.sleep(2)

        workflow_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'گردش کار')]/ancestor::button[@mat-menu-item]")))
        driver.execute_script("arguments[0].click();", workflow_button)
        time.sleep(8)

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
                date, personal, email = extract_info(node["text"])
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
        time.sleep(2)

    return j, skips

def main(LOGIN_URL, 
         USERNAME, 
         PASSWORD, 
         START_DATE, 
         END_DATE, 
         OUTPUT_DIR, 
         CHROMEPATH,
         i_value, 
         name_value, 
         START_MESSAGE_NUMBER=-1):
    start = time.time()  # Get current time
    # ---------- Setup ----------
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--incognito")  # optional
    options.add_argument("--force-device-scale-factor=0.60")  # UI scale to ~60%

    # service = Service(ChromeDriverManager().install())
    CHROMEDRIVER_PATH = CHROMEPATH
    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service)


    wait = WebDriverWait(driver, 20)

    # ---------- Configuration ----------
    LOGIN_URL = LOGIN_URL
    USERNAME = USERNAME
    PASSWORD = PASSWORD
    START_DATE = jdatetime.datetime.strptime(START_DATE, "%Y/%m/%d")
    END_DATE = jdatetime.datetime.strptime(END_DATE, "%Y/%m/%d")
    START_MESSAGE_NUMBER = START_MESSAGE_NUMBER
    sleep_time = 4
    OUTPUT_DIR = OUTPUT_DIR
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # ---------- Step 1: Login ----------
    driver.get(LOGIN_URL)
    time.sleep(8)

    # Replace these selectors with the actual ones on your login page
    wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(USERNAME)
    driver.find_element(By.ID, "password").send_keys(PASSWORD)
    driver.find_element(By.NAME, "_eventId").click()
    time.sleep(10)

    driver.find_element(By.ID, "consultantApplicationButton").click()
    time.sleep(30)

    supporters_btn = wait.until(EC.element_to_be_clickable((
        By.XPATH,
        "//a[contains(@class,'tree-item')][.//span[contains(@class,'tree-item__name') and normalize-space()='حامیان']]"
    )))
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", supporters_btn)
    driver.execute_script("arguments[0].click();", supporters_btn)
    time.sleep(2)

    rows = driver.find_elements(By.XPATH, "//td[contains(@class, 'mat-column-action')]/ancestor::tr")
    # Step 1: Get all rows (just identifiers, not WebElements)
    rows_info = []
    rows = driver.find_elements(By.XPATH, "//td[contains(@class, 'mat-column-action')]/ancestor::tr")
    for idx, row in enumerate(rows):
        sender = row.find_element(By.XPATH, ".//td[contains(@class, 'mat-column-sender')]").text
        date = row.find_element(By.XPATH, ".//td[contains(@class, 'mat-column-date')]").text
        rows_info.append({"sender": sender, "date": date, "index": idx + 1})

    # Select row by exact text in the first (sender) column instead of by index

    if not name_value:
        raise ValueError("Set NAME_VALUE environment variable to the exact text of the first column.")

    def _norm(s: str) -> str:
        return " ".join(s.split())

    _target = None
    for r in rows:
        try:
            sender_txt = r.find_element(By.XPATH, ".//td[contains(@class,'mat-column-sender')]//span").text
            if _norm(sender_txt) == _norm(name_value):
                _target = r
                break
        except Exception:
            continue

    if _target is None:
        raise RuntimeError(f"No row found with first column equal to: {name_value}")

    row = _target

    # Click the “move_to_inbox” button in this row
    button = row.find_element(By.XPATH, ".//app-font-icon[@name='move_to_inbox']")
    driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", button)
    driver.execute_script("arguments[0].click();", button)
    time.sleep(5)

    # Click the “همه” toggle
    button_all = driver.find_element(By.XPATH, "//button[@class='mat-button-toggle-button mat-focus-indicator' and .//span[text()='همه']]")
    driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", button_all)
    driver.execute_script("arguments[0].click();", button_all)
    time.sleep(5)

    j = 0
    skips = 0
    j, skips = save_docs(i=i_value, 
                         j=j, 
                         skips=skips, 
                         start_date=START_DATE, 
                         end_date=END_DATE, 
                         start_message_number=START_MESSAGE_NUMBER,
                         driver=driver,
                         wait=wait,
                         OUTPUT_DIR=OUTPUT_DIR)
    # logger.info(f"Processing i={i_value} | {j-skips} documents saved")

    while True:
        next_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "button.mat-mdc-paginator-navigation-next")))
        is_disabled = next_button.get_attribute("aria-disabled") == "true"
        if not is_disabled:
            driver.execute_script("arguments[0].click();", next_button)
            time.sleep(9)
            j, skips = save_docs(i=i_value, 
                                 j=j, 
                                 skips=skips, 
                                 start_date=START_DATE, 
                                 end_date=END_DATE, 
                                 start_message_number=START_MESSAGE_NUMBER,
                                 driver=driver,
                                 wait=wait,
                                 OUTPUT_DIR=OUTPUT_DIR)
        else:
            break
    end = time.time()
    duration = end - start
    
# main(LOGIN_URL= "https://mail.iau.ac.ir",
#      USERNAME= "Manager105001@iau.ir",
#      PASSWORD= "@Hamiyazd110",
#      START_DATE= "1402/01/01",
#      END_DATE= "1404/12/29",
#      OUTPUT_DIR= "/mnt/Data1/Python_Projects/Datasets/Hami_Data/hami_data/",
#      i_value= 105001,
#      name_value= "حامی 001 واحد یزد",
#      CHROMEPATH="/home/keivan/drivers/chromedriver/chromedriver",
# )