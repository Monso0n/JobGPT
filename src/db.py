#!/usr/bin/env python3
"""
Database module for AI tailor functionality
Provides simple database functions for job document generation
"""

from linkedin_db import LinkedInJobsDB

def _get_db():
    """Get a new database connection for each request"""
    db = LinkedInJobsDB()
    db.connect()
    return db

def get_job_by_id(job_id: int):
    """Get a job by ID"""
    db = _get_db()
    try:
        return db.get_job_by_id(job_id)
    finally:
        db.disconnect()

def update_job_resume(job_id: int, resume_json: str) -> bool:
    """Update the resume JSON data for a job"""
    db = _get_db()
    try:
        return db.update_job_resume(job_id, resume_json)
    finally:
        db.disconnect()

def update_job_resume_file_path(job_id: int, resume_file_path: str) -> bool:
    """Update the resume file path for a job"""
    db = _get_db()
    try:
        return db.update_job_resume_file_path(job_id, resume_file_path)
    finally:
        db.disconnect()

def update_job_cover_letter(job_id: int, cover_letter_json: str) -> bool:
    """Update the cover letter JSON data for a job"""
    db = _get_db()
    try:
        return db.update_job_cover_letter(job_id, cover_letter_json)
    finally:
        db.disconnect()

def update_job_cover_letter_file_path(job_id: int, cover_letter_file_path: str) -> bool:
    """Update the cover letter file path for a job"""
    db = _get_db()
    try:
        return db.update_job_cover_letter_file_path(job_id, cover_letter_file_path)
    finally:
        db.disconnect() 