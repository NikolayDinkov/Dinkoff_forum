import uuid
from flask import Flask
from flask import render_template, request, redirect, make_response, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, LoginManager, current_user
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'azsumsecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test1.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    login_id = db.Column(db.String(36), nullable=True)

    def __repr__(self):
        return '<User %r>' % self.username
    
    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    def get_id(self):
        return self.login_id

class Discussion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"Post('{self.title}')"

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.now)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    discussion_id = db.Column(db.Integer, db.ForeignKey('discussion.id'), nullable=False)
    writer = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"


db.create_all()
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(login_id=user_id).first()

@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for('login'))

@app.route('/')
def start():
    return redirect(url_for('homepage'))

@app.route('/home')
def homepage():
    return render_template('homepage.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    else:
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email address already exists.')
            return redirect(url_for('register'))

        new_user = User(email=email, username=username, password=generate_password_hash(password))

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            user.login_id = str(uuid.uuid4())
            db.session.commit()
            login_user(user)
            return redirect(url_for('homepage'))
        else:
            return redirect(url_for('login'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('homepage'))

@app.route('/discussions', methods=['GET', 'POST'])
def discussions():
    if request.method == 'POST':
        discussion_title = request.form['title']
        discussion_content = request.form['content']
        new_discussion = Discussion(title=discussion_title, content=discussion_content)
        db.session.add(new_discussion)
        db.session.commit()
        return redirect('/discussions')
    else:
        all_discussions = Discussion.query.all()
        return render_template('discussions.html', discussions=all_discussions)

@app.route('/discussions/new', methods=['GET', 'POST'])
@login_required
def new_discussion():
    return render_template('newdiscussion.html')

@app.route('/discussions/<int:id>', methods=['GET', 'POST'])
def posts(id):
    if request.method == 'POST':
        post_title = request.form['title']
        post_content = request.form['content']
        new_post = Post(title=post_title, content=post_content, user_id=current_user.id, discussion_id=id, writer=current_user.username)
        db.session.add(new_post)
        db.session.commit()
    all_posts = Post.query.order_by(Post.date_posted).filter_by(discussion_id=id).all()
    return render_template('posts.html', id=id, posts=all_posts)

@app.route('/discussions/<int:id>/new', methods=['GET', 'POST'])
@login_required
def new_post(id):
    return render_template('newpost.html', id=id)

@app.route('/discussions/<int:id1>/edit/<int:id2>', methods=['GET', 'POST'])
@login_required
def edit(id1, id2):
    post = Post.query.get_or_404(id2)
    if request.method == 'POST':
        post.title = request.form['title']
        post.content = request.form['content']
        db.session.commit()
        return redirect('/discussions/' + str(id1))
    else:
        return render_template('edit.html', id=id1, post=post)

@app.route('/discussions/<int:id1>/delete/<int:id2>')
@login_required
def delete(id1, id2):
    post = Post.query.get_or_404(id2)
    db.session.delete(post)
    db.session.commit()
    return redirect('/discussions/' + str(id1))


if __name__ == '__main__':
    app.run(debug=True)