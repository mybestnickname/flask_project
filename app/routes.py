# -*- coding: utf-8 -*-
from datetime import datetime
from flask import render_template, flash, redirect, url_for, request
from flask_login import login_required
from functools import wraps
from app import app
from app.forms import LoginForm, RegistrationForm, EditProfileForm
from app.forms import DeckCreationForm, PostCreationForm, NewCommentForm
from app.forms import EditDeckForm, SearchUserForm, CreateCardForm
from flask_login import current_user, login_user, logout_user
from app.models import User, Deck, Post, Comment, Skill
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


@app.route('/users', methods=['GET', 'POST'])
@login_required
def users():
    search_form = SearchUserForm()
    # если прожали поиск по пользователям
    if search_form.validate_on_submit():
        username = search_form.search_username.data
        users = User.query.filter(
            User.username.like("%{}%".format(username))).all()
        if users:
            return render_template('users.html', title='Users',
                                   form=search_form, users=users)
        else:
            flash('Никого не нашли.')
        return render_template('users.html', title='Users',
                               form=search_form, users=users)
    # тут просто подгружаем на страницу всех пользователей
    users = User.query.all()
    return render_template('users.html', title='Users',
                           form=search_form, users=users)


@app.route('/microblog')
@login_required
def microblog():
    posts = Post.query.all()
    return render_template('microblog.html', title='Microblog', posts=posts)


@app.route('/microblog/posts/<post_id>', methods=['GET', 'POST'])
@login_required
def show_post(post_id):
    post = Post.query.filter_by(id=post_id).first()
    # раз зашли в пост, то нужно увеличить кол-во просмотров
    post.add_views()
    comment_form = NewCommentForm()
    # если добавляли новый пост
    if comment_form.validate_on_submit():
        comment = Comment(user_id=current_user.id, post_id=post.id,
                          comment_text=comment_form.comment_text.data)
        db.session.add(comment)
        db.session.commit()
    comments = post.comments
    return render_template('show_post.html', title=post.post_title, post=post,
                           comments=comments, comment_form=comment_form)


@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    comments = [
        {'author': user, 'comment_text': 'Test post #1'},
        {'author': user, 'comment_text': 'Test post #2'}
    ]
    decks = user.decks
    deck_counter = 0
    # правильно ли делать это тут?
    for deck in decks:
        deck_counter += 1
    # пробуем вытащить скиллы пользователя
    try:
        skills = current_user.skills[0]
    except IndexError:
        # если скиллов нету, то пишем об этом
        sk = Skill()
        skills = {
            'first_skill': sk.default_skills(),
            'second_skill': '',
            'third_skill': '',
            'fourth_skill': '',
            'fifth_skill': ''
        }
    return render_template('user.html', title=user.username,
                           user=user, comments=comments,
                           deck_counter=str(deck_counter), decks=decks,
                           skills=skills)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_user = form.about_user.data
        # загрузим все скиллы
        five_skills_lst = [form.first_skill.data, form.second_skill.data,
                           form.third_skill.data, form.fourth_skill.data,
                           form.fifth_skill.data]
        skills_updater(user_id=current_user.id,
                       five_skills_lst=five_skills_lst)
        # загрузим аватар
        file = form.avatar_pic.data
        if file:
            filename = secure_filename(file.filename)
            # ищем в папке аватаров такой же файл
            # если нашли, то не разрешаем поставить такой же
            check_path = os.path.join('app/static/img/avatars', filename)
            if os.path.exists(check_path):
                flash('Аватар с таким именем файла уже существует.')
                return render_template('edit_profile.html',
                                       title='Edit Profile', form=form)
            # проверяем был ли аватар, если был то удаляем из папки файл
            if current_user.userpic:
                old_avatar_path = 'app{}'.format(current_user.userpic)
                os.remove(old_avatar_path)
            # проверяем и сохраняем файл с аватаром
            file.save(os.path.join('app/static/img/avatars', filename))
            current_user.userpic = os.path.join(
                '/static/img/avatars', filename)
        db.session.commit()
        flash('Изменения сохранены.')
        return redirect(url_for('user', username=current_user.username))
    # если формы нужно предзаполнить
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_user.data = current_user.about_user
        # form.first_skill.data = current_user.skills
        try:
            skills = current_user.skills[0]
        except IndexError:
            skills = None
        # skills = Skill.query.filter_by(user_id=current_user.id).first()
        if skills:
            form.first_skill.data = skills.first_skill
            form.second_skill.data = skills.second_skill
            form.third_skill.data = skills.third_skill
            form.fourth_skill.data = skills.fourth_skill
            form.fifth_skill.data = skills.fifth_skill
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)


def skills_updater(user_id, five_skills_lst=['', '', '', '', '']):
    """Вспомогательная функция для обновления скиллов"""
    skills = Skill.query.filter_by(user_id=current_user.id).first()
    # если нашли, то перезаполняем
    if skills:
        skills.first_skill = five_skills_lst[0]
        skills.second_skill = five_skills_lst[1]
        skills.third_skill = five_skills_lst[2]
        skills.fourth_skill = five_skills_lst[3]
        skills.fifth_skill = five_skills_lst[4]
    # если не нашли, то создаём
    else:
        skills = Skill(first_skill=five_skills_lst[0],
                       second_skill=five_skills_lst[1],
                       third_skill=five_skills_lst[2],
                       fourth_skill=five_skills_lst[3],
                       fifth_skill=five_skills_lst[4],
                       user_id=current_user.id)
        db.session.add(skills)


@app.route('/create_deck', methods=['GET', 'POST'])
@login_required
def create_deck():
    form = DeckCreationForm()
    if form.validate_on_submit():
        new_deck = Deck(deck_name=form.deck_name.data,
                        deck_info=form.deck_info.data,
                        user_id=current_user.id)
        # сохраняем изображение в static, а путь к нему в бд
        try:
            # проверять размер!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            f = request.files['file']
        except BadRequestKeyError:
            f = None
        if f and allowed_file(f.filename):
            image = secure_filename(f.filename)
            path_to_save = os.path.join('app/static/img/decks_img',
                                        image)
            f.save(path_to_save)
            ref_for_db = os.path.join('/static/img/decks_img',
                                      image)
            new_deck.deckpic = ref_for_db
        db.session.add(new_deck)
        db.session.commit()
        flash('Колода создана.')
        return redirect(url_for('user', username=current_user.username))
    return render_template('create_deck.html', form=form,
                           title='Deck creation')


@app.route('/edit_deck/<deck_id>', methods=['GET', 'POST'])
@login_required
def edit_deck(deck_id):
    # находим колоду по переданному deck_id
    deck = Deck.query.filter_by(id=deck_id).first_or_404()
    # не разрешаем редактировать не свою колоду
    if deck.owner != current_user:
        flash('Редактирование чужих колод запрещено!')
        return redirect(url_for('user', username=current_user.username))
    # если формы нужно предзаполнить
    form = EditDeckForm()
    # если формы отправляются
    if form.validate_on_submit():
        deck.deck_name = form.deck_name.data
        deck.deck_info = form.deck_info.data
        # картинка
        try:
            # проверять размер!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            f = request.files['file']
        except BadRequestKeyError:
            f = None
        if f and allowed_file(f.filename):
            image = secure_filename(f.filename)
            path_to_save = os.path.join('app/static/img/decks_img',
                                        image)
            f.save(path_to_save)
            ref_for_db = os.path.join('/static/img/decks_img',
                                      image)
            deck.deckpic = ref_for_db

        db.session.commit()
        return render_template('edit_deck.html', title='Edit Deck',
                               form=form, deck=deck)
    # если формы нужно предзаполнить
    elif request.method == 'GET':
        form.deck_name.data = deck.deck_name
        form.deck_info.data = deck.deck_info
        return render_template('edit_deck.html', title='Edit Deck',
                               form=form, deck=deck)


@app.route('/delete_deck/<deck_id>', methods=['GET', 'POST'])
@login_required
def delete_deck(deck_id):
    # находим колоду по переданному deck_id
    deck = Deck.query.filter_by(id=deck_id).first_or_404()
    # не разрешаем удалять не свою колоду
    if deck.owner != current_user:
        flash('Редактирование чужих колод запрещено!')
        return redirect(url_for('user', username=current_user.username))
    # удаляем её
    db.session.delete(deck)
    db.session.commit()
    return redirect(url_for('user', username=current_user.username))


def admin_user_required(func):
    """Декоратор для проверки, что текущий юзер админ"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if current_user.username != 'admin':
            flash('Функция только для администратора.')
            return redirect(url_for('user', username=current_user.username))
        return func(*args, **kwargs)
    return wrapper


@app.route('/new_post', methods=['GET', 'POST'])
@admin_user_required
def new_post():
    form = PostCreationForm()
    # если прожали submit при создании поста
    if form.validate_on_submit():
        # получаем, проверяем, сохраняем
        ref_for_db = ''
        if request.method == 'POST':
            # проверяем передавался ли файл
            try:
                # проверять размер!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
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


@app.route('/edit_deck_cards/<deck_id>', methods=['GET', 'POST'])
def edit_deck_cards(deck_id):
    """
    Редактирование карточек в колоде
    """
    deck = Deck.query.filter_by(id=deck_id).first()
    # не разрешаем редактировать не свою колоду
    if deck.owner != current_user:
        flash('Редактирование чужих колод запрещено!')
        return redirect(url_for('user', username=current_user.username))
    cards = deck.cards
    card_creation_form = CreateCardForm()
    return render_template('edit_deck_cards.html',
                           title='Редактирование колоды.',
                           deck=deck,
                           cards=cards,
                           creation_form=card_creation_form)
# @login_required - декоратор, сделает логин обязательным
# для просмотра страницы
