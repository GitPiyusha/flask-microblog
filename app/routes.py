from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from datetime import datetime, timezone
import sqlalchemy as sa

from app import app, db
from app.models import User
from app.forms import EditProfileForm, LoginForm


# ---------------- BEFORE REQUEST ----------------
@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()


# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()

    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == form.username.data)
        )

        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))

        login_user(user)
        return redirect(url_for('index'))

    return render_template('login.html', title='Sign In', form=form)


# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


# ---------------- HOME ----------------
@app.route('/')
@app.route('/index')
@login_required
def index():
    posts = [
        {'author': current_user, 'body': 'Test post 1'},
        {'author': current_user, 'body': 'Test post 2'}
    ]
    return render_template('index.html', posts=posts)


# ---------------- USER PROFILE ----------------
@app.route('/user/<username>')
@login_required
def user(username):
    user = db.session.scalar(
        sa.select(User).where(User.username == username)
    )

    posts = [
        {'author': user, 'body': 'User post 1'},
        {'author': user, 'body': 'User post 2'}
    ]

    return render_template('user.html', user=user, posts=posts)


# ---------------- EDIT PROFILE ----------------
@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)


    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Profile updated!')
        return redirect(url_for('edit_profile'))

    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me

    return render_template('edit_profile.html',
                           title='Edit Profile',
                           form=form)
