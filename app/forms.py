from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, Length, Optional

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Create Admin User')

class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    content_type = SelectField('Content Type', choices=[
        ('markdown', 'Markdown'),
        ('html', 'HTML')
    ], default='markdown', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])
    preview = TextAreaField('Preview Text', validators=[DataRequired(), Length(max=500)])
    image = StringField('Image Path (optional)', validators=[Optional(), Length(max=200)])
    published = BooleanField('Published')
    featured = BooleanField('Featured')
    show_dates = BooleanField('Show Dates', default=True)
    display_order = StringField('Display Order', validators=[Optional()], description='Lower numbers appear first (0, 1, 2, etc.)')
    submit = SubmitField('Save Post')
