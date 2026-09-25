#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hami Scraper - Desktop Application
A minimal, Apple-inspired web scraping application
"""

import sys
import os
import re
import json
import jdatetime
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QFileDialog,
    QFrame, QScrollArea, QProgressBar, QDateEdit, QCalendarWidget,
    QComboBox, QDialog, QListWidget, QListWidgetItem, QMessageBox,
    QInputDialog, QDialogButtonBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QDate, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon
from scraper import HamiScraper
from scraper_by_rf import HamiScraperByReferenceCode


def get_app_data_dir():
    """
    Get persistent directory for app data (config, pairs, etc.)
    Works both when running as script and as PyInstaller exe.
    """
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller exe - use directory where exe is located
        return Path(sys.executable).parent
    else:
        # Running as script - use script directory
        return Path(__file__).parent


def get_resource_path(relative_path):
    """
    Get path to bundled resources (like icons).
    Works both when running as script and as PyInstaller exe.
    """
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller exe - resources are in _MEIPASS temp dir
        base_path = Path(sys._MEIPASS)
    else:
        # Running as script
        base_path = Path(__file__).parent
    return base_path / relative_path


class ScraperThread(QThread):
    """Thread to run scraper without blocking UI"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.total_saved = 0
        self.total_skipped = 0
        
    def progress_callback(self, message_type, details):
        """Callback function for scraper to report progress"""
        if message_type == "file_saved":
            self.total_saved += 1
            self.progress.emit(f"📄 Message #{self.total_saved} saved: {details.get('subject', 'N/A')}")
        elif message_type == "workflow_saved":
            self.progress.emit(f"🔄 Workflow #{self.total_saved} saved")
        elif message_type == "file_empty":
            self.progress.emit(f"⚠️ Warning: Empty content for message #{details.get('index', '?')}")
        elif message_type == "workflow_empty":
            self.progress.emit(f"⚠️ Warning: Empty workflow for message #{details.get('index', '?')}")
        elif message_type == "skipped":
            self.total_skipped += 1
            self.progress.emit(f"⏭️ Skipped message (status: {details.get('status', 'unknown')})")
        elif message_type == "page_change":
            self.progress.emit(f"📃 Moving to page {details.get('page', '?')}...")
        elif message_type == "outdate_warning":
            self.progress.emit(f"⏳ Out-of-date message ({details.get('count', '?')}/{details.get('tolerance', '?')}): {details.get('date', 'N/A')}")
        elif message_type == "outdate_stop":
            self.progress.emit(f"🛑 Stopping: {details.get('count', '?')} consecutive out-of-date messages reached tolerance")
        
    def run(self):
        try:
            self.progress.emit("🔧 Initializing scraper...")
            scraper = HamiScraper(
                LOGIN_URL=self.config['login_url'],
                USERNAME=self.config['username'],
                PASSWORD=self.config['password'],
                START_DATE=self.config['start_date'],
                END_DATE=self.config['end_date'],
                OUTPUT_DIR=self.config['output_dir'],
                CHROMEPATH=self.config['chrome_path'],
                i_value=self.config['i_value'],
                name_value=self.config['name_value'],
                file_load_sleep=self.config.get('file_load_sleep', 3),
                workflow_load_sleep=self.config.get('workflow_load_sleep', 5),
                page_load_sleep=self.config.get('page_load_sleep', 5),
                outdate_tolerance=self.config.get('outdate_tolerance', 3),
                progress_callback=self.progress_callback
            )
            
            self.progress.emit("🌐 Setting up Chrome driver...")
            scraper.setup_driver()
            
            self.progress.emit("🔐 Logging in...")
            scraper.login()
            
            self.progress.emit("📊 Processing data...")
            scraper.main_process()
            
            self.progress.emit("🧹 Cleaning up...")
            scraper.driver.quit()
            
            self.progress.emit(f"\n🎉 SUCCESS! Total messages saved: {self.total_saved}, Skipped: {self.total_skipped}")
            self.finished.emit(True, "✅ Scraping completed successfully!")
            
        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            self.progress.emit(error_msg)
            self.finished.emit(False, error_msg)


class BatchScraperThread(QThread):
    """Thread to run batch scraping for multiple Hami entries"""
    progress = pyqtSignal(str)
    single_finished = pyqtSignal(dict, bool, str)  # pair, success, message
    all_finished = pyqtSignal(list, list)  # successful_pairs, failed_pairs
    
    def __init__(self, base_config, pairs_to_process):
        super().__init__()
        self.base_config = base_config
        self.pairs_to_process = pairs_to_process
        self.successful_pairs = []
        self.failed_pairs = []
        self._stop_requested = False
        
    def request_stop(self):
        """Request to stop batch processing after current item"""
        self._stop_requested = True
        
    def run(self):
        total = len(self.pairs_to_process)
        
        for idx, pair in enumerate(self.pairs_to_process, 1):
            if self._stop_requested:
                self.progress.emit(f"\n⏹️ Batch scraping stopped by user")
                break
                
            self.progress.emit(f"\n{'='*50}")
            self.progress.emit(f"📋 Processing {idx}/{total}: {pair['name']} (ID: {pair['id']})")
            self.progress.emit(f"{'='*50}")
            
            # Create config for this pair
            config = self.base_config.copy()
            config['i_value'] = pair['id']
            config['name_value'] = pair['name']
            
            # Run scraper for this pair
            success, message = self._run_single_scraper(config)
            
            if success:
                self.successful_pairs.append(pair)
                self.progress.emit(f"✅ Completed: {pair['name']}")
            else:
                self.failed_pairs.append({'pair': pair, 'error': message})
                self.progress.emit(f"❌ Failed: {pair['name']} - {message}")
            
            self.single_finished.emit(pair, success, message)
        
        # Emit final results
        self.all_finished.emit(self.successful_pairs, self.failed_pairs)
    
    def _run_single_scraper(self, config):
        """Run scraper for a single Hami entry"""
        total_saved = 0
        total_skipped = 0
        
        def progress_callback(message_type, details):
            nonlocal total_saved, total_skipped
            if message_type == "file_saved":
                total_saved += 1
                self.progress.emit(f"📄 Message #{total_saved} saved: {details.get('subject', 'N/A')}")
            elif message_type == "workflow_saved":
                self.progress.emit(f"🔄 Workflow #{total_saved} saved")
            elif message_type == "file_empty":
                self.progress.emit(f"⚠️ Warning: Empty content for message #{details.get('index', '?')}")
            elif message_type == "workflow_empty":
                self.progress.emit(f"⚠️ Warning: Empty workflow for message #{details.get('index', '?')}")
            elif message_type == "skipped":
                total_skipped += 1
                self.progress.emit(f"⏭️ Skipped message (status: {details.get('status', 'unknown')})")
            elif message_type == "page_change":
                self.progress.emit(f"📃 Moving to page {details.get('page', '?')}...")
            elif message_type == "outdate_warning":
                self.progress.emit(f"⏳ Out-of-date message ({details.get('count', '?')}/{details.get('tolerance', '?')}): {details.get('date', 'N/A')}")
            elif message_type == "outdate_stop":
                self.progress.emit(f"🛑 Stopping: {details.get('count', '?')} consecutive out-of-date messages reached tolerance")
        
        try:
            self.progress.emit("🔧 Initializing scraper...")
            scraper = HamiScraper(
                LOGIN_URL=config['login_url'],
                USERNAME=config['username'],
                PASSWORD=config['password'],
                START_DATE=config['start_date'],
                END_DATE=config['end_date'],
                OUTPUT_DIR=config['output_dir'],
                CHROMEPATH=config['chrome_path'],
                i_value=config['i_value'],
                name_value=config['name_value'],
                file_load_sleep=config.get('file_load_sleep', 3),
                workflow_load_sleep=config.get('workflow_load_sleep', 5),
                page_load_sleep=config.get('page_load_sleep', 5),
                outdate_tolerance=config.get('outdate_tolerance', 3),
                progress_callback=progress_callback
            )
            
            self.progress.emit("🌐 Setting up Chrome driver...")
            scraper.setup_driver()
            
            self.progress.emit("🔐 Logging in...")
            scraper.login()
            
            self.progress.emit("📊 Processing data...")
            scraper.main_process()
            
            self.progress.emit("🧹 Cleaning up...")
            scraper.driver.quit()
            
            self.progress.emit(f"🎉 SUCCESS! Total messages saved: {total_saved}, Skipped: {total_skipped}")
            return True, f"Saved: {total_saved}, Skipped: {total_skipped}"
            
        except Exception as e:
            # Make sure to close driver if it exists
            try:
                if 'scraper' in locals() and scraper.driver:
                    scraper.driver.quit()
            except:
                pass
            error_msg = str(e)
            self.progress.emit(f"❌ Error: {error_msg}")
            return False, error_msg


class SearchByReferenceCodeThread(QThread):
    """Thread to run reference code search scraping without blocking UI"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, config, reference_codes):
        super().__init__()
        self.config = config
        self.reference_codes = reference_codes
        self.total_processed = 0
        self.total_success = 0
        self.total_error = 0
        
    def progress_callback(self, message_type, details):
        """Callback function for scraper to report progress"""
        if message_type == "init":
            self.progress.emit(f"🔧 {details.get('status', 'Initializing')}")
        elif message_type == "login_complete":
            self.progress.emit("🔐 Login successful!")
        elif message_type == "navigation":
            step = details.get('step', 'unknown')
            if step == "clicked_menu":
                self.progress.emit("📍 Navigated to menu")
            elif step == "clicked_received_requests":
                self.progress.emit("📨 Opened received requests section")
            elif step == "clicked_all_toggle":
                self.progress.emit("✓ Selected 'All' filter")
        elif message_type == "processing_start":
            progress = details.get('progress', '?')
            ref_code = details.get('ref_code', '?')
            self.total_processed += 1
            self.progress.emit(f"\n🔍 Processing reference code: {ref_code} ({progress})")
        elif message_type == "search_step":
            step = details.get('step', 'unknown')
            ref_code = details.get('ref_code', '?')
            if step == "clicked_search_button":
                self.progress.emit(f"   🔎 Opening search dialog")
            elif step == "input_reference_code":
                self.progress.emit(f"   📝 Entered code: {ref_code}")
            elif step == "executed_search":
                self.progress.emit(f"   🔍 Searching...")
            elif step == "closed_search_overlay":
                self.progress.emit(f"   ✓ Search overlay closed")
        elif message_type == "extract_step":
            ref_code = details.get('ref_code', '?')
            step = details.get('step', 'unknown')
            if step == "clicked_result":
                self.progress.emit(f"   ✓ Clicked on search result")
            elif step == "loaded_message_data":
                self.progress.emit(f"   📄 Loaded message data")
        elif message_type == "supporter_resolved":
            supporter = details.get('supporter') or 'unknown'
            i_value = details.get('i_value')
            if details.get('mapped'):
                self.progress.emit(f"   👤 Hami: {supporter} → {i_value}")
            else:
                self.progress.emit(f"   ⚠️ Hami '{supporter}' is not in the mapping, saving as {i_value}")
        elif message_type == "unmapped_supporters":
            names = details.get('names', [])
            self.progress.emit(
                f"\n⚠️ {len(names)} hami name(s) missing from the mapping "
                f"(saved as file_{details.get('i_value')}_*.txt):"
            )
            for name in names:
                self.progress.emit(f"   • {name}")
        elif message_type == "file_saved":
            ref_code = details.get('ref_code', '?')
            subject = details.get('subject', 'N/A')
            self.total_success += 1
            self.progress.emit(f"   ✅ File saved: {subject}")
        elif message_type == "workflow_saved":
            ref_code = details.get('ref_code', '?')
            self.progress.emit(f"   ✅ Workflow saved")
        elif message_type == "extract_error":
            ref_code = details.get('ref_code', '?')
            error = details.get('error', 'unknown')
            self.total_error += 1
            self.progress.emit(f"   ❌ Error: {error}")
        elif message_type == "extract_warning":
            ref_code = details.get('ref_code', '?')
            warning = details.get('warning', 'unknown')
            self.progress.emit(f"   ⚠️ Warning: {warning}")
        elif message_type == "search_error":
            ref_code = details.get('ref_code', '?')
            error = details.get('error', 'unknown')
            self.total_error += 1
            self.progress.emit(f"   ❌ Search error: {error}")
        elif message_type == "complete":
            processed = details.get('processed', 0)
            success = details.get('success', 0)
            error = details.get('error', 0)
            self.progress.emit(f"\n📊 Summary: {processed} processed, {success} success, {error} errors")
    
    def run(self):
        try:
            self.progress.emit("🔧 Initializing reference code scraper...")
            scraper = HamiScraperByReferenceCode(
                LOGIN_URL=self.config['login_url'],
                USERNAME=self.config['username'],
                PASSWORD=self.config['password'],
                OUTPUT_DIR=self.config['output_dir_rf'],
                CHROMEPATH=self.config['chrome_path'],
                REFERENCE_CODES=self.reference_codes,
                SUPPORTER_MAP=self.config.get('supporter_map', {}),
                search_wait_time=self.config.get('search_wait_time', 5),
                file_load_sleep=self.config.get('file_load_sleep', 3),
                workflow_load_sleep=self.config.get('workflow_load_sleep', 5),
                progress_callback=self.progress_callback
            )
            
            self.progress.emit("🌐 Setting up Chrome driver...")
            scraper.setup_driver()
            
            self.progress.emit("🔐 Logging in...")
            scraper.login()
            
            self.progress.emit("📊 Processing reference codes...")
            scraper.main_process()
            
            self.progress.emit("🧹 Cleaning up...")
            scraper.driver.quit()
            
            self.progress.emit(f"\n🎉 SUCCESS! Processed {self.total_processed} codes, {self.total_success} success, {self.total_error} errors")
            self.finished.emit(True, "✅ Reference code search completed successfully!")
            
        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            self.progress.emit(error_msg)
            self.finished.emit(False, error_msg)


class BatchScrapingDialog(QDialog):
    """Dialog for selecting multiple Hami entries for batch scraping"""
    
    def __init__(self, pairs, parent=None):
        super().__init__(parent)
        self.pairs = pairs
        self.selected_pairs = []
        self.setWindowTitle("Batch Scraping - Select Hami Entries")
        self.setMinimumSize(650, 550)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Title
        title = QLabel("📋 Select Hami Entries for Batch Scraping")
        title.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: 600;
                color: #2C3E50;
                margin-bottom: 8px;
            }
        """)
        layout.addWidget(title)
        
        # Instructions
        instructions = QLabel("Select one or more Hami entries to scrape in sequence. Each will open a new browser window.")
        instructions.setStyleSheet("font-size: 14px; color: #7F8C8D; margin-bottom: 8px;")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Select All / Deselect All buttons
        select_layout = QHBoxLayout()
        select_all_btn = QPushButton("☑️ Select All")
        select_all_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 14px;
                background-color: #3498DB;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
        """)
        select_all_btn.clicked.connect(self.select_all)
        
        deselect_all_btn = QPushButton("☐ Deselect All")
        deselect_all_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 14px;
                background-color: #95A5A6;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #7F8C8D;
            }
        """)
        deselect_all_btn.clicked.connect(self.deselect_all)
        
        select_layout.addWidget(select_all_btn)
        select_layout.addWidget(deselect_all_btn)
        select_layout.addStretch()
        layout.addLayout(select_layout)
        
        # List widget with checkboxes
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                border: 1px solid #D5DBDB;
                border-radius: 8px;
                padding: 8px;
                background-color: #FFFFFF;
                font-size: 16px;
                color: #2C3E50;
            }
            QListWidget::item {
                padding: 10px;
                border-radius: 4px;
            }
            QListWidget::item:hover {
                background-color: #EBF5FB;
            }
            QListWidget::item:selected {
                background-color: #D5E8F7;
                color: #2C3E50;
            }
        """)
        
        # Add items with checkboxes
        for pair in self.pairs:
            item = QListWidgetItem(f"{pair['id']} - {pair['name']}")
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            item.setData(Qt.UserRole, pair)
            self.list_widget.addItem(item)
        
        layout.addWidget(self.list_widget)
        
        # Selected count label
        self.count_label = QLabel("Selected: 0 entries")
        self.count_label.setStyleSheet("font-size: 14px; color: #7F8C8D;")
        layout.addWidget(self.count_label)
        
        # Connect item changed signal
        self.list_widget.itemChanged.connect(self.update_count)
        
        # Dialog buttons
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 16px;
                background-color: #ECF0F1;
                color: #2C3E50;
                border: 1px solid #BDC3C7;
            }
            QPushButton:hover {
                background-color: #D5DBDB;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        
        start_btn = QPushButton("🚀 Start Batch Scraping")
        start_btn.setStyleSheet("""
            QPushButton {
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 16px;
                background-color: #27AE60;
                color: white;
                border: none;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #219A52;
            }
        """)
        start_btn.clicked.connect(self.start_batch)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(start_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def select_all(self):
        """Select all items"""
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setCheckState(Qt.Checked)
    
    def deselect_all(self):
        """Deselect all items"""
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setCheckState(Qt.Unchecked)
    
    def update_count(self):
        """Update selected count label"""
        count = sum(1 for i in range(self.list_widget.count()) 
                    if self.list_widget.item(i).checkState() == Qt.Checked)
        self.count_label.setText(f"Selected: {count} entries")
    
    def start_batch(self):
        """Start batch scraping with selected items"""
        self.selected_pairs = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.Checked:
                self.selected_pairs.append(item.data(Qt.UserRole))
        
        if not self.selected_pairs:
            QMessageBox.warning(self, "No Selection", "Please select at least one Hami entry to scrape.")
            return
        
        self.accept()


class ModernLineEdit(QLineEdit):
    """Custom styled line edit with modern appearance"""
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setStyleSheet("""
            QLineEdit {
                padding: 14px 18px;
                border: 1px solid #BDC3C7;
                border-radius: 8px;
                background-color: white;
                font-size: 22px;
                color: #2C3E50;
                min-height: 30px;
            }
            QLineEdit:focus {
                border: 2px solid #3498DB;
                background-color: white;
            }
            QLineEdit:hover {
                background-color: #F8F9FA;
                border: 1px solid #3498DB;
            }
        """)


class JalaliDateEdit(QLineEdit):
    """Custom Jalali (Shamsi) date edit with modern appearance"""
    dateChanged = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._jdate = jdatetime.date.today()
        self.setPlaceholderText("YYYY/MM/DD")
        self.setText(self._jdate.strftime("%Y/%m/%d"))
        self.setStyleSheet("""
            QLineEdit {
                padding: 14px 18px;
                border: 1px solid #BDC3C7;
                border-radius: 8px;
                background-color: white;
                font-size: 22px;
                color: #2C3E50;
                min-height: 30px;
            }
            QLineEdit:focus {
                border: 2px solid #3498DB;
                background-color: white;
            }
            QLineEdit:hover {
                background-color: #F8F9FA;
                border: 1px solid #3498DB;
            }
        """)
        self.textChanged.connect(self._validate_and_update)
        
    def _validate_and_update(self, text):
        """Validate and update the Jalali date"""
        try:
            # Try to parse the date
            parts = text.split('/')
            if len(parts) == 3:
                year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
                # Validate Jalali date
                new_date = jdatetime.date(year, month, day)
                self._jdate = new_date
                self.dateChanged.emit()
        except:
            # Invalid date, don't update
            pass
    
    def set_jdate(self, year, month, day):
        """Set the Jalali date"""
        try:
            self._jdate = jdatetime.date(year, month, day)
            self.setText(self._jdate.strftime("%Y/%m/%d"))
            self.dateChanged.emit()
        except:
            pass
    
    def get_jdate_string(self):
        """Get the date as a string in YYYY/MM/DD format"""
        return self._jdate.strftime("%Y/%m/%d")
    
    def get_jdate(self):
        """Get the jdatetime.date object"""
        return self._jdate


class ModernDateEdit(QDateEdit):
    """Custom styled date edit with modern appearance (kept for compatibility)"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCalendarPopup(True)
        self.setDisplayFormat("yyyy/MM/dd")
        self.setStyleSheet("""
            QDateEdit {
                padding: 14px 18px;
                border: 1px solid #BDC3C7;
                border-radius: 8px;
                background-color: white;
                font-size: 22px;
                color: #2C3E50;
                min-height: 30px;
            }
            QDateEdit:focus {
                border: 2px solid #3498DB;
                background-color: white;
            }
            QDateEdit:hover {
                background-color: #F8F9FA;
                border: 1px solid #3498DB;
            }
            QDateEdit::drop-down {
                border: none;
                width: 30px;
            }
            QDateEdit::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #7F8C8D;
                margin-right: 8px;
            }
        """)


class ModernButton(QPushButton):
    """Custom styled button with modern appearance"""
    def __init__(self, text, primary=False, parent=None):
        super().__init__(text, parent)
        self.primary = primary
        self.setMinimumHeight(44)
        self.setCursor(Qt.PointingHandCursor)
        self._update_style()
        
    def _update_style(self):
        if self.primary:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #3498DB;
                    color: white;
                    border: none;
                    border-radius: 10px;
                    padding: 14px 28px;
                    font-size: 22px;
                    font-weight: 600;
                    min-height: 50px;
                }
                QPushButton:hover {
                    background-color: #2980B9;
                }
                QPushButton:pressed {
                    background-color: #2471A3;
                }
                QPushButton:disabled {
                    background-color: #D5DBDB;
                    color: #95A5A6;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #ECF0F1;
                    color: #2C3E50;
                    border: 1px solid #BDC3C7;
                    border-radius: 10px;
                    padding: 14px 28px;
                    font-size: 22px;
                    font-weight: 500;
                    min-height: 50px;
                }
                QPushButton:hover {
                    background-color: #D5DBDB;
                }
                QPushButton:pressed {
                    background-color: #BDC3C7;
                }
            """)


class SectionCard(QFrame):
    """Card container for grouping related inputs"""
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #BDC3C7;
                padding: 4px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 26px;
                font-weight: 600;
                color: #2C3E50;
                margin-bottom: 6px;
            }
        """)
        layout.addWidget(title_label)
        
        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(14)
        layout.addLayout(self.content_layout)
        
        self.setLayout(layout)
    
    def add_field(self, label_text, widget):
        """Add a labeled field to the card"""
        label = QLabel(label_text)
        label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: 500;
                color: #7F8C8D;
                margin-bottom: 6px;
            }
        """)
        self.content_layout.addWidget(label)
        self.content_layout.addWidget(widget)
        return widget


class AboutDialog(QDialog):
    """Dialog for showing application information"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About Hami Scraper")
        self.setFixedSize(500, 450)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(40, 30, 40, 30)
        
        # App Icon/Title
        title = QLabel("Hami Scraper")
        title.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: 700;
                color: #2C3E50;
                letter-spacing: -0.5px;
            }
        """)
        title.setAlignment(Qt.AlignCenter)
        title.setWordWrap(True)
        layout.addWidget(title)
        
        # Version
        version = QLabel("Version 3.0")
        version.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #7F8C8D;
                font-weight: 400;
            }
        """)
        version.setAlignment(Qt.AlignCenter)
        version.setWordWrap(True)
        layout.addWidget(version)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #BDC3C7; max-height: 1px;")
        separator.setFixedHeight(1)
        layout.addWidget(separator)
        
        layout.addSpacing(5)
        
        # Director Info
        director_label = QLabel("Directed by")
        director_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #7F8C8D;
                font-weight: 500;
            }
        """)
        director_label.setAlignment(Qt.AlignCenter)
        director_label.setWordWrap(True)
        layout.addWidget(director_label)
        
        director_name = QLabel("Keivan Jamali")
        director_name.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: 600;
                color: #2C3E50;
                margin-top: 5px;
            }
        """)
        director_name.setAlignment(Qt.AlignCenter)
        director_name.setWordWrap(True)
        layout.addWidget(director_name)
        
        layout.addSpacing(15)
        
        # Website
        website_label = QLabel("✅ Website")
        website_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #7F8C8D;
                font-weight: 500;
            }
        """)
        website_label.setAlignment(Qt.AlignCenter)
        website_label.setWordWrap(True)
        layout.addWidget(website_label)
        
        website_link = QLabel('<a href="https://keivanjamali.com" style="color: #3498DB; text-decoration: none;">keivanjamali.com</a>')
        website_link.setOpenExternalLinks(True)
        website_link.setStyleSheet("""
            QLabel {
                font-size: 15px;
                font-weight: 500;
                margin-top: 5px;
            }
        """)
        website_link.setAlignment(Qt.AlignCenter)
        website_link.setWordWrap(True)
        website_link.setTextFormat(Qt.RichText)
        layout.addWidget(website_link)
        
        layout.addSpacing(15)
        
        # Email
        email_label = QLabel("✅ Contact")
        email_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #7F8C8D;
                font-weight: 500;
            }
        """)
        email_label.setAlignment(Qt.AlignCenter)
        email_label.setWordWrap(True)
        layout.addWidget(email_label)
        
        email_link = QLabel('<a href="mailto:k1jamali01@gmail.com" style="color: #3498DB; text-decoration: none;">k1jamali01@gmail.com</a>')
        email_link.setOpenExternalLinks(True)
        email_link.setStyleSheet("""
            QLabel {
                font-size: 15px;
                font-weight: 500;
                margin-top: 5px;
            }
        """)
        email_link.setAlignment(Qt.AlignCenter)
        email_link.setWordWrap(True)
        email_link.setTextFormat(Qt.RichText)
        layout.addWidget(email_link)
        
        layout.addSpacing(20)
        layout.addStretch()
        
        # Close button
        close_btn = ModernButton("Close", primary=True)
        close_btn.setMinimumHeight(44)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)


class SettingsDialog(QDialog):
    """Dialog for managing ID-Name pairs"""
    
    def __init__(self, pairs, parent=None):
        super().__init__(parent)
        self.pairs = pairs.copy()  # Work with a copy
        self.setWindowTitle("Manage ID-Name Pairs")
        self.setMinimumSize(600, 500)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Title
        title = QLabel("ID-Name Pairs")
        title.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: 600;
                color: #2C3E50;
                margin-bottom: 8px;
            }
        """)
        layout.addWidget(title)
        
        # List widget
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                border: 1px solid #D5DBDB;
                border-radius: 8px;
                padding: 8px;
                background-color: #FFFFFF;
                font-size: 14px;
                color: #2C3E50;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
            }
            QListWidget::item:hover {
                background-color: #EBF5FB;
            }
            QListWidget::item:selected {
                background-color: #3498DB;
                color: white;
            }
        """)
        self.refresh_list()
        layout.addWidget(self.list_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        add_btn = ModernButton("➕ Add New")
        add_btn.clicked.connect(self.add_pair)
        
        edit_btn = ModernButton("✏️ Edit")
        edit_btn.clicked.connect(self.edit_pair)
        
        remove_btn = ModernButton("🗑️ Remove")
        remove_btn.clicked.connect(self.remove_pair)
        
        button_layout.addWidget(add_btn)
        button_layout.addWidget(edit_btn)
        button_layout.addWidget(remove_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 14px;
            }
        """)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def refresh_list(self):
        """Refresh the list display"""
        self.list_widget.clear()
        for pair in self.pairs:
            item_text = f"{pair['id']} - {pair['name']}"
            self.list_widget.addItem(item_text)
    
    def add_pair(self):
        """Add a new ID-Name pair"""
        id_value, ok1 = QInputDialog.getInt(
            self, "Add Pair", "Enter ID Value:", 
            105001, 100000, 999999
        )
        if not ok1:
            return
        
        name_value, ok2 = QInputDialog.getText(
            self, "Add Pair", "Enter Name:"
        )
        if not ok2 or not name_value:
            return
        
        self.pairs.append({"id": id_value, "name": name_value})
        self.refresh_list()
    
    def edit_pair(self):
        """Edit selected pair"""
        current_row = self.list_widget.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a pair to edit")
            return
        
        pair = self.pairs[current_row]
        
        id_value, ok1 = QInputDialog.getInt(
            self, "Edit Pair", "Enter ID Value:", 
            pair['id'], 100000, 999999
        )
        if not ok1:
            return
        
        name_value, ok2 = QInputDialog.getText(
            self, "Edit Pair", "Enter Name:", 
            text=pair['name']
        )
        if not ok2 or not name_value:
            return
        
        self.pairs[current_row] = {"id": id_value, "name": name_value}
        self.refresh_list()
        self.list_widget.setCurrentRow(current_row)
    
    def remove_pair(self):
        """Remove selected pair"""
        current_row = self.list_widget.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a pair to remove")
            return
        
        reply = QMessageBox.question(
            self, "Confirm Delete",
            "Are you sure you want to remove this pair?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            del self.pairs[current_row]
            self.refresh_list()


class HamiScraperApp(QMainWindow):
    """Main application window"""
    
    # Default ID-Name pairs
    DEFAULT_PAIRS = [
        {"id": 105001, "name": "حامی 001 واحد یزد"},
        {"id": 105002, "name": "حامی 002 واحد یزد"},
        {"id": 105003, "name": "حامی 003 واحد یزد"},
        {"id": 105004, "name": "حامی 004 واحد یزد"},
        {"id": 105005, "name": "حامی 005 واحد یزد"},
        {"id": 105006, "name": "حامی 006 واحد یزد"},
        {"id": 105007, "name": "حامی 007 واحد یزد"},
        {"id": 105008, "name": "حامی 008 واحد یزد"},
        {"id": 105009, "name": "حامی 009 واحد یزد"},
        {"id": 105010, "name": "حامی 010 واحد یزد"},
        {"id": 105011, "name": "حامی 011 واحد یزد"},
        {"id": 105012, "name": "حامی 012 واحد یزد"},
        {"id": 105013, "name": "حامی 013 واحد یزد"},
        {"id": 105014, "name": "حامی 014 واحد یزد"},
        {"id": 105015, "name": "حامی 015 واحد یزد"},
        {"id": 105016, "name": "حامی 016 واحد یزد"},
        {"id": 105017, "name": "حامی 017 واحد یزد"},
        {"id": 105018, "name": "حامی 018 واحد یزد"},
        {"id": 105019, "name": "حامی 019 واحد یزد"},
        {"id": 105266, "name": "sup105266"},
        {"id": 105335, "name": "sup105335"},
        {"id": 105434, "name": "sup105434"},
        {"id": 105860, "name": "sup105860"},
        {"id": 105949, "name": "sup105949"},
    ]
    
    def __init__(self):
        super().__init__()
        # Use persistent directory for config files (works with PyInstaller exe)
        app_data_dir = get_app_data_dir()
        self.config_file = app_data_dir / "config.json"
        self.pairs_file = app_data_dir / "pairs.json"
        self.scraper_thread = None
        self.batch_thread = None
        self.rf_search_thread = None
        self.id_name_pairs = []
        
        # Set application icon (use resource path for bundled icon)
        icon_path = get_resource_path("app_logo_icon.ico")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        self.load_pairs()
        self.init_ui()
        self.load_config()
        
    def init_ui(self):
        self.setWindowTitle("Hami Scraper")
        self.setMinimumSize(800, 900)
        
        # Set application style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ECF0F1;
            }
            QScrollArea {
                border: 1px solid #D5DBDB;
                background-color: #F8F9FA;
            }
            QWidget {
                background-color: #F8F9FA;
            }
        """)
        
        # Central widget with scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        container = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(20)
        
        # Header
        header = self.create_header()
        main_layout.addWidget(header)
        
        # Configuration Cards
        self.login_card = self.create_login_card()
        main_layout.addWidget(self.login_card)
        
        self.date_card = self.create_date_card()
        main_layout.addWidget(self.date_card)
        
        self.scraper_card = self.create_scraper_card()
        main_layout.addWidget(self.scraper_card)
        
        self.path_card = self.create_path_card()
        main_layout.addWidget(self.path_card)
        
        # Timing settings card
        self.timing_card = self.create_timing_card()
        main_layout.addWidget(self.timing_card)
        
        # Reference Code Search Card (SEPARATE SECTION)
        self.rf_card = self.create_rf_search_card()
        main_layout.addWidget(self.rf_card)
        
        # Control buttons
        button_layout = self.create_button_layout()
        main_layout.addLayout(button_layout)
        
        # Progress section
        self.progress_card = self.create_progress_card()
        main_layout.addWidget(self.progress_card)
        
        main_layout.addStretch()
        
        container.setLayout(main_layout)
        scroll.setWidget(container)
        self.setCentralWidget(scroll)
        
    def create_header(self):
        """Create application header"""
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
            }
        """)
        
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Left side - title and subtitle
        left_layout = QVBoxLayout()
        left_layout.setSpacing(8)
        
        title = QLabel("Hami Scraper")
        title.setStyleSheet("""
            QLabel {
                font-size: 42px;
                font-weight: 700;
                color: #2C3E50;
                letter-spacing: -0.5px;
            }
        """)
        
        subtitle = QLabel("Automated data extraction tool")
        subtitle.setStyleSheet("""
            QLabel {
                font-size: 22px;
                color: #7F8C8D;
                font-weight: 400;
            }
        """)
        
        left_layout.addWidget(title)
        left_layout.addWidget(subtitle)
        
        # Right side - about button
        about_btn = ModernButton("About")
        about_btn.setMaximumWidth(140)
        about_btn.setMaximumHeight(55)
        about_btn.clicked.connect(self.show_about)
        
        main_layout.addLayout(left_layout)
        main_layout.addStretch()
        main_layout.addWidget(about_btn, alignment=Qt.AlignTop)
        
        header.setLayout(main_layout)
        
        return header
    
    def create_login_card(self):
        """Create login credentials card"""
        card = SectionCard("✅ Login Credentials")
        
        self.url_input = card.add_field("Login URL", ModernLineEdit("https://mail.iau.ac.ir"))
        self.username_input = card.add_field("Username", ModernLineEdit("your@email.com"))
        self.password_input = card.add_field("Password", ModernLineEdit("••••••••"))
        self.password_input.setEchoMode(QLineEdit.Password)
        
        return card
    
    def create_date_card(self):
        """Create date range card"""
        card = SectionCard("✅ Date Range (Shamsi/Jalali)")
        
        date_container = QWidget()
        date_layout = QHBoxLayout()
        date_layout.setSpacing(16)
        date_layout.setContentsMargins(0, 0, 0, 0)
        
        # Start date
        start_container = QWidget()
        start_layout = QVBoxLayout()
        start_layout.setSpacing(4)
        start_layout.setContentsMargins(0, 0, 0, 0)
        start_label = QLabel("Start Date (شروع)")
        start_label.setStyleSheet("font-size: 20px; font-weight: 500; color: #7F8C8D;")
        self.start_date = JalaliDateEdit()
        self.start_date.set_jdate(1404, 7, 1)
        start_layout.addWidget(start_label)
        start_layout.addWidget(self.start_date)
        start_container.setLayout(start_layout)
        
        # End date
        end_container = QWidget()
        end_layout = QVBoxLayout()
        end_layout.setSpacing(4)
        end_layout.setContentsMargins(0, 0, 0, 0)
        end_label = QLabel("End Date (پایان)")
        end_label.setStyleSheet("font-size: 20px; font-weight: 500; color: #7F8C8D;")
        self.end_date = JalaliDateEdit()
        self.end_date.set_jdate(1404, 8, 1)
        end_layout.addWidget(end_label)
        end_layout.addWidget(self.end_date)
        end_container.setLayout(end_layout)
        
        date_layout.addWidget(start_container)
        date_layout.addWidget(end_container)
        date_container.setLayout(date_layout)
        
        card.content_layout.addWidget(date_container)
        
        return card
    
    def create_scraper_card(self):
        """Create scraper configuration card"""
        card = SectionCard("⚙️ Scraper Settings")
        
        # Selector dropdown
        selector_container = QWidget()
        selector_layout = QHBoxLayout()
        selector_layout.setSpacing(8)
        selector_layout.setContentsMargins(0, 0, 0, 0)
        
        self.pair_selector = QComboBox()
        self.pair_selector.setStyleSheet("""
            QComboBox {
                padding: 14px 18px;
                border: 1px solid #D5DBDB;
                border-radius: 8px;
                background-color: #FFFFFF;
                font-size: 22px;
                color: #2C3E50;
                min-height: 30px;
            }
            QComboBox:hover {
                background-color: #F8F9FA;
                border: 1px solid #BDC3C7;
            }
            QComboBox:focus {
                border: 2px solid #3498DB;
                background-color: #FFFFFF;
            }
            QComboBox::drop-down {
                border: none;
                width: 35px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 7px solid #7F8C8D;
                margin-right: 10px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #D5DBDB;
                border-radius: 8px;
                background-color: #FFFFFF;
                selection-background-color: #3498DB;
                selection-color: white;
                padding: 6px;
                font-size: 22px;
            }
        """)
        self.populate_pair_selector()
        self.pair_selector.currentIndexChanged.connect(self.on_pair_selected)
        
        manage_btn = ModernButton("⚙️ Manage")
        manage_btn.setMaximumWidth(100)
        manage_btn.clicked.connect(self.open_settings)
        
        selector_layout.addWidget(self.pair_selector)
        selector_layout.addWidget(manage_btn)
        selector_container.setLayout(selector_layout)
        card.add_field("Select ID-Name Pair", selector_container)
        
        # Manual input fields (still available)
        self.i_value_input = card.add_field("I Value (Manual)", ModernLineEdit("105001"))
        self.name_value_input = card.add_field("Name Value (Manual)", ModernLineEdit("حامی 001 واحد یزد"))
        
        return card
    
    def create_path_card(self):
        """Create path configuration card"""
        card = SectionCard("✅ Paths")
        
        # Chrome path
        chrome_container = QWidget()
        chrome_layout = QHBoxLayout()
        chrome_layout.setSpacing(8)
        chrome_layout.setContentsMargins(0, 0, 0, 0)
        self.chrome_path_input = ModernLineEdit("/path/to/chromedriver")
        chrome_btn = ModernButton("Browse")
        chrome_btn.setMaximumWidth(100)
        chrome_btn.clicked.connect(self.browse_chrome_path)
        chrome_layout.addWidget(self.chrome_path_input)
        chrome_layout.addWidget(chrome_btn)
        chrome_container.setLayout(chrome_layout)
        card.add_field("ChromeDriver Path", chrome_container)
        
        # Output directory
        output_container = QWidget()
        output_layout = QHBoxLayout()
        output_layout.setSpacing(8)
        output_layout.setContentsMargins(0, 0, 0, 0)
        self.output_dir_input = ModernLineEdit("./output")
        output_btn = ModernButton("Browse")
        output_btn.setMaximumWidth(100)
        output_btn.clicked.connect(self.browse_output_dir)
        output_layout.addWidget(self.output_dir_input)
        output_layout.addWidget(output_btn)
        output_container.setLayout(output_layout)
        card.add_field("Output Directory", output_container)
        
        return card
    
    def create_timing_card(self):
        """Create timing settings card for controlling wait times"""
        card = SectionCard("⏱️ Timing Settings")
        
        timing_container = QWidget()
        timing_layout = QHBoxLayout()
        timing_layout.setSpacing(16)
        timing_layout.setContentsMargins(0, 0, 0, 0)
        
        # File load sleep time
        file_container = QWidget()
        file_layout = QVBoxLayout()
        file_layout.setSpacing(4)
        file_layout.setContentsMargins(0, 0, 0, 0)
        file_label = QLabel("File Wait (sec)")
        file_label.setStyleSheet("font-size: 20px; font-weight: 500; color: #7F8C8D;")
        self.file_load_sleep_input = ModernLineEdit("3")
        self.file_load_sleep_input.setPlaceholderText("3")
        file_layout.addWidget(file_label)
        file_layout.addWidget(self.file_load_sleep_input)
        file_container.setLayout(file_layout)
        
        # Workflow load sleep time
        workflow_container = QWidget()
        workflow_layout = QVBoxLayout()
        workflow_layout.setSpacing(4)
        workflow_layout.setContentsMargins(0, 0, 0, 0)
        workflow_label = QLabel("Workflow Wait (sec)")
        workflow_label.setStyleSheet("font-size: 20px; font-weight: 500; color: #7F8C8D;")
        self.workflow_load_sleep_input = ModernLineEdit("5")
        self.workflow_load_sleep_input.setPlaceholderText("5")
        workflow_layout.addWidget(workflow_label)
        workflow_layout.addWidget(self.workflow_load_sleep_input)
        workflow_container.setLayout(workflow_layout)
        
        # Page load sleep time
        page_container = QWidget()
        page_layout = QVBoxLayout()
        page_layout.setSpacing(4)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_label = QLabel("Page Wait (sec)")
        page_label.setStyleSheet("font-size: 20px; font-weight: 500; color: #7F8C8D;")
        self.page_load_sleep_input = ModernLineEdit("5")
        self.page_load_sleep_input.setPlaceholderText("5")
        page_layout.addWidget(page_label)
        page_layout.addWidget(self.page_load_sleep_input)
        page_container.setLayout(page_layout)
        
        # Outdate tolerance
        tolerance_container = QWidget()
        tolerance_layout = QVBoxLayout()
        tolerance_layout.setSpacing(4)
        tolerance_layout.setContentsMargins(0, 0, 0, 0)
        tolerance_label = QLabel("Outdate Tolerance")
        tolerance_label.setStyleSheet("font-size: 20px; font-weight: 500; color: #7F8C8D;")
        self.outdate_tolerance_input = ModernLineEdit("3")
        self.outdate_tolerance_input.setPlaceholderText("3")
        tolerance_layout.addWidget(tolerance_label)
        tolerance_layout.addWidget(self.outdate_tolerance_input)
        tolerance_container.setLayout(tolerance_layout)
        
        timing_layout.addWidget(file_container)
        timing_layout.addWidget(workflow_container)
        timing_layout.addWidget(page_container)
        timing_layout.addWidget(tolerance_container)
        timing_container.setLayout(timing_layout)
        
        card.content_layout.addWidget(timing_container)
        
        # Help text
        help_label = QLabel("💡 Outdate Tolerance: How many out-of-date messages to check before stopping (resets when in-date message found)")
        help_label.setStyleSheet("font-size: 18px; color: #95A5A6; margin-top: 8px;")
        help_label.setWordWrap(True)
        card.content_layout.addWidget(help_label)
        
        return card
    
    def create_rf_search_card(self):
        """Create reference code search card (SEPARATE from date range scraper)"""
        card = SectionCard("🔍 Reference Code Search")
        
        # Info label
        info_label = QLabel("💡 Search the website by reference codes. Paste one code per line.")
        info_label.setStyleSheet("font-size: 18px; color: #7F8C8D; margin-bottom: 8px;")
        info_label.setWordWrap(True)
        card.content_layout.addWidget(info_label)
        
        # Reference codes input
        codes_label = QLabel("Reference Codes (paste one per line):")
        codes_label.setStyleSheet("font-size: 20px; font-weight: 500; color: #7F8C8D;")
        card.content_layout.addWidget(codes_label)
        
        self.rf_codes_input = QTextEdit()
        self.rf_codes_input.setPlaceholderText("123456\n654321\n789012")
        self.rf_codes_input.setMinimumHeight(150)
        self.rf_codes_input.setStyleSheet("""
            QTextEdit {
                padding: 14px 18px;
                border: 1px solid #D5DBDB;
                border-radius: 8px;
                background-color: #FFFFFF;
                font-size: 20px;
                color: #2C3E50;
                font-family: monospace;
            }
            QTextEdit:focus {
                border: 2px solid #3498DB;
                background-color: #FFFFFF;
            }
        """)
        card.content_layout.addWidget(self.rf_codes_input)
        
        # Configuration section
        config_label = QLabel("Configuration:")
        config_label.setStyleSheet("font-size: 20px; font-weight: 500; color: #7F8C8D; margin-top: 12px;")
        card.content_layout.addWidget(config_label)
        
        # RF specific settings
        rf_config_container = QWidget()
        rf_config_layout = QHBoxLayout()
        rf_config_layout.setSpacing(16)
        rf_config_layout.setContentsMargins(0, 0, 0, 0)
        
        # Output directory for RF
        rf_output_container = QWidget()
        rf_output_layout = QVBoxLayout()
        rf_output_layout.setSpacing(4)
        rf_output_layout.setContentsMargins(0, 0, 0, 0)
        rf_output_label = QLabel("Output Dir")
        rf_output_label.setStyleSheet("font-size: 20px; font-weight: 500; color: #7F8C8D;")
        self.rf_output_dir_input = ModernLineEdit("./output_rf")
        browse_rf_output_btn = ModernButton("Browse")
        browse_rf_output_btn.setMaximumWidth(100)
        browse_rf_output_btn.clicked.connect(self.browse_rf_output_dir)
        
        rf_output_sub_layout = QHBoxLayout()
        rf_output_sub_layout.setSpacing(8)
        rf_output_sub_layout.addWidget(self.rf_output_dir_input)
        rf_output_sub_layout.addWidget(browse_rf_output_btn)
        
        rf_output_layout.addWidget(rf_output_label)
        rf_output_layout.addLayout(rf_output_sub_layout)
        rf_output_container.setLayout(rf_output_layout)
        
        # Search wait time
        search_wait_container = QWidget()
        search_wait_layout = QVBoxLayout()
        search_wait_layout.setSpacing(4)
        search_wait_layout.setContentsMargins(0, 0, 0, 0)
        search_wait_label = QLabel("Search Wait (sec)")
        search_wait_label.setStyleSheet("font-size: 20px; font-weight: 500; color: #7F8C8D;")
        self.rf_search_wait_input = ModernLineEdit("5")
        self.rf_search_wait_input.setPlaceholderText("5")
        search_wait_layout.addWidget(search_wait_label)
        search_wait_layout.addWidget(self.rf_search_wait_input)
        search_wait_container.setLayout(search_wait_layout)
        
        rf_config_layout.addWidget(rf_output_container)
        rf_config_layout.addWidget(search_wait_container)
        rf_config_container.setLayout(rf_config_layout)
        
        card.content_layout.addWidget(rf_config_container)
        
        # Hami name -> ID mapping
        mapping_label = QLabel("Hami Mapping (one per line, e.g.  مجید امیدواری = 105006):")
        mapping_label.setStyleSheet("font-size: 20px; font-weight: 500; color: #7F8C8D; margin-top: 12px;")
        card.content_layout.addWidget(mapping_label)
        
        mapping_hint = QLabel(
            "💡 The site only shows the hami name, not the ID. Codes whose hami is "
            "missing here are saved as file_0_*.txt."
        )
        mapping_hint.setWordWrap(True)
        mapping_hint.setStyleSheet("font-size: 16px; color: #95A5A6;")
        card.content_layout.addWidget(mapping_hint)
        
        self.rf_mapping_input = QTextEdit()
        self.rf_mapping_input.setPlaceholderText("مجید امیدواری = 105006\nمحمود معلائی = 105001")
        self.rf_mapping_input.setMinimumHeight(120)
        self.rf_mapping_input.setStyleSheet("""
            QTextEdit {
                background-color: #FFFFFF;
                border: 2px solid #E0E0E0;
                border-radius: 10px;
                padding: 12px;
                font-size: 20px;
                color: #2C3E50;
            }
            QTextEdit:focus {
                border: 2px solid #007AFF;
            }
        """)
        card.content_layout.addWidget(self.rf_mapping_input)
        
        return card
    
    def create_button_layout(self):
        """Create action buttons"""
        layout = QHBoxLayout()
        layout.setSpacing(12)
        
        self.save_btn = ModernButton("✅ Save Configuration")
        self.save_btn.clicked.connect(lambda: self.save_config(show_message=True))
        
        self.start_btn = ModernButton("▶️ Start Scraping", primary=True)
        self.start_btn.clicked.connect(self.start_scraping)
        
        self.batch_btn = ModernButton("📋 Batch Scrape")
        self.batch_btn.setStyleSheet("""
            QPushButton {
                padding: 14px 28px;
                border: none;
                border-radius: 10px;
                font-size: 22px;
                font-weight: 600;
                min-height: 35px;
                background-color: #9B59B6;
                color: white;
            }
            QPushButton:hover {
                background-color: #8E44AD;
            }
            QPushButton:pressed {
                background-color: #7D3C98;
            }
            QPushButton:disabled {
                background-color: #D7BDE2;
                color: #F5EEF8;
            }
        """)
        self.batch_btn.clicked.connect(self.start_batch_scraping)
        
        # SEPARATOR - Visual break between tools
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setStyleSheet("color: #BDC3C7; max-width: 2px;")
        separator.setFixedWidth(2)
        
        # Reference Code Search button (SEPARATE)
        self.rf_search_btn = ModernButton("🔍 Start Reference Code Search", primary=True)
        self.rf_search_btn.setStyleSheet("""
            QPushButton {
                padding: 14px 28px;
                border: none;
                border-radius: 10px;
                font-size: 22px;
                font-weight: 600;
                min-height: 35px;
                background-color: #16A085;
                color: white;
            }
            QPushButton:hover {
                background-color: #138D75;
            }
            QPushButton:pressed {
                background-color: #0E6251;
            }
            QPushButton:disabled {
                background-color: #A9DFBF;
                color: #D5F4E6;
            }
        """)
        self.rf_search_btn.clicked.connect(self.start_rf_search)
        
        layout.addWidget(self.save_btn)
        layout.addWidget(self.start_btn)
        layout.addWidget(self.batch_btn)
        layout.addWidget(separator)
        layout.addWidget(self.rf_search_btn)
        
        return layout
    
    def create_progress_card(self):
        """Create progress monitoring card"""
        card = SectionCard("✅ Progress")
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 6px;
                background-color: #ECF0F1;
                height: 8px;
            }
            QProgressBar::chunk {
                border-radius: 6px;
                background-color: #3498DB;
            }
        """)
        self.progress_bar.hide()
        
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setMinimumHeight(400)
        self.log_display.setStyleSheet("""
            QTextEdit {
                background-color: #1E2127;
                color: #ABB2BF;
                border: 2px solid #3E4451;
                border-radius: 12px;
                padding: 24px;
                font-family: 'JetBrains Mono', 'Fira Code', 'SF Mono', 'Monaco', 'Menlo', 'Consolas', monospace;
                font-size: 22px;
                font-weight: 600;
                line-height: 2.0;
                letter-spacing: 0.5px;
            }
        """)
        
        card.content_layout.addWidget(self.progress_bar)
        card.content_layout.addWidget(self.log_display)
        
        return card
    
    def browse_chrome_path(self):
        """Browse for ChromeDriver executable"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select ChromeDriver",
            str(Path.home()),
            "Executable Files (*)"
        )
        if file_path:
            self.chrome_path_input.setText(file_path)
    
    def browse_output_dir(self):
        """Browse for output directory"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            str(Path.home())
        )
        if dir_path:
            self.output_dir_input.setText(dir_path)
    
    def browse_rf_output_dir(self):
        """Browse for RF search output directory"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Reference Code Search Output Directory",
            str(Path.home())
        )
        if dir_path:
            self.rf_output_dir_input.setText(dir_path)
    
    def parse_supporter_map(self):
        """Parse the mapping editor into {hami name: id}. Accepts '=', ':' or ',' as separator."""
        mapping = {}
        for line in self.rf_mapping_input.toPlainText().splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = re.split(r'\s*[=:,]\s*', line, maxsplit=1)
            if len(parts) != 2:
                continue
            name, id_text = parts[0].strip(), parts[1].strip()
            if name and id_text.isdigit():
                mapping[name] = int(id_text)
        return mapping

    def format_supporter_map(self, mapping):
        """Render {hami name: id} back into editor lines."""
        return "\n".join(f"{name} = {value}" for name, value in (mapping or {}).items())

    def get_rf_config(self):
        """Get reference code search configuration from UI"""
        # Get reference codes from text area
        codes_text = self.rf_codes_input.toPlainText().strip()
        reference_codes = [code.strip() for code in codes_text.split('\n') if code.strip()]
        
        # Build config dictionary
        config = self.get_config()  # Get base config (login, chrome path, etc.)
        config.update({
            'reference_codes': reference_codes,
            'output_dir_rf': self.rf_output_dir_input.text(),
            'supporter_map': self.parse_supporter_map(),
            'search_wait_time': int(self.rf_search_wait_input.text() or '5'),
        })
        
        return config, reference_codes
    
    def load_rf_config(self, config):
        """Restore the reference-code section from a loaded config dict"""
        self.rf_output_dir_input.setText(config.get('output_dir_rf', './output_rf'))
        self.rf_search_wait_input.setText(str(config.get('search_wait_time', '5')))
        self.rf_codes_input.setPlainText(config.get('reference_codes_text', '\n'.join(
            str(code) for code in config.get('reference_codes', [])
        )))
        # Keep the raw text so lines the parser could not understand are not lost.
        self.rf_mapping_input.setPlainText(config.get(
            'supporter_map_text',
            self.format_supporter_map(config.get('supporter_map', {}))
        ))
    
    def start_rf_search(self):
        """Start reference code search"""
        if self.scraper_thread and self.scraper_thread.isRunning():
            self.log("⚠️ Date range scraper is already running! Please wait or stop it first.")
            return
        
        if self.batch_thread and self.batch_thread.isRunning():
            self.log("⚠️ Batch scraper is already running! Please wait or stop it first.")
            return
        
        if self.rf_search_thread and self.rf_search_thread.isRunning():
            self.log("⚠️ Reference code search is already running!")
            return
        
        try:
            config, reference_codes = self.get_rf_config()
            
            if not reference_codes:
                self.log("❌ No reference codes provided! Please paste at least one code.")
                return
            
            # Validate configuration
            if not config['username'] or not config['password']:
                self.log("❌ Please provide username and password!")
                return
            
            if not config['chrome_path'] or not Path(config['chrome_path']).exists():
                self.log("❌ Invalid ChromeDriver path!")
                return
            
            # Clear log
            self.log_display.clear()
            self.log(f"🚀 Starting reference code search with {len(reference_codes)} codes...")
            self.log(f"📝 Codes: {', '.join(reference_codes)}")
            
            # Disable RF search button
            self.rf_search_btn.setEnabled(False)
            self.rf_search_btn.setText("⏳ Searching...")
            
            # Show progress bar
            self.progress_bar.setMaximum(0)  # Indeterminate
            self.progress_bar.show()
            
            # Create and start thread
            self.rf_search_thread = SearchByReferenceCodeThread(config, reference_codes)
            self.rf_search_thread.progress.connect(self.log)
            self.rf_search_thread.finished.connect(self.rf_search_finished)
            self.rf_search_thread.start()
            
        except Exception as e:
            self.log(f"❌ Error starting reference code search: {str(e)}")
            self.rf_search_btn.setEnabled(True)
            self.rf_search_btn.setText("🔍 Start Reference Code Search")
            self.progress_bar.hide()
    
    def rf_search_finished(self, success, message):
        """Handle reference code search completion"""
        self.log(message)
        self.rf_search_btn.setEnabled(True)
        self.rf_search_btn.setText("🔍 Start Reference Code Search")
        self.progress_bar.hide()
        
        if success:
            self.log("\n🎉 Reference code search complete! Check your output directory for results.")
    
    def load_pairs(self):
        """Load ID-Name pairs from file or use defaults"""
        if self.pairs_file.exists():
            try:
                with open(self.pairs_file, 'r', encoding='utf-8') as f:
                    self.id_name_pairs = json.load(f)
            except Exception:
                self.id_name_pairs = self.DEFAULT_PAIRS.copy()
        else:
            self.id_name_pairs = self.DEFAULT_PAIRS.copy()
            self.save_pairs()
    
    def save_pairs(self):
        """Save ID-Name pairs to file"""
        try:
            with open(self.pairs_file, 'w', encoding='utf-8') as f:
                json.dump(self.id_name_pairs, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving pairs: {e}")
    
    def populate_pair_selector(self):
        """Populate the pair selector dropdown"""
        self.pair_selector.clear()
        for pair in self.id_name_pairs:
            display_text = f"{pair['id']} - {pair['name']}"
            self.pair_selector.addItem(display_text)
    
    def on_pair_selected(self, index):
        """Handle pair selection from dropdown"""
        if index >= 0 and index < len(self.id_name_pairs):
            pair = self.id_name_pairs[index]
            self.i_value_input.setText(str(pair['id']))
            self.name_value_input.setText(pair['name'])
    
    def show_about(self):
        """Show about dialog"""
        dialog = AboutDialog(self)
        dialog.exec_()
    
    def open_settings(self):
        """Open settings dialog to manage pairs"""
        dialog = SettingsDialog(self.id_name_pairs, self)
        if dialog.exec_() == QDialog.Accepted:
            self.id_name_pairs = dialog.pairs
            self.save_pairs()
            # Remember current selection
            current_i = self.i_value_input.text()
            current_name = self.name_value_input.text()
            # Refresh dropdown
            self.populate_pair_selector()
            # Try to restore selection
            for i, pair in enumerate(self.id_name_pairs):
                if str(pair['id']) == current_i and pair['name'] == current_name:
                    self.pair_selector.setCurrentIndex(i)
                    break
    
    def get_config(self):
        """Get current configuration from UI"""
        return {
            'login_url': self.url_input.text(),
            'username': self.username_input.text(),
            'password': self.password_input.text(),
            'start_date': self.start_date.get_jdate_string(),
            'end_date': self.end_date.get_jdate_string(),
            'i_value': int(self.i_value_input.text() or '0'),
            'name_value': self.name_value_input.text(),
            'chrome_path': self.chrome_path_input.text(),
            'output_dir': self.output_dir_input.text(),
            'file_load_sleep': int(self.file_load_sleep_input.text() or '3'),
            'workflow_load_sleep': int(self.workflow_load_sleep_input.text() or '5'),
            'page_load_sleep': int(self.page_load_sleep_input.text() or '5'),
            'outdate_tolerance': int(self.outdate_tolerance_input.text() or '3')
        }
    
    def save_config(self, show_message=True):
        """Save every field of the UI to the JSON file"""
        try:
            config = self.get_config()
            codes_text = self.rf_codes_input.toPlainText()
            config.update({
                'output_dir_rf': self.rf_output_dir_input.text(),
                'search_wait_time': int(self.rf_search_wait_input.text() or '5'),
                'reference_codes': [c.strip() for c in codes_text.split('\n') if c.strip()],
                'reference_codes_text': codes_text,
                'supporter_map': self.parse_supporter_map(),
                'supporter_map_text': self.rf_mapping_input.toPlainText(),
                'selected_pair_index': self.pair_selector.currentIndex(),
            })
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            if show_message:
                self.log("✅ Configuration saved successfully!")
        except Exception as e:
            if show_message:
                self.log(f"❌ Error saving configuration: {str(e)}")
    
    def load_config(self):
        """Load configuration from JSON file"""
        if not self.config_file.exists():
            return
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Restore the dropdown first: it overwrites the manual fields when it changes.
            index = config.get('selected_pair_index', -1)
            if isinstance(index, int) and 0 <= index < self.pair_selector.count():
                self.pair_selector.setCurrentIndex(index)
            
            self.url_input.setText(config.get('login_url', ''))
            self.username_input.setText(config.get('username', ''))
            self.password_input.setText(config.get('password', ''))
            
            start_parts = config.get('start_date', '1404/07/01').split('/')
            if len(start_parts) == 3:
                self.start_date.set_jdate(int(start_parts[0]), int(start_parts[1]), int(start_parts[2]))
            
            end_parts = config.get('end_date', '1404/08/01').split('/')
            if len(end_parts) == 3:
                self.end_date.set_jdate(int(end_parts[0]), int(end_parts[1]), int(end_parts[2]))
            
            self.i_value_input.setText(str(config.get('i_value', '105001')))
            self.name_value_input.setText(config.get('name_value', ''))
            self.chrome_path_input.setText(config.get('chrome_path', ''))
            self.output_dir_input.setText(config.get('output_dir', './output'))
            
            # Load timing settings
            self.file_load_sleep_input.setText(str(config.get('file_load_sleep', '3')))
            self.workflow_load_sleep_input.setText(str(config.get('workflow_load_sleep', '5')))
            self.page_load_sleep_input.setText(str(config.get('page_load_sleep', '5')))
            self.outdate_tolerance_input.setText(str(config.get('outdate_tolerance', '3')))
            
            self.load_rf_config(config)
            
            self.log("📂 Previous configuration loaded")
        except Exception as e:
            self.log(f"⚠️ Could not load previous configuration: {str(e)}")
    
    def log(self, message):
        """Add message to log display with formatting"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        # Color coding based on message type
        if "❌" in message or "Error" in message.lower():
            color = "#E06C75"  # Red for errors
        elif "✅" in message or "success" in message.lower() or "done" in message.lower():
            color = "#98C379"  # Green for success
        elif "⚠️" in message or "warning" in message.lower():
            color = "#E5C07B"  # Yellow for warnings
        elif "🚀" in message or "Starting" in message.lower():
            color = "#61AFEF"  # Blue for start
        elif "🔧" in message or "🌐" in message or "🔐" in message or "📊" in message or "🧹" in message:
            color = "#C678DD"  # Purple for process steps
        elif "📂" in message:
            color = "#56B6C2"  # Cyan for file operations
        elif "🎉" in message:
            color = "#98C379"  # Green for celebration
        else:
            color = "#ABB2BF"  # Default gray
        
        formatted_message = f'<span style="color: #5C6370; font-size: 18px;">[{timestamp}]</span> <span style="color: {color}; font-size: 24px; font-weight: 600;">{message}</span>'
        self.log_display.append(formatted_message)
        
        # Auto-scroll to bottom
        scrollbar = self.log_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def start_scraping(self):
        """Start the scraping process"""
        if self.scraper_thread and self.scraper_thread.isRunning():
            self.log("⚠️ Scraper is already running!")
            return
        
        try:
            config = self.get_config()
            
            # Validate configuration
            if not config['username'] or not config['password']:
                self.log("❌ Please provide username and password!")
                return
            
            if not config['chrome_path'] or not Path(config['chrome_path']).exists():
                self.log("❌ Invalid ChromeDriver path!")
                return
            
            # Clear log
            self.log_display.clear()
            self.log("🚀 Starting scraper...")
            
            # Disable start button
            self.start_btn.setEnabled(False)
            self.start_btn.setText("⏳ Running...")
            
            # Show progress bar
            self.progress_bar.setMaximum(0)  # Indeterminate
            self.progress_bar.show()
            
            # Create and start thread
            self.scraper_thread = ScraperThread(config)
            self.scraper_thread.progress.connect(self.log)
            self.scraper_thread.finished.connect(self.scraping_finished)
            self.scraper_thread.start()
            
        except Exception as e:
            self.log(f"❌ Error starting scraper: {str(e)}")
            self.start_btn.setEnabled(True)
            self.start_btn.setText("▶️ Start Scraping")
            self.progress_bar.hide()
    
    def scraping_finished(self, success, message):
        """Handle scraping completion"""
        self.log(message)
        self.start_btn.setEnabled(True)
        self.start_btn.setText("▶️ Start Scraping")
        self.progress_bar.hide()
        
        if success:
            # Flash success
            self.log("\n🎉 All done! Check your output directory for results.")
    
    def start_batch_scraping(self):
        """Start batch scraping process"""
        if self.scraper_thread and self.scraper_thread.isRunning():
            self.log("⚠️ Single scraper is already running!")
            return
        
        if self.batch_thread and self.batch_thread.isRunning():
            self.log("⚠️ Batch scraper is already running!")
            return
        
        # Open batch selection dialog
        dialog = BatchScrapingDialog(self.id_name_pairs, self)
        if dialog.exec_() != QDialog.Accepted:
            return
        
        selected_pairs = dialog.selected_pairs
        if not selected_pairs:
            return
        
        try:
            config = self.get_config()
            
            # Validate configuration
            if not config['username'] or not config['password']:
                self.log("❌ Please provide username and password!")
                return
            
            if not config['chrome_path'] or not Path(config['chrome_path']).exists():
                self.log("❌ Invalid ChromeDriver path!")
                return
            
            # Clear log
            self.log_display.clear()
            self.log(f"🚀 Starting batch scraping for {len(selected_pairs)} Hami entries...")
            self.log(f"📋 Queue: {', '.join([p['name'] for p in selected_pairs])}")
            
            # Disable buttons
            self.start_btn.setEnabled(False)
            self.batch_btn.setEnabled(False)
            self.batch_btn.setText("⏳ Batch Running...")
            
            # Show progress bar
            self.progress_bar.setMaximum(0)
            self.progress_bar.show()
            
            # Create and start batch thread
            self.batch_thread = BatchScraperThread(config, selected_pairs)
            self.batch_thread.progress.connect(self.log)
            self.batch_thread.all_finished.connect(self.batch_scraping_finished)
            self.batch_thread.start()
            
        except Exception as e:
            self.log(f"❌ Error starting batch scraper: {str(e)}")
            self.start_btn.setEnabled(True)
            self.batch_btn.setEnabled(True)
            self.batch_btn.setText("📋 Batch Scrape")
            self.progress_bar.hide()
    
    def batch_scraping_finished(self, successful_pairs, failed_pairs):
        """Handle batch scraping completion"""
        self.start_btn.setEnabled(True)
        self.batch_btn.setEnabled(True)
        self.batch_btn.setText("📋 Batch Scrape")
        self.progress_bar.hide()
        
        # Show summary
        self.log("\n" + "="*60)
        self.log("📊 BATCH SCRAPING SUMMARY")
        self.log("="*60)
        
        self.log(f"\n✅ Successful ({len(successful_pairs)}):")
        if successful_pairs:
            for pair in successful_pairs:
                self.log(f"   ✓ {pair['name']} (ID: {pair['id']})")
        else:
            self.log("   (none)")
        
        self.log(f"\n❌ Failed ({len(failed_pairs)}):")
        if failed_pairs:
            for item in failed_pairs:
                self.log(f"   ✗ {item['pair']['name']} (ID: {item['pair']['id']})")
                self.log(f"     Error: {item['error']}")
        else:
            self.log("   (none)")
        
        self.log("\n" + "="*60)
        total = len(successful_pairs) + len(failed_pairs)
        self.log(f"🎉 Batch complete! {len(successful_pairs)}/{total} succeeded.")
        self.log("="*60)


def main():
    app = QApplication(sys.argv)
    
    # Set application-wide font
    font = QFont("SF Pro Display", 14)
    if not font.exactMatch():
        font = QFont("Segoe UI", 14)
    app.setFont(font)
    
    # Set color palette
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#F8F9FA"))
    palette.setColor(QPalette.WindowText, QColor("#2C3E50"))
    app.setPalette(palette)
    
    window = HamiScraperApp()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
