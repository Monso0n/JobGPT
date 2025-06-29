#!/usr/bin/env python3
"""
Database Schema Verification Script
Shows the structure and contents of the LinkedIn jobs database.
"""

import sqlite3
import os
from datetime import datetime

def verify_database_schema():
    """Verify and display the database schema"""
    db_path = 'data/linkedin_jobs.db'
    
    if not os.path.exists(db_path):
        print("❌ Database file not found!")
        print("Please run the LinkedIn scraper first to create the database.")
        return
    
    print("=" * 60)
    print("🔍 LINKEDIN JOBS DATABASE SCHEMA VERIFICATION")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"\n📋 Found {len(tables)} tables:")
        for table in tables:
            print(f"   • {table[0]}")
        
        print("\n" + "=" * 60)
        
        # Show schema for each table
        for table in tables:
            table_name = table[0]
            print(f"\n📊 TABLE: {table_name}")
            print("-" * 40)
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            print("Columns:")
            for col in columns:
                col_id, name, data_type, not_null, default_val, pk = col
                pk_str = " (PRIMARY KEY)" if pk else ""
                not_null_str = " NOT NULL" if not_null else ""
                default_str = f" DEFAULT {default_val}" if default_val else ""
                print(f"   • {name}: {data_type}{not_null_str}{default_str}{pk_str}")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"\nRow count: {count}")
            
            # Show sample data for jobs table
            if table_name == 'jobs' and count > 0:
                print("\nSample data (first 3 rows):")
                cursor.execute(f"SELECT id, title, company, status, scraped_at FROM {table_name} LIMIT 3")
                sample_rows = cursor.fetchall()
                for row in sample_rows:
                    print(f"   • ID {row[0]}: {row[1]} at {row[2]} (Status: {row[3]}, Scraped: {row[4]})")
        
        print("\n" + "=" * 60)
        print("✅ Database schema verification complete!")
        
        # Show some statistics
        print("\n📈 DATABASE STATISTICS:")
        print("-" * 30)
        
        # Total jobs
        cursor.execute("SELECT COUNT(*) FROM jobs")
        total_jobs = cursor.fetchone()[0]
        print(f"Total jobs: {total_jobs}")
        
        # Jobs by status
        cursor.execute("SELECT status, COUNT(*) FROM jobs GROUP BY status")
        status_counts = cursor.fetchall()
        if status_counts:
            print("Jobs by status:")
            for status, count in status_counts:
                print(f"   • {status}: {count}")
        
        # Recent jobs
        cursor.execute("SELECT COUNT(*) FROM jobs WHERE scraped_at >= datetime('now', '-7 days')")
        recent_jobs = cursor.fetchone()[0]
        print(f"Jobs scraped in last 7 days: {recent_jobs}")
        
        # Search history
        cursor.execute("SELECT COUNT(*) FROM search_history")
        search_count = cursor.fetchone()[0]
        print(f"Search history entries: {search_count}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error verifying database: {e}")

def show_table_contents(table_name: str, limit: int = 5):
    """Show contents of a specific table"""
    db_path = 'data/linkedin_jobs.db'
    
    if not os.path.exists(db_path):
        print("❌ Database file not found!")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if not cursor.fetchone():
            print(f"❌ Table '{table_name}' not found!")
            return
        
        print(f"\n📋 CONTENTS OF TABLE: {table_name}")
        print("=" * 60)
        
        # Get all rows
        cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
        rows = cursor.fetchall()
        
        # Get column names
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cursor.fetchall()]
        
        if not rows:
            print("No data found in this table.")
            return
        
        # Print header
        header = " | ".join(columns)
        print(header)
        print("-" * len(header))
        
        # Print rows
        for row in rows:
            formatted_row = []
            for i, value in enumerate(row):
                if value is None:
                    formatted_row.append("NULL")
                elif isinstance(value, str) and len(value) > 50:
                    formatted_row.append(f"{value[:47]}...")
                else:
                    formatted_row.append(str(value))
            print(" | ".join(formatted_row))
        
        # Show total count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        total_count = cursor.fetchone()[0]
        print(f"\nTotal rows in {table_name}: {total_count}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error showing table contents: {e}")

if __name__ == "__main__":
    print("🔍 LinkedIn Jobs Database Verification Tool")
    print("=" * 50)
    
    # Verify schema
    verify_database_schema()
    
    # Ask user if they want to see specific table contents
    print("\n" + "=" * 60)
    print("Would you like to see the contents of a specific table?")
    print("Available tables: jobs, job_status_history, search_history")
    
    while True:
        choice = input("\nEnter table name (or 'quit' to exit): ").strip().lower()
        
        if choice == 'quit':
            break
        elif choice in ['jobs', 'job_status_history', 'search_history']:
            limit = input("How many rows to show? (default 5): ").strip()
            try:
                limit = int(limit) if limit else 5
            except ValueError:
                limit = 5
            show_table_contents(choice, limit)
        else:
            print("❌ Invalid table name. Please choose from: jobs, job_status_history, search_history")
    
    print("\n👋 Database verification complete!") 