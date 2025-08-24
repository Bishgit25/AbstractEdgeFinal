from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# --- App and Database Configuration ---
app = Flask(__name__)
# It's crucial to set a secret key for session management and flash messages.
# Replace 'a-very-secret-key' with a real, random secret key in production.
app.config['SECRET_KEY'] = 'a-very-secret-key' 
# Configure the database location. SQLite is a file-based database.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db' 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
# If a user tries to access a protected page without being logged in, 
# they will be redirected to the 'login' page.
login_manager.login_view = 'login' 


# --- User Model ---
# The UserMixin provides default implementations for methods that Flask-Login expects user objects to have.
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    # We use a property to set the password to ensure it's always hashed.
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # Method to check if the provided password matches the stored hash.
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# This function is required by Flask-Login to reload the user object from the user ID stored in the session.
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# --- Routes ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
@login_required # This decorator protects the route. Only logged-in users can access it.
def dashboard():
    return render_template('dashboard.html', user=current_user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    # If the user is already logged in, redirect them to the dashboard.
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        # Check if the user exists and the password is correct.
        if user and user.check_password(password):
            login_user(user) # This function from Flask-Login handles the session.
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')
            
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if a user with the same username or email already exists.
        existing_user_email = User.query.filter_by(email=email).first()
        if existing_user_email:
            flash('An account with this email already exists.', 'danger')
            return redirect(url_for('register'))

        existing_user_name = User.query.filter_by(username=username).first()
        if existing_user_name:
            flash('This username is already taken.', 'danger')
            return redirect(url_for('register'))

        # Create a new user instance
        new_user = User(username=username, email=email)
        new_user.set_password(password) # Hash the password

        # Add the new user to the database
        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully! You can now log in.', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user() # This function from Flask-Login clears the session.
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# --- Other Pages (We will make these functional later) ---

@app.route('/market-data')
def market_data():
    return render_template('market-data.html')

@app.route('/ico-ido-calendar')
def ico_ido_calendar():
    return render_template('ico-ido-calendar.html')

@app.route('/crypto-news')
def crypto_news():
    return render_template('crypto-news.html')


# This is the standard entry point for running the Flask app.
if __name__ == '__main__':
    # Before running the app for the first time, we need to create the database tables.
    with app.app_context():
        db.create_all()
    app.run(debug=True)
