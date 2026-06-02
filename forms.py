from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, SelectField, TextAreaField,
                     IntegerField, DecimalField, BooleanField, DateField, SubmitField)
from wtforms.validators import (DataRequired, Email, Length, EqualTo,
                                 NumberRange, Optional, ValidationError)
import re


def strong_password(form, field):
    pw = field.data
    if len(pw) < 8:
        raise ValidationError('Password must be at least 8 characters.')
    if not re.search(r'[A-Z]', pw):
        raise ValidationError('Password must contain an uppercase letter.')
    if not re.search(r'[0-9]', pw):
        raise ValidationError('Password must contain a number.')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember me')
    submit = SubmitField('Sign In')


class RegisterForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(3, 120)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    national_id = StringField('National ID / Student ID', validators=[Optional(), Length(max=20)])
    password = PasswordField('Password', validators=[DataRequired(), strong_password])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Create Account')


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), strong_password])
    confirm_password = PasswordField('Confirm New Password',
                                     validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Change Password')


class CourseForm(FlaskForm):
    title = StringField('Course Title', validators=[DataRequired(), Length(5, 200)])
    code = StringField('Course Code', validators=[DataRequired(), Length(3, 20)])
    description = TextAreaField('Description', validators=[Optional()])
    duration_months = IntegerField('Duration (Months)', validators=[DataRequired(),
                                                                     NumberRange(2, 6)])
    price = DecimalField('Price (KES)', validators=[DataRequired(), NumberRange(min=0)],
                          places=2)
    max_students = IntegerField('Maximum Students', validators=[DataRequired(),
                                                                 NumberRange(1, 200)])
    category_id = SelectField('Category', coerce=int, validators=[Optional()])
    instructor_id = SelectField('Instructor', coerce=int, validators=[Optional()])
    schedule = StringField('Schedule', validators=[Optional(), Length(max=200)])
    prerequisites = TextAreaField('Prerequisites', validators=[Optional()])
    start_date = DateField('Start Date', validators=[Optional()])
    end_date = DateField('End Date', validators=[Optional()])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save Course')


class UserForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(3, 120)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    national_id = StringField('National ID', validators=[Optional(), Length(max=20)])
    role = SelectField('Role', choices=[('student', 'Student'),
                                        ('instructor', 'Instructor'),
                                        ('admin', 'Admin')])
    is_active = BooleanField('Active', default=True)
    password = PasswordField('Password (leave blank to keep)', validators=[Optional(), strong_password])
    submit = SubmitField('Save User')


class EnrollmentForm(FlaskForm):
    student_id = SelectField('Student', coerce=int, validators=[DataRequired()])
    course_id = SelectField('Course', coerce=int, validators=[DataRequired()])
    status = SelectField('Status', choices=[('pending', 'Pending'),
                                             ('active', 'Active'),
                                             ('completed', 'Completed'),
                                             ('dropped', 'Dropped')])
    submit = SubmitField('Save Enrollment')


class PaymentForm(FlaskForm):
    student_id = SelectField('Student', coerce=int, validators=[DataRequired()])
    enrollment_id = SelectField('Enrollment / Course', coerce=int, validators=[Optional()])
    amount = DecimalField('Amount (KES)', validators=[DataRequired(), NumberRange(min=1)], places=2)
    method = SelectField('Payment Method', choices=[
        ('mpesa', 'M-Pesa'),
        ('bank', 'Bank Transfer'),
        ('cash', 'Cash'),
    ])
    reference = StringField('Reference / Receipt No.', validators=[Optional(), Length(max=100)])
    notes = TextAreaField('Notes', validators=[Optional()])
    status = SelectField('Status', choices=[('pending', 'Pending'),
                                             ('confirmed', 'Confirmed'),
                                             ('failed', 'Failed')])
    submit = SubmitField('Record Payment')


class AnnouncementForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(5, 200)])
    body = TextAreaField('Message', validators=[DataRequired()])
    course_id = SelectField('Target (leave blank for school-wide)', coerce=int, validators=[Optional()])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Post Announcement')


class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired(), Length(2, 100)])
    description = TextAreaField('Description', validators=[Optional()])
    submit = SubmitField('Save Category')
