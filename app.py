from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import load_dotenv
import os

# -------------------- Load environment --------------------
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
SECRET_KEY = os.getenv("SECRET_KEY")

if not MONGO_URI:
    raise ValueError("⚠️ MONGO_URI not set in .env file!")

if not SECRET_KEY:
    raise ValueError("⚠️ SECRET_KEY not set in .env file!")

# -------------------- Flask App & MongoDB --------------------
app = Flask(__name__)
app.secret_key = SECRET_KEY

# ✅ Fix for Render: force TLS and allow certs
client = MongoClient(
    MONGO_URI,
    tls=True,
    tlsAllowInvalidCertificates=True
)
db_name = os.getenv("DB_NAME", "student_collab_db")
db = client[db_name]

users_collection = db["users"]
posts_collection = db["posts"]
post_registrations_collection = db["post_registrations"]

print(f"✅ Connected to MongoDB Atlas database: {db.name}")
print(f"📂 Current collections: {db.list_collection_names()}")

# -------------------- Routes --------------------
@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    posts = posts_collection.find()
    return render_template("index.html", posts=posts, username=session['username'])

@app.route('/create_post', methods=['GET', 'POST'])
def create_post():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        posts_collection.insert_one({
            'title': title,
            'content': content,
            'author': session['username']
        })
        flash("Post created successfully!")
        return redirect(url_for('index'))
    return render_template("create_post.html")

@app.route('/register_post/<post_id>', methods=['GET', 'POST'])
def register_post(post_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    post = posts_collection.find_one({"_id": ObjectId(post_id)})
    if not post:
        flash("Post not found.")
        return redirect(url_for('index'))
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        interests = request.form['interests']
        post_registrations_collection.insert_one({
            "username": session['username'],
            "post_id": ObjectId(post_id),
            "post_title": post['title'],
            "name": name,
            "email": email,
            "interests": interests
        })
        flash("Successfully registered for this event!")
        return redirect(url_for('index'))
    return render_template("register_post.html", post=post)

@app.route('/profile')
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    user_posts = posts_collection.find({'author': username})
    collab_regs = post_registrations_collection.find({'username': username})
    return render_template("profile.html",
                           user_posts=user_posts,
                           collab_regs=collab_regs,
                           username=username)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        existing_user = users_collection.find_one({'username': username})
        print(f"📝 Signup attempt for: {username}")
        if existing_user:
            flash('Username already exists. Try logging in.')
            return redirect(url_for('signup'))
        hashed_pw = generate_password_hash(password)
        result = users_collection.insert_one({'username': username, 'password': hashed_pw})
        print(f"✅ Inserted new user with _id: {result.inserted_id}")
        flash("Signup successful! Please login.")
        return redirect(url_for('login'))
    return render_template("signup.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users_collection.find_one({'username': username})
        print(f"🔍 Login attempt for: {username}")
        if user and check_password_hash(user['password'], password):
            session['username'] = username
            flash("Login successful!")
            return redirect(url_for('index'))
        else:
            flash("Invalid username or password.")
            return redirect(url_for('login'))
    return render_template("login.html")

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("Logged out successfully.")
    return redirect(url_for('login'))

# -------------------- Run Server --------------------
if __name__ == '__main__':
    print("🚀 Server running on http://127.0.0.1:5000/")
    app.run(debug=True)
