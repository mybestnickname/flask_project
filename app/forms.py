from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms import TextAreaField, FileField
from wtforms.validators import DataRequired, Length
from wtforms.validators import ValidationError, Email, EqualTo
from flask_uploads import UploadSet, IMAGES
from app.models import User


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[
                           DataRequired(), Length(min=4, max=25)])
    password = PasswordField('Password', validators=[
                             DataRequired(), Length(min=7, max=25)])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(),
                                                     Length(min=7, max=25)])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        """
        Проверяем что такого юзернейма ещё нет
        """
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        """
        Проверяем что такого мыла ещё нет
        """
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')


class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    about_user = TextAreaField('About user',
                               validators=[Length(min=0, max=140)])
    first_skill = StringField('First skill:', validators=[
                              Length(min=0, max=128)])
    second_skill = StringField('Second skill:', validators=[
        Length(min=0, max=128)])
    third_skill = StringField('Third skill:', validators=[
                              Length(min=0, max=128)])
    fourth_skill = StringField('Fourth skill:', validators=[
        Length(min=0, max=128)])
    fifth_skill = StringField('Fifth skill:', validators=[
                              Length(min=0, max=128)])

    avatar_pic = FileField('image', validators=[
                           FileAllowed(['jpeg', 'jpg', 'png', 'gif'],
                                       'Images only!')])

    submit = SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.')


class DeckCreationForm(FlaskForm):
    photos = UploadSet('photos', IMAGES)
    deck_name = StringField('Deck name', validators=[DataRequired(),
                                                     Length(min=7, max=64)])
    deck_info = TextAreaField('Deck info', validators=[Length(min=1, max=256)])
    deck_pic = FileField()
    submit = SubmitField('CreateDeck')


class PostCreationForm(FlaskForm):
    """Формы создания нового поста админом"""
    post_title = StringField('New post title:',
                             validators=[DataRequired(),
                                         Length(min=1, max=128)])
    post_text = TextAreaField('New post text:',
                              validators=[DataRequired(),
                                          Length(min=1, max=1024)])
    submit = SubmitField('Добавить пост.')


class NewCommentForm(FlaskForm):
    """Формы создания нового коммента к посту"""
    comment_text = TextAreaField('Текст комментария:',
                                 validators=[DataRequired(),
                                             Length(min=1, max=256)])
    submit = SubmitField('Отправить комментарий')


class EditDeckForm(FlaskForm):
    """Формы редактирования колоды"""
    deck_name = StringField('Deck name', validators=[DataRequired(),
                                                     Length(min=7, max=64)])
    deck_info = TextAreaField('Deck info', validators=[Length(min=1, max=256)])
    deck_pic = FileField()
    submit = SubmitField('Edit Deck')


class SearchUserForm(FlaskForm):
    """Форма для поиска пользователя по имени"""
    search_username = StringField('Имя пользователя:',
                                  validators=[DataRequired(),
                                              Length(min=2, max=64)])
    submit = SubmitField('Искать.')


class CreateCardForm(FlaskForm):
    """Форма для создания новой карточки в колоду"""
    card_name = StringField('Название карточки:',
                            validators=[DataRequired(),
                                        Length(min=1, max=64)])
    question = TextAreaField('Вопрос:', validators=[DataRequired(),
                                                    Length(min=1, max=256)])
    answer = TextAreaField('Ответ:', validators=[DataRequired(),
                                                 Length(min=1, max=1024)])
    submit = SubmitField('Добавить карточку.')
