# JobGPT 🤖

**AI-Powered Resume & Cover Letter Generator**

JobGPT is a full-stack web application that leverages Large Language Models to automatically generate tailored resumes and cover letters for job applications. The system scrapes job postings from LinkedIn, analyzes them with AI, and creates personalized application documents.

## ✨ Features

- **LinkedIn Job Scraping**: Automated scraping of job postings using Playwright
- **AI-Powered Tailoring**: Uses OpenAI GPT-4o to customize resumes and cover letters
- **Real-time Generation**: Instant document generation with live preview
- **PDF Export**: Professional PDF output ready for submission
- **Job Tracking**: SQLite database for managing job applications
- **Modern UI**: React frontend with responsive design
- **Document Combination**: Merge resume and cover letter into single PDF

## 🏗️ Architecture

```
Frontend (React) ←→ Backend (Flask) ←→ OpenAI API
     ↓                    ↓              ↓
  User Interface    Business Logic    AI Generation
```

## 🚀 Tech Stack

### Backend
- **Python 3.12+**
- **Flask** - Web framework
- **OpenAI API** - AI document generation
- **SQLite** - Database
- **Playwright** - Web scraping
- **PyPDF2** - PDF manipulation

### Frontend
- **React 19** - UI framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **React Router** - Navigation

### Document Generation
- **resumed** - JSON to HTML conversion
- **wkhtmltopdf** - HTML to PDF conversion
- **JsonResume** - Standardized resume format

## 📦 Installation

### Prerequisites
- Python 3.12+
- Node.js 18+
- wkhtmltopdf
- OpenAI API key

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/Monso0n/JobGPT.git
   cd JobGPT
   ```

2. **Install Python dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Install Node.js dependencies**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

4. **Set up environment variables**
   ```bash
   export OPENAI_API_KEY="your-openai-api-key-here"
   ```

5. **Install system dependencies**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install wkhtmltopdf
   
   # macOS
   brew install wkhtmltopdf
   
   # Windows
   # Download from https://wkhtmltopdf.org/downloads.html
   ```

## 🎯 Usage

### 1. Start the Backend
```bash
python api_server.py
```
The API server will run on `http://localhost:5000`

### 2. Start the Frontend
```bash
cd frontend
npm start
```
The React app will run on `http://localhost:3000`

### 3. Generate Documents
1. Browse scraped jobs in the web interface
2. Click "Generate Resume" to create a tailored resume
3. Click "Generate Cover Letter" to create a matching cover letter
4. Click "Combine Files" to merge both documents
5. View and download the generated PDFs

## 📁 Project Structure

```
JobGPT/
├── api_server.py              # Flask API server
├── src/
│   ├── ai_tailor.py          # AI document generation
│   ├── db.py                 # Database operations
│   └── scraper.py            # LinkedIn scraper
├── frontend/                 # React application
│   ├── src/
│   │   ├── components/       # React components
│   │   └── App.tsx          # Main app component
│   └── package.json
├── mydetails/               # Personal data & templates
│   ├── master_resume.json   # Master resume template
│   ├── master_coverletter.json # Master cover letter template
│   └── prompts/             # AI prompts
├── data/                    # Scraped job data
├── job_applications/        # Generated documents
└── migrations/              # Database migrations
```

## 🔧 Configuration

### Master Templates
- `mydetails/master_resume.json` - Your base resume in JsonResume format
- `mydetails/master_coverletter.json` - Your base cover letter template

### AI Prompts
- `mydetails/prompts/resume_system_prompt.txt` - Resume generation system prompt
- `mydetails/prompts/resume_user_prompt.txt` - Resume generation user prompt
- `mydetails/prompts/cover_letter_system_prompt.txt` - Cover letter system prompt
- `mydetails/prompts/cover_letter_user_prompt.txt` - Cover letter user prompt

## 🤖 AI Features

### Resume Tailoring
- Analyzes job description for key requirements
- Selects most relevant skills and projects
- Maintains factual accuracy from master resume
- Optimizes for one-page format

### Cover Letter Generation
- References tailored resume for consistency
- Personalizes content for specific company/role
- Maintains professional tone and structure
- Includes specific achievements and skills

## 📊 API Endpoints

### Job Management
- `GET /api/jobs` - List all jobs with filtering
- `GET /api/jobs/<id>` - Get specific job details
- `POST /api/jobs/<id>/toggle-like` - Toggle job like status
- `POST /api/jobs/<id>/toggle-applied` - Toggle applied status

### Document Generation
- `POST /api/jobs/<id>/generate-resume` - Generate tailored resume
- `POST /api/jobs/<id>/generate-cover-letter` - Generate cover letter
- `POST /api/jobs/<id>/combine-files` - Combine documents

### File Serving
- `GET /api/jobs/<id>/resume-html` - Serve resume HTML
- `GET /api/jobs/<id>/cover-letter-html` - Serve cover letter HTML
- `GET /api/jobs/<id>/combined-html` - Serve combined HTML

## 🔒 Security

- API keys stored in environment variables
- Sensitive data excluded from repository
- Input validation on all endpoints
- CORS enabled for frontend communication

## 🚀 Deployment

### Local Development
```bash
# Terminal 1 - Backend
python api_server.py

# Terminal 2 - Frontend
cd frontend && npm start
```

### Production
1. Set up environment variables
2. Install system dependencies
3. Run backend with production WSGI server
4. Build and serve frontend

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [JsonResume](https://jsonresume.org/) - Resume schema standard
- [OpenAI](https://openai.com/) - AI capabilities
- [Playwright](https://playwright.dev/) - Web scraping
- [React](https://reactjs.org/) - Frontend framework

## 📞 Contact

Mayank Kainth - [LinkedIn](https://www.linkedin.com/in/mayank-kainth-8a0989195/) - mayank.kainth@torontomu.ca

Project Link: [https://github.com/Monso0n/JobGPT](https://github.com/Monso0n/JobGPT)

---

⭐ **Star this repository if you find it helpful!**