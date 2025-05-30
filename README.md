# Eldiiar Academy

A Khan Academy-style learning platform built with Flask, Python, and Supabase. This platform provides an interactive learning experience with courses, lessons, and a social discussion system.

## Features

- ✅ User Authentication

  - Signup/login with email + password via Supabase Auth
  - Auth state stored client-side securely
  - Public User Profiles with:
    - Username (displayed)
    - @handle (used in URLs for public profile)
    - Bio (max 180 characters)
    - Avatar (initials from username, max 2 letters)
    - Account creation date
    - Last login date
    - Badges
    - Energy points

- ✅ Dashboard Page

  - Displays all profile fields
  - Visual representation of badges
  - Progress tracking

- ✅ Course System
  - Browse Courses page
  - Individual course pages
  - Units and Lessons under each course
  - "Mark as completed" functionality
  - Full social media style discussion section with:
    - Likes/Dislikes
    - Edit/Delete messages
    - Reply to comments

## Tech Stack

- **Frontend:**

  - HTML
  - CSS
  - Vanilla JavaScript
  - Tailwind CSS

- **Backend:**
  - Flask (Python)
  - Supabase (PostgreSQL + Auth)
  - Render (Deployment)

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git
- Supabase account
- Render account (for deployment)

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/eldiiar-academy.git
   cd eldiiar-academy
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the root directory with your Supabase credentials:

   ```
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   SUPABASE_DB_NAME=your_db_name
   SUPABASE_DB_USER=your_db_user
   SUPABASE_DB_PASSWORD=your_db_password
   SUPABASE_DB_HOST=your_db_host
   SUPABASE_DB_PORT=5432
   FLASK_SECRET_KEY=your_secret_key
   ```

5. Initialize the database:

   ```bash
   flask init-db
   ```

6. Run the development server:
   ```bash
   flask run
   ```

The application will be available at `http://localhost:5000`

### Deployment

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Set the following:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
   - Add all environment variables from your `.env` file

## Project Structure

```
eldiiar-academy/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── .env               # Environment variables (not in git)
├── .gitignore         # Git ignore file
├── static/            # Static files (CSS, JS, images)
│   ├── css/
│   ├── js/
│   └── images/
└── templates/         # HTML templates
    ├── base.html      # Base template
    ├── index.html     # Home page
    ├── login.html     # Login page
    ├── signup.html    # Signup page
    ├── dashboard.html # User dashboard
    └── ...
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Flask](https://flask.palletsprojects.com/)
- [Supabase](https://supabase.io/)
- [Tailwind CSS](https://tailwindcss.com/)
- [Render](https://render.com/)
