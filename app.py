import os
import random
import string
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from captcha.image import ImageCaptcha 


app = Flask(__name__)

app.secret_key = os.urandom(24) 
CAPTCHA_DIR = os.path.join(app.root_path, 'static')
CAPTCHA_FILENAME = "captcha.png"


if not os.path.exists(CAPTCHA_DIR):
    os.makedirs(CAPTCHA_DIR)

CHARACTERS = string.ascii_letters + string.digits
CAPTCHA_LENGTH = 6
IMAGE_WIDTH = 280
IMAGE_HEIGHT = 90

def generate_random_text(length):
    """Generates a random alphanumeric string."""
    return ''.join(random.choice(CHARACTERS) for _ in range(length))

def generate_image_captcha():
    """Generates a new CAPTCHA, saves it, and stores the text in the session."""
    captcha_text = generate_random_text(CAPTCHA_LENGTH)
    
    
    image_generator = ImageCaptcha(width=IMAGE_WIDTH, height=IMAGE_HEIGHT)

    
    file_path = os.path.join(CAPTCHA_DIR, CAPTCHA_FILENAME)
    image_generator.write(captcha_text, file_path)
    
    
    session['captcha_answer'] = captcha_text
    
    return CAPTCHA_FILENAME


USERS = {} 


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or not session['logged_in']:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function



@app.route('/')
def index():
    """Homepage: Links to Login and Register."""
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page with CAPTCHA."""
    
    captcha_image_url = url_for('static', filename=CAPTCHA_FILENAME) + f'?v={random.randint(0, 999999)}'
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        captcha_input = request.form['captcha_input'].strip()
        
        
        if username in USERS:
            flash('Username already exists. Please choose another.', 'danger')
            generate_image_captcha() 
            return render_template('register.html', captcha_image=captcha_image_url)

        
        if 'captcha_answer' not in session or captcha_input.lower() != session['captcha_answer'].lower():
            flash('CAPTCHA verification failed. Please try again.', 'danger')
            generate_image_captcha() 
            return render_template('register.html', captcha_image=captcha_image_url)
        
        
        USERS[username] = password
        session['logged_in'] = True
        session['username'] = username
        flash('Registration successful! You are now logged in.', 'success')
        return redirect(url_for('learn'))

    
    generate_image_captcha()
    return render_template('register.html', captcha_image=captcha_image_url)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in USERS and USERS[username] == password:
            session['logged_in'] = True
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('learn'))
        else:
            flash('Invalid username or password.', 'danger')
            return render_template('login.html')

    return render_template('login.html')

@app.route('/learn')
@login_required 
def learn():
    """Custom Python Learning Web Page."""
    return render_template('python_learning_page.html', username=session.get('username', 'Guest'))

@app.route('/logout')
def logout():
    """Logs the user out and clears the session."""
    session.pop('logged_in', None)
    session.pop('username', None)
    session.pop('captcha_answer', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/refresh_captcha')
def refresh_captcha():
    """API endpoint to generate and return the URL for a new CAPTCHA image."""
    generate_image_captcha()
    
    return url_for('static', filename=CAPTCHA_FILENAME) + f'?v={random.randint(0, 999999)}'


if __name__ == '__main__':
    app.run(debug=True)