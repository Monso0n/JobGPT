#!/usr/bin/env python3
"""
Check SQLite Database Contents
Simple script to view the scraped jobs in the SQLite database.
"""

import sqlite3

def check_database():
    """Check the contents of the SQLite database"""
    try:
        # Connect to the database
        conn = sqlite3.connect('data/linkedin_jobs.db')
        cursor = conn.cursor()
        
        # Get table info
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("Tables in database:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Get job count
        cursor.execute("SELECT COUNT(*) FROM jobs")
        count = cursor.fetchone()[0]
        print(f"\nTotal jobs in database: {count}")
        
        # Get sample jobs
        cursor.execute("SELECT id, title, company, location, scraped_at FROM jobs ORDER BY id DESC LIMIT 5")
        jobs = cursor.fetchall()
        
        print("\nRecent jobs:")
        print("-" * 80)
        for job in jobs:
            job_id, title, company, location, scraped_at = job
            print(f"ID: {job_id}")
            print(f"Title: {title}")
            print(f"Company: {company}")
            print(f"Location: {location}")
            print(f"Scraped: {scraped_at}")
            print("-" * 80)
        
        # Get full details of the most recent job
        cursor.execute("SELECT * FROM jobs ORDER BY id DESC LIMIT 1")
        latest_job = cursor.fetchone()
        if latest_job:
            print(f"\nFull details of most recent job (ID: {latest_job[0]}):")
            print(f"Title: {latest_job[1]}")
            print(f"Company: {latest_job[2]}")
            print(f"Location: {latest_job[3]}")
            print(f"Description length: {len(latest_job[4]) if latest_job[4] else 0} characters")
            print(f"URL: {latest_job[5]}")
            print(f"Scraped at: {latest_job[6]}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking database: {e}")

if __name__ == "__main__":
    check_database() 