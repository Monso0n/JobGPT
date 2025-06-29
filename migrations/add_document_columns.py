#!/usr/bin/env python3
"""
Migration script to add document-related columns to the jobs table
"""

import sqlite3
import os
from pathlib import Path

def add_document_columns():
    """Add columns for storing resume and cover letter data"""
    db_path = 'data/linkedin_jobs.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(jobs)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Columns to add
        new_columns = [
            ('resume_json', 'TEXT'),
            ('resume_file_path', 'TEXT'),
            ('cover_letter_json', 'TEXT'),
            ('cover_letter_file_path', 'TEXT')
        ]
        
        added_columns = []
        for column_name, column_type in new_columns:
            if column_name not in columns:
                cursor.execute(f"ALTER TABLE jobs ADD COLUMN {column_name} {column_type}")
                added_columns.append(column_name)
                print(f"✅ Added column: {column_name}")
            else:
                print(f"ℹ️  Column already exists: {column_name}")
        
        conn.commit()
        conn.close()
        
        if added_columns:
            print(f"🎉 Successfully added {len(added_columns)} columns to jobs table")
        else:
            print("ℹ️  All required columns already exist")
        
        return True
        
    except Exception as e:
        print(f"❌ Error adding columns: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Running migration: Adding document columns to jobs table")
    success = add_document_columns()
    if success:
        print("✅ Migration completed successfully")
    else:
        print("❌ Migration failed") 