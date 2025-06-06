# Creation process tutorial
by Eldiiar Bekbolotov - June 6, 2025

## Eldiiar Academy: a demonstration of a fullstack education website built with Python

Welcome to a beginner-friendly tutorial on the creation of this fullstack educational academy built with Python. You will learn about the systems design, hosting and database setup, and overall process of creating this app. 

Tech stack (you don't need to be fluent in these languages):
HTML, CSS, and JavaScript for the frontend. Python (along with some libraries) for the backend. Supabase database is created using PostgreSQL. Render is used to host web service on the cloud. 

Database and cloud hosting services we will be using will be through their free tier.

This is not a step-by-step tutorial on creating the exact same thing as Eldiiar-Academy. Rather, it is a beginner-friendly comprehensive creation process tutorial that you can learn from to create your own fullstack application.

## Setting up your services
You can use the code editor and version control system of your choice. I used Visual Studio Code and GitHub. 
After opening your repository in your code editor, create the following:
```
static folder
templates folder
app.py file
requirements.txt file
.env file
.gitignore file
```

The .env file will contain environmental variables necessary for our app to run locally, and the gitignore file will prevent unnecessary files and folders from being committed to GitHub, like .env and venv. It is extremely important that you never share the contents of your .env file publicly, as it contains sensitive information like your database password, which can open up huge security vulnerabilities.

Next, create a Render account and Supabase account. It is best if you create your accounts using GitHub.
In Supabase, you will create a new project. You will then go to the Project Settings page and find the API Keys section. Copy and save your public key, you will need it later. Then, click connect project, select Python, and copy and save your transaction pooler information. If you forgot your database password, you can go to Database and reset your password.

Create a .env file in the root directory with your Supabase credentials:

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

In Render, you will need to create a new Web Service. Copy paste your .env file into the environmental variables section in Render.
Now, your project is setup and connected to the necessary services.

## How the system works
An overview of the main Python libraries I used that you will probably use are:
Flask, a Python web framework: Backbone of the whole project, routes every HTML page in the templates folder/connects everything with Python. 
psycopg2, a PostgreSQL database adapter for Python:
Supabase client to create/update my database using Python
Jinja2, a Python templating engine for my HTMl files.
