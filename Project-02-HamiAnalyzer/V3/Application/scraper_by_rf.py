import re
import os
import sys
import time
import uuid
import json
import jdatetime
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class HamiScraperByReferenceCode:
    """
    Scraper for extracting data from Hami application by searching reference codes.
    Similar structure to HamiScraper but searches by reference code instead of date range.
    """
    
    def __init__(self,
                 LOGIN_URL: str,
                 USERNAME: str,
                 PASSWORD: str,
                 OUTPUT_DIR: str,
                 CHROMEPATH: str,
                 REFERENCE_CODES: list,
                 i_value: int,
                 name_value: str,
                 short_sleep_time: int = 4,
                 long_sleep_time: int = 10,
                 too_long_sleep_time: int = 15,
                 file_load_sleep: int = 6,
                 workflow_load_sleep: int = 10,
                 search_wait_time: int = 10,
                 progress_callback=None):
        """
        Initialize the Reference Code Scraper.
        
        Args:
            LOGIN_URL: URL of the login page
            USERNAME: Username for login
            PASSWORD: Password for login
            OUTPUT_DIR: Directory where to save output files
            CHROMEPATH: Path to chromedriver executable
            REFERENCE_CODES: List of reference codes to search
            i_value: Identifier for this scraping session (used in file naming)
            name_value: Name of the supporter ("حامی XXX")
            short_sleep_time: Short wait time between actions (default 2s)
            long_sleep_time: Medium wait time for page loads (default 5s)
            too_long_sleep_time: Long wait time for major transitions (default 10s)
            file_load_sleep: Wait time for file content to load (default 3s)
            workflow_load_sleep: Wait time for workflow to load (default 5s)
            search_wait_time: Wait time after search completes (default 5s)
            progress_callback: Callback function for reporting progress
        """
        self.LOGIN_URL = LOGIN_URL
        self.USERNAME = USERNAME
        self.PASSWORD = PASSWORD
        self.OUTPUT_DIR = Path(OUTPUT_DIR)
        self.CHROMEPATH = CHROMEPATH
        self.REFERENCE_CODES = REFERENCE_CODES
        self.i_value = i_value
        self.name_value = name_value
        self.short_sleep_time = short_sleep_time
        self.long_sleep_time = long_sleep_time
        self.too_long_sleep_time = too_long_sleep_time
        self.file_load_sleep = file_load_sleep
        self.workflow_load_sleep = workflow_load_sleep
        self.search_wait_time = search_wait_time
        self.progress_callback = progress_callback
        self.driver = None
        self.wait = None
        self.processed_count = 0
        self.success_count = 0
        self.error_count = 0

    def report_progress(self, message_type, details=None):
        """Report progress to the callback if available"""
        if self.progress_callback:
            self.progress_callback(message_type, details or {})

    def clear_folder_and_create_it(self, folder_path: Path):
        """Clear existing folder or create new one"""
        if folder_path.exists():
            for file in folder_path.iterdir():
                if file.is_file():
                    file.unlink()
        else:
            os.makedirs(folder_path, exist_ok=True)

    def setup_driver(self):
        """Initialize the Chrome WebDriver with necessary options"""
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--incognito")
        chrome_options.add_argument("--force-device-scale-factor=0.60")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        service = Service(executable_path=str(self.CHROMEPATH))
        driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 30)
        self.driver.set_page_load_timeout(60)

    def login(self):
        """Login to the application"""
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
        time.sleep(self.long_sleep_time)
        login_button.click()
        
        # Wait for page to change after login
        time.sleep(self.too_long_sleep_time)
        self.report_progress("login_complete", {})

    def navigate_to_search(self):
        """
        Navigate to search page:
        1. Click on menu button (consultant)
        2. Click on "درخواست‌های دریافتی" (Received Requests)
        3. Click on "همه" toggle
        """
        # Step 1: Click on consultant/menu button
        try:
            consultant_btn = self.wait.until(
                EC.element_to_be_clickable((By.ID, "consultantApplicationButton"))
            )
            consultant_btn.click()
            time.sleep(self.too_long_sleep_time)
            self.report_progress("navigation", {"step": "clicked_menu"})
        except Exception as e:
            self.report_progress("navigation_error", {"step": "menu", "error": str(e)})
            raise

        # Step 2: Click on "درخواست‌های دریافتی" (Received Requests)
        try:
            received_requests_btn = self.driver.find_element(
                By.XPATH,
                "//div[contains(@class,'tree-item')][.//span[contains(@class,'tree-item__name') and normalize-space()='درخواست‌های دریافتی']]"
            )
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", received_requests_btn)
            time.sleep(self.short_sleep_time)
            self.driver.execute_script("arguments[0].click();", received_requests_btn)
            time.sleep(self.long_sleep_time)
            self.report_progress("navigation", {"step": "clicked_received_requests"})
        except Exception as e:
            self.report_progress("navigation_error", {"step": "received_requests", "error": str(e)})
            raise

        # Step 3: Click the "همه" toggle
        try:
            button_all = self.driver.find_element(
                By.XPATH,
                "//button[@class='mat-button-toggle-button mat-focus-indicator' and .//span[text()='همه']]"
            )
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", button_all)
            self.driver.execute_script("arguments[0].click();", button_all)
            time.sleep(self.too_long_sleep_time + 5)
            self.report_progress("navigation", {"step": "clicked_all_toggle"})
        except Exception as e:
            self.report_progress("navigation_error", {"step": "all_toggle", "error": str(e)})
            raise

    def search_reference_code(self, reference_code: str):
        """
        Search for a specific reference code by finding and filling the hidden form directly.
        The form elements exist in the DOM even before the menu button is clicked.
        """
        # IMPORTANT: Keep reference_code as STRING throughout - no conversions!
        reference_code = str(reference_code).strip()  # Ensure it's a string
        
        try:
            print(f"[DEBUG] Step 1: Finding search input field with label 'کد پیگیری'...")
            
            # Find ALL input elements that have 'کد پیگیری' label nearby
            all_inputs = self.driver.find_elements(By.TAG_NAME, "input")
            print(f"[DEBUG] Found {len(all_inputs)} input elements on page")
            
            search_input = None
            
            # Method 1: Find input by searching for the label and getting its 'for' attribute
            try:
                labels = self.driver.find_elements(By.XPATH, "//mat-label[contains(text(), 'کد پیگیری')]")
                print(f"[DEBUG] Found {len(labels)} labels with 'کد پیگیری'")
                
                if labels:
                    label = labels[0]
                    # Get parent form field
                    form_field = label.find_element(By.XPATH, "ancestor::mat-form-field")
                    # Find input inside this form field
                    search_input = form_field.find_element(By.TAG_NAME, "input")
                    print(f"[DEBUG] Found input via label ancestor: {search_input.get_attribute('id')}")
            except Exception as e:
                print(f"[DEBUG] Method 1 failed: {str(e)}")
            
            # Method 2: Try to find by looking at ALL form fields with inputs
            if not search_input:
                try:
                    form_fields = self.driver.find_elements(By.TAG_NAME, "mat-form-field")
                    print(f"[DEBUG] Found {len(form_fields)} mat-form-field elements")
                    
                    for idx, field in enumerate(form_fields):
                        try:
                            label_text = field.text
                            if 'کد پیگیری' in label_text:
                                search_input = field.find_element(By.TAG_NAME, "input")
                                print(f"[DEBUG] Found input in form field {idx}: {search_input.get_attribute('id')}")
                                break
                        except:
                            continue
                except Exception as e:
                    print(f"[DEBUG] Method 2 failed: {str(e)}")
            
            if not search_input:
                raise Exception("Could not find search input field")
            
            print(f"[DEBUG] Input ID: {search_input.get_attribute('id')}")
            print(f"[DEBUG] Input value: {search_input.get_attribute('value')}")
            
            # Step 2: Click and focus the input
            print(f"[DEBUG] Step 2: Clicking and focusing input...")
            search_input.click()
            time.sleep(0.3)
            
            # Step 3: Clear and enter reference code
            print(f"[DEBUG] Step 3: Entering reference code...")
            search_input.clear()
            time.sleep(0.2)
            search_input.send_keys(str(reference_code))
            time.sleep(0.5)
            
            input_value = search_input.get_attribute('value')
            print(f"[DEBUG] Input now contains: {input_value}")
            
            if input_value != str(reference_code):
                print(f"[DEBUG] WARNING: Value mismatch! Expected {reference_code}, got {input_value}")
            
            self.report_progress("search_step", {"step": "input_reference_code", "ref_code": reference_code})
            
            # Step 4: Find and click the search button (جستجو)
            print(f"[DEBUG] Step 4: Finding جستجو button...")
            
            search_btn = None
            buttons = self.driver.find_elements(By.XPATH, "//button")
            
            for idx, btn in enumerate(buttons):
                try:
                    btn_text = btn.text
                    if 'جستجو' in btn_text:
                        print(f"[DEBUG] Found جستجو button at index {idx}")
                        search_btn = btn
                        break
                    
                    # Also check spans inside button
                    spans = btn.find_elements(By.TAG_NAME, "span")
                    for span in spans:
                        if 'جستجو' in span.text:
                            print(f"[DEBUG] Found جستجو in span at button index {idx}")
                            search_btn = btn
                            break
                    
                    if search_btn:
                        break
                except:
                    continue
            
            if not search_btn:
                raise Exception("Could not find جستجو button")
            
            # Click the button
            print(f"[DEBUG] Clicking جستجو button...")
            try:
                search_btn.click()
            except:
                self.driver.execute_script("arguments[0].click();", search_btn)
            
            print(f"[DEBUG] Button clicked")
            time.sleep(self.search_wait_time)
            
            # Step 5: Verify results appeared
            print(f"[DEBUG] Step 5: Checking for results...")
            try:
                rows = self.driver.find_elements(By.XPATH, "//tr[@mat-row]")
                print(f"[DEBUG] Found {len(rows)} result rows")
                
                if len(rows) == 0:
                    print(f"[DEBUG] WARNING: No result rows found")
            except Exception as e:
                print(f"[DEBUG] Could not check rows: {str(e)}")
            
            print(f"[DEBUG] Search completed successfully!")
            self.report_progress("search_step", {"step": "executed_search", "ref_code": reference_code})
            
            return True
            
        except Exception as e:
            print(f"[DEBUG] ERROR in search_reference_code: {str(e)}")
            import traceback
            print(f"[DEBUG] Traceback: {traceback.format_exc()}")
            self.report_progress("search_error", {"ref_code": str(reference_code), "error": str(e)})
            return False

    def extract_single_result(self, reference_code: str):
        """
        Extract data from the single search result (same as save_docs logic but for one item).
        Returns True if successful, False otherwise.
        """
        try:
            # Wait for rows to appear
            self.wait.until(EC.presence_of_element_located((By.XPATH, "//tr[@mat-row]")))
            time.sleep(0.5)
            
            # Get rows
            rows = self.driver.find_elements(By.XPATH, "//tr[@mat-row]")
            
            if len(rows) == 0:
                self.report_progress("extract_error", {
                    "ref_code": reference_code,
                    "error": "No search results found"
                })
                self.error_count += 1
                return False
            elif len(rows) > 1:
                self.report_progress("extract_warning", {
                    "ref_code": reference_code,
                    "warning": f"Multiple results found ({len(rows)}), processing first one"
                })
            
            # Process first row
            row = rows[0]
            
            # Click on sender to open the message
            try:
                cell = row.find_element(By.XPATH, ".//td[contains(@class, 'mat-column-sender')]")
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", cell)
                time.sleep(0.5)
                self.driver.execute_script("arguments[0].click();", cell)
                time.sleep(1)
                self.report_progress("extract_step", {"ref_code": reference_code, "step": "clicked_result"})
            except Exception as e:
                self.report_progress("extract_error", {
                    "ref_code": reference_code,
                    "error": f"Failed to click result: {str(e)}"
                })
                self.error_count += 1
                return False

            # Wait for popup form to load
            try:
                input_element = self.wait.until(
                    EC.presence_of_element_located((By.XPATH, "//input[@placeholder='موضوع']"))
                )
                input_value = input_element.get_attribute("value")

                reference_code_elements = self.wait.until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "input[readonly='true']"))
                )
                reference_code_extracted = reference_code_elements[1].get_attribute("value") if len(reference_code_elements) > 1 else ""

                major = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[readonly='true'].mat-mdc-input-element"))
                ).get_attribute("value")

                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "mat-select")))
                self.report_progress("extract_step", {"ref_code": reference_code, "step": "loaded_message_data"})
            except Exception as e:
                self.report_progress("extract_error", {
                    "ref_code": reference_code,
                    "error": f"Failed to extract message data: {str(e)}"
                })
                self.error_count += 1
                return False

            # Save file content
            try:
                pattern = re.compile(rf"^file_{self.i_value}_(\d+)\.txt$")
                indices = []
                for name in os.listdir(self.OUTPUT_DIR):
                    m = pattern.match(name)
                    if m:
                        indices.append(int(m.group(1)))
                next_index = (max(indices) + 1) if indices else 1
                file_path = os.path.join(self.OUTPUT_DIR, f"file_{self.i_value}_{next_index}.txt")
                
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(f"Subject : {input_value}\nCode: {reference_code_extracted}\nMajor: {major}\n\n\n")

                # Get TinyMCE content
                iframe = self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))
                self.driver.switch_to.frame(iframe)
                time.sleep(self.file_load_sleep)
                tinymce_body = self.wait.until(EC.presence_of_element_located((By.ID, "tinymce")))
                popup_text = tinymce_body.text
                
                if not popup_text or popup_text.strip() == "":
                    self.report_progress("file_warning", {
                        "ref_code": reference_code,
                        "index": next_index,
                        "warning": "Empty file content"
                    })
                
                with open(file_path, "a", encoding="utf-8") as f:
                    f.write(popup_text)
                self.driver.switch_to.default_content()
                
                self.report_progress("file_saved", {
                    "ref_code": reference_code,
                    "index": next_index,
                    "subject": input_value
                })
            except Exception as e:
                self.driver.switch_to.default_content()
                self.report_progress("extract_error", {
                    "ref_code": reference_code,
                    "error": f"Failed to save file: {str(e)}"
                })
                self.error_count += 1
                return False

            # Close message popup
            try:
                time.sleep(0.5)
                close_btn = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//mat-dialog-container//app-font-icon[@name='close']/parent::button"))
                )
                self.driver.execute_script("arguments[0].click();", close_btn)
            except:
                close_buttons = self.driver.find_elements(By.XPATH, "//app-font-icon[@name='close']/parent::button")
                if close_buttons:
                    for btn in reversed(close_buttons):
                        try:
                            self.driver.execute_script("arguments[0].click();", btn)
                            break
                        except:
                            continue
            
            time.sleep(1.0)
            
            # Extract and save workflow
            try:
                # Re-fetch rows after closing popup
                rows = self.driver.find_elements(By.XPATH, "//tr[@mat-row]")
                if len(rows) > 0:
                    row = rows[0]
                    more_vert = row.find_element(By.XPATH, ".//app-font-icon[@name='more_vert']")
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", more_vert)
                    time.sleep(0.3)
                    self.driver.execute_script("arguments[0].click();", more_vert)
                    time.sleep(0.5)
                    
                    # Click workflow
                    workflow_button = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'گردش کار')]/ancestor::button[@mat-menu-item]"))
                    )
                    self.driver.execute_script("arguments[0].click();", workflow_button)
                    time.sleep(1)
                    time.sleep(self.workflow_load_sleep)
                    
                    # Extract workflow HTML
                    overlay_panes = self.driver.find_elements(By.CSS_SELECTOR, "div.cdk-overlay-pane")
                    if overlay_panes:
                        popup = overlay_panes[-1]
                        html = popup.get_attribute("innerHTML")
                    else:
                        html = ""
                    
                    soup = BeautifulSoup(html, 'html.parser')
                    tree_container = soup.find("mat-tree")
                    
                    if not tree_container:
                        self.report_progress("workflow_warning", {
                            "ref_code": reference_code,
                            "warning": "No workflow data found"
                        })
                        workflow_nodes = []
                    else:
                        def extract_node(node):
                            box_id = str(uuid.uuid4())
                            box_text = node.get_text(separator="\n", strip=True)
                            children = []
                            for group in node.find_all("div", role="group", recursive=False):
                                for child in group.find_all(["mat-tree-node", "mat-nested-tree-node"], recursive=False):
                                    children.append(extract_node(child))
                            return {
                                "id": box_id,
                                "text": box_text,
                                "children": children
                            }

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

                        workflow_file = os.path.join(self.OUTPUT_DIR, f"workflow_{self.i_value}_{next_index}.txt")
                        with open(workflow_file, "w", encoding="utf-8") as f:
                            for node in workflow_nodes:
                                write_workflow_node(f, node)
                        
                        self.report_progress("workflow_saved", {
                            "ref_code": reference_code,
                            "index": next_index
                        })

                    # Close workflow popup
                    time.sleep(0.3)
                    close_buttons = self.driver.find_elements(By.XPATH, "//app-font-icon[@name='close']/parent::button")
                    if close_buttons:
                        close_btn = close_buttons[-1]
                        self.driver.execute_script("arguments[0].click();", close_btn)
                    time.sleep(0.8)
                    
            except Exception as e:
                self.report_progress("workflow_error", {
                    "ref_code": reference_code,
                    "error": f"Failed to extract workflow: {str(e)}"
                })

            self.success_count += 1
            return True
            
        except Exception as e:
            self.report_progress("extract_error", {
                "ref_code": reference_code,
                "error": f"Unexpected error: {str(e)}"
            })
            self.error_count += 1
            return False

    def extract_info(self, text):
        """Extract date, name, and email from workflow node text"""
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
                    for next_line in lines[i+1:]:
                        next_line = next_line.strip()
                        if next_line and not re.match(r'[\w\.-]+@[\w\.-]+', next_line):
                            name = next_line
                            break
                    break

        return date, name, email

    def main_process(self):
        """Main processing loop: navigate to search and process each reference code"""
        # Navigate to search page
        print(f"[DEBUG] main_process: Starting navigation to search page...")
        self.navigate_to_search()
        print(f"[DEBUG] main_process: Navigation completed, waiting for page to be fully ready...")
        
        # Wait for page to be completely ready before making API calls
        time.sleep(self.too_long_sleep_time)
        print(f"[DEBUG] main_process: Page ready, starting reference code processing...")
        
        # Process each reference code
        for idx, reference_code in enumerate(self.REFERENCE_CODES):
            self.processed_count = idx + 1
            self.report_progress("processing_start", {
                "ref_code": reference_code,
                "progress": f"{idx + 1}/{len(self.REFERENCE_CODES)}"
            })
            
            # Search for reference code
            if not self.search_reference_code(reference_code):
                self.error_count += 1
                continue
            
            # Extract and save data
            self.extract_single_result(reference_code)
            
            self.report_progress("processing_complete", {
                "ref_code": reference_code,
                "progress": f"{idx + 1}/{len(self.REFERENCE_CODES)}"
            })

    def run(self):
        """Main entry point: setup, login, and process"""
        try:
            # Clear and create output directory
            self.clear_folder_and_create_it(self.OUTPUT_DIR)
            self.report_progress("init", {"status": "output_dir_cleared"})
            
            # Setup driver and login
            self.setup_driver()
            self.report_progress("init", {"status": "driver_ready"})
            
            self.login()
            
            # Main processing
            self.main_process()
            
            # Final report
            self.report_progress("complete", {
                "processed": self.processed_count,
                "success": self.success_count,
                "error": self.error_count
            })
            
        except Exception as e:
            self.report_progress("fatal_error", {"error": str(e)})
        finally:
            if self.driver:
                self.driver.quit()


if __name__ == "__main__":
    reference_codes = ["CODE1", "CODE2", "CODE3"]
    
    scraper = HamiScraperByReferenceCode(
        LOGIN_URL="https://mail.iau.ac.ir",
        USERNAME="Manager105001@iau.ir",
        PASSWORD="@Hamiyazd110",
        OUTPUT_DIR="./output_rf",
        CHROMEPATH="/home/keivan/drivers/chromedriver/chromedriver",
        REFERENCE_CODES=reference_codes,
        i_value=105001,
        name_value="حامی 001 واحد یزد"
    )
    scraper.run()
