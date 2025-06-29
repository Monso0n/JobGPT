from playwright.sync_api import sync_playwright
import time
import random
import json
import csv
import sqlite3
from datetime import datetime
import os
import codecs
import urllib.parse

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')

def human_wait(min_time=1, max_time=2):
    wait_time = random.uniform(min_time, max_time)
    print(f"[WAIT] Sleeping for {wait_time:.2f} seconds...")
    time.sleep(wait_time)

def load_cookies(context, cookie_file=None):
    if cookie_file is None:
        cookie_file = os.path.join(DATA_DIR, "cookies.json")
    try:
        with open(cookie_file, "r", encoding='utf-8') as f:
            cookies = json.load(f)
        context.add_cookies(cookies)
        print(f"[COOKIES] Loaded cookies from {cookie_file}")
        return True
    except Exception as e:
        print(f"[COOKIES] Failed to load cookies from {cookie_file}: {e}")
        return False

def is_logged_in(page):
    try:
        page.goto("https://www.linkedin.com/feed/", timeout=15000)
        if page.query_selector("div.feed-identity-module") or page.query_selector("img.global-nav__me-photo"):
            print("[LOGIN] Already logged in!")
            return True
        if not page.query_selector("input[name='session_key']"):
            print("[LOGIN] Already logged in (no login form)!")
            return True
        print("[LOGIN] Not logged in.")
        return False
    except Exception as e:
        print(f"[LOGIN] Error during login check: {e}")
        return False

def manual_login(page, context, cookie_file=None):
    if cookie_file is None:
        cookie_file = os.path.join(DATA_DIR, "cookies.json")
    print(f"[LOGIN] Please log in manually in the opened browser window. Press Enter here when done...")
    input()
    if is_logged_in(page):
        cookies = context.cookies()
        with open(cookie_file, "w", encoding='utf-8') as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
        print(f"[COOKIES] Cookies saved to {cookie_file}")
        return True
    else:
        print("[LOGIN] Login failed. Please try again.")
        return False

def get_search_configuration():
    """Get search configuration from user input"""
    print("\n=== LinkedIn Job Search Configuration ===")
    print()
    
    # Keywords
    print("1. JOB KEYWORDS:")
    print("   Examples: 'software engineer', 'data scientist', 'product manager'")
    keywords = input("Enter job keywords (default: 'software engineer'): ").strip()
    if not keywords:
        keywords = "software engineer"
    
    # Location
    print("\n2. LOCATION:")
    print("   Examples: 'Vancouver, BC', 'Remote', 'United States', 'Toronto'")
    location = input("Enter location (default: 'Canada'): ").strip()
    if not location:
        location = "Canada"
    
    # Date posted
    print("\n3. DATE POSTED:")
    print("   Options: 'Any Time', 'Past 24 hours', 'Past Week', 'Past Month'")
    print("   Enter number: 1=Any Time, 2=Past 24h, 3=Past Week, 4=Past Month")
    date_choice = input("Enter choice (1-4, default: 1): ").strip()
    
    date_mapping = {
        "1": "Any Time",
        "2": "Past 24 hours", 
        "3": "Past Week",
        "4": "Past Month"
    }
    date_posted = date_mapping.get(date_choice, "Any Time")
    
    # Experience level
    print("\n4. EXPERIENCE LEVEL:")
    print("   Options: 'All', 'Internship', 'Entry level', 'Associate', 'Mid-Senior level', 'Director', 'Executive'")
    print("   Enter number: 1=All, 2=Internship, 3=Entry, 4=Associate, 5=Mid-Senior, 6=Director, 7=Executive")
    exp_choice = input("Enter choice (1-7, default: 1): ").strip()
    
    exp_mapping = {
        "1": "All",
        "2": "Internship",
        "3": "Entry level", 
        "4": "Associate",
        "5": "Mid-Senior level",
        "6": "Director",
        "7": "Executive"
    }
    experience_level = exp_mapping.get(exp_choice, "All")
    
    # Job type
    print("\n5. JOB TYPE:")
    print("   Options: 'All', 'Full-time', 'Part-time', 'Contract', 'Temporary', 'Internship'")
    print("   Enter number: 1=All, 2=Full-time, 3=Part-time, 4=Contract, 5=Temporary, 6=Internship")
    type_choice = input("Enter choice (1-6, default: 1): ").strip()
    
    type_mapping = {
        "1": "All",
        "2": "Full-time",
        "3": "Part-time",
        "4": "Contract", 
        "5": "Temporary",
        "6": "Internship"
    }
    job_type = type_mapping.get(type_choice, "All")
    
    # On-site/remote
    print("\n6. WORK MODEL:")
    print("   Options: 'All', 'On-site', 'Remote', 'Hybrid'")
    print("   Enter number: 1=All, 2=On-site, 3=Remote, 4=Hybrid")
    model_choice = input("Enter choice (1-4, default: 1): ").strip()
    
    model_mapping = {
        "1": "All",
        "2": "On-site",
        "3": "Remote",
        "4": "Hybrid"
    }
    work_model = model_mapping.get(model_choice, "All")
    
    config = {
        "keywords": keywords,
        "location": location,
        "date_posted": date_posted,
        "experience_level": experience_level,
        "job_type": job_type,
        "work_model": work_model
    }
    
    print(f"\n=== Search Configuration Summary ===")
    print(f"Keywords: {keywords}")
    print(f"Location: {location}")
    print(f"Date Posted: {date_posted}")
    print(f"Experience Level: {experience_level}")
    print(f"Job Type: {job_type}")
    print(f"Work Model: {work_model}")
    print()
    
    confirm = input("Proceed with this configuration? (y/n, default: y): ").strip().lower()
    if confirm in ['n', 'no']:
        return get_search_configuration()
    
    return config

def build_linkedin_url(config):
    """Build LinkedIn search URL with the given configuration"""
    base_url = "https://www.linkedin.com/jobs/search/"
    
    # Build query parameters
    params = {}
    
    # Keywords
    if config["keywords"]:
        params["keywords"] = config["keywords"]
    
    # Location
    if config["location"]:
        params["location"] = config["location"]
    
    # Date posted (LinkedIn uses specific values)
    date_mapping = {
        "Any Time": "",  # No filter for any time
        "Past 24 hours": "r86400",
        "Past Week": "r604800",  # 7 days in seconds
        "Past Month": "r2592000"  # 30 days in seconds
    }
    if config["date_posted"] in date_mapping and date_mapping[config["date_posted"]]:
        params["f_TPR"] = date_mapping[config["date_posted"]]
    
    # Experience level
    exp_mapping = {
        "All": "",
        "Internship": "1",
        "Entry level": "2",
        "Associate": "3", 
        "Mid-Senior level": "4",
        "Director": "5",
        "Executive": "6"
    }
    if config["experience_level"] in exp_mapping and exp_mapping[config["experience_level"]]:
        params["f_E"] = exp_mapping[config["experience_level"]]
    
    # Job type
    type_mapping = {
        "All": "",
        "Full-time": "F",
        "Part-time": "P",
        "Contract": "C",
        "Temporary": "T",
        "Internship": "I"
    }
    if config["job_type"] in type_mapping and type_mapping[config["job_type"]]:
        params["f_JT"] = type_mapping[config["job_type"]]
    
    # Work model
    model_mapping = {
        "All": "",
        "On-site": "1",
        "Remote": "2",
        "Hybrid": "3"
    }
    if config["work_model"] in model_mapping and model_mapping[config["work_model"]]:
        params["f_WT"] = model_mapping[config["work_model"]]
    
    # Build URL
    if params:
        query_string = urllib.parse.urlencode(params)
        url = f"{base_url}?{query_string}"
    else:
        url = base_url
    
    return url

def setup_database():
    """Setup SQLite database"""
    try:
        db_path = os.path.join(DATA_DIR, 'linkedin_jobs.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create jobs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                location TEXT,
                description TEXT,
                url TEXT UNIQUE,
                search_keywords TEXT,
                search_location TEXT,
                search_date_posted TEXT,
                search_experience_level TEXT,
                search_job_type TEXT,
                search_work_model TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'new',
                liked BOOLEAN DEFAULT 0,
                resume_created BOOLEAN DEFAULT 0,
                cover_letter_created BOOLEAN DEFAULT 0,
                applied BOOLEAN DEFAULT 0,
                notes TEXT,
                salary_min REAL,
                salary_max REAL,
                salary_currency TEXT,
                job_type TEXT,
                experience_level TEXT,
                work_model TEXT
            )
        ''')
        
        # Create job status history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS job_status_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER,
                status TEXT,
                changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (job_id) REFERENCES jobs (id)
            )
        ''')
        
        # Create search history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keywords TEXT,
                location TEXT,
                date_posted TEXT,
                experience_level TEXT,
                job_type TEXT,
                work_model TEXT,
                jobs_found INTEGER,
                jobs_scraped INTEGER,
                search_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        print("[DB] Database setup complete")
        return conn, cursor
    except Exception as e:
        print(f"[DB ERROR] Failed to setup database: {e}")
        return None, None

def save_to_database(cursor, conn, job_data):
    """Save job data to SQLite database with duplicate checking"""
    try:
        # Check if job already exists by title and company (more reliable than URL)
        check_query = "SELECT id FROM jobs WHERE title = ? AND company = ?"
        cursor.execute(check_query, (job_data.get('title'), job_data.get('company')))
        existing_job = cursor.fetchone()
        
        if existing_job:
            print(f"[DB] Job already exists in database (ID: {existing_job[0]}) - skipping")
            return existing_job[0]
        
        # Also check by URL as backup
        check_url_query = "SELECT id FROM jobs WHERE url = ?"
        cursor.execute(check_url_query, (job_data.get('url'),))
        existing_job_by_url = cursor.fetchone()
        
        if existing_job_by_url:
            print(f"[DB] Job with this URL already exists (ID: {existing_job_by_url[0]}) - skipping")
            return existing_job_by_url[0]
        
        # Insert new job with search fields
        insert_query = """
        INSERT INTO jobs (title, company, location, description, url, search_keywords, search_location, search_date_posted, search_experience_level, search_job_type, search_work_model)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        cursor.execute(insert_query, (
            job_data.get('title'),
            job_data.get('company'),
            job_data.get('location'),
            job_data.get('description'),
            job_data.get('url'),
            job_data.get('search_keywords'),
            job_data.get('search_location'),
            job_data.get('search_date_posted'),
            job_data.get('experience_level'),
            job_data.get('job_type'),
            job_data.get('work_model')
        ))
        
        job_id = cursor.lastrowid
        conn.commit()
        print(f"[DB] Saved new job to database with ID: {job_id}")
        return job_id
        
    except sqlite3.IntegrityError as e:
        if "UNIQUE constraint failed" in str(e):
            print(f"[DB] Job with this URL already exists - skipping")
            return None
        else:
            print(f"[DB] Database integrity error: {e}")
            conn.rollback()
            return None
    except Exception as e:
        print(f"[DB] Error saving to database: {e}")
        conn.rollback()
        return None

def scrape_linkedin_jobs(cookie_file=None, num_jobs=5, search_config=None):
    if cookie_file is None:
        cookie_file = os.path.join(DATA_DIR, "cookies.json")
    # Setup database
    db_conn, db_cursor = setup_database()
    if not db_conn:
        print("[WARNING] Database connection failed. Jobs will only be saved to files.")
    
    # Get search configuration if not provided
    if not search_config:
        search_config = get_search_configuration()
    
    # Build the search URL
    search_url = build_linkedin_url(search_config)
    print(f"[SEARCH] Using URL: {search_url}")
    
    with sync_playwright() as p:
        print("[BROWSER] Launching browser in headful mode...")
        browser = p.chromium.launch(headless=False, slow_mo=50)
        context = browser.new_context()
        page = context.new_page()

        # Try to load cookies and check login
        load_cookies(context, cookie_file)
        page = context.new_page()
        if not is_logged_in(page):
            page.goto("https://www.linkedin.com/login")
            if not manual_login(page, context, cookie_file):
                print("[EXIT] Could not log in. Exiting.")
                browser.close()
                return
        else:
            print("[LOGIN] Using existing session.")

        print(f"[NAVIGATE] Going to LinkedIn jobs page with custom search...")
        page.goto(search_url)
        human_wait(1, 2 )

        job_data = []
        jobs_scraped = 0
        current_page = 1
        max_pages = 50  # Increased limit to get more jobs
        consecutive_errors = 0  # Track consecutive errors to avoid infinite loops

        while jobs_scraped < num_jobs and current_page <= max_pages:
            print(f"\n[PAGE] Processing page {current_page}...")
            
            # Scroll to load more jobs if needed
            if current_page == 1:
                print(f"[SCROLL] Scrolling to load more jobs...")
                for scroll_attempt in range(3):
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    human_wait(1, 2 )
                    print(f"[SCROLL] Scroll attempt {scroll_attempt + 1}/3")
            
            # Try multiple selectors for job cards
            job_cards = []
            selectors_to_try = [
                # Modern LinkedIn selectors
                "ul.jobs-search__results-list li",
                ".job-card-container",
                "[data-occludable-job-id]",
                # Your collected selector pattern
                "li[id^='ember'] > div:nth-child(1) > div:nth-child(1)",
                # Alternative selectors
                ".job-search-card",
                ".job-card",
                "li[data-job-id]",
                "[data-test-job-card]",
                # More generic selectors
                "li:has([data-job-id])",
                "li:has(.job-card-container)",
                # Try to find by role
                "[role='listitem']",
                # Fallback to any clickable job elements
                "li:has(a[href*='/jobs/'])",
                "div:has(a[href*='/jobs/'])"
            ]
            
            for selector in selectors_to_try:
                print(f"[SELECTOR] Trying selector: {selector}")
                job_cards = page.query_selector_all(selector)
                if job_cards:
                    print(f"[SUCCESS] Found {len(job_cards)} job cards with selector: {selector}")
                    
                    # Debug: Show first few job cards
                    for i, card in enumerate(job_cards[:3]):
                        try:
                            card_text = card.inner_text()[:100] + "..." if len(card.inner_text()) > 100 else card.inner_text()
                            print(f"[DEBUG] Job card {i}: {card_text}")
                        except:
                            print(f"[DEBUG] Job card {i}: [Could not extract text]")
                    
                    break
                else:
                    print(f"[FAILED] No job cards found with selector: {selector}")

            if not job_cards:
                print(f"[WARNING] No job cards found on page {current_page}")
                
                # Debug: Try to find any job-related elements
                print(f"[DEBUG] Looking for any job-related elements...")
                all_links = page.query_selector_all("a[href*='/jobs/']")
                print(f"[DEBUG] Found {len(all_links)} job links on page")
                
                # Try to find job list container
                job_list = page.query_selector("ul.jobs-search__results-list, .jobs-search__results-list, [role='list']")
                if job_list:
                    print(f"[DEBUG] Found job list container")
                    list_items = job_list.query_selector_all("li")
                    print(f"[DEBUG] Job list has {len(list_items)} items")
                else:
                    print(f"[DEBUG] No job list container found")
                
                consecutive_errors += 1
                if consecutive_errors >= 3:
                    print(f"[ERROR] Too many consecutive errors, stopping...")
                    break
                continue
            else:
                consecutive_errors = 0  # Reset error counter on success

            print(f"[SCRAPE] Found {len(job_cards)} job cards on page {current_page}")
            
            # Calculate how many jobs to scrape from this page
            jobs_needed = num_jobs - jobs_scraped
            jobs_on_this_page = min(jobs_needed, len(job_cards))
            
            print(f"[SCRAPE] Will scrape {jobs_on_this_page} jobs from page {current_page}")
            print(f"[SCRAPE] Total jobs needed: {num_jobs}, already scraped: {jobs_scraped}")
            
            # Scrape jobs from current page
            for i, job in enumerate(job_cards[:jobs_on_this_page]):
                print(f"\n[SCRAPE] Processing job {jobs_scraped + i + 1}/{num_jobs} (page {current_page})...")
                
                try:
                    # Click on the job card to load details
                    print(f"[CLICK] Clicking job card...")
                    job.click()
                    human_wait(1, 2 )

                    
                    # Wait for job details to load
                    print(f"[WAIT] Waiting for job details to load...")
                    try:
                        # Wait for job title to appear
                        page.wait_for_selector("h1", timeout=10000)
                        print(f"[SUCCESS] Job details loaded")
                    except:
                        print(f"[WARNING] Job details might not have loaded completely")
                    
                    # Extract job data
                    print(f"[EXTRACT] Extracting job data...")
                    
                    # Title - try multiple selectors
                    title = None
                    title_selectors = [
                        "h1",
                        ".job-details-jobs-unified-top-card__job-title",
                        "h1.jobs-unified-top-card__job-title"
                    ]
                    for selector in title_selectors:
                        title_elem = page.query_selector(selector)
                        if title_elem:
                            title = title_elem.inner_text().strip()
                            print(f"[TITLE] Found with selector: {selector}")
                            break
                    
                    # Company - try multiple selectors
                    company = None
                    company_selectors = [
                        ".job-details-jobs-unified-top-card__company-name",
                        ".jobs-unified-top-card__company-name",
                        "span[data-test-id='company-name']"
                    ]
                    for selector in company_selectors:
                        try:
                            company_elem = page.query_selector(selector)
                            if company_elem:
                                company = company_elem.inner_text().strip()
                                if company and company != "new feed updates notifications":
                                    print(f"[COMPANY] Found in job details with selector: {selector}")
                                    break
                        except:
                            continue
                    
                    # If still not found, try to extract from URL or other sources
                    if not company or company == "new feed updates notifications":
                        # Try to get company from the job card's HTML structure
                        try:
                            job_html = job.inner_html()
                            # Look for company name patterns in the HTML
                            if 'company-name' in job_html:
                                # Try to find company name in the HTML structure
                                company_elem = job.query_selector("[class*='company']")
                                if company_elem:
                                    company = company_elem.inner_text().strip()
                                    print(f"[COMPANY] Found using class pattern")
                        except:
                            pass
                    
                    # Final fallback - try to get from page title or breadcrumb
                    if not company or company == "new feed updates notifications":
                        try:
                            # Try to get from page title
                            page_title = page.title()
                            if " at " in page_title:
                                company = page_title.split(" at ")[-1].split(" | ")[0].strip()
                                print(f"[COMPANY] Extracted from page title")
                        except:
                            pass
                    
                    # Location - extract actual job location only
                    location = None
                    
                    print(f"[LOCATION] Extracting actual job location...")
                    print(f"[LOCATION] Search location is: '{search_config['location']}'")
                    
                    # Method 1: Try to get location from job card BEFORE clicking (most reliable)
                    print(f"[LOCATION] Method 1: Extracting from job card...")
                    try:
                        # Look for location in the job card's text content
                        card_text = job.inner_text()
                        print(f"[LOCATION] Job card text: {card_text[:200]}...")
                        
                        # Split by lines and look for location patterns
                        lines = card_text.split('\n')
                        for line in lines:
                            line = line.strip()
                            if line and len(line) > 3:
                                # Look for Canadian location patterns
                                if ("," in line and 
                                    any(province in line.lower() for province in ["on", "qc", "bc", "ab", "mb", "sk", "ns", "nb", "pe", "nl", "nt", "nu", "yt"]) and
                                    line != search_config["location"] and
                                    not line.startswith(search_config["location"])):
                                    location = line
                                    print(f"[LOCATION] ✅ Found in job card: '{location}'")
                                    break
                    except Exception as e:
                        print(f"[LOCATION] Error extracting from job card: {e}")
                    
                    # Method 2: Try specific location selectors in job details
                    if not location:
                        print(f"[LOCATION] Method 2: Checking job details...")
                        location_selectors = [
                            ".job-details-jobs-unified-top-card__location",
                            ".jobs-unified-top-card__location",
                            "span.jobs-unified-top-card__bullet",
                            "span.jobs-details-top-card__bullet",
                            "[data-test-id='job-location']"
                        ]
                        
                        for selector in location_selectors:
                            try:
                                location_elem = page.query_selector(selector)
                                if location_elem:
                                    location_text = location_elem.inner_text().strip()
                                    print(f"[LOCATION] Found with selector '{selector}': '{location_text}'")
                                    
                                    # Only accept if it looks like a real location
                                    if (location_text and 
                                        location_text != search_config["location"] and
                                        not location_text.startswith(search_config["location"]) and
                                        location_text.lower() not in ["city, state, or zip code", "location", "remote", "on-site", "hybrid"] and
                                        len(location_text) > 3 and
                                        ("," in location_text or 
                                         any(province in location_text.lower() for province in ["on", "qc", "bc", "ab", "mb", "sk", "ns", "nb", "pe", "nl", "nt", "nu", "yt"]))):
                                        location = location_text
                                        print(f"[LOCATION] ✅ ACCEPTED from job details: '{location}'")
                                        break
                                    else:
                                        print(f"[LOCATION] ❌ REJECTED: '{location_text}' (not a real location)")
                            except Exception as e:
                                print(f"[LOCATION] Error with selector {selector}: {e}")
                                continue
                    
                    # Method 3: Look for location in all spans on the page
                    if not location:
                        print(f"[LOCATION] Method 3: Scanning all spans for location...")
                        try:
                            all_spans = page.query_selector_all("span")
                            for i, span in enumerate(all_spans):
                                try:
                                    span_text = span.inner_text().strip()
                                    if (span_text and 
                                        len(span_text) > 5 and 
                                        "," in span_text and
                                        span_text != search_config["location"] and
                                        not span_text.startswith(search_config["location"]) and
                                        any(province in span_text.lower() for province in ["on", "qc", "bc", "ab", "mb", "sk", "ns", "nb", "pe", "nl", "nt", "nu", "yt"])):
                                        location = span_text
                                        print(f"[LOCATION] ✅ Found in span {i}: '{location}'")
                                        break
                                except:
                                    continue
                        except Exception as e:
                            print(f"[LOCATION] Error scanning spans: {e}")
                    
                    # Method 4: Try to extract from URL
                    if not location:
                        print(f"[LOCATION] Method 4: Extracting from URL...")
                        try:
                            if "/jobs/" in job_url:
                                url_parts = job_url.split("/")
                                for i, part in enumerate(url_parts):
                                    if part == "jobs" and i + 2 < len(url_parts):
                                        potential_location = url_parts[i + 2].replace("-", " ").title()
                                        if potential_location and potential_location != search_config["location"]:
                                            location = potential_location
                                            print(f"[LOCATION] ✅ Extracted from URL: '{location}'")
                                            break
                        except Exception as e:
                            print(f"[LOCATION] Error extracting from URL: {e}")
                    
                    # Final fallback
                    if not location:
                        location = "Location not specified"
                        print(f"[LOCATION] ❌ No location found, using placeholder")
                    
                    print(f"[LOCATION] Final location: '{location}'")
                    
                    # Description - try multiple selectors
                    description = None
                    description_selectors = [
                        "div.jobs-description-content__text",
                        "div.jobs-box__html-content",
                        "main#main > div:nth-child(1) > div:nth-child(2) > div:nth-child(2) > div:nth-child(1) > div:nth-child(2) > div:nth-child(1) > div:nth-child(2) > div:nth-child(1) > div:nth-child(1)",  # Your collected selector
                        ".jobs-description__content"
                    ]
                    for selector in description_selectors:
                        desc_elem = page.query_selector(selector)
                        if desc_elem:
                            description = desc_elem.inner_text().strip()
                            print(f"[DESCRIPTION] Found with selector: {selector}")
                            break

                    # Get current URL (job link)
                    job_url = page.url
                    print(f"[URL] Job URL: {job_url}")

                    job_info = {
                        "title": title,
                        "company": company,
                        "location": location,
                        "description": description,  # Save full description without truncation
                        "url": job_url,
                        "search_keywords": search_config["keywords"],
                        "search_location": search_config["location"],
                        "search_date_posted": search_config["date_posted"],
                        "experience_level": search_config["experience_level"],
                        "job_type": search_config["job_type"],
                        "work_model": search_config["work_model"]
                    }

                    job_data.append(job_info)
                    
                    # Save to database if connection is available
                    if db_conn and db_cursor:
                        save_to_database(db_cursor, db_conn, job_info)
                    
                    print(f"\n[SUCCESS] Scraped job data:")
                    print(f"  Title: {title}")
                    print(f"  Company: {company}")
                    print(f"  Location: {location}")
                    print(f"  Description length: {len(description) if description else 0} characters")
                    print(f"  Description preview: {description[:200] + '...' if description and len(description) > 200 else description}")
                    print(f"  URL: {job_url}")
                    
                except Exception as e:
                    print(f"[ERROR] Error scraping job: {e}")
                    # Try to refresh the page if we get stale element errors
                    if "Element is not attached to the DOM" in str(e):
                        print(f"[RECOVERY] Attempting to refresh page due to stale elements...")
                        try:
                            page.reload()
                            human_wait(1, 2)

                            # Re-find job cards after refresh
                            job_cards = page.query_selector_all("li[id^='ember'] > div:nth-child(1) > div:nth-child(1)")
                            if job_cards and i < len(job_cards):
                                job = job_cards[i]
                                print(f"[RECOVERY] Successfully refreshed and re-found job card")
                            else:
                                print(f"[RECOVERY] Could not re-find job card after refresh, skipping...")
                                continue
                        except Exception as refresh_error:
                            print(f"[RECOVERY] Failed to refresh page: {refresh_error}")
                            continue
                
            human_wait(1, 2 )

            # Update jobs scraped count
            jobs_scraped += jobs_on_this_page
            print(f"\n[PROGRESS] Scraped {jobs_scraped}/{num_jobs} jobs so far")
            
            # Check if we need more jobs and if there's a next page
            if jobs_scraped < num_jobs:
                print(f"[PAGINATION] Looking for next page...")
                
                # Try to find and click the next page button
                next_page_found = False
                next_page_selectors = [
                    # Modern LinkedIn selectors
                    "button[aria-label='Next']",
                    "button[aria-label='Next page']",
                    "button.artdeco-pagination__button--next",
                    "button[data-test-pagination-page-btn]",
                    "a[aria-label='Next']",
                    "a[aria-label='Next page']",
                    # More specific selectors
                    "button[aria-label='Next']:not([disabled])",
                    ".artdeco-pagination__button--next:not([disabled])",
                    "li.artdeco-pagination__indicator--active + li button",
                    # Alternative selectors
                    "[data-test-pagination-page-btn='next']",
                    "button[aria-label*='Next']",
                    "a[aria-label*='Next']",
                    # Generic pagination
                    ".pagination__next",
                    ".pagination-next",
                    "button:contains('Next')",
                    # Try to find by text content
                    "button:has-text('Next')",
                    "a:has-text('Next')"
                ]
                
                # Debug: Print current page info
                print(f"[PAGINATION] Current page: {current_page}")
                print(f"[PAGINATION] Jobs scraped so far: {jobs_scraped}")
                
                # First, try to find any pagination elements
                pagination_elements = page.query_selector_all("[class*='pagination'], [class*='Pagination']")
                print(f"[PAGINATION] Found {len(pagination_elements)} pagination elements")
                
                for i, elem in enumerate(pagination_elements):
                    try:
                        text = elem.inner_text()
                        print(f"[PAGINATION] Element {i}: '{text}'")
                    except:
                        pass
                
                for selector in next_page_selectors:
                    try:
                        next_button = page.query_selector(selector)
                        if next_button:
                            print(f"[PAGINATION] Found element with selector: {selector}")
                            print(f"[PAGINATION] Element text: '{next_button.inner_text()}'")
                            print(f"[PAGINATION] Element visible: {next_button.is_visible()}")
                            print(f"[PAGINATION] Element disabled: {next_button.get_attribute('disabled')}")
                            
                            if next_button.is_visible() and not next_button.get_attribute("disabled"):
                                print(f"[PAGINATION] Clicking next page button: {selector}")
                                next_button.click()
                                human_wait(3, 5)  # Wait longer for page load
                                current_page += 1
                                next_page_found = True
                                print(f"[PAGINATION] Successfully moved to page {current_page}")
                                break
                            else:
                                print(f"[PAGINATION] Button found but not clickable (visible: {next_button.is_visible()}, disabled: {next_button.get_attribute('disabled')})")
                    except Exception as e:
                        print(f"[PAGINATION] Error with selector {selector}: {e}")
                        continue
                
                # If no next button found, try alternative approach
                if not next_page_found:
                    print(f"[PAGINATION] Trying alternative pagination detection...")
                    
                    # Try to find pagination by looking for page numbers
                    try:
                        page_numbers = page.query_selector_all("[class*='pagination'] button, [class*='Pagination'] button")
                        print(f"[PAGINATION] Found {len(page_numbers)} pagination buttons")
                        
                        for i, btn in enumerate(page_numbers):
                            try:
                                btn_text = btn.inner_text().strip()
                                print(f"[PAGINATION] Button {i}: '{btn_text}'")
                                
                                # Look for next page number or "Next" text
                                if btn_text.isdigit() and int(btn_text) == current_page + 1:
                                    print(f"[PAGINATION] Found next page number: {btn_text}")
                                    btn.click()
                                    human_wait(1, 2)

                                    current_page += 1
                                    next_page_found = True
                                    break
                                elif "next" in btn_text.lower():
                                    print(f"[PAGINATION] Found 'Next' button: {btn_text}")
                                    btn.click()
                                    human_wait(2,3)
                                    current_page += 1
                                    next_page_found = True
                                    break
                            except Exception as e:
                                print(f"[PAGINATION] Error checking button {i}: {e}")
                                continue
                    except Exception as e:
                        print(f"[PAGINATION] Error in alternative detection: {e}")
                
                if not next_page_found:
                    print(f"[PAGINATION] No next page found. Reached end of results.")
                    print(f"[INFO] Total jobs scraped: {jobs_scraped}")
                    print(f"[INFO] Current page: {current_page}")
                    
                    # Try to get total job count from page
                    try:
                        total_jobs_elem = page.query_selector("[class*='results-context'], [class*='search-results']")
                        if total_jobs_elem:
                            total_text = total_jobs_elem.inner_text()
                            print(f"[INFO] Page shows: {total_text}")
                    except:
                        pass
                    
                    print(f"[INFO] This might be all available jobs for this search.")
                    break
            else:
                print(f"[COMPLETE] Reached target number of jobs ({num_jobs})")
                break

        # Save results to files with proper UTF-8 encoding
        print(f"\n[SAVE] Saving {len(job_data)} jobs to files...")
        
        # Save to JSON
        with open(os.path.join(DATA_DIR, "linkedin_jobs.json"), "w", encoding='utf-8') as f:
            json.dump(job_data, f, ensure_ascii=False, indent=2)
        print("[SAVE] Saved to data/linkedin_jobs.json")
        
        # Save to CSV
        with open(os.path.join(DATA_DIR, "linkedin_jobs.csv"), "w", newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['title', 'company', 'location', 'description', 'url', 'search_keywords', 'search_location', 'search_date_posted', 'experience_level', 'job_type', 'work_model'])
            writer.writeheader()
            for job in job_data:
                writer.writerow(job)
        print("[SAVE] Saved to data/linkedin_jobs.csv")

        print(f"\n[COMPLETE] Scraped {len(job_data)} jobs from {current_page} page(s)!")
        print(f"[SEARCH] Search criteria: {search_config['keywords']} in {search_config['location']}")
        
        # Close database connection
        if db_conn:
            db_conn.close()
            print("[DB] SQLite database connection closed")
        
        print("[BROWSER] Browser will remain open for manual inspection. Close it when done.")
        print("[BROWSER] Press Enter to close the browser...")
        input()  # Wait for user input before closing
        browser.close()

if __name__ == "__main__":
    # Choose which account to use
    print("Choose LinkedIn account:")
    print("1. Main account (data/cookies.json)")
    print("2. Second account (data/cookies2.json)")
    choice = input("Choose account (1 or 2, default: 1): ").strip()
    
    if choice == "2":
        cookie_file = os.path.join(DATA_DIR, 'cookies2.json')
    else:
        cookie_file = os.path.join(DATA_DIR, 'cookies.json')
    
    # Get number of jobs to scrape
    try:
        num_jobs = int(input("How many jobs to scrape? (default 5): ").strip() or "5")
    except ValueError:
        num_jobs = 5
    
    print(f"[SCRAPE] Will scrape {num_jobs} jobs")
    scrape_linkedin_jobs(cookie_file, num_jobs)
