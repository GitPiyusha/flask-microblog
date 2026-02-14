from datetime import datetime, timezone
from hashlib import md5
import sqlalchemy as sa
import sqlalchemy.orm as so

from app import db, login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from time import time
import jwt
from app import app



# ---------------- FOLLOWERS TABLE ----------------
followers = sa.Table(
    'followers',
    db.metadata,
    sa.Column('follower_id', sa.Integer, sa.ForeignKey('user.id'),
              primary_key=True),
    sa.Column('followed_id', sa.Integer, sa.ForeignKey('user.id'),
              primary_key=True)
)


# ---------------- USER MODEL ----------------
class User(UserMixin, db.Model):
    id = sa.Column(sa.Integer, primary_key=True)
    username = sa.Column(sa.String(64), index=True, unique=True)
    email = sa.Column(sa.String(120), index=True, unique=True)
    password_hash = sa.Column(sa.String(256))
    about_me = sa.Column(sa.String(140))
    last_seen = sa.Column(
        sa.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    posts = db.relationship('Post', backref='author', lazy='dynamic')

    following = so.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=so.backref('followers', lazy='dynamic'),
        lazy='dynamic'
    )

    def __repr__(self):
        return f'<User {self.username}>'

    # ---------------- PASSWORD ----------------
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if self.password_hash is None:
            return False
        return check_password_hash(self.password_hash, password)

    # ---------------- AVATAR ----------------
    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'

    # ---------------- FOLLOW SYSTEM ----------------
    def follow(self, user):
        if not self.is_following(user):
            self.following.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.following.remove(user)

    def is_following(self, user):
        return self.following.filter(
            followers.c.followed_id == user.id).count() > 0

    def followers_count(self):
        return self.followers.count()

    def following_count(self):
        return self.following.count()

    # ---------------- FEED POSTS (FINAL FIXED) ----------------
    def following_posts(self):
        followed = (
            sa.select(Post)
            .join(followers,
                  followers.c.followed_id == Post.user_id)
            .where(followers.c.follower_id == self.id)
        )

        own = sa.select(Post).where(Post.user_id == self.id)

        union_query = followed.union(own).subquery()

        return sa.select(Post).join(
            union_query, Post.id == union_query.c.id
        ).order_by(Post.timestamp.desc())


# ---------------- POST MODEL ----------------
class Post(db.Model):
    id = sa.Column(sa.Integer, primary_key=True)
    body = sa.Column(sa.String(140))
    timestamp = sa.Column(
        sa.DateTime,
        index=True,
        default=lambda: datetime.now(timezone.utc)
    )
    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))

    def __repr__(self):
        return f'<Post {self.body}>'


# ---------------- LOGIN LOADER ----------------
@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))

def get_reset_password_token(self, expires_in=600):
    return jwt.encode(
        {'reset_password': self.id, 'exp': time() + expires_in},
        app.config['SECRET_KEY'],
        algorithm='HS256'
    )

@staticmethod
def verify_reset_password_token(token):
    try:
        id = jwt.decode(
            token,
            app.config['SECRET_KEY'],
            algorithms=['HS256']
        )['reset_password']
    except:
        return
    return db.session.get(User, id)

