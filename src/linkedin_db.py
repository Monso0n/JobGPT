#!/usr/bin/env python3
"""
LinkedIn Jobs Database Module
Handles all database operations for the LinkedIn job scraper.
"""

import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')

class LinkedInJobsDB:
    """Database manager for LinkedIn jobs"""
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = os.path.join(DATA_DIR, 'linkedin_jobs.db')
        self.db_path: str = db_path
        self.conn = None
        self.cursor = None
    
    def connect(self) -> bool:
        """Connect to the database"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            return True
        except Exception as e:
            print(f"[DB ERROR] Failed to connect to database: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the database"""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None
    
    def create_tables(self):
        """Create the database tables if they don't exist"""
        if self.cursor is None or self.conn is None:
            raise RuntimeError("Database connection not established. Call connect() first.")
        try:
            # Main jobs table
            self.cursor.execute('''
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
            
            # Job status history table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS job_status_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER,
                    status TEXT,
                    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT,
                    FOREIGN KEY (job_id) REFERENCES jobs (id)
                )
            ''')
            
            # Search history table
            self.cursor.execute('''
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
            
            self.conn.commit()
            print("[DB] Database tables created successfully")
            return True
            
        except Exception as e:
            print(f"[DB ERROR] Failed to create tables: {e}")
            return False
    
    def job_exists(self, url: Optional[str], title: Optional[str] = None, company: Optional[str] = None) -> bool:
        """Check if a job already exists in the database"""
        if self.cursor is None:
            raise RuntimeError("Database connection not established. Call connect() first.")
        try:
            # Check by URL first (most reliable)
            if url is not None:
                self.cursor.execute("SELECT id FROM jobs WHERE url = ?", (url,))
            if self.cursor.fetchone():
                return True
            # If no URL match, check by title + company combination
            if title is not None and company is not None:
                self.cursor.execute(
                    "SELECT id FROM jobs WHERE title = ? AND company = ?", 
                    (title, company)
                )
                if self.cursor.fetchone():
                    return True
            return False
        except Exception as e:
            print(f"[DB ERROR] Error checking if job exists: {e}")
            return False
    
    def save_job(self, job_data: Dict[str, Any]) -> bool:
        """Save a job to the database"""
        if self.cursor is None or self.conn is None:
            raise RuntimeError("Database connection not established. Call connect() first.")
        try:
            # Check if job already exists
            if self.job_exists(job_data.get('url'), job_data.get('title'), job_data.get('company')):
                print(f"[DB] Job already exists: {job_data.get('title')} at {job_data.get('company')}")
                return False
            
            # Insert new job
            self.cursor.execute('''
                INSERT INTO jobs (
                    title, company, location, description, url,
                    search_keywords, search_location, search_date_posted,
                    search_experience_level, search_job_type, search_work_model
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                job_data.get('title'),
                job_data.get('company'),
                job_data.get('location'),
                job_data.get('description'),
                job_data.get('url'),
                job_data.get('search_keywords'),
                job_data.get('search_location'),
                job_data.get('search_date_posted'),
                job_data.get('search_experience_level'),
                job_data.get('search_job_type'),
                job_data.get('search_work_model')
            ))
            
            self.conn.commit()
            print(f"[DB] Saved job: {job_data.get('title')} at {job_data.get('company')}")
            return True
            
        except Exception as e:
            print(f"[DB ERROR] Failed to save job: {e}")
            return False
    
    def get_jobs(self, limit: Optional[int] = None, status: Optional[str] = None, liked: Optional[bool] = None) -> List[Dict]:
        """Get jobs from the database with optional filters"""
        if self.cursor is None:
            raise RuntimeError("Database connection not established. Call connect() first.")
        try:
            query = "SELECT * FROM jobs"
            params = []
            
            # Build WHERE clause
            conditions = []
            if status is not None:
                conditions.append("status = ?")
                params.append(status)
            if liked is not None:
                conditions.append("liked = ?")
                params.append(1 if liked else 0)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY scraped_at DESC"
            
            if limit is not None:
                query += " LIMIT ?"
                params.append(limit)
            
            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()
            
            # Convert to list of dictionaries
            columns = [description[0] for description in self.cursor.description]
            jobs = []
            for row in rows:
                job = dict(zip(columns, row))
                jobs.append(job)
            
            return jobs
            
        except Exception as e:
            print(f"[DB ERROR] Failed to get jobs: {e}")
            return []
    
    def update_job_status(self, job_id: int, status: str, notes: str = None) -> bool:
        """Update job status and add to history"""
        if self.cursor is None or self.conn is None:
            raise RuntimeError("Database connection not established. Call connect() first.")
        if status is None:
            raise ValueError("Status must not be None.")
        try:
            # Update job status
            self.cursor.execute(
                "UPDATE jobs SET status = ? WHERE id = ?",
                (status, job_id)
            )
            
            # Add to status history
            self.cursor.execute('''
                INSERT INTO job_status_history (job_id, status, notes)
                VALUES (?, ?, ?)
            ''', (job_id, status, notes))
            
            self.conn.commit()
            print(f"[DB] Updated job {job_id} status to: {status}")
            return True
            
        except Exception as e:
            print(f"[DB ERROR] Failed to update job status: {e}")
            return False
    
    def toggle_job_like(self, job_id: int) -> bool:
        """Toggle the liked status of a job"""
        if self.cursor is None or self.conn is None:
            raise RuntimeError("Database connection not established. Call connect() first.")
        try:
            self.cursor.execute(
                "UPDATE jobs SET liked = CASE WHEN liked = 1 THEN 0 ELSE 1 END WHERE id = ?",
                (job_id,)
            )
            self.conn.commit()
            
            # Get the new liked status
            self.cursor.execute("SELECT liked FROM jobs WHERE id = ?", (job_id,))
            result = self.cursor.fetchone()
            if result:
                liked = bool(result[0])
                print(f"[DB] Job {job_id} {'liked' if liked else 'unliked'}")
                return True
            
            return False
            
        except Exception as e:
            print(f"[DB ERROR] Failed to toggle job like: {e}")
            return False
    
    def mark_resume_created(self, job_id: int) -> bool:
        """Mark that a resume has been created for a job"""
        if self.cursor is None or self.conn is None:
            raise RuntimeError("Database connection not established. Call connect() first.")
        try:
            self.cursor.execute(
                "UPDATE jobs SET resume_created = 1 WHERE id = ?",
                (job_id,)
            )
            self.conn.commit()
            print(f"[DB] Marked resume created for job {job_id}")
            return True
        except Exception as e:
            print(f"[DB ERROR] Failed to mark resume created: {e}")
            return False
    
    def mark_cover_letter_created(self, job_id: int) -> bool:
        """Mark that a cover letter has been created for a job"""
        if self.cursor is None or self.conn is None:
            raise RuntimeError("Database connection not established. Call connect() first.")
        try:
            self.cursor.execute(
                "UPDATE jobs SET cover_letter_created = 1 WHERE id = ?",
                (job_id,)
            )
            self.conn.commit()
            print(f"[DB] Marked cover letter created for job {job_id}")
            return True
        except Exception as e:
            print(f"[DB ERROR] Failed to mark cover letter created: {e}")
            return False
    
    def update_job_resume(self, job_id: int, resume_json: str) -> bool:
        """Update the resume JSON data for a job"""
        if self.cursor is None or self.conn is None:
            raise RuntimeError("Database connection not established. Call connect() first.")
        try:
            self.cursor.execute(
                "UPDATE jobs SET resume_json = ? WHERE id = ?",
                (resume_json, job_id)
            )
            self.conn.commit()
            print(f"[DB] Updated resume JSON for job {job_id}")
            return True
        except Exception as e:
            print(f"[DB ERROR] Failed to update resume JSON: {e}")
            return False
    
    def update_job_resume_file_path(self, job_id: int, resume_file_path: str) -> bool:
        """Update the resume file path for a job"""
        if self.cursor is None or self.conn is None:
            raise RuntimeError("Database connection not established. Call connect() first.")
        try:
            self.cursor.execute(
                "UPDATE jobs SET resume_file_path = ? WHERE id = ?",
                (resume_file_path, job_id)
            )
            self.conn.commit()
            print(f"[DB] Updated resume file path for job {job_id}")
            return True
        except Exception as e:
            print(f"[DB ERROR] Failed to update resume file path: {e}")
            return False
    
    def update_job_cover_letter(self, job_id: int, cover_letter_json: str) -> bool:
        """Update the cover letter JSON data for a job"""
        if self.cursor is None or self.conn is None:
            raise RuntimeError("Database connection not established. Call connect() first.")
        try:
            self.cursor.execute(
                "UPDATE jobs SET cover_letter_json = ? WHERE id = ?",
                (cover_letter_json, job_id)
            )
            self.conn.commit()
            print(f"[DB] Updated cover letter JSON for job {job_id}")
            return True
        except Exception as e:
            print(f"[DB ERROR] Failed to update cover letter JSON: {e}")
            return False
    
    def update_job_cover_letter_file_path(self, job_id: int, cover_letter_file_path: str) -> bool:
        """Update the cover letter file path for a job"""
        if self.cursor is None or self.conn is None:
            raise RuntimeError("Database connection not established. Call connect() first.")
        try:
            self.cursor.execute(
                "UPDATE jobs SET cover_letter_file_path = ? WHERE id = ?",
                (cover_letter_file_path, job_id)
            )
            self.conn.commit()
            print(f"[DB] Updated cover letter file path for job {job_id}")
            return True
        except Exception as e:
            print(f"[DB ERROR] Failed to update cover letter file path: {e}")
            return False
    
    def mark_applied(self, job_id: int) -> bool:
        """Mark that an application has been submitted for a job"""
        if self.cursor is None or self.conn is None:
            raise RuntimeError("Database connection not established. Call connect() first.")
        try:
            self.cursor.execute(
                "UPDATE jobs SET applied = 1 WHERE id = ?",
                (job_id,)
            )
            self.conn.commit()
            print(f"[DB] Marked job {job_id} as applied")
            return True
        except Exception as e:
            print(f"[DB ERROR] Failed to mark job as applied: {e}")
            return False
    
    def add_job_notes(self, job_id: int, notes: str) -> bool:
        """Add or update notes for a job"""
        if self.cursor is None or self.conn is None:
            raise RuntimeError("Database connection not established. Call connect() first.")
        try:
            self.cursor.execute(
                "UPDATE jobs SET notes = ? WHERE id = ?",
                (notes, job_id)
            )
            self.conn.commit()
            print(f"[DB] Added notes for job {job_id}")
            return True
        except Exception as e:
            print(f"[DB ERROR] Failed to add job notes: {e}")
            return False
    
    def get_job_by_id(self, job_id: int) -> Optional[Dict]:
        """Get a specific job by ID"""
        if self.cursor is None:
            raise RuntimeError("Database connection not established. Call connect() first.")
        try:
            self.cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
            row = self.cursor.fetchone()
            
            if row:
                columns = [description[0] for description in self.cursor.description]
                return dict(zip(columns, row))
            
            return None
            
        except Exception as e:
            print(f"[DB ERROR] Failed to get job by ID: {e}")
            return None
    
    def search_jobs(self, query: str) -> List[Dict]:
        """Search jobs by title, company, or description"""
        if self.cursor is None:
            raise RuntimeError("Database connection not established. Call connect() first.")
        try:
            search_term = f"%{query}%"
            self.cursor.execute('''
                SELECT * FROM jobs 
                WHERE title LIKE ? OR company LIKE ? OR description LIKE ?
                ORDER BY scraped_at DESC
            ''', (search_term, search_term, search_term))
            
            rows = self.cursor.fetchall()
            columns = [description[0] for description in self.cursor.description]
            jobs = []
            for row in rows:
                job = dict(zip(columns, row))
                jobs.append(job)
            
            return jobs
            
        except Exception as e:
            print(f"[DB ERROR] Failed to search jobs: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            stats = {}
            
            # Total jobs
            self.cursor.execute("SELECT COUNT(*) FROM jobs")
            stats['total_jobs'] = self.cursor.fetchone()[0]
            
            # Jobs by status
            self.cursor.execute("SELECT status, COUNT(*) FROM jobs GROUP BY status")
            stats['by_status'] = dict(self.cursor.fetchall())
            
            # Liked jobs
            self.cursor.execute("SELECT COUNT(*) FROM jobs WHERE liked = 1")
            stats['liked_jobs'] = self.cursor.fetchone()[0]
            
            # Jobs with resume created
            self.cursor.execute("SELECT COUNT(*) FROM jobs WHERE resume_created = 1")
            stats['resume_created'] = self.cursor.fetchone()[0]
            
            # Jobs with cover letter created
            self.cursor.execute("SELECT COUNT(*) FROM jobs WHERE cover_letter_created = 1")
            stats['cover_letter_created'] = self.cursor.fetchone()[0]
            
            # Applied jobs
            self.cursor.execute("SELECT COUNT(*) FROM jobs WHERE applied = 1")
            stats['applied_jobs'] = self.cursor.fetchone()[0]
            
            # Recent jobs (last 7 days)
            self.cursor.execute('''
                SELECT COUNT(*) FROM jobs 
                WHERE scraped_at >= datetime('now', '-7 days')
            ''')
            stats['recent_jobs'] = self.cursor.fetchone()[0]
            
            return stats
            
        except Exception as e:
            print(f"[DB ERROR] Failed to get statistics: {e}")
            return {}
    
    def save_search_history(self, search_data: Dict[str, Any], jobs_found: int, jobs_scraped: int) -> bool:
        """Save search history"""
        try:
            self.cursor.execute('''
                INSERT INTO search_history (
                    keywords, location, date_posted, experience_level,
                    job_type, work_model, jobs_found, jobs_scraped
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                search_data.get('keywords'),
                search_data.get('location'),
                search_data.get('date_posted'),
                search_data.get('experience_level'),
                search_data.get('job_type'),
                search_data.get('work_model'),
                jobs_found,
                jobs_scraped
            ))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            print(f"[DB ERROR] Failed to save search history: {e}")
            return False

# Convenience functions for backward compatibility
def init_database(db_path: Optional[str] = None) -> LinkedInJobsDB:
    """Initialize and return a database connection"""
    db = LinkedInJobsDB(db_path)
    if db.connect():
        db.create_tables()
    return db

def save_job_to_db(job_data: Dict[str, Any], db_path: Optional[str] = None) -> bool:
    """Save a job to the database (convenience function)"""
    db = LinkedInJobsDB(db_path)
    if db.connect():
        result = db.save_job(job_data)
        db.disconnect()
        return result
    return False
