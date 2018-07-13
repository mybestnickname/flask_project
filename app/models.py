from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5
import datetime
import random


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    reg_datetime = db.Column(db.DateTime, index=True,
                             default=datetime.datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    about_user = db.Column(db.String(140))
    userpic = db.Column(db.String(128))
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    decks = db.relationship('Deck', backref='owner', lazy='dynamic')
    skills = db.relationship('Skill', backref='skilluser', lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        """
        Метод генирирует геометрические аватары с помощью сервиса Gravatar
        """
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)


class Deck(db.Model):
    __tablename__ = 'decks'
    id = db.Column(db.Integer, primary_key=True)
    deck_name = db.Column(db.String(128))
    deck_info = db.Column(db.String(256))
    creation_datetime = db.Column(db.DateTime, index=True,
                                  default=datetime.datetime.utcnow)
    deckpic = db.Column(db.String(128),
                        default="/static/img/decks_img/default_deckpic.gif")
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    cards = db.relationship('Card', backref='deck', lazy='dynamic')
    # для расшаривания колоды для других пользователей
    # shared = db.Table('users',
    #                 db.Column('sherid', db.Integer,
    #                          db.ForeignKey('user.id')),
    #               db.Column('sherid', db.Integer,
    #                        db.ForeignKey('user.id')),
    #             db.Column('sherid', db.Integer,
    #                      db.ForeignKey('user.id')),
    #           db.Column('sherid', db.Integer,
    #                    db.ForeignKey('user.id')),
    #         db.Column('sherid', db.Integer,
    #                  db.ForeignKey('user.id'))
    #       )

    def __repr__(self):
        return '<Deck {} User {}>'.format(self.deck_name, self.user_id)


class Card(db.Model):
    __tablename__ = 'cards'
    id = db.Column(db.Integer, primary_key=True)
    card_name = db.Column(db.String(64))
    question = db.Column(db.String(256))
    answer = db.Column(db.String(1024))
    card_img1 = db.Column(db.String(128))
    card_img2 = db.Column(db.String(128))
    card_img3 = db.Column(db.String(128))
    card_statistic = db.Column(db.String(32),
                               default='0,0,0')
    deck_id = db.Column(db.Integer, db.ForeignKey('decks.id'))

    def __repr__(self):
        return '<Card {} Deck {}>'.format(self.card_name, self.deck_id)


class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    post_title = db.Column(db.String(128))
    post_text = db.Column(db.String(1024))
    post_datetime = db.Column(db.DateTime, index=True,
                              default=datetime.datetime.utcnow)
    views = db.Column(db.Integer, default=1)
    post_image_ref = db.Column(db.String(256))
    comments = db.relationship('Comment', backref='post', lazy='dynamic')

    def __repr__(self):
        return '<Post {}>'.format(self.post_title)

    def add_views(self):
        self.views += 1
        db.session.commit()


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    comment_text = db.Column(db.String(256))
    comment_datetime = db.Column(db.DateTime, index=True,
                                 default=datetime.datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))

    def __repr__(self):
        return '<Comment {} User {} Post>'.format(self.comment_text,
                                                  self.user_id, self.post_id)


class Skill(db.Model):
    __tablename__ = 'skills'
    id = db.Column(db.Integer, primary_key=True)
    first_skill = db.Column(db.String(128))
    second_skill = db.Column(db.String(128))
    third_skill = db.Column(db.String(128))
    fourth_skill = db.Column(db.String(128))
    fifth_skill = db.Column(db.String(128))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def default_skills(self):
        """
        Метод возвращает случайный скилл из списка, который будет
        отображаться, если нет нормальных
        """
        d_skills_lst = ['Отдыхать', 'Кушать', 'Спать']
        random_index = random.randint(0, len(d_skills_lst) - 1)
        return d_skills_lst[random_index]
