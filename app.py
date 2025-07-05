from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import load_dotenv
import os

# Load .env
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
SECRET_KEY = os.getenv("SECRET_KEY")
DB_NAME = os.getenv("DB_NAME", "student_collab_db")

if not MONGO_URI or not SECRET_KEY:
    raise ValueError("MONGO_URI or SECRET_KEY not set!")

# Init Flask & Mongo
app = Flask(__name__)
app.secret_key = SECRET_KEY

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

users_collection = db["users"]
posts_collection = db["posts"]
post_registrations_collection = db["post_registrations"]

print(f"✅ Connected to MongoDB database: {db.name}")

# Routes
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
        posts_collection.insert_one({
            'title': request.form['title'],
            'content': request.form['content'],
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
        post_registrations_collection.insert_one({
            "username": session['username'],
            "post_id": ObjectId(post_id),
            "post_title": post['title'],
            "name": request.form['name'],
            "email": request.form['email'],
            "interests": request.form['interests']
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
    return render_template("profile.html", user_posts=user_posts, collab_regs=collab_regs, username=username)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if users_collection.find_one({'username': username}):
            flash('Username already exists. Try logging in.')
            return redirect(url_for('signup'))
        hashed_pw = generate_password_hash(password)
        users_collection.insert_one({'username': username, 'password': hashed_pw})
        flash("Signup successful! Please login.")
        return redirect(url_for('login'))
    return render_template("signup.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = users_collection.find_one({'username': request.form['username']})
        if user and check_password_hash(user['password'], request.form['password']):
            session['username'] = request.form['username']
            flash("Login successful!")
            return redirect(url_for('index'))
        flash("Invalid username or password.")
    return render_template("login.html")

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("Logged out successfully.")
    return redirect(url_for('login'))

# Run with Render's PORT
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Server running on 0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port)
