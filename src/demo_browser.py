#!/usr/bin/env python3
"""
Demo script for LinkedIn Job Browser
Shows all features without requiring user interaction.
"""

from job_browser import JobBrowser

DB_PATH = '/home/monsoon/Desktop/LinkedIn Scraper FRFR/data/linkedin_jobs.db'

def demo_browser():
    """Demonstrate all browser features"""
    print("=== LinkedIn Job Browser Demo ===\n")
    
    browser = JobBrowser()
    
    # Check if database exists
    if not browser.get_total_jobs():
        print("No jobs found in database. Please run the scraper first.")
        return
    
    print(f"Database contains {browser.get_total_jobs()} jobs\n")
    
    # 1. Show statistics
    print("1. DATABASE STATISTICS:")
    print("-" * 40)
    browser.show_statistics()
    
    # 2. List recent jobs
    print("\n2. RECENT JOBS (Last 3):")
    print("-" * 40)
    recent_jobs = browser.get_all_jobs(limit=3)
    browser.display_job_list(recent_jobs)
    
    # 3. Show first job in detail
    print("\n3. FIRST JOB DETAILS:")
    print("-" * 40)
    first_job = browser.get_job(1)
    if first_job:
        browser.display_job(first_job)
    
    # 4. Search demo
    print("\n4. SEARCH DEMO:")
    print("-" * 40)
    print("Searching for 'Engineer' in titles...")
    engineer_jobs = browser.search_jobs('Engineer', 'title')
    if engineer_jobs:
        print(f"Found {len(engineer_jobs)} jobs with 'Engineer' in title:")
        browser.display_job_list(engineer_jobs)
    else:
        print("No jobs found with 'Engineer' in title.")
    
    # 5. List all jobs (summary)
    print("\n5. ALL JOBS SUMMARY:")
    print("-" * 40)
    all_jobs = browser.get_all_jobs()
    browser.display_job_list(all_jobs)
    
    print("\n=== Demo Complete ===")
    print("Run 'python job_browser.py' for interactive browsing!")

if __name__ == "__main__":
    demo_browser() 