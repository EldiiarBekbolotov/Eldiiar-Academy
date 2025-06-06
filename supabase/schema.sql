-- enable row level security on auth.users table
ALTER TABLE auth.users ENABLE ROW LEVEL SECURITY;

-- create profiles table for user information
CREATE TABLE profiles (
    id UUID REFERENCES auth.users(id) PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    handle TEXT UNIQUE NOT NULL,
    bio TEXT CHECK (char_length(bio) <= 180),
    avatar TEXT,
    account_created TIMESTAMP WITH TIME ZONE DEFAULT now(),
    last_logged_in TIMESTAMP WITH TIME ZONE DEFAULT now(),
    badges TEXT[] DEFAULT '{}',
    energy_points INTEGER DEFAULT 0
);

-- enable RLS and define policies for profiles table
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public profiles are viewable by everyone" ON profiles FOR SELECT USING (true);
CREATE POLICY "Users can update their own profile" ON profiles FOR UPDATE USING (auth.uid() = id);

-- create courses table for course information
CREATE TABLE courses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- enable RLS and define policy for courses table
ALTER TABLE courses ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Courses are viewable by everyone" ON courses FOR SELECT USING (true);

-- create units table for course units
CREATE TABLE units (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    course_id UUID REFERENCES courses(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- enable RLS and define policy for units table
ALTER TABLE units ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Units are viewable by everyone" ON units FOR SELECT USING (true);

-- create lessons table for lesson content
CREATE TABLE lessons (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    unit_id UUID REFERENCES units(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    content TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- enable RLS and define policy for lessons table
ALTER TABLE lessons ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Lessons are viewable by everyone" ON lessons FOR SELECT USING (true);

-- create lesson_completions table to track completed lessons
CREATE TABLE lesson_completions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    lesson_id UUID REFERENCES lessons(id) ON DELETE CASCADE,
    completed_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE(user_id, lesson_id)
);

-- enable RLS and define policies for lesson_completions table
ALTER TABLE lesson_completions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view their own completions" ON lesson_completions FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert their own completions" ON lesson_completions FOR INSERT WITH CHECK (auth.uid() = user_id);

-- create comments table for lesson discussions
CREATE TABLE comments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lesson_id UUID REFERENCES lessons(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    parent_id UUID REFERENCES comments(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- enable RLS and define policies for comments table
ALTER TABLE comments ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Comments are viewable by everyone" ON comments FOR SELECT USING (true);
CREATE POLICY "Users can insert their own comments" ON comments FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update their own comments" ON comments FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete their own comments" ON comments FOR DELETE USING (auth.uid() = user_id);

-- create login_sessions table to track user logins
CREATE TABLE login_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    login_date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE(user_id, login_date)
);

-- enable RLS and define policies for login_sessions table
ALTER TABLE login_sessions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view their own login sessions" ON login_sessions FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert their own login sessions" ON login_sessions FOR INSERT WITH CHECK (auth.uid() = user_id);