from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import random
import string
import validators

app = Flask(__name__)

app.config['SECRET_KEY'] = 'secret123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# ---------------- DATABASE MODELS ----------------

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)


class URL(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_url = db.Column(db.String(500))
    short_url = db.Column(db.String(20))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


with app.app_context():
    db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ---------------- SHORT URL GENERATOR ----------------

def generate_short_code(length=6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


# ---------------- HOME ----------------

@app.route('/')
def home():
    return render_template("home.html")


# ---------------- SIGNUP ----------------

@app.route('/signup', methods=['GET', 'POST'])
def signup():

    error = ""

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        if len(username) < 5 or len(username) > 9:
            error = "Username must be between 5 to 9 characters"

        elif User.query.filter_by(username=username).first():
            error = "This username already exists"

        else:
            new_user = User(username=username, password=password)
            db.session.add(new_user)
            db.session.commit()

            return redirect('/login')

    return render_template("signup.html", error=error)


# ---------------- LOGIN ----------------

@app.route('/login', methods=['GET', 'POST'])
def login():

    error = ""

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and user.password == password:
            login_user(user)
            return redirect('/dashboard')

        else:
            error = "Invalid username or password"

    return render_template("login.html", error=error)


# ---------------- DASHBOARD ----------------

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():

    short_url = ""
    error = ""

    user_urls = URL.query.filter_by(user_id=current_user.id).all()

    if request.method == 'POST':

        long_url = request.form['url']

        if not validators.url(long_url):
            error = "Invalid URL!"

        else:
            code = generate_short_code()

            new_url = URL(
                original_url=long_url,
                short_url=code,
                user_id=current_user.id
            )

            db.session.add(new_url)
            db.session.commit()

            short_url = request.host_url + code

            user_urls = URL.query.filter_by(user_id=current_user.id).all()

    return render_template("dashboard.html",
                           short_url=short_url,
                           urls=user_urls,
                           error=error)


# ---------------- REDIRECT ----------------

@app.route('/<code>')
def redirect_url(code):

    url_data = URL.query.filter_by(short_url=code).first()

    if url_data:
        return redirect(url_data.original_url)

    return "URL Not Found!"


# ---------------- LOGOUT ----------------

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)