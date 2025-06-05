import os
from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    session,
    redirect,
    url_for,
    flash,
)
from dotenv import load_dotenv
from supabase import create_client, Client
import time
import psycopg2
import psycopg2.extras
from datetime import datetime
import pytz
import re
import json

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret")


# Custom filter to extract YouTube video ID
@app.template_filter("youtube_id")
def youtube_id_filter(url):
    if not url:
        return ""
    # Regular expressions for different YouTube URL formats
    patterns = [
        r"(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?]+)",
        r"youtube\.com\/embed\/([^&\n?]+)",
        r"youtube\.com\/v\/([^&\n?]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return ""


# Initialize Supabase client
supabase: Client = create_client(
    os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY")
)


# PostgreSQL connection (Supabase DB)
def get_db_connection():
    return psycopg2.connect(
        dbname=os.environ.get("SUPABASE_DB_NAME"),
        user=os.environ.get("SUPABASE_DB_USER"),
        password=os.environ.get("SUPABASE_DB_PASSWORD"),
        host=os.environ.get("SUPABASE_DB_HOST"),
        port=os.environ.get("SUPABASE_DB_PORT", 5432),
        cursor_factory=psycopg2.extras.RealDictCursor,
    )


def init_db():
    """Initialize database schema and policies"""
    try:
        # Create profiles table
        response = (
            supabase.table("profiles")
            .insert(
                {
                    "id": "uuid references auth.users(id) primary key",
                    "username": "text unique not null",
                    "handle": "text unique not null",
                    "bio": "text check (char_length(bio) <= 180)",
                    "avatar": "text",
                    "account_created": "timestamp with time zone default now()",
                    "last_logged_in": "timestamp with time zone default now()",
                    "badges": "text[] default '{}'",
                    "energy_points": "integer default 0",
                }
            )
            .execute()
        )
        print("Profiles table created:", response)

        # Create courses table
        response = (
            supabase.table("courses")
            .insert(
                {
                    "id": "uuid primary key default uuid_generate_v4()",
                    "title": "text not null",
                    "description": "text",
                    "created_at": "timestamp with time zone default now()",
                }
            )
            .execute()
        )
        print("Courses table created:", response)

        # Create units table
        response = (
            supabase.table("units")
            .insert(
                {
                    "id": "uuid primary key default uuid_generate_v4()",
                    "course_id": "uuid references courses(id) on delete cascade",
                    "title": "text not null",
                    "created_at": "timestamp with time zone default now()",
                }
            )
            .execute()
        )
        print("Units table created:", response)

        # Create lessons table
        response = (
            supabase.table("lessons")
            .insert(
                {
                    "id": "uuid primary key default uuid_generate_v4()",
                    "unit_id": "uuid references units(id) on delete cascade",
                    "title": "text not null",
                    "content": "text",
                    "created_at": "timestamp with time zone default now()",
                }
            )
            .execute()
        )
        print("Lessons table created:", response)

        # Create lesson_completions table
        response = (
            supabase.table("lesson_completions")
            .insert(
                {
                    "id": "uuid primary key default uuid_generate_v4()",
                    "user_id": "uuid references auth.users(id) on delete cascade",
                    "lesson_id": "uuid references lessons(id) on delete cascade",
                    "completed_at": "timestamp with time zone default now()",
                    "unique(user_id, lesson_id)": "",
                }
            )
            .execute()
        )
        print("Lesson completions table created:", response)

        # Create comments table
        response = (
            supabase.table("comments")
            .insert(
                {
                    "id": "uuid primary key default uuid_generate_v4()",
                    "lesson_id": "uuid references lessons(id) on delete cascade",
                    "user_id": "uuid references auth.users(id) on delete cascade",
                    "content": "text not null",
                    "parent_id": "uuid references comments(id) on delete cascade",
                    "created_at": "timestamp with time zone default now()",
                    "updated_at": "timestamp with time zone default now()",
                }
            )
            .execute()
        )
        print("Comments table created:", response)

        print("Database initialized successfully!")
        return True
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        return False


def setup_rls_policies():
    """Set up Row Level Security policies"""
    try:
        # Profiles policies
        supabase.table("profiles").insert(
            {
                "policy_name": "Public profiles are viewable by everyone",
                "definition": "true",
                "operation": "select",
            }
        ).execute()

        supabase.table("profiles").insert(
            {
                "policy_name": "Users can update their own profile",
                "definition": "auth.uid() = id",
                "operation": "update",
            }
        ).execute()

        # Courses policies
        supabase.table("courses").insert(
            {
                "policy_name": "Courses are viewable by everyone",
                "definition": "true",
                "operation": "select",
            }
        ).execute()

        # Units policies
        supabase.table("units").insert(
            {
                "policy_name": "Units are viewable by everyone",
                "definition": "true",
                "operation": "select",
            }
        ).execute()

        # Lessons policies
        supabase.table("lessons").insert(
            {
                "policy_name": "Lessons are viewable by everyone",
                "definition": "true",
                "operation": "select",
            }
        ).execute()

        # Lesson completions policies
        supabase.table("lesson_completions").insert(
            {
                "policy_name": "Users can view their own completions",
                "definition": "auth.uid() = user_id",
                "operation": "select",
            }
        ).execute()

        supabase.table("lesson_completions").insert(
            {
                "policy_name": "Users can insert their own completions",
                "definition": "auth.uid() = user_id",
                "operation": "insert",
            }
        ).execute()

        # Comments policies
        supabase.table("comments").insert(
            {
                "policy_name": "Comments are viewable by everyone",
                "definition": "true",
                "operation": "select",
            }
        ).execute()

        supabase.table("comments").insert(
            {
                "policy_name": "Users can insert their own comments",
                "definition": "auth.uid() = user_id",
                "operation": "insert",
            }
        ).execute()

        supabase.table("comments").insert(
            {
                "policy_name": "Users can update their own comments",
                "definition": "auth.uid() = user_id",
                "operation": "update",
            }
        ).execute()

        supabase.table("comments").insert(
            {
                "policy_name": "Users can delete their own comments",
                "definition": "auth.uid() = user_id",
                "operation": "delete",
            }
        ).execute()

        print("RLS policies set up successfully!")
        return True
    except Exception as e:
        print(f"Error setting up RLS policies: {str(e)}")
        return False


def ensure_schema():
    """Create all tables and RLS policies if they do not exist."""
    conn = get_db_connection()
    cur = conn.cursor()

    # Enable uuid extension if not exists
    cur.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')

    # Create tables
    tables = {
        "profiles": """
            CREATE TABLE IF NOT EXISTS profiles (
                id UUID PRIMARY KEY REFERENCES auth.users(id),
                username TEXT UNIQUE NOT NULL,
                handle TEXT UNIQUE NOT NULL,
                bio TEXT,
                avatar TEXT,
                account_created TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                last_logged_in TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                badges TEXT[] DEFAULT '{}',
                energy_points INTEGER DEFAULT 0,
                is_admin BOOLEAN DEFAULT FALSE
            );
        """,
        "courses": """
            CREATE TABLE IF NOT EXISTS courses (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                title TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                created_by UUID REFERENCES auth.users(id)
            );
        """,
        "units": """
            CREATE TABLE IF NOT EXISTS units (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                course_id UUID REFERENCES courses(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                order_index INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                created_by UUID REFERENCES auth.users(id),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_by UUID REFERENCES auth.users(id)
            );
        """,
        "lessons": """
            CREATE TABLE IF NOT EXISTS lessons (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                unit_id UUID REFERENCES units(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                content TEXT,
                lesson_type TEXT NOT NULL CHECK (lesson_type IN ('text', 'video', 'quiz')),
                video_url TEXT,
                quiz_data JSONB,
                order_index INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                created_by UUID REFERENCES auth.users(id),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_by UUID REFERENCES auth.users(id)
            );
        """,
        "lesson_completions": """
            CREATE TABLE IF NOT EXISTS lesson_completions (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                lesson_id UUID REFERENCES lessons(id) ON DELETE CASCADE,
                user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
                completed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(lesson_id, user_id)
            );
        """,
        "comments": """
            CREATE TABLE IF NOT EXISTS comments (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                lesson_id UUID REFERENCES lessons(id) ON DELETE CASCADE,
                user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
                content TEXT NOT NULL,
                parent_id UUID REFERENCES comments(id) ON DELETE CASCADE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """,
        "login_sessions": """
            CREATE TABLE IF NOT EXISTS login_sessions (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
                login_date DATE NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, login_date)
            );
        """,
    }

    # Create all tables
    for table_name, create_sql in tables.items():
        cur.execute(create_sql)
        print(f"Ensured table exists: {table_name}")

    # Ensure is_admin column exists in profiles
    cur.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='profiles' AND column_name='is_admin'
            ) THEN
                ALTER TABLE profiles ADD COLUMN is_admin BOOLEAN DEFAULT FALSE;
            END IF;
        END$$;
    """)

    # Ensure created_by column exists in courses
    cur.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='courses' AND column_name='created_by'
            ) THEN
                ALTER TABLE courses ADD COLUMN created_by UUID REFERENCES auth.users(id);
            END IF;
        END$$;
    """)

    # Ensure order_index columns exist
    cur.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='units' AND column_name='order_index'
            ) THEN
                ALTER TABLE units ADD COLUMN order_index INTEGER NOT NULL DEFAULT 0;
            END IF;
            
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='lessons' AND column_name='order_index'
            ) THEN
                ALTER TABLE lessons ADD COLUMN order_index INTEGER NOT NULL DEFAULT 0;
            END IF;
        END$$;
    """)

    # Ensure lesson_type and video_url columns exist in lessons
    cur.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='lessons' AND column_name='lesson_type'
            ) THEN
                ALTER TABLE lessons ADD COLUMN lesson_type TEXT NOT NULL DEFAULT 'text' CHECK (lesson_type IN ('text', 'video', 'quiz'));
            END IF;
            
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='lessons' AND column_name='video_url'
            ) THEN
                ALTER TABLE lessons ADD COLUMN video_url TEXT;
            END IF;
            
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='lessons' AND column_name='quiz_data'
            ) THEN
                ALTER TABLE lessons ADD COLUMN quiz_data JSONB;
            END IF;
        END$$;
    """)

    # Ensure lesson metadata columns exist
    cur.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='lessons' AND column_name='created_by'
            ) THEN
                ALTER TABLE lessons ADD COLUMN created_by UUID REFERENCES auth.users(id);
            END IF;
            
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='lessons' AND column_name='updated_at'
            ) THEN
                ALTER TABLE lessons ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
            END IF;
            
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='lessons' AND column_name='updated_by'
            ) THEN
                ALTER TABLE lessons ADD COLUMN updated_by UUID REFERENCES auth.users(id);
            END IF;
        END$$;
    """)

    # Ensure unit metadata columns exist
    cur.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='units' AND column_name='created_by'
            ) THEN
                ALTER TABLE units ADD COLUMN created_by UUID REFERENCES auth.users(id);
            END IF;
            
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='units' AND column_name='updated_at'
            ) THEN
                ALTER TABLE units ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
            END IF;
            
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='units' AND column_name='updated_by'
            ) THEN
                ALTER TABLE units ADD COLUMN updated_by UUID REFERENCES auth.users(id);
            END IF;
        END$$;
    """)

    # Enable Row Level Security
    cur.execute("ALTER TABLE profiles ENABLE ROW LEVEL SECURITY")
    cur.execute("ALTER TABLE courses ENABLE ROW LEVEL SECURITY")
    cur.execute("ALTER TABLE units ENABLE ROW LEVEL SECURITY")
    cur.execute("ALTER TABLE lessons ENABLE ROW LEVEL SECURITY")
    cur.execute("ALTER TABLE lesson_completions ENABLE ROW LEVEL SECURITY")
    cur.execute("ALTER TABLE comments ENABLE ROW LEVEL SECURITY")
    cur.execute("ALTER TABLE login_sessions ENABLE ROW LEVEL SECURITY")

    # Helper function to create policy if it doesn't exist
    def create_policy_if_not_exists(table_name, policy_name, operation, using_clause):
        cur.execute(f"""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_policies 
                    WHERE tablename = '{table_name}' 
                    AND policyname = '{policy_name}'
                ) THEN
                    EXECUTE 'CREATE POLICY "{policy_name}" ON {table_name} 
                        FOR {operation} 
                        {"USING" if operation in ["SELECT", "DELETE"] else "WITH CHECK"} 
                        ({using_clause})';
                END IF;
            END$$;
        """)

    # Create policies
    # Profiles policies
    create_policy_if_not_exists(
        "profiles", "Public profiles are viewable by everyone", "SELECT", "true"
    )
    create_policy_if_not_exists(
        "profiles", "Users can update their own profile", "UPDATE", "auth.uid() = id"
    )

    # Courses policies
    create_policy_if_not_exists(
        "courses", "Courses are viewable by everyone", "SELECT", "true"
    )
    create_policy_if_not_exists(
        "courses",
        "Only admins can create courses",
        "INSERT",
        "EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND is_admin = true)",
    )
    create_policy_if_not_exists(
        "courses",
        "Only admins can update courses",
        "UPDATE",
        "EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND is_admin = true)",
    )
    create_policy_if_not_exists(
        "courses",
        "Only admins can delete courses",
        "DELETE",
        "EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND is_admin = true)",
    )

    # Units policies
    create_policy_if_not_exists(
        "units", "Units are viewable by everyone", "SELECT", "true"
    )
    create_policy_if_not_exists(
        "units",
        "Only admins can create units",
        "INSERT",
        "EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND is_admin = true)",
    )
    create_policy_if_not_exists(
        "units",
        "Only admins can update units",
        "UPDATE",
        "EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND is_admin = true)",
    )
    create_policy_if_not_exists(
        "units",
        "Only admins can delete units",
        "DELETE",
        "EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND is_admin = true)",
    )

    # Lessons policies
    create_policy_if_not_exists(
        "lessons", "Lessons are viewable by everyone", "SELECT", "true"
    )
    create_policy_if_not_exists(
        "lessons",
        "Only admins can create lessons",
        "INSERT",
        "EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND is_admin = true)",
    )
    create_policy_if_not_exists(
        "lessons",
        "Only admins can update lessons",
        "UPDATE",
        "EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND is_admin = true)",
    )
    create_policy_if_not_exists(
        "lessons",
        "Only admins can delete lessons",
        "DELETE",
        "EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND is_admin = true)",
    )

    # Lesson completions policies
    create_policy_if_not_exists(
        "lesson_completions",
        "Users can view their own lesson completions",
        "SELECT",
        "auth.uid() = user_id",
    )
    create_policy_if_not_exists(
        "lesson_completions",
        "Users can create their own lesson completions",
        "INSERT",
        "auth.uid() = user_id",
    )
    create_policy_if_not_exists(
        "lesson_completions",
        "Users can delete their own lesson completions",
        "DELETE",
        "auth.uid() = user_id",
    )

    # Comments policies
    create_policy_if_not_exists(
        "comments", "Comments are viewable by everyone", "SELECT", "true"
    )
    create_policy_if_not_exists(
        "comments", "Users can create comments", "INSERT", "auth.uid() = user_id"
    )
    create_policy_if_not_exists(
        "comments",
        "Users can update their own comments",
        "UPDATE",
        "auth.uid() = user_id",
    )
    create_policy_if_not_exists(
        "comments",
        "Users can delete their own comments",
        "DELETE",
        "auth.uid() = user_id",
    )

    # Login sessions policies
    create_policy_if_not_exists(
        "login_sessions",
        "Users can view their own login sessions",
        "SELECT",
        "auth.uid() = user_id",
    )
    create_policy_if_not_exists(
        "login_sessions",
        "Users can create their own login sessions",
        "INSERT",
        "auth.uid() = user_id",
    )

    conn.commit()
    conn.close()
    print("Database schema and policies have been ensured.")


def update_admin_status():
    """Update admin status for existing users with matching email."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Get the user ID for the admin email
        cur.execute(
            """
            SELECT id FROM auth.users 
            WHERE email = %s
        """,
            ("ebekb1@ocdsb.ca",),
        )
        admin_user = cur.fetchone()

        if admin_user:
            # Update the profile to set is_admin to true
            cur.execute(
                """
                UPDATE profiles 
                SET is_admin = true 
                WHERE id = %s
            """,
                (admin_user["id"],),
            )
            conn.commit()
            print(f"Updated admin status for user {admin_user['id']}")

        conn.close()
    except Exception as e:
        print(f"Error updating admin status: {str(e)}")


# Call ensure_schema and update_admin_status on startup
ensure_schema()
update_admin_status()


# Add context processor for datetime
@app.context_processor
def inject_now():
    return {"now": datetime.now(), "datetime": datetime}


# --- Page Routes ---
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    try:
        # Get profile from database with badges
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT p.*, 
                   COALESCE(p.badges, ARRAY[]::text[]) as badges
            FROM profiles p
            WHERE p.id = %s
        """,
            (user_id,),
        )
        profile = cur.fetchone()
        conn.close()

        if not profile:
            return redirect(
                url_for("signup")
            )  # Redirect to signup if no profile exists

        # Convert datetime strings to datetime objects
        if isinstance(profile.get("account_created"), str):
            profile["account_created"] = datetime.fromisoformat(
                profile["account_created"].replace("Z", "+00:00")
            )
        if isinstance(profile.get("last_logged_in"), str):
            profile["last_logged_in"] = datetime.fromisoformat(
                profile["last_logged_in"].replace("Z", "+00:00")
            )

        return render_template("dashboard.html", profile=profile)
    except Exception as e:
        print(f"Error fetching profile: {str(e)}")
        return "Error loading dashboard", 500


@app.route("/course/<course_id>")
def course(course_id):
    user_id = session.get("user_id")
    user = None
    if user_id:
        try:
            response = (
                supabase.table("profiles").select("*").eq("id", user_id).execute()
            )
            if response.data:
                user = response.data[0]
        except Exception as e:
            print(f"Error fetching user profile for course view: {str(e)}")

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Get course info with counts
        cur.execute(
            """
            SELECT c.*, 
                COUNT(DISTINCT u.id) as units_count,
                COUNT(DISTINCT l.id) as lessons_count
            FROM courses c
            LEFT JOIN units u ON c.id = u.course_id
            LEFT JOIN lessons l ON u.id = l.unit_id
            WHERE c.id = %s
            GROUP BY c.id
        """,
            (course_id,),
        )
        course = cur.fetchone()

        if not course:
            conn.close()
            return "Course not found", 404

        # Get units with their lessons
        cur.execute(
            """
            SELECT u.*, 
                COUNT(l.id) as lessons_count
            FROM units u
            LEFT JOIN lessons l ON u.id = l.unit_id
            WHERE u.course_id = %s
            GROUP BY u.id
            ORDER BY COALESCE(u.order_index, 0)
        """,
            (course_id,),
        )
        units = cur.fetchall()

        # For each unit, get its lessons
        for unit in units:
            cur.execute(
                """
                SELECT l.*, 
                    CASE WHEN lc.id IS NOT NULL THEN true ELSE false END as completed
                FROM lessons l
                LEFT JOIN lesson_completions lc ON l.id = lc.lesson_id AND lc.user_id = %s
                WHERE l.unit_id = %s
                ORDER BY COALESCE(l.order_index, 0)
            """,
                (user_id, unit["id"]),
            )
            unit["lessons"] = cur.fetchall()

        conn.close()
        return render_template("course.html", course=course, units=units, user=user)
    except Exception as e:
        print(f"Error fetching course: {str(e)}")
        return "Error loading course", 500


@app.route("/lesson/<lesson_id>")
def lesson(lesson_id):
    user_id = session.get("user_id")
    print(f"Session user_id: {user_id}")  # Debug log

    if not user_id:
        print("No user_id in session, redirecting to login")  # Debug log
        return redirect(url_for("login"))

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Get lesson details with creator and updater info
        cur.execute(
            """
            SELECT l.*, 
                   c.username as creator_username,
                   u.username as updater_username
            FROM lessons l
            LEFT JOIN profiles c ON l.created_by = c.id
            LEFT JOIN profiles u ON l.updated_by = u.id
            WHERE l.id = %s
        """,
            (lesson_id,),
        )
        lesson = cur.fetchone()

        if not lesson:
            conn.close()
            flash("Lesson not found", "error")
            return redirect(url_for("browse_courses"))

        # Get unit details
        cur.execute(
            """
            SELECT u.*, c.title as course_title
            FROM units u
            JOIN courses c ON u.course_id = c.id
            WHERE u.id = %s
        """,
            (lesson["unit_id"],),
        )
        unit = cur.fetchone()

        # Get all units in the course
        cur.execute(
            """
            SELECT u.*, 
                   COUNT(l.id) as lessons_count
            FROM units u
            LEFT JOIN lessons l ON u.id = l.unit_id
            WHERE u.course_id = %s
            GROUP BY u.id
            ORDER BY u.order_index
        """,
            (unit["course_id"],),
        )
        units = cur.fetchall()

        # Get all lessons in the current unit
        cur.execute(
            """
            SELECT l.*, 
                   CASE WHEN lc.id IS NOT NULL THEN true ELSE false END as completed
            FROM lessons l
            LEFT JOIN lesson_completions lc ON l.id = lc.lesson_id AND lc.user_id = %s
            WHERE l.unit_id = %s
            ORDER BY l.order_index
        """,
            (user_id, unit["id"]),
        )
        lessons = cur.fetchall()

        # Check if lesson is completed
        cur.execute(
            """
            SELECT id FROM lesson_completions 
            WHERE lesson_id = %s AND user_id = %s
        """,
            (lesson_id, user_id),
        )
        completion = cur.fetchone()

        # Get comments for the lesson
        cur.execute(
            """
            SELECT c.*, p.username, p.handle
            FROM comments c
            JOIN profiles p ON c.user_id = p.id
            WHERE c.lesson_id = %s
            ORDER BY c.created_at DESC
        """,
            (lesson_id,),
        )
        comments_result = cur.fetchall()

        # Organize comments and replies
        comments = []
        replies = []

        for comment in comments_result:
            comment_data = {
                "id": comment["id"],
                "user_id": comment["user_id"],
                "content": comment["content"],
                "created_at": comment["created_at"],
                "username": comment["username"],
                "handle": comment["handle"],
                "parent_id": comment["parent_id"],  # Add parent_id to comment data
                "replies": [],
            }

            if comment["parent_id"] is None:
                comments.append(comment_data)
            else:
                replies.append(comment_data)

        # Attach replies to their parent comments
        for reply in replies:
            for comment in comments:
                if reply["parent_id"] == comment["id"]:
                    comment["replies"].append(reply)
                    break

        # Get user profile for admin check
        cur.execute("SELECT * FROM profiles WHERE id = %s", (user_id,))
        user_profile = cur.fetchone()

        if not user_profile:
            print(f"No profile found for user {user_id}")  # Debug log
            conn.close()
            return redirect(url_for("signup"))

        # Create user object with all necessary fields
        user = {
            "id": user_id,
            "is_admin": user_profile["is_admin"],
            "can_comment": True,  # All logged-in users can comment
            "username": user_profile["username"],
            "handle": user_profile["handle"],
        }

        print(f"User object created: {user}")  # Debug log

        conn.close()
        return render_template(
            "lesson.html",
            lesson=lesson,
            unit=unit,
            course={"id": unit["course_id"], "title": unit["course_title"]},
            units=units,
            lessons=lessons,
            completed=bool(completion),
            comments=comments,
            user=user,  # Pass the complete user object
        )
    except Exception as e:
        print(f"Error in lesson route: {str(e)}")
        flash(str(e), "error")
        return redirect(url_for("browse_courses"))


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/signup")
def signup():
    return render_template("signup.html")


@app.route("/logout")
def logout():
    # Clear the session
    session.clear()
    # Redirect to home page
    return redirect(url_for("index"))


@app.route("/browse_courses")
def browse_courses():
    user_id = session.get("user_id")
    user = None
    if user_id:
        try:
            response = (
                supabase.table("profiles").select("*").eq("id", user_id).execute()
            )
            if response.data:
                user = response.data[0]
        except Exception as e:
            print(f"Error fetching user profile for browse_courses: {str(e)}")
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Get courses with detailed information
        cur.execute(
            """
            SELECT c.*, 
                COUNT(DISTINCT u.id) as units_count,
                COUNT(DISTINCT l.id) as lessons_count,
                COUNT(DISTINCT CASE WHEN lc.id IS NOT NULL THEN l.id END) as completed_lessons_count
            FROM courses c
            LEFT JOIN units u ON c.id = u.course_id
            LEFT JOIN lessons l ON u.id = l.unit_id
            LEFT JOIN lesson_completions lc ON l.id = lc.lesson_id AND lc.user_id = %s
            GROUP BY c.id
            ORDER BY c.created_at DESC
        """,
            (user_id,),
        )
        courses = cur.fetchall()

        # For each course, get its units and lessons
        for course in courses:
            cur.execute(
                """
                SELECT u.*, 
                    COUNT(l.id) as lessons_count,
                    COUNT(CASE WHEN lc.id IS NOT NULL THEN 1 END) as completed_lessons_count
                FROM units u
                LEFT JOIN lessons l ON u.id = l.unit_id
                LEFT JOIN lesson_completions lc ON l.id = lc.lesson_id AND lc.user_id = %s
                WHERE u.course_id = %s
                GROUP BY u.id
                ORDER BY COALESCE(u.order_index, 0)
            """,
                (user_id, course["id"]),
            )
            course["units"] = cur.fetchall()

            # For each unit, get its lessons
            for unit in course["units"]:
                cur.execute(
                    """
                    SELECT l.*, 
                        CASE WHEN lc.id IS NOT NULL THEN true ELSE false END as completed
                    FROM lessons l
                    LEFT JOIN lesson_completions lc ON l.id = lc.lesson_id AND lc.user_id = %s
                    WHERE l.unit_id = %s
                    ORDER BY COALESCE(l.order_index, 0)
                """,
                    (user_id, unit["id"]),
                )
                unit["lessons"] = cur.fetchall()

        conn.close()
        return render_template("browse_courses.html", courses=courses, user=user)
    except Exception as e:
        print(f"Error fetching courses: {str(e)}")
        return "Error loading courses", 500


@app.route("/public_profile/<user_id>")
def public_profile(user_id):
    return render_template("public_profile.html", user_id=user_id)


@app.route("/discussion/<lesson_id>")
def discussion(lesson_id):
    return render_template("discussion.html", lesson_id=lesson_id)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/blog")
def blog():
    return render_template("blog.html")


@app.route("/help")
def help_center():
    return render_template("help_center.html")


@app.route("/terms")
def terms():
    return render_template("terms.html", now=datetime.now())


@app.route("/privacy")
def privacy():
    return render_template("privacy.html", now=datetime.now())


@app.route("/guidelines")
def guidelines():
    return render_template("guidelines.html", now=datetime.now())


# --- API Endpoints ---
@app.route("/api/auth/signup", methods=["POST"])
def api_signup():
    data = request.json
    email = data.get("email")
    password = data.get("password")
    username = data.get("username")
    handle = data.get("handle")

    try:
        # Sign up user with Supabase
        auth_response = supabase.auth.sign_up({"email": email, "password": password})
        user = auth_response.user
        print("User signed up:", user)

        # Check if user is admin
        is_admin = email.lower() == "ebekb1@ocdsb.ca"

        # Create profile in profiles table using direct SQL
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO profiles (id, username, handle, is_admin)
            VALUES (%s, %s, %s, %s)
            """,
            (user.id, username, handle, is_admin),
        )
        conn.commit()
        conn.close()

        # Set session
        session["user_id"] = user.id

        return jsonify(
            {
                "message": "Signup successful",
                "user": {"id": user.id, "email": user.email, "is_admin": is_admin},
            }
        ), 200
    except Exception as e:
        print(f"Error during signup: {str(e)}")
        return jsonify({"error": str(e)}), 400


@app.route("/api/auth/login", methods=["POST"])
def api_login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    try:
        # Login user with Supabase
        auth_response = supabase.auth.sign_in_with_password(
            {"email": email, "password": password}
        )
        user = auth_response.user
        print(f"User logged in: {user.id}")  # Debug log

        # Update last_logged_in and record login session using direct SQL
        conn = get_db_connection()
        cur = conn.cursor()

        # Get user profile
        cur.execute("SELECT * FROM profiles WHERE id = %s", (user.id,))
        profile = cur.fetchone()

        if not profile:
            conn.close()
            return jsonify({"error": "Profile not found. Please sign up first."}), 400

        # Update last login time
        cur.execute(
            """
            UPDATE profiles SET last_logged_in = CURRENT_TIMESTAMP WHERE id = %s;
            INSERT INTO login_sessions (user_id, login_date)
            VALUES (%s, CURRENT_DATE)
            ON CONFLICT (user_id, login_date) DO UPDATE SET login_date = CURRENT_DATE;
            """,
            (user.id, user.id),
        )
        conn.commit()
        conn.close()

        # Set session
        session.clear()  # Clear any existing session
        session["user_id"] = user.id
        print(f"Session set: {session.get('user_id')}")  # Debug log

        # Extract relevant user data
        user_data = {
            "id": user.id,
            "email": user.email,
            "username": profile["username"],
            "handle": profile["handle"],
            "is_admin": profile["is_admin"],
        }

        return jsonify({"message": "Login successful", "user": user_data}), 200
    except Exception as e:
        print(f"Error during login: {str(e)}")
        return jsonify({"error": str(e)}), 400


@app.route("/api/profile/<user_id>/login-activity", methods=["GET"])
def api_login_activity(user_id):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Get login activity for the past year
        cur.execute(
            """
            WITH dates AS (
                SELECT generate_series(
                    CURRENT_DATE - INTERVAL '1 year',
                    CURRENT_DATE,
                    '1 day'::interval
                )::date AS date
            )
            SELECT 
                dates.date,
                CASE WHEN ls.login_date IS NOT NULL THEN 1 ELSE 0 END as logged_in
            FROM dates
            LEFT JOIN login_sessions ls ON 
                ls.user_id = %s AND 
                DATE(ls.login_date) = dates.date
            ORDER BY dates.date
        """,
            (user_id,),
        )
        activity_data = cur.fetchall()

        # Get total logins
        cur.execute(
            """
            SELECT COUNT(*) as total 
            FROM login_sessions 
            WHERE user_id = %s
        """,
            (user_id,),
        )
        total_result = cur.fetchone()
        total_logins = total_result["total"] if total_result else 0

        # Format data for chart
        labels = []
        values = []
        for row in activity_data:
            date_str = row["date"].strftime("%Y-%m-%d")
            labels.append(date_str)
            values.append(int(row["logged_in"]))

        return jsonify(
            {"labels": labels, "values": values, "totalLogins": total_logins}
        ), 200

    except Exception as e:
        print(f"Error fetching login activity: {str(e)}")
        return jsonify({"error": "Failed to fetch login activity data"}), 500
    finally:
        if conn:
            conn.close()


@app.route("/api/profile/<user_id>", methods=["GET", "POST", "DELETE"])
def api_profile(user_id):
    try:
        if request.method == "GET":
            # Get profile from profiles table
            response = (
                supabase.table("profiles").select("*").eq("id", user_id).execute()
            )
            if not response.data:
                return jsonify({"error": "Profile not found"}), 404
            return jsonify(response.data[0]), 200
        elif request.method == "POST":
            data = request.json
            # Validate required fields
            if not all(k in data for k in ["username", "handle"]):
                return jsonify({"error": "Username and handle are required"}), 400

            # Validate field lengths
            if len(data["username"]) < 3:
                return jsonify(
                    {"error": "Username must be at least 3 characters long"}
                ), 400
            if len(data["handle"]) < 3:
                return jsonify(
                    {"error": "Handle must be at least 3 characters long"}
                ), 400
            if data.get("bio") and len(data["bio"]) > 180:
                return jsonify({"error": "Bio must be 180 characters or less"}), 400

            # Use direct SQL to check for duplicates
            conn = get_db_connection()
            cur = conn.cursor()

            # Check username
            cur.execute(
                "SELECT id FROM profiles WHERE username = %s AND id != %s",
                (data["username"], user_id),
            )
            if cur.fetchone():
                conn.close()
                return jsonify({"error": "Username is already taken"}), 400

            # Check handle
            cur.execute(
                "SELECT id FROM profiles WHERE handle = %s AND id != %s",
                (data["handle"], user_id),
            )
            if cur.fetchone():
                conn.close()
                return jsonify({"error": "Handle is already taken"}), 400

            # Update profile using direct SQL
            cur.execute(
                """
                UPDATE profiles 
                SET username = %s, handle = %s, bio = %s
                WHERE id = %s
                RETURNING *
                """,
                (data["username"], data["handle"], data.get("bio", ""), user_id),
            )
            updated_profile = cur.fetchone()
            conn.commit()
            conn.close()

            if not updated_profile:
                return jsonify({"error": "Failed to update profile"}), 400

            return jsonify(
                {"message": "Profile updated", "profile": dict(updated_profile)}
            ), 200
        elif request.method == "DELETE":
            # Delete user's auth account
            supabase.auth.admin.delete_user(user_id)

            # Delete profile and related data
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM profiles WHERE id = %s", (user_id,))
            conn.commit()
            conn.close()

            # Clear session
            session.clear()

            return jsonify({"message": "Account deleted successfully"}), 200
    except Exception as e:
        print(f"Error in profile API: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/courses", methods=["GET", "POST"])
def api_courses():
    if request.method == "GET":
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT c.*, 
                    COUNT(DISTINCT u.id) as units_count,
                    COUNT(DISTINCT l.id) as lessons_count
                FROM courses c
                LEFT JOIN units u ON c.id = u.course_id
                LEFT JOIN lessons l ON u.id = l.unit_id
                GROUP BY c.id
                ORDER BY c.created_at DESC
            """)
            courses = cur.fetchall()
            conn.close()
            return jsonify([dict(course) for course in courses])
        except Exception as e:
            print(f"Error fetching courses: {str(e)}")
            return jsonify({"error": str(e)}), 500
    else:  # POST
        if not session.get("user_id"):
            return jsonify({"error": "Unauthorized"}), 401

        # Check if user is admin
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT is_admin FROM profiles WHERE id = %s", (session["user_id"],)
        )
        profile = cur.fetchone()
        if not profile or not profile["is_admin"]:
            conn.close()
            return jsonify({"error": "Only admins can create courses"}), 403

        data = request.json
        if not data or not data.get("title"):
            conn.close()
            return jsonify({"error": "Title is required"}), 400

        try:
            cur.execute(
                """
                INSERT INTO courses (title, description, created_by)
                VALUES (%s, %s, %s)
                RETURNING *
                """,
                (data["title"], data.get("description"), session["user_id"]),
            )
            course = cur.fetchone()
            conn.commit()
            conn.close()
            return jsonify(dict(course)), 201
        except Exception as e:
            conn.close()
            print(f"Error creating course: {str(e)}")
            return jsonify({"error": str(e)}), 500


@app.route("/api/courses/<course_id>", methods=["GET", "PUT", "DELETE"])
def api_course(course_id):
    if request.method == "GET":
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT c.*, 
                    COUNT(DISTINCT u.id) as units_count,
                    COUNT(DISTINCT l.id) as lessons_count
                FROM courses c
                LEFT JOIN units u ON c.id = u.course_id
                LEFT JOIN lessons l ON u.id = l.unit_id
                WHERE c.id = %s
                GROUP BY c.id
            """,
                (course_id,),
            )
            course = cur.fetchone()
            if not course:
                conn.close()
                return jsonify({"error": "Course not found"}), 404

            # Get units and lessons
            cur.execute(
                """
                SELECT u.*, 
                    COUNT(l.id) as lessons_count
                FROM units u
                LEFT JOIN lessons l ON u.id = l.unit_id
                WHERE u.course_id = %s
                GROUP BY u.id
                ORDER BY u.order_index
            """,
                (course_id,),
            )
            units = cur.fetchall()

            for unit in units:
                cur.execute(
                    """
                    SELECT l.*, 
                        CASE WHEN lc.id IS NOT NULL THEN true ELSE false END as completed
                    FROM lessons l
                    LEFT JOIN lesson_completions lc ON l.id = lc.lesson_id AND lc.user_id = %s
                    WHERE l.unit_id = %s
                    ORDER BY l.order_index
                """,
                    (session.get("user_id"), unit["id"]),
                )
                unit["lessons"] = cur.fetchall()

            course["units"] = units
            conn.close()
            return jsonify(dict(course))
        except Exception as e:
            print(f"Error fetching course: {str(e)}")
            return jsonify({"error": str(e)}), 500
    elif request.method in ["PUT", "DELETE"]:
        if not session.get("user_id"):
            return jsonify({"error": "Unauthorized"}), 401

        # Check if user is admin
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT is_admin FROM profiles WHERE id = %s", (session["user_id"],)
        )
        profile = cur.fetchone()
        if not profile or not profile["is_admin"]:
            conn.close()
            return jsonify({"error": "Only admins can modify courses"}), 403

        if request.method == "PUT":
            data = request.json
            if not data or not data.get("title"):
                conn.close()
                return jsonify({"error": "Title is required"}), 400

            try:
                cur.execute(
                    """
                    UPDATE courses 
                    SET title = %s, description = %s
                    WHERE id = %s
                    RETURNING *
                    """,
                    (data["title"], data.get("description"), course_id),
                )
                course = cur.fetchone()
                if not course:
                    conn.close()
                    return jsonify({"error": "Course not found"}), 404
                conn.commit()
                conn.close()
                return jsonify(dict(course))
            except Exception as e:
                conn.close()
                print(f"Error updating course: {str(e)}")
                return jsonify({"error": str(e)}), 500
        else:  # DELETE
            try:
                cur.execute(
                    "DELETE FROM courses WHERE id = %s RETURNING id", (course_id,)
                )
                deleted = cur.fetchone()
                if not deleted:
                    conn.close()
                    return jsonify({"error": "Course not found"}), 404
                conn.commit()
                conn.close()
                return jsonify({"message": "Course deleted successfully"})
            except Exception as e:
                conn.close()
                print(f"Error deleting course: {str(e)}")
                return jsonify({"error": str(e)}), 500


@app.route("/api/courses/<course_id>/units", methods=["POST"])
def api_create_unit(course_id):
    if not session.get("user_id"):
        return jsonify({"error": "Unauthorized"}), 401

    # Check if user is admin
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT is_admin FROM profiles WHERE id = %s", (session["user_id"],))
    profile = cur.fetchone()
    if not profile or not profile["is_admin"]:
        conn.close()
        return jsonify({"error": "Only admins can create units"}), 403

    data = request.json
    if not data or not data.get("title"):
        conn.close()
        return jsonify({"error": "Title is required"}), 400

    try:
        # Get the highest order_index
        cur.execute(
            """
            SELECT COALESCE(MAX(order_index), 0) + 1 as next_order
            FROM units
            WHERE course_id = %s
        """,
            (course_id,),
        )
        next_order = cur.fetchone()["next_order"]

        cur.execute(
            """
            INSERT INTO units (course_id, title, order_index)
            VALUES (%s, %s, %s)
            RETURNING *
            """,
            (course_id, data["title"], next_order),
        )
        unit = cur.fetchone()
        conn.commit()
        conn.close()
        return jsonify(dict(unit)), 201
    except Exception as e:
        conn.close()
        print(f"Error creating unit: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/units/<unit_id>/lessons", methods=["POST"])
def api_create_lesson(unit_id):
    if not session.get("user_id"):
        return jsonify({"error": "Unauthorized"}), 401

    # Check if user is admin
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT is_admin FROM profiles WHERE id = %s", (session["user_id"],))
    profile = cur.fetchone()
    if not profile or not profile["is_admin"]:
        conn.close()
        return jsonify({"error": "Only admins can create lessons"}), 403

    data = request.json
    if not data or not data.get("title") or not data.get("lesson_type"):
        conn.close()
        return jsonify({"error": "Title and lesson type are required"}), 400

    # Validate lesson type
    if data["lesson_type"] not in ["text", "video", "quiz"]:
        conn.close()
        return jsonify(
            {"error": "Invalid lesson type. Must be 'text', 'video', or 'quiz'"}
        ), 400

    # Validate video URL if lesson type is video
    if data["lesson_type"] == "video" and not data.get("video_url"):
        conn.close()
        return jsonify({"error": "Video URL is required for video lessons"}), 400

    # Validate quiz data if lesson type is quiz
    if data["lesson_type"] == "quiz":
        if not data.get("quiz_data"):
            conn.close()
            return jsonify({"error": "Quiz data is required for quiz lessons"}), 400
        try:
            # Ensure quiz_data is valid JSON
            if isinstance(data["quiz_data"], str):
                data["quiz_data"] = json.loads(data["quiz_data"])
            # Validate quiz data structure
            if (
                not isinstance(data["quiz_data"], dict)
                or "questions" not in data["quiz_data"]
            ):
                conn.close()
                return jsonify(
                    {
                        "error": "Invalid quiz data format. Must include 'questions' array"
                    }
                ), 400
        except json.JSONDecodeError:
            conn.close()
            return jsonify(
                {"error": "Invalid quiz data format. Please check your JSON"}
            ), 400

    try:
        # Get the highest order_index
        cur.execute(
            """
            SELECT COALESCE(MAX(order_index), 0) + 1 as next_order
            FROM lessons
            WHERE unit_id = %s
        """,
            (unit_id,),
        )
        next_order = cur.fetchone()["next_order"]

        # Convert quiz_data to JSON string if it exists
        quiz_data = None
        if data.get("quiz_data"):
            quiz_data = json.dumps(data["quiz_data"])

        cur.execute(
            """
            INSERT INTO lessons (
                unit_id, 
                title, 
                content, 
                lesson_type,
                video_url,
                quiz_data,
                order_index,
                created_by,
                updated_by
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (
                unit_id,
                data["title"],
                data.get("content", ""),
                data["lesson_type"],
                data.get("video_url", ""),
                quiz_data,
                next_order,
                session["user_id"],
                session["user_id"],
            ),
        )
        lesson = cur.fetchone()
        conn.commit()
        conn.close()
        return jsonify(dict(lesson)), 201
    except Exception as e:
        conn.close()
        print(f"Error creating lesson: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/course/<course_id>", methods=["GET"])
def api_course_detail(course_id):
    try:
        # Get course detail from courses table
        course = supabase.table("courses").select("*").eq("id", course_id).execute()
        return jsonify(course.data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/lesson/<lesson_id>", methods=["GET", "POST"])
def api_lesson(lesson_id):
    if request.method == "GET":
        try:
            # Get lesson detail from lessons table
            lesson = supabase.table("lessons").select("*").eq("id", lesson_id).execute()
            return jsonify(lesson.data), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 400
    elif request.method == "POST":
        if not session.get("user_id"):
            return jsonify({"error": "Unauthorized"}), 401

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            # Check if lesson exists
            cur.execute("SELECT id FROM lessons WHERE id = %s", (lesson_id,))
            if not cur.fetchone():
                conn.close()
                return jsonify({"error": "Lesson not found"}), 404

            # Insert completion record, update energy points, and check for badges
            cur.execute(
                """
                WITH completion AS (
                    INSERT INTO lesson_completions (lesson_id, user_id)
                    VALUES (%s, %s)
                    ON CONFLICT (lesson_id, user_id) DO NOTHING
                    RETURNING id
                ),
                energy_update AS (
                    UPDATE profiles
                    SET energy_points = energy_points + 3
                    WHERE id = %s AND EXISTS (SELECT 1 FROM completion)
                    RETURNING energy_points
                ),
                completed_lessons AS (
                    SELECT COUNT(*) as count
                    FROM lesson_completions
                    WHERE user_id = %s
                ),
                total_lessons AS (
                    SELECT COUNT(*) as count
                    FROM lessons
                ),
                badge_check AS (
                    UPDATE profiles
                    SET badges = CASE
                        WHEN NOT badges @> ARRAY['First Lesson']::text[] AND 
                             (SELECT count FROM completed_lessons) = 1
                        THEN array_append(badges, 'First Lesson')
                        WHEN NOT badges @> ARRAY['Course Master']::text[] AND 
                             (SELECT count FROM completed_lessons) = (SELECT count FROM total_lessons)
                        THEN array_append(badges, 'Course Master')
                        ELSE badges
                    END
                    WHERE id = %s
                    RETURNING badges
                )
                SELECT 
                    e.energy_points,
                    b.badges
                FROM energy_update e
                LEFT JOIN badge_check b ON true
                """,
                (
                    lesson_id,
                    session["user_id"],
                    session["user_id"],
                    session["user_id"],
                    session["user_id"],
                ),
            )

            result = cur.fetchone()
            conn.commit()
            conn.close()

            if result:
                return jsonify(
                    {
                        "message": "Lesson marked as completed",
                        "energy_points": result["energy_points"],
                        "badges": result["badges"],
                    }
                ), 200
            else:
                return jsonify({"message": "Lesson was already completed"}), 200

        except Exception as e:
            print(f"Error marking lesson as completed: {str(e)}")
            return jsonify({"error": str(e)}), 500


@app.route("/api/lessons/<lesson_id>", methods=["DELETE", "PUT"])
def api_lessons_manage(lesson_id):
    if not session.get("user_id"):
        return jsonify({"error": "Unauthorized"}), 401

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Check if user is admin
        cur.execute(
            "SELECT is_admin FROM profiles WHERE id = %s", (session["user_id"],)
        )
        profile = cur.fetchone()
        if not profile or not profile["is_admin"]:
            conn.close()
            return jsonify({"error": "Only admins can manage lessons"}), 403

        # Check if lesson exists
        cur.execute("SELECT id FROM lessons WHERE id = %s", (lesson_id,))
        if not cur.fetchone():
            conn.close()
            return jsonify({"error": "Lesson not found"}), 404

        if request.method == "DELETE":
            # Delete the lesson (cascade will handle related records)
            cur.execute("DELETE FROM lessons WHERE id = %s RETURNING id", (lesson_id,))
            deleted = cur.fetchone()
            conn.commit()
            conn.close()

            if not deleted:
                return jsonify({"error": "Failed to delete lesson"}), 500

            return jsonify({"message": "Lesson deleted successfully"}), 200

        elif request.method == "PUT":
            data = request.get_json()
            if not data:
                conn.close()
                return jsonify({"error": "No data provided"}), 400

            # Validate required fields
            if not data.get("title"):
                conn.close()
                return jsonify({"error": "Title is required"}), 400

            # Validate lesson type if provided
            if data.get("lesson_type") and data["lesson_type"] not in [
                "text",
                "video",
                "quiz",
            ]:
                conn.close()
                return jsonify(
                    {"error": "Invalid lesson type. Must be 'text', 'video', or 'quiz'"}
                ), 400

            # Validate video URL if lesson type is video
            if data.get("lesson_type") == "video" and not data.get("video_url"):
                conn.close()
                return jsonify(
                    {"error": "Video URL is required for video lessons"}
                ), 400

            # Validate quiz data if lesson type is quiz
            if data.get("lesson_type") == "quiz":
                if not data.get("quiz_data"):
                    conn.close()
                    return jsonify(
                        {"error": "Quiz data is required for quiz lessons"}
                    ), 400
                try:
                    # Ensure quiz_data is valid JSON
                    if isinstance(data["quiz_data"], str):
                        data["quiz_data"] = json.loads(data["quiz_data"])
                    # Validate quiz data structure
                    if (
                        not isinstance(data["quiz_data"], dict)
                        or "questions" not in data["quiz_data"]
                    ):
                        conn.close()
                        return jsonify(
                            {
                                "error": "Invalid quiz data format. Must include 'questions' array"
                            }
                        ), 400
                except json.JSONDecodeError:
                    conn.close()
                    return jsonify(
                        {"error": "Invalid quiz data format. Please check your JSON"}
                    ), 400

            # Convert quiz_data to JSON string if it exists
            quiz_data = None
            if data.get("quiz_data"):
                quiz_data = json.dumps(data["quiz_data"])

            # Update the lesson
            cur.execute(
                """
                UPDATE lessons 
                SET title = %s,
                    content = %s,
                    lesson_type = %s,
                    video_url = %s,
                    quiz_data = %s,
                    updated_at = CURRENT_TIMESTAMP,
                    updated_by = %s
                WHERE id = %s
                RETURNING *
                """,
                (
                    data["title"],
                    data.get("content", ""),
                    data.get("lesson_type", "text"),
                    data.get("video_url", ""),
                    quiz_data,
                    session["user_id"],
                    lesson_id,
                ),
            )
            updated_lesson = cur.fetchone()
            conn.commit()
            conn.close()

            if not updated_lesson:
                return jsonify({"error": "Failed to update lesson"}), 500

            return jsonify(dict(updated_lesson)), 200

    except Exception as e:
        print(f"Error managing lesson: {str(e)}")
        if "conn" in locals():
            conn.close()
        return jsonify({"error": str(e)}), 500


@app.route("/api/comments/<lesson_id>", methods=["GET", "POST", "DELETE"])
def api_comments(lesson_id):
    if request.method == "GET":
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            # Get all comments for the lesson with user info
            cur.execute(
                """
                SELECT c.*, p.username, p.handle
                FROM comments c
                JOIN profiles p ON c.user_id = p.id
                WHERE c.lesson_id = %s
                ORDER BY c.created_at DESC
                """,
                (lesson_id,),
            )
            comments_result = cur.fetchall()
            conn.close()

            # Organize comments and replies
            comments = []
            replies = []

            for comment in comments_result:
                comment_data = {
                    "id": comment["id"],
                    "user_id": comment["user_id"],
                    "content": comment["content"],
                    "created_at": comment["created_at"],
                    "username": comment["username"],
                    "handle": comment["handle"],
                    "parent_id": comment["parent_id"],  # Add parent_id to comment data
                    "replies": [],
                }

                if comment["parent_id"] is None:
                    comments.append(comment_data)
                else:
                    replies.append(comment_data)

            # Attach replies to their parent comments
            for reply in replies:
                for comment in comments:
                    if reply["parent_id"] == comment["id"]:
                        comment["replies"].append(reply)
                        break

            return jsonify(comments)
        except Exception as e:
            print(f"Error fetching comments: {str(e)}")
            return jsonify({"error": str(e)}), 500

    elif request.method == "POST":
        user_id = session.get("user_id")
        print(f"POST comment - User ID: {user_id}")  # Debug log

        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401

        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "No data provided"}), 400

            content = data.get("content")
            parent_id = data.get("parent_id")  # Optional parent_id for replies

            if not content:
                return jsonify({"error": "Content is required"}), 400

            conn = get_db_connection()
            cur = conn.cursor()

            # Verify user exists
            cur.execute("SELECT id FROM profiles WHERE id = %s", (user_id,))
            if not cur.fetchone():
                conn.close()
                return jsonify({"error": "User profile not found"}), 404

            # Insert the comment
            cur.execute(
                """
                INSERT INTO comments (lesson_id, user_id, content, parent_id)
                VALUES (%s, %s, %s, %s)
                RETURNING id, created_at
                """,
                (lesson_id, user_id, content, parent_id),
            )

            new_comment = cur.fetchone()
            if not new_comment:
                conn.close()
                return jsonify({"error": "Failed to create comment"}), 500

            conn.commit()
            conn.close()

            # Get user info for the response
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT username, handle FROM profiles WHERE id = %s", (user_id,)
            )
            user_info = cur.fetchone()
            conn.close()

            return jsonify(
                {
                    "id": new_comment["id"],
                    "content": content,
                    "created_at": new_comment["created_at"],
                    "user_id": user_id,
                    "username": user_info["username"],
                    "handle": user_info["handle"],
                    "parent_id": parent_id,  # Add parent_id to the response
                }
            ), 201

        except Exception as e:
            print(f"Error posting comment: {str(e)}")
            if "conn" in locals():
                conn.close()
            return jsonify({"error": str(e)}), 500

    elif request.method == "DELETE":
        user_id = session.get("user_id")
        print(f"DELETE comment - User ID: {user_id}")  # Debug log

        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401

        try:
            comment_id = request.args.get("comment_id")
            if not comment_id:
                return jsonify({"error": "Comment ID is required"}), 400

            conn = get_db_connection()
            cur = conn.cursor()

            # Delete the comment (RLS will ensure user can only delete their own comments)
            cur.execute(
                """
                DELETE FROM comments 
                WHERE id = %s AND lesson_id = %s AND user_id = %s
                RETURNING id
                """,
                (comment_id, lesson_id, user_id),
            )
            deleted = cur.fetchone()
            conn.commit()
            conn.close()

            if not deleted:
                return jsonify({"error": "Comment not found or unauthorized"}), 404

            return jsonify({"message": "Comment deleted successfully"}), 200
        except Exception as e:
            print(f"Error deleting comment: {str(e)}")
            conn.close()
            return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
