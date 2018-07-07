# -*- coding: utf-8 -*-
from datetime import datetime
from flask import render_template, flash, redirect, url_for, request
from flask_login import login_required
from app import app
from app.forms import LoginForm, RegistrationForm, EditProfileForm
from app.forms import DeckCreationForm, PostCreationForm
from flask_login import current_user, login_user, logout_user
from app.models import User, Deck, Post
from werkzeug import secure_filename
from werkzeug.urls import url_parse
from werkzeug.exceptions import BadRequestKeyError
import os
from app import db


@app.before_request
def before_request():
    """
    Выполняется перед каждым запросом к серверу
    """
    if current_user.is_authenticated:
        # запоминаем время последнего действия авторизированного юзера
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@app.route('/')
@app.route('/index')
def index():
    # если не залогинен
    if not current_user.is_authenticated:
        return render_template("pls_log.html", title='Pls Login Page')
    # если залогинен, то инфу о нём
        # пока деки и комменты через затычку, потом из бд
    decks = [
        {
            'owner': {'username': 'John'},
            'deck_name': 'Eng deck'
        },
        {
            'owner': {'username': 'Susan'},
            'deck_name': 'Math deck'
        },
        {
            'owner': {'username': 'Ипполит'},
            'deck_name': 'Others deck'
        }
    ]
    return render_template("index.html", title='Home Page', decks=decks)


@app.route('/login', methods=['GET', 'POST'])
def login():
    # если уже залогинен
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    # проверяем валидность формы
    if form.validate_on_submit():
        # ищем юзера в бд
        user = User.query.filter_by(username=form.username.data).first()
        # если не нашли или не подошёл пароль
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        # иначе залогинили и запомнили
        login_user(user, remember=form.remember_me.data)
        # редиректим на index или next-page(откуда попали на логин)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            # что бы next_page точно был
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/users')
@login_required
def users():
    return render_template('users.html', title='Users')


@app.route('/microblog')
@login_required
def microblog():
    posts = Post.query.all()
    return render_template('microblog.html', title='Microblog', posts=posts)


@app.route('/microblog/posts/<post_id>')
@login_required
def show_post(post_id):
    post = Post.query.filter_by(id=post_id).first()
    # раз зашли в пост, то нужно увеличить кол-во просмотров
    post.add_views()
    return render_template('show_post.html', title=post.post_title, post=post)


@app.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    comments = [
        {'author': user, 'comment_text': 'Test post #1'},
        {'author': user, 'comment_text': 'Test post #2'}
    ]
    decks = current_user.decks
    return render_template('user.html', title=user.username,
                           user=user, comments=comments, decks=decks)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_user = form.about_user.data
        db.session.commit()
        flash('Изменения сохранены.')
        return redirect(url_for('edit_profile'))
    # если формы нужно предзаполнить
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_user.data = current_user.about_user
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)


@app.route('/create_deck', methods=['GET', 'POST'])
@login_required
def create_deck():
    form = DeckCreationForm()
    if form.validate_on_submit():
        new_deck = Deck(deck_name=form.deck_name.data,
                        deck_info=form.deck_info.data,
                        # deckpic=form.deck_pic.data,
                        user_id=current_user.id
                        )
        # тут доделать загрузку фото в static
        print(type(form.deck_pic.data))
        db.session.add(new_deck)
        db.session.commit()
    return render_template('create_deck.html', form=form,
                           title='Deck creation')


@app.route('/new_post', methods=['GET', 'POST'])
def new_post():
    if current_user.username != 'admin':
        flash('Добавлять посты может только администратор.')
        return redirect(url_for('user', username=current_user.username))
    form = PostCreationForm()
    # если прожали submit при создании поста
    if form.validate_on_submit():
        # получаем, проверяем, сохраняем
        ref_for_db = ''
        if request.method == 'POST':
            # проверяем передавался ли файл
            try:
                f = request.files['file']
            except BadRequestKeyError:
                f = None
            if f and allowed_file(f.filename):
                image = secure_filename(f.filename)
                path_to_save = os.path.join('app/static/img/posts_img',
                                            image)
                f.save(path_to_save)
                ref_for_db = os.path.join('/static/img/posts_img',
                                          image)
        new_post = Post(post_title=form.post_title.data,
                        post_text=form.post_text.data,
                        post_image_ref=ref_for_db)
        db.session.add(new_post)
        db.session.commit()
        flash('Пост добавлен!')
        return redirect(url_for('microblog'))
    return render_template('create_post.html', form=form,
                           title='Post creation')


def allowed_file(filename):
    """Проверка типа файла, загружаемого на сервер."""
    ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS
# @login_required - декоратор, сделает логин обязательным
# для просмотра страницы
