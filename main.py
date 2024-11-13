from flask import Flask, render_template, request, redirect, session, url_for, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from gtts import gTTS
import speech_recognition as sr
import os
import time 
import uuid

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Config SQLAlchemy
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Database Model - Single Row with DB
class User(db.Model):
    # Class Variables
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(25), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Routes
@app.route("/")
def home():
    # Verify if it's logged in
    if "username" in session:
        return redirect(url_for('dashboard'))
    return render_template("index.html")

# Login
@app.route("/login", methods=["POST"])
def login():
    # Collect info from the form
    username = request.form['username']
    password = request.form["password"]
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        session['username'] = username
        return redirect(url_for('dashboard'))
    else:
        return render_template("index.html")

# Register
@app.route("/register", methods=["POST"])
def register():
    username = request.form['username']
    password = request.form["password"]
    user = User.query.filter_by(username=username).first()
    if user:
        return render_template("index.html", error="User already exists")
    else:
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        session['username'] = username
        return redirect(url_for('dashboard'))

# Dashboard
@app.route("/dashboard")
def dashboard():
    if "username" in session:
        return render_template("dashboard.html", username=session['username'])
    return redirect(url_for('home'))

# Logout
@app.route("/logout")
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

@app.route("/speech_to_text_page")
def speech_to_text_page():
    if "username" in session:
        return render_template("speech_to_text.html", username=session['username'])
    return redirect(url_for('home'))

@app.route("/speech_to_text", methods=["GET", "POST"])
def speech_to_text():
    recognized_text = ""
    if request.method == "POST":
        if "text" in request.form:
            recognized_text = request.form['text']
    
    return render_template("speech_to_text.html", username=session['username'], recognized_text=recognized_text)

@app.route("/text_to_speech_page")
def text_to_speech_page():
    if "username" in session:
        return render_template("text_to_speech.html", username=session['username'], audio_files=session.get('audio_files', []))
    return redirect(url_for('home'))

# Text to Speech FORM
@app.route("/text_to_speech", methods=["POST"])
def text_to_speech():
    text = request.form['text']
    
    file_name = f'audio_{uuid.uuid4().hex}_{int(time.time())}.mp3'
    audio_directory = 'static/audio'
   
    if not os.path.exists(audio_directory):
        os.makedirs(audio_directory)

    full_path = os.path.join(audio_directory, file_name)
    tts = gTTS(text=text, lang='en')
    tts.save(full_path)

    if 'audio_files' not in session:
        session['audio_files'] = []
    else:
        session['audio_files'] = [f for f in session['audio_files'] if os.path.exists(os.path.join('static', f))]

    session['audio_files'].append(f'audio/{file_name}')
    return render_template("text_to_speech.html", username=session['username'], audio_files=session['audio_files'])

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
