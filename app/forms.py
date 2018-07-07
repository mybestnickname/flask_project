from flask_wtf import FlaskForm
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


class DeleteDeckForm(FlaskForm):
    check_box = BooleanField()
    submit = SubmitField('Confirm delete')


class PostCreationForm(FlaskForm):
    """Формы создания нового поста админом"""
    post_title = StringField('New post title:',
                             validators=[DataRequired(),
                                         Length(min=1, max=128)])
    post_text = TextAreaField('New post text:',
                              validators=[DataRequired(),
                                          Length(min=1, max=1024)])
    submit = SubmitField('CreatePost')
