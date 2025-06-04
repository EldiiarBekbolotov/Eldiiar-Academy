How to run the program using the terminal:

<pre><code>
bash python -m venv/venv # if this doesn't work, python -m venv/venv
source venv/bin/activate

pip install -r requirements.txt
</code></pre>

Create a `.env` file in the root directory with your Supabase credentials:

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

Finally, run the program:
```flask run```
if you want auto reloading on code changes, use:
```flask --app app.py --debug run```