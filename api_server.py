#!/usr/bin/env python3
"""
Flask API server to serve LinkedIn jobs data from SQLite database
"""

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime
import sys
from pathlib import Path
import json

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent / 'src'))

# Import the AI tailor module
from ai_tailor import (
    generate_html_from_json, 
    generate_pdf_from_html,
    combine_pdfs,
    load_master_resume, 
    load_master_cover_letter, 
    load_career_facts, 
    sanitize_filename, 
    generate_tailored_resume,
    generate_tailored_cover_letter,
    clean_location
)
import db

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

DATABASE_PATH = 'data/linkedin_jobs.db'
OUTPUT_BASE_DIR = "job_applications"

def get_db_connection():
    """Create a database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # This allows column access by name
    return conn

@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    """Get all jobs with optional filtering"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get query parameters for filtering
        limit = request.args.get('limit', type=int, default=50)
        offset = request.args.get('offset', type=int, default=0)
        search = request.args.get('search', type=str, default='')
        location = request.args.get('location', type=str, default='')
        company = request.args.get('company', type=str, default='')
        
        # Build query
        query = """
            SELECT id, title, company, location, description, url, 
                   search_keywords, search_location, search_date_posted,
                   experience_level, job_type, work_model, scraped_at,
                   status, liked, applied
            FROM jobs 
            WHERE 1=1
        """
        params = []
        
        if search:
            query += " AND (title LIKE ? OR company LIKE ? OR description LIKE ?)"
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param])
        
        if location:
            query += " AND location LIKE ?"
            params.append(f"%{location}%")
        
        if company:
            query += " AND company LIKE ?"
            params.append(f"%{company}%")
        
        query += " ORDER BY scraped_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        jobs = cursor.fetchall()
        
        # Convert to list of dictionaries
        jobs_list = []
        for job in jobs:
            job_dict = dict(job)
            # Truncate description for list view
            if job_dict['description'] and len(job_dict['description']) > 200:
                job_dict['description_preview'] = job_dict['description'][:200] + "..."
            else:
                job_dict['description_preview'] = job_dict['description']
            jobs_list.append(job_dict)
        
        conn.close()
        return jsonify({
            'jobs': jobs_list,
            'total': len(jobs_list),
            'limit': limit,
            'offset': offset
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/jobs/<int:job_id>', methods=['GET'])
def get_job(job_id):
    """Get a specific job by ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, title, company, location, description, url, 
                   search_keywords, search_location, search_date_posted,
                   experience_level, job_type, work_model, scraped_at,
                   status, liked, applied, notes
            FROM jobs 
            WHERE id = ?
        """, (job_id,))
        
        job = cursor.fetchone()
        conn.close()
        
        if job:
            return jsonify(dict(job))
        else:
            return jsonify({'error': 'Job not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/jobs/<int:job_id>/toggle-like', methods=['POST'])
def toggle_job_like(job_id):
    """Toggle the liked status of a job"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get current liked status
        cursor.execute("SELECT liked FROM jobs WHERE id = ?", (job_id,))
        job = cursor.fetchone()
        
        if not job:
            conn.close()
            return jsonify({'error': 'Job not found'}), 404
        
        # Toggle liked status
        new_liked = 0 if job['liked'] else 1
        cursor.execute("UPDATE jobs SET liked = ? WHERE id = ?", (new_liked, job_id))
        conn.commit()
        conn.close()
        
        return jsonify({'liked': bool(new_liked)})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/jobs/<int:job_id>/toggle-applied', methods=['POST'])
def toggle_job_applied(job_id):
    """Toggle the applied status of a job"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get current applied status
        cursor.execute("SELECT applied FROM jobs WHERE id = ?", (job_id,))
        job = cursor.fetchone()

        if not job:
            conn.close()
            return jsonify({'error': 'Job not found'}), 404

        # Toggle applied status
        new_applied = 0 if job['applied'] else 1
        cursor.execute("UPDATE jobs SET applied = ? WHERE id = ?", (new_applied, job_id))
        conn.commit()
        conn.close()

        return jsonify({'applied': bool(new_applied)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/jobs/<int:job_id>/mark-applied', methods=['POST'])
def mark_job_applied(job_id):
    """Mark a job as applied"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("UPDATE jobs SET applied = 1 WHERE id = ?", (job_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get job statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Total jobs
        cursor.execute("SELECT COUNT(*) as total FROM jobs")
        total_jobs = cursor.fetchone()['total']
        
        # Jobs by status
        cursor.execute("SELECT status, COUNT(*) as count FROM jobs GROUP BY status")
        status_counts = dict(cursor.fetchall())
        
        # Top companies
        cursor.execute("""
            SELECT company, COUNT(*) as count 
            FROM jobs 
            GROUP BY company 
            ORDER BY count DESC 
            LIMIT 10
        """)
        top_companies = [dict(row) for row in cursor.fetchall()]
        
        # Top locations
        cursor.execute("""
            SELECT location, COUNT(*) as count 
            FROM jobs 
            WHERE location IS NOT NULL AND location != 'Location not specified'
            GROUP BY location 
            ORDER BY count DESC 
            LIMIT 10
        """)
        top_locations = [dict(row) for row in cursor.fetchall()]
        
        # Recent jobs (last 7 days)
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM jobs 
            WHERE scraped_at >= datetime('now', '-7 days')
        """)
        recent_jobs = cursor.fetchone()['count']
        
        conn.close()
        
        return jsonify({
            'total_jobs': total_jobs,
            'status_counts': status_counts,
            'top_companies': top_companies,
            'top_locations': top_locations,
            'recent_jobs': recent_jobs
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search', methods=['GET'])
def search_jobs():
    """Search jobs with advanced filters"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get search parameters
        keywords = request.args.get('keywords', type=str, default='')
        location = request.args.get('location', type=str, default='')
        company = request.args.get('company', type=str, default='')
        experience_level = request.args.get('experience_level', type=str, default='')
        job_type = request.args.get('job_type', type=str, default='')
        work_model = request.args.get('work_model', type=str, default='')
        limit = request.args.get('limit', type=int, default=50)
        offset = request.args.get('offset', type=int, default=0)
        
        # Build query
        query = """
            SELECT id, title, company, location, description, url, 
                   search_keywords, search_location, search_date_posted,
                   experience_level, job_type, work_model, scraped_at,
                   status, liked, applied
            FROM jobs 
            WHERE 1=1
        """
        params = []
        
        if keywords:
            query += " AND (title LIKE ? OR description LIKE ? OR search_keywords LIKE ?)"
            keywords_param = f"%{keywords}%"
            params.extend([keywords_param, keywords_param, keywords_param])
        
        if location:
            query += " AND location LIKE ?"
            params.append(f"%{location}%")
        
        if company:
            query += " AND company LIKE ?"
            params.append(f"%{company}%")
        
        if experience_level and experience_level != 'All':
            query += " AND experience_level = ?"
            params.append(experience_level)
        
        if job_type and job_type != 'All':
            query += " AND job_type = ?"
            params.append(job_type)
        
        if work_model and work_model != 'All':
            query += " AND work_model = ?"
            params.append(work_model)
        
        query += " ORDER BY scraped_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        jobs = cursor.fetchall()
        
        # Convert to list of dictionaries
        jobs_list = []
        for job in jobs:
            job_dict = dict(job)
            # Truncate description for list view
            if job_dict['description'] and len(job_dict['description']) > 200:
                job_dict['description_preview'] = job_dict['description'][:200] + "..."
            else:
                job_dict['description_preview'] = job_dict['description']
            jobs_list.append(job_dict)
        
        conn.close()
        return jsonify({
            'jobs': jobs_list,
            'total': len(jobs_list),
            'filters': {
                'keywords': keywords,
                'location': location,
                'company': company,
                'experience_level': experience_level,
                'job_type': job_type,
                'work_model': work_model
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/jobs/<int:job_id>/generate-resume', methods=['POST'])
def generate_resume(job_id):
    """Generate only the resume for a specific job."""
    try:
        # Get job details
        job = db.get_job_by_id(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404
        
        print(f"🔄 Generating resume for Job ID: {job_id} - {job['title']} at {job['company']}")
        
        # Generate resume with AI
        tailored_resume = generate_tailored_resume(job)
        
        if not tailored_resume:
            return jsonify({"error": "Failed to generate resume"}), 500
        
        # Create output directory and filenames
        sanitized_company = sanitize_filename(job['company'])
        sanitized_title = sanitize_filename(job['title'])
        output_dir = Path(OUTPUT_BASE_DIR) / sanitized_company
        output_dir.mkdir(parents=True, exist_ok=True)
        
        base_filename = f"{sanitized_company}_{sanitized_title}"
        resume_json_filepath = output_dir / f"{base_filename}_resume.json"
        resume_html_filepath = output_dir / f"{base_filename}_resume.html"
        resume_pdf_filepath = output_dir / f"{base_filename}_resume.pdf"
        
        # Save JSON file
        with open(resume_json_filepath, 'w', encoding='utf-8') as f:
            json.dump(tailored_resume, f, indent=2)
        
        # Generate HTML
        html_success = generate_html_from_json(resume_json_filepath, resume_html_filepath, "resume")
        
        if not html_success:
            return jsonify({"error": "Failed to generate HTML"}), 500
        
        # Generate PDF
        pdf_success = generate_pdf_from_html(resume_html_filepath, resume_pdf_filepath)
        
        if not pdf_success:
            return jsonify({"error": "Failed to generate PDF"}), 500
        
        # Update database
        db.update_job_resume(job_id, json.dumps(tailored_resume))
        db.update_job_resume_file_path(job_id, str(resume_html_filepath))
        
        return jsonify({
            "message": "Resume generated successfully",
            "resume_json": tailored_resume,
            "html_path": str(resume_html_filepath),
            "pdf_path": str(resume_pdf_filepath)
        })
        
    except Exception as e:
        print(f"❌ Error generating resume for job {job_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/jobs/<int:job_id>/generate-cover-letter', methods=['POST'])
def generate_cover_letter(job_id):
    """Generate only the cover letter for a specific job."""
    try:
        # Get job details
        job = db.get_job_by_id(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404
        
        # Clean the location
        job['location'] = clean_location(job.get('location', ''))
        
        print(f"🔄 Generating cover letter for Job ID: {job_id} - {job['title']} at {job['company']}")
        
        # Load the tailored resume that was created for this job
        sanitized_company = sanitize_filename(job['company'])
        sanitized_title = sanitize_filename(job['title'])
        output_dir = Path(OUTPUT_BASE_DIR) / sanitized_company
        base_filename = f"{sanitized_company}_{sanitized_title}"
        resume_json_filepath = output_dir / f"{base_filename}_resume.json"
        
        # Check if tailored resume exists
        if not resume_json_filepath.exists():
            return jsonify({"error": "Tailored resume not found. Generate resume first."}), 404
        
        # Load the tailored resume
        try:
            with open(resume_json_filepath, 'r', encoding='utf-8') as f:
                tailored_resume = json.load(f)
        except Exception as e:
            return jsonify({"error": f"Failed to load tailored resume: {e}"}), 500
        
        # Generate cover letter with AI using the actual tailored resume
        tailored_cover_letter = generate_tailored_cover_letter(job, tailored_resume)
        
        if not tailored_cover_letter:
            return jsonify({"error": "Failed to generate cover letter"}), 500
        
        # Create output directory and filenames
        sanitized_company = sanitize_filename(job['company'])
        sanitized_title = sanitize_filename(job['title'])
        output_dir = Path(OUTPUT_BASE_DIR) / sanitized_company
        output_dir.mkdir(parents=True, exist_ok=True)
        
        base_filename = f"{sanitized_company}_{sanitized_title}"
        cover_letter_json_filepath = output_dir / f"{base_filename}_cover_letter.json"
        cover_letter_html_filepath = output_dir / f"{base_filename}_cover_letter.html"
        cover_letter_pdf_filepath = output_dir / f"{base_filename}_cover_letter.pdf"
        
        # Save JSON file
        with open(cover_letter_json_filepath, 'w', encoding='utf-8') as f:
            json.dump(tailored_cover_letter, f, indent=2)
        
        # Generate HTML
        html_success = generate_html_from_json(cover_letter_json_filepath, cover_letter_html_filepath, "cover letter")
        
        if not html_success:
            return jsonify({"error": "Failed to generate HTML"}), 500
        
        # Generate PDF
        pdf_success = generate_pdf_from_html(cover_letter_html_filepath, cover_letter_pdf_filepath)
        
        if not pdf_success:
            return jsonify({"error": "Failed to generate PDF"}), 500
        
        # Update database
        db.update_job_cover_letter(job_id, json.dumps(tailored_cover_letter))
        db.update_job_cover_letter_file_path(job_id, str(cover_letter_html_filepath))
        
        return jsonify({
            "message": "Cover letter generated successfully",
            "cover_letter_json": tailored_cover_letter,
            "html_path": str(cover_letter_html_filepath),
            "pdf_path": str(cover_letter_pdf_filepath)
        })
        
    except Exception as e:
        print(f"❌ Error generating cover letter for job {job_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/jobs/<int:job_id>/combine-files', methods=['POST'])
def combine_files(job_id):
    """Combine existing resume and cover letter HTMLs into a single document."""
    try:
        # Get job details
        job = db.get_job_by_id(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404
        
        job_title = job['title']
        company_name = job['company']
        
        # Create output directory and filenames
        sanitized_company = sanitize_filename(company_name)
        sanitized_title = sanitize_filename(job_title)
        output_dir = Path(OUTPUT_BASE_DIR) / sanitized_company
        output_dir.mkdir(parents=True, exist_ok=True)
        
        base_filename = f"{sanitized_company}_{sanitized_title}"
        cover_letter_json_filepath = output_dir / f"{base_filename}_cover_letter.json"
        resume_json_filepath = output_dir / f"{base_filename}_resume.json"
        combined_html_filepath = output_dir / f"{base_filename}_combined.html"
        combined_pdf_filepath = output_dir / f"{base_filename}_combined.pdf"
        
        # Check if individual files exist
        if not cover_letter_json_filepath.exists():
            return jsonify({"error": "Cover letter JSON not found. Generate cover letter first."}), 404
        
        if not resume_json_filepath.exists():
            return jsonify({"error": "Resume JSON not found. Generate resume first."}), 404
        
        # Generate HTML files from JSON files
        cover_letter_html = cover_letter_json_filepath.with_suffix('.html')
        resume_html = resume_json_filepath.with_suffix('.html')
        
        if not generate_html_from_json(cover_letter_json_filepath, cover_letter_html, "cover letter"):
            return jsonify({"error": "Failed to generate cover letter HTML"}), 500
        
        if not generate_html_from_json(resume_json_filepath, resume_html, "resume"):
            return jsonify({"error": "Failed to generate resume HTML"}), 500
        
        # Combine HTML files (simple concatenation)
        try:
            with open(cover_letter_html, 'r', encoding='utf-8') as f:
                cover_letter_content = f.read()
            
            with open(resume_html, 'r', encoding='utf-8') as f:
                resume_content = f.read()
            
            # Insert a page break between cover letter and resume
            combined_content = cover_letter_content.replace('</body>', '<div style="page-break-before: always;"></div>' + resume_content)
            
            with open(combined_html_filepath, 'w', encoding='utf-8') as f:
                f.write(combined_content)
            
            print(f"✅ Successfully created combined HTML: {combined_html_filepath}")
        except Exception as e:
            print(f"❌ Error creating combined HTML: {e}")
            return jsonify({"error": "Failed to create combined HTML"}), 500
        
        # Generate PDFs from JSON files
        cover_letter_pdf = cover_letter_json_filepath.with_suffix('.pdf')
        resume_pdf = resume_json_filepath.with_suffix('.pdf')
        
        if not generate_pdf_from_html(cover_letter_html, cover_letter_pdf):
            return jsonify({"error": "Failed to generate cover letter PDF"}), 500
        
        if not generate_pdf_from_html(resume_html, resume_pdf):
            return jsonify({"error": "Failed to generate resume PDF"}), 500
        
        # Combine the PDFs
        pdf_success = combine_pdfs(cover_letter_pdf, resume_pdf, combined_pdf_filepath)
        
        if pdf_success:
            return jsonify({
                "message": "Files combined successfully",
                "combined_html_path": str(combined_html_filepath),
                "combined_pdf_path": str(combined_pdf_filepath)
            })
        else:
            return jsonify({"error": "Failed to combine PDFs"}), 500
            
    except Exception as e:
        print(f"❌ Error combining files for job {job_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/jobs/<int:job_id>/resume-html', methods=['GET'])
def serve_resume_html(job_id):
    """Serve the resume HTML file."""
    try:
        job = db.get_job_by_id(job_id)
        if not job or not job.get('resume_file_path'):
            return jsonify({"error": "Resume HTML not found"}), 404
        
        html_path = Path(job['resume_file_path'])
        if not html_path.exists():
            return jsonify({"error": "Resume HTML file not found"}), 404
        
        return send_file(html_path, mimetype='text/html')
        
    except Exception as e:
        print(f"❌ Error serving resume HTML for job {job_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/jobs/<int:job_id>/cover-letter-html', methods=['GET'])
def serve_cover_letter_html(job_id):
    """Serve the cover letter HTML file."""
    try:
        job = db.get_job_by_id(job_id)
        if not job or not job.get('cover_letter_file_path'):
            return jsonify({"error": "Cover letter HTML not found"}), 404
        
        html_path = Path(job['cover_letter_file_path'])
        if not html_path.exists():
            return jsonify({"error": "Cover letter HTML file not found"}), 404
        
        return send_file(html_path, mimetype='text/html')
        
    except Exception as e:
        print(f"❌ Error serving cover letter HTML for job {job_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/jobs/<int:job_id>/combined-html', methods=['GET'])
def serve_combined_html(job_id):
    """Serve the combined HTML file."""
    try:
        job = db.get_job_by_id(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404
        
        job_title = job['title']
        company_name = job['company']
        
        # Construct the expected path
        sanitized_company = sanitize_filename(company_name)
        sanitized_title = sanitize_filename(job_title)
        output_dir = Path(OUTPUT_BASE_DIR) / sanitized_company
        base_filename = f"{sanitized_company}_{sanitized_title}"
        combined_html_filepath = output_dir / f"{base_filename}_combined.html"
        
        if not combined_html_filepath.exists():
            return jsonify({"error": "Combined HTML not found"}), 404
        
        return send_file(combined_html_filepath, mimetype='text/html')
        
    except Exception as e:
        print(f"❌ Error serving combined HTML for job {job_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/jobs/<int:job_id>/update-location', methods=['POST'])
def update_job_location(job_id):
    data = request.get_json()
    new_location = data.get('location', '')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE jobs SET location = ? WHERE id = ?", (new_location, job_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'location': new_location})

if __name__ == '__main__':
    # Check if database exists
    if not os.path.exists(DATABASE_PATH):
        print(f"Database not found at {DATABASE_PATH}")
        print("Please run the LinkedIn scraper first to create the database.")
        exit(1)
    
    print(f"Starting API server...")
    print(f"Database: {DATABASE_PATH}")
    print(f"API will be available at: http://localhost:5000")
    print(f"React frontend should connect to: http://localhost:3000")
    
    app.run(debug=True, host='0.0.0.0', port=5000) 