from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,SubmitField
from wtforms.validators import DataRequired,Email,ValidationError
from flask_wtf.file import FileField, FileAllowed
from AttendanceProject.models import User
from flask_login import current_user

class AddCourseForm(FlaskForm):
    name = StringField('Course Name',validators=[DataRequired()])
    author_id = StringField('Doctor Full Name',validators=[DataRequired()])
    submit = SubmitField('Add Course')
class AddUserForm(FlaskForm):
    first_name = StringField('First Name',validators=[DataRequired()])
    last_name = StringField('Last Name',validators=[DataRequired()])
    uni_number = StringField('University Number')
    email = StringField('Email',validators=[DataRequired(),Email()])
    password = StringField('Password',validators=[DataRequired()])
    account_type = StringField('Account Type',validators=[DataRequired()])
    submit = SubmitField('Add User')
class ManageCoursesForm(FlaskForm):
    name = StringField('Course Name',validators=[DataRequired()])
    author_id = StringField('Doctor Full Name',validators=[DataRequired()])
    submit = SubmitField('Delete Course')
class DoctorCoursesForm(FlaskForm):
    name = StringField('Course Name',validators=[DataRequired()])
    enrolled_number = StringField('Students Enrolled Count',validators=[DataRequired()])
    submit = SubmitField('See Course')
class LoginForm(FlaskForm):
    email = StringField('Email',validators=[DataRequired(),Email()])
    password = PasswordField('Password',validators=[DataRequired()])
    submit = SubmitField('Log in')
class DashBoard(FlaskForm):
    first_name= StringField('Email',validators=[DataRequired()])
    last_name= StringField('Email',validators=[DataRequired()])
    email = StringField('Email',validators=[DataRequired(),Email()])
class DoctorAddStudent(FlaskForm):
    student_id= StringField('University Number',validators=[DataRequired()])
    submit = SubmitField('Add Student')
class ChangePasswordForm(FlaskForm):
    current_password= StringField('Current Password',validators=[DataRequired()])
    new_password= StringField('New Password',validators=[DataRequired()])
    submit = SubmitField('Change Password')
class StudentCoursesForm(FlaskForm):
    name = StringField('Course Name',validators=[DataRequired()])
    submit = SubmitField('See Course')
class DoctorAddCourseForm(FlaskForm):
    course_name = StringField('Course Name',validators=[DataRequired()])
    submit = SubmitField('Add Course')
class DoctorRemoveStudent(FlaskForm):
    student_id= StringField('University Number',validators=[DataRequired()])
    submit = SubmitField('Remove Student')
