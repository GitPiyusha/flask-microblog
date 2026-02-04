from flask import render_template
from app import app

@app.route('/')
@app.route('/index')
def index():
    user = {'username': 'Miguel'}
    posts = [
        {'author': {'username': 'John'}, 'body': 'Beautiful day!'},
        {'author': {'username': 'Susan'}, 'body': 'Flask is cool!'}
    ]
    return render_template('index.html', title='Home', user=user, posts=posts)
