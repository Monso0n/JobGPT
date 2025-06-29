import os
import json
import openai
import re
import subprocess
import sys
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Try to import db module, but don't fail if it's not available
try:
    import db
except ImportError:
    # If running as a standalone script, db might not be available
    db = None

# --- Configuration ---
MASTER_RESUME_PATH = "mydetails/master_resume.json"
MASTER_COVER_LETTER_PATH = "mydetails/master_coverletter.json"
CAREER_FACTS_PATH = "mydetails/careerfacts.txt"

# Resume prompts
RESUME_SYSTEM_PROMPT_PATH = "mydetails/prompts/resume_system_prompt.txt"
RESUME_USER_PROMPT_PATH = "mydetails/prompts/resume_user_prompt.txt"

# Cover letter prompts
COVER_LETTER_SYSTEM_PROMPT_PATH = "mydetails/prompts/cover_letter_system_prompt.txt"
COVER_LETTER_USER_PROMPT_PATH = "mydetails/prompts/cover_letter_user_prompt.txt"

MODEL_NAME = "gpt-4o"

TEMPERATURE_COVERLETTER = 0.4
TEMPERATURE_RESUME = 0.3
MAX_TOKENS = 4000
OUTPUT_BASE_DIR = "job_applications"

def get_today_date():
    """Returns today's date in the format 'Month Day, Year' (e.g., 'January 27, 2025')"""
    return datetime.now().strftime("%B %d, %Y")

def load_prompt(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()

def load_master_resume():
    """Loads the master resume from the specified JSON file."""
    try:
        with open(MASTER_RESUME_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: Master resume file not found at '{MASTER_RESUME_PATH}'")
        return None
    except json.JSONDecodeError:
        print(f"❌ Error: Could not decode JSON from '{MASTER_RESUME_PATH}'")
        return None

def load_master_cover_letter():
    """Loads the master cover letter from the specified JSON file."""
    try:
        with open(MASTER_COVER_LETTER_PATH, 'r', encoding='utf-8') as f:
            master_cover_letter = json.load(f)
            # Update the date to today's date
            master_cover_letter['coverLetter']['date'] = get_today_date()
            return master_cover_letter
    except FileNotFoundError:
        print(f"❌ Error: Master cover letter file not found at '{MASTER_COVER_LETTER_PATH}'")
        return None
    except json.JSONDecodeError:
        print(f"❌ Error: Could not decode JSON from '{MASTER_COVER_LETTER_PATH}'")
        return None

def load_career_facts():
    """Loads the career facts from the specified text file."""
    try:
        with open(CAREER_FACTS_PATH, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"⚠️  Warning: Career facts file not found at '{CAREER_FACTS_PATH}'. Using empty string.")
        return ""
    except Exception as e:
        print(f"⚠️  Warning: Could not read career facts file: {e}. Using empty string.")
        return ""

def clean_location(location: str) -> str:
    """Remove parenthesis and their contents from a location string."""
    return re.sub(r"\s*\(.*?\)", "", location).strip()

def generate_tailored_resume(job: dict):
    """Generate a tailored resume using OpenAI API."""
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("❌ OPENAI_API_KEY environment variable not set.")
    
    client = openai.OpenAI(api_key=api_key)
    
    # Load master resume and prompts
    master_resume = load_master_resume()
    career_facts = load_career_facts()
    resume_system_prompt = load_prompt(RESUME_SYSTEM_PROMPT_PATH)
    resume_user_prompt = load_prompt(RESUME_USER_PROMPT_PATH)
    
    if not master_resume:
        raise ValueError("❌ Could not load master resume.")
    
    if not resume_system_prompt:
        raise ValueError("❌ Could not load resume system prompt.")
    
    if not resume_user_prompt:
        raise ValueError("❌ Could not load resume user prompt.")

    # Format the user prompt with job context
    formatted_user_prompt = resume_user_prompt.format(
        job_title=job["title"],
        company_name=job["company"],
        job_description=job["description"],
        career_facts=career_facts,
        master_resume_json=json.dumps(master_resume, indent=2)
    )

    messages = [
        {
            "role": "system",
            "content": resume_system_prompt
        },
        {
            "role": "user",
            "content": formatted_user_prompt
        }
    ]

    try:
        print("🤖 Making API call to generate tailored resume...")
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=TEMPERATURE_RESUME,
            max_tokens=MAX_TOKENS,
            response_format={"type": "json_object"}
        )
        
        result = response.choices[0].message.content
        print("✅ Successfully received tailored resume from AI.")
        
        # Parse and validate the response
        try:
            tailored_resume = json.loads(result)
            json.dumps(tailored_resume)  # Validate JSON structure
            return tailored_resume
            
        except json.JSONDecodeError:
            print("❌ Error: AI response was not valid JSON.")
            print("Raw AI Output:\n", result)
            return None
            
    except Exception as e:
        print(f"❌ An error occurred with the OpenAI API call: {e}")
        return None

def generate_tailored_cover_letter(job: dict, tailored_resume: dict):
    """Generate a tailored cover letter using OpenAI API."""
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("❌ OPENAI_API_KEY environment variable not set.")
    
    client = openai.OpenAI(api_key=api_key)

    # Load master documents and prompts
    master_resume = load_master_resume()
    master_cover_letter = load_master_cover_letter()
    career_facts = load_career_facts()
    cover_letter_system_prompt = load_prompt(COVER_LETTER_SYSTEM_PROMPT_PATH)
    cover_letter_user_prompt = load_prompt(COVER_LETTER_USER_PROMPT_PATH)
    
    # Enhanced error handling for missing data
    if not master_resume:
        raise ValueError("❌ Could not load master resume.")
    if not master_cover_letter:
        raise ValueError("❌ Could not load master cover letter.")
    if not career_facts:
        raise ValueError("❌ Could not load career facts.")
    if not cover_letter_system_prompt:
        raise ValueError("❌ Could not load cover letter system prompt.")
    if not cover_letter_user_prompt:
        raise ValueError("❌ Could not load cover letter user prompt.")

    # Format the user prompt with job context
    job_location = clean_location(job.get("location", ""))
    formatted_user_prompt = cover_letter_user_prompt.format(
        job_title=job["title"],
        company_name=job["company"],
        job_description=job["description"],
        job_location=job_location,
        tailored_resume_json=json.dumps(tailored_resume, indent=2),
        master_cover_letter_json=json.dumps(master_cover_letter, indent=2)
    )

    messages = [
        {
            "role": "system",
            "content": cover_letter_system_prompt
        },
        {
            "role": "user",
            "content": formatted_user_prompt
        }
    ]

    try:
        print("🤖 Making API call to generate tailored cover letter...")
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=TEMPERATURE_COVERLETTER,
            max_tokens=MAX_TOKENS,
            response_format={"type": "json_object"}
        )
        
        result = response.choices[0].message.content
        print("✅ Successfully received tailored cover letter from AI.")
        
        # Parse and validate the response
        try:
            tailored_cover_letter = json.loads(result)
            json.dumps(tailored_cover_letter)  # Validate JSON structure
            return tailored_cover_letter
            
        except json.JSONDecodeError:
            print("❌ Error: AI response was not valid JSON.")
            print("Raw AI Output:\n", result)
            return None
            
    except Exception as e:
        print(f"❌ An error occurred with the OpenAI API call: {e}")
        return None

def sanitize_filename(name: str) -> str:
    """Removes invalid characters from a string to make it a valid filename component."""
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    name = re.sub(r'\s+', '_', name)
    return name.strip('_').lower()

def generate_html_from_json(json_filepath: Path, html_filepath: Path, document_type: str = "resume"):
    """
    Generate an HTML file from a JSON file using the resumed command.
    
    Args:
        json_filepath: Path to the JSON file
        html_filepath: Path where the HTML should be saved
        document_type: Either "resume" or "cover_letter" to determine which template to use
    """
    print(f"📄 Generating {document_type} HTML using 'resumed'...")
    resume_dir = Path("mydetails").resolve()
    print(f"🔩 Changing working directory to: {resume_dir}")
    
    # For cover letters, we need to handle the nested JSON structure
    temp_json_filepath = json_filepath
    if document_type == "cover letter":
        try:
            # Read the original JSON file
            with open(json_filepath, 'r', encoding='utf-8') as f:
                original_data = json.load(f)
            
            # Check if the cover letter is nested under masterCoverLetter
            if 'masterCoverLetter' in original_data and 'coverLetter' in original_data['masterCoverLetter']:
                print("🔧 Detected nested cover letter structure, extracting...")
                # Extract the cover letter data and create a new structure
                cover_letter_data = original_data['masterCoverLetter']['coverLetter']
                basics_data = original_data['masterCoverLetter'].get('basics', {})
                
                # Create the correct structure for the template
                template_data = {
                    "basics": basics_data,
                    "coverLetter": cover_letter_data
                }
                
                # Create a temporary JSON file with the correct structure
                temp_json_filepath = json_filepath.parent / f"temp_{json_filepath.name}"
                with open(temp_json_filepath, 'w', encoding='utf-8') as f:
                    json.dump(template_data, f, indent=2)
                
                print(f"✅ Created temporary JSON with correct structure: {temp_json_filepath}")
            else:
                print("ℹ️  Cover letter structure appears to be correct, proceeding...")
        except Exception as e:
            print(f"⚠️  Warning: Could not process nested JSON structure: {e}")
            print("ℹ️  Proceeding with original JSON file...")
    
    command = [
        "npx", "resumed", "render",
        str(temp_json_filepath.resolve()),
        "--theme", "jsonresume-theme-scholar",
        "-o", str(html_filepath.resolve())
    ]
    
    try:
        # On Windows, npx is often a .cmd file. We handle this for cross-platform compatibility.
        npx_command = "npx"
        if sys.platform == "win32":
            try:
                # Check if 'npx' works
                subprocess.run([npx_command, "--version"], check=True, capture_output=True, cwd=resume_dir)
            except FileNotFoundError:
                # If not, try 'npx.cmd'
                npx_command = "npx.cmd"

        print(f"🚀 Running command: {' '.join(command)}")
        
        # Run the command
        result = subprocess.run(
            command,
            cwd=resume_dir,
            capture_output=True,
            text=True,
            check=True
        )
        
        print(f"✅ Successfully generated {document_type} HTML: {html_filepath}")
        print(f"📊 Command output: {result.stdout}")
        
        # Verify the file was created
        if html_filepath.exists():
            file_size = html_filepath.stat().st_size
            print(f"📁 HTML file created successfully. Size: {file_size} bytes")
            
            # Clean up temporary JSON file if it was created
            if document_type == "cover letter" and temp_json_filepath != json_filepath:
                try:
                    temp_json_filepath.unlink()
                    print(f"🧹 Cleaned up temporary JSON file: {temp_json_filepath}")
                except Exception as e:
                    print(f"⚠️  Warning: Could not clean up temporary JSON file: {e}")
            
            return True
        else:
            print(f"❌ HTML file was not created at expected location: {html_filepath}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running resumed command: {e}")
        print(f"📄 Command output: {e.stdout}")
        print(f"❌ Error output: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def generate_pdf_from_html(html_filepath: Path, pdf_filepath: Path):
    """
    Generate a PDF file from an HTML file using wkhtmltopdf with 0.5 inch margins.
    
    Args:
        html_filepath: Path to the HTML file
        pdf_filepath: Path where the PDF should be saved
    """
    print(f"📄 Generating PDF from HTML using wkhtmltopdf...")
    
    # wkhtmltopdf command with 0.5 inch margins
    command = [
        "wkhtmltopdf",
        "--margin-top", "0.5in",
        "--margin-bottom", "0in", 
        "--margin-left", "0.5in",
        "--margin-right", "0.5in",
        "--page-size", "Letter",
        str(html_filepath.resolve()),
        str(pdf_filepath.resolve())
    ]
    
    try:
        print(f"🚀 Running command: {' '.join(command)}")
        
        # Run the command
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )
        
        print(f"✅ Successfully generated PDF: {pdf_filepath}")
        
        # Verify the file was created
        if pdf_filepath.exists():
            file_size = pdf_filepath.stat().st_size
            print(f"📁 PDF file created successfully. Size: {file_size} bytes")
            return True
        else:
            print(f"❌ PDF file was not created at expected location: {pdf_filepath}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running wkhtmltopdf command: {e}")
        print(f"📄 Command output: {e.stdout}")
        print(f"❌ Error output: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def combine_pdfs(cover_letter_pdf: Path, resume_pdf: Path, combined_pdf: Path):
    """
    Combine two PDF files with cover letter first, then resume.
    
    Args:
        cover_letter_pdf: Path to the cover letter PDF
        resume_pdf: Path to the resume PDF  
        combined_pdf: Path where the combined PDF should be saved
    """
    print(f"📄 Combining PDFs (cover letter + resume) into one PDF...")
    
    try:
        from PyPDF2 import PdfMerger
        
        # Check that both PDFs exist
        if not cover_letter_pdf.exists():
            raise FileNotFoundError(f"Cover letter PDF not found: {cover_letter_pdf}")
        if not resume_pdf.exists():
            raise FileNotFoundError(f"Resume PDF not found: {resume_pdf}")
        
        # Create PDF merger
        merger = PdfMerger()
        
        # Add cover letter first, then resume
        merger.append(str(cover_letter_pdf))
        merger.append(str(resume_pdf))
        
        # Write the combined PDF
        merger.write(str(combined_pdf))
        merger.close()
        
        print(f"✅ Successfully combined PDFs: {combined_pdf}")
        
        # Verify the file was created
        if combined_pdf.exists():
            file_size = combined_pdf.stat().st_size
            print(f"📁 Combined PDF created successfully. Size: {file_size} bytes")
            return True
        else:
            print(f"❌ Combined PDF was not created at expected location: {combined_pdf}")
            return False
            
    except ImportError:
        print("❌ PyPDF2 is not installed. Please install it with: pip install PyPDF2")
        return False
    except Exception as e:
        print(f"❌ Error combining PDFs: {e}")
        return False


