# Creation process tutorial
by Eldiiar Bekbolotov - June 6, 2025. 15 min read.

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

The .env file will contain environmental variables necessary for the app to run locally, and the gitignore file will prevent unnecessary files and folders from being committed to GitHub, like .env and venv. It is extremely important that you never share the contents of your .env file publicly, as it contains sensitive information like your database password, which can open up huge security vulnerabilities.

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

Before programming your own fullstack project, I advise you to get a piece of paper and brainstorm everything related to the backend - the backbone of your app's functionality.

It's great if you know all the features that you need to implement, because then it becomes like a todo list which you complete one by one. 

For this app, I had the following functionalities in mind:

```Sign Up -> Account creation (database) -> Email Confirmation -> Account verification (database)```

```Sign Up form fields: email, password, username, handle```

```Login form fields: email, password```

```Login -> Increment total logins -> Set last login to current date```

Creating a sitemap is also useful and will speed up the development process.

```
Sitemap: About, Blog, Help Center, Terms of Service (ToS), Privacy Policy, Community Guidelines, Courses, Welcome, Learner Dashboard, Course View, Lesson View
```

## Programming Overview
An overview of the main Python libraries I used that you will probably use are:

  <em>Flask, a Python web framework: Backbone of the whole project, routes every HTML page in the templates folder/connects everything with Python. 
  
  psycopg2, a PostgreSQL database adapter for Python: Allows my Flask application to connect directly to and interact with the PostgreSQL database. Very useful.
  
  Supabase client to create/update my database using Python, essentially simplifies working with Supabase without writing raw SQL for every interaction.
  
  Jinja2, a Python templating engine for my HTMl files: I use it to dynamically generate HTML content by embedding Python code in my HTML files.
  
  gunicorn, a Python WSGI HTTP Server for UNIX: Used by production environment (in this case, Render) to serve my Flask application.
  
  dotenv, like the name suggests, "reads key-value pairs from a .env file and can set them as environment variables", according to their package description</em>

If you have prior experience (even a little bit) with creating static websites using HTML, CSS, JavaScript, and also know some Python, using these Python libraries will be fairly simple. You can look into their documentation online and learn it on the go, as they are written very professionally (even I was fairly new these libraries and had to go to the documentation multiple times).

After creating the basic HTML pages, we need to route them using Flask. 
e.g.: using Flask decorators, we can set the URL (e.g. eldiiar-academy.onrender.com/) to render the index.html template.
```
@app.route("/")
def index():
    return render_template("index.html")
```
Key term: Routing: Mapping specific URLs to corresponding functions or pieces of code within a web application.

A simplified example of the entire codebase would look like this:

<em>templates folder contains HTML files

HTML files that need to receive data from server will use a simple JavaScript fetch function to make network requests

app.py will contain all routes - for every HTML file

route functions will contain the majority of the code associated with the specific function the file requires

functions that need to receive and send data will have all of the required code inside the function (cleaner codebase)

in app.py, all of the data read, created, and deleted will be pulled using the Supabase client (cur.execute)

meanwhile, all of the data sent back to the required HTML files will be `return`ed through `jsonify`
</em>

jsonify is a small library, we are using it to turn a Python dictionary into a JSON formatted response.

It is important to get everything running by setting up the basic functionalities first. I spent way too much time debugging my app's Python logic when the bug was actually SQL/database related, so I had to rehaul the database a few times before it finally worked.

### Thanks for reading - Good luck with your fullstack Python project!
Extra materials: Visit GETTINGSTARTED.md for terminal setup guide.
