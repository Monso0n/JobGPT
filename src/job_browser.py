#!/usr/bin/env python3
"""
LinkedIn Job Browser - Console Interface
Interactive console application to browse and manage scraped LinkedIn jobs.
"""

import sqlite3
import os
import sys
from datetime import datetime

DB_PATH = '/home/monsoon/Desktop/LinkedIn Scraper FRFR/data/linkedin_jobs.db'

class JobBrowser:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.current_job_id = None
        self.total_jobs = 0
        
    def connect_db(self):
        """Connect to the SQLite database"""
        try:
            if not os.path.exists(self.db_path):
                print(f"[ERROR] Database file '{self.db_path}' not found!")
                print("Please run the scraper first to create the database.")
                return None
                
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # This allows column access by name
            return conn
        except Exception as e:
            print(f"[ERROR] Failed to connect to database: {e}")
            return None
    
    def get_total_jobs(self):
        """Get total number of jobs in database"""
        conn = self.connect_db()
        if not conn:
            return 0
            
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM jobs")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            print(f"[ERROR] Failed to get job count: {e}")
            conn.close()
            return 0
    
    def get_job(self, job_id):
        """Get a specific job by ID"""
        conn = self.connect_db()
        if not conn:
            return None
            
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
            job = cursor.fetchone()
            conn.close()
            return job
        except Exception as e:
            print(f"[ERROR] Failed to get job {job_id}: {e}")
            conn.close()
            return None
    
    def get_all_jobs(self, limit=None):
        """Get all jobs with optional limit"""
        conn = self.connect_db()
        if not conn:
            return []
            
        try:
            cursor = conn.cursor()
            if limit:
                cursor.execute("SELECT * FROM jobs ORDER BY id DESC LIMIT ?", (limit,))
            else:
                cursor.execute("SELECT * FROM jobs ORDER BY id DESC")
            jobs = cursor.fetchall()
            conn.close()
            return jobs
        except Exception as e:
            print(f"[ERROR] Failed to get jobs: {e}")
            conn.close()
            return []
    
    def search_jobs(self, query, field='title'):
        """Search jobs by field"""
        conn = self.connect_db()
        if not conn:
            return []
            
        try:
            cursor = conn.cursor()
            search_query = f"SELECT * FROM jobs WHERE {field} LIKE ? ORDER BY id DESC"
            cursor.execute(search_query, (f'%{query}%',))
            jobs = cursor.fetchall()
            conn.close()
            return jobs
        except Exception as e:
            print(f"[ERROR] Failed to search jobs: {e}")
            conn.close()
            return []
    
    def display_job(self, job):
        """Display a single job in a formatted way"""
        if not job:
            print("[ERROR] No job data to display")
            return
            
        print("\n" + "="*80)
        print(f"JOB ID: {job['id']}")
        print("="*80)
        print(f"Title: {job['title']}")
        print(f"Company: {job['company']}")
        print(f"Location: {job['location']}")
        print(f"Scraped: {job['scraped_at']}")
        
        # Display search information if available
        if 'search_keywords' in job and job['search_keywords']:
            print(f"Search Keywords: {job['search_keywords']}")
        if 'search_location' in job and job['search_location']:
            print(f"Search Location: {job['search_location']}")
        if 'search_date_posted' in job and job['search_date_posted']:
            print(f"Date Filter: {job['search_date_posted']}")
        
        print(f"URL: {job['url']}")
        print("-"*80)
        print("DESCRIPTION:")
        print("-"*80)
        
        # Display description with preserved newlines and word wrapping
        description = job['description'] or "No description available"
        
        # Split by newlines first to preserve paragraph structure
        paragraphs = description.split('\n')
        
        for paragraph in paragraphs:
            if paragraph.strip():  # Only process non-empty paragraphs
                # Word wrap within each paragraph
                words = paragraph.split()
                line_length = 0
                max_line_length = 78
                
                for word in words:
                    if line_length + len(word) + 1 > max_line_length:
                        print()
                        line_length = 0
                    if line_length == 0:
                        print(word, end='')
                        line_length = len(word)
                    else:
                        print(f" {word}", end='')
                        line_length += len(word) + 1
                print()  # Add newline after each paragraph
            else:
                print()  # Add blank line for empty paragraphs
        
        print("="*80)
    
    def display_job_list(self, jobs, show_details=False):
        """Display a list of jobs"""
        if not jobs:
            print("No jobs found.")
            return
            
        print(f"\nFound {len(jobs)} job(s):")
        print("-" * 120)
        
        for job in jobs:
            # Basic job info
            print(f"ID: {job['id']:3d} | {job['title'][:40]:<40} | {job['company'][:20]:<20} | {job['location'][:15]:<15}")
            
            # Show search info if available
            if show_details and 'search_keywords' in job and job['search_keywords']:
                print(f"     Search: '{job['search_keywords']}' in {job.get('search_location', 'Unknown')} ({job.get('search_date_posted', 'Any Time')})")
                print(f"     URL: {job['url']}")
                print(f"     Scraped: {job['scraped_at']}")
                print("-" * 120)
    
    def browse_jobs(self):
        """Interactive job browser"""
        self.total_jobs = self.get_total_jobs()
        
        if self.total_jobs == 0:
            print("No jobs found in database. Please run the scraper first.")
            return
        
        print(f"\n=== LinkedIn Job Browser ===")
        print(f"Total jobs in database: {self.total_jobs}")
        
        # Start with the most recent job
        latest_job = self.get_job(self.total_jobs)
        if latest_job:
            self.current_job_id = latest_job['id']
        
        while True:
            if self.current_job_id:
                current_job = self.get_job(self.current_job_id)
                if current_job:
                    self.display_job(current_job)
            
            print(f"\nCurrent job: {self.current_job_id}/{self.total_jobs}")
            print("\nNavigation:")
            print("  n - Next job")
            print("  p - Previous job")
            print("  f - First job")
            print("  l - Last job")
            print("  g - Go to specific job ID")
            print("  s - Search jobs")
            print("  a - List all jobs")
            print("  r - Recent jobs (last 10)")
            print("  q - Quit")
            
            choice = input("\nEnter choice: ").strip().lower()
            
            if choice == 'q':
                print("Goodbye!")
                break
            elif choice == 'n':
                if self.current_job_id and self.current_job_id < self.total_jobs:
                    self.current_job_id += 1
                else:
                    print("Already at the last job.")
            elif choice == 'p':
                if self.current_job_id and self.current_job_id > 1:
                    self.current_job_id -= 1
                else:
                    print("Already at the first job.")
            elif choice == 'f':
                self.current_job_id = 1
            elif choice == 'l':
                self.current_job_id = self.total_jobs
            elif choice == 'g':
                try:
                    job_id = int(input("Enter job ID: "))
                    if 1 <= job_id <= self.total_jobs:
                        self.current_job_id = job_id
                    else:
                        print(f"Job ID must be between 1 and {self.total_jobs}")
                except ValueError:
                    print("Please enter a valid number.")
            elif choice == 's':
                self.search_interface()
            elif choice == 'a':
                self.list_all_jobs()
            elif choice == 'r':
                self.list_recent_jobs()
            else:
                print("Invalid choice. Please try again.")
    
    def search_interface(self):
        """Interactive search interface"""
        print("\n=== Search Jobs ===")
        print("Search fields: title, company, location, description, search_keywords, search_location")
        
        field = input("Search in field (default: title): ").strip().lower()
        if not field or field not in ['title', 'company', 'location', 'description', 'search_keywords', 'search_location']:
            field = 'title'
        
        query = input(f"Enter search term for {field}: ").strip()
        if not query:
            print("No search term entered.")
            return
        
        jobs = self.search_jobs(query, field)
        if jobs:
            print(f"\nFound {len(jobs)} job(s) matching '{query}' in {field}:")
            self.display_job_list(jobs)
            
            if len(jobs) == 1:
                choice = input("\nView this job? (y/n): ").strip().lower()
                if choice == 'y':
                    self.current_job_id = jobs[0]['id']
        else:
            print(f"No jobs found matching '{query}' in {field}.")
    
    def list_all_jobs(self):
        """List all jobs in the database"""
        jobs = self.get_all_jobs()
        if jobs:
            self.display_job_list(jobs, show_details=True)
        else:
            print("No jobs found in database.")
    
    def list_recent_jobs(self):
        """List recent jobs (last 10)"""
        jobs = self.get_all_jobs(limit=10)
        if jobs:
            print("\n=== Recent Jobs (Last 10) ===")
            self.display_job_list(jobs)
        else:
            print("No jobs found in database.")
    
    def show_statistics(self):
        """Show database statistics including search information"""
        conn = self.connect_db()
        if not conn:
            return
            
        try:
            cursor = conn.cursor()
            
            # Basic stats
            cursor.execute("SELECT COUNT(*) FROM jobs")
            total_jobs = cursor.fetchone()[0]
            
            # Search statistics
            cursor.execute("SELECT DISTINCT search_keywords FROM jobs WHERE search_keywords IS NOT NULL")
            keywords = [row[0] for row in cursor.fetchall()]
            
            cursor.execute("SELECT DISTINCT search_location FROM jobs WHERE search_location IS NOT NULL")
            locations = [row[0] for row in cursor.fetchall()]
            
            cursor.execute("SELECT DISTINCT search_date_posted FROM jobs WHERE search_date_posted IS NOT NULL")
            date_filters = [row[0] for row in cursor.fetchall()]
            
            print("\n=== Database Statistics ===")
            print(f"Total jobs: {total_jobs}")
            
            if keywords:
                print(f"\nSearch Keywords Used:")
                for keyword in keywords:
                    cursor.execute("SELECT COUNT(*) FROM jobs WHERE search_keywords = ?", (keyword,))
                    count = cursor.fetchone()[0]
                    print(f"  '{keyword}': {count} jobs")
            
            if locations:
                print(f"\nSearch Locations Used:")
                for location in locations:
                    cursor.execute("SELECT COUNT(*) FROM jobs WHERE search_location = ?", (location,))
                    count = cursor.fetchone()[0]
                    print(f"  '{location}': {count} jobs")
            
            if date_filters:
                print(f"\nDate Filters Used:")
                for date_filter in date_filters:
                    cursor.execute("SELECT COUNT(*) FROM jobs WHERE search_date_posted = ?", (date_filter,))
                    count = cursor.fetchone()[0]
                    print(f"  '{date_filter}': {count} jobs")
            
            # Recent activity
            cursor.execute("SELECT scraped_at FROM jobs ORDER BY scraped_at DESC LIMIT 1")
            latest = cursor.fetchone()
            if latest:
                print(f"\nLatest scrape: {latest[0]}")
            
            conn.close()
            
        except Exception as e:
            print(f"[ERROR] Failed to get statistics: {e}")
            conn.close()

def main():
    """Main function"""
    print("LinkedIn Job Browser")
    print("===================")
    
    browser = JobBrowser()
    
    # Check if database exists
    if not os.path.exists(DB_PATH):
        print("Database not found. Please run the scraper first to create the database.")
        return
    
    while True:
        print("\nMain Menu:")
        print("1. Browse jobs (interactive)")
        print("2. List all jobs")
        print("3. List recent jobs")
        print("4. Search jobs")
        print("5. Show statistics")
        print("6. Quit")
        
        choice = input("\nEnter choice (1-6): ").strip()
        
        if choice == '1':
            browser.browse_jobs()
        elif choice == '2':
            browser.list_all_jobs()
        elif choice == '3':
            browser.list_recent_jobs()
        elif choice == '4':
            browser.search_interface()
        elif choice == '5':
            browser.show_statistics()
        elif choice == '6':
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please enter 1-6.")

if __name__ == "__main__":
    main() 