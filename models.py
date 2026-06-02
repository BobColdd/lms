from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class Role:
    ADMIN = 'admin'
    INSTRUCTOR = 'instructor'
    STUDENT = 'student'


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=Role.STUDENT)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    profile_photo = db.Column(db.String(255), nullable=True)
    national_id = db.Column(db.String(20), nullable=True)

    # Relationships
    enrollments = db.relationship('Enrollment', backref='student', lazy='dynamic',
                                   foreign_keys='Enrollment.student_id')
    instructed_courses = db.relationship('Course', backref='instructor', lazy='dynamic',
                                          foreign_keys='Course.instructor_id')
    
    payments = db.relationship('Payment', backref='student', lazy='dynamic',
                            foreign_keys='Payment.student_id')
    announcements = db.relationship('Announcement', backref='author', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == Role.ADMIN

    def is_instructor(self):
        return self.role == Role.INSTRUCTOR

    def is_student(self):
        return self.role == Role.STUDENT

    def __repr__(self):
        return f'<User {self.email}>'


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    courses = db.relationship('Course', backref='category', lazy='dynamic')

    def __repr__(self):
        return f'<Category {self.name}>'


class Course(db.Model):
    __tablename__ = 'courses'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    duration_months = db.Column(db.Integer, nullable=False)  # 2–6 months
    price = db.Column(db.Numeric(10, 2), nullable=False)
    max_students = db.Column(db.Integer, default=30)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    schedule = db.Column(db.String(200), nullable=True)  # e.g. "Mon/Wed/Fri 8AM–10AM"
    prerequisites = db.Column(db.Text, nullable=True)
    thumbnail = db.Column(db.String(255), nullable=True)

    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    instructor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Relationships
    enrollments = db.relationship('Enrollment', backref='course', lazy='dynamic')
    modules = db.relationship('Module', backref='course', lazy='dynamic',
                               order_by='Module.order')
    announcements = db.relationship('Announcement', backref='course', lazy='dynamic')

    @property
    def enrolled_count(self):
        return self.enrollments.filter_by(status='active').count()

    @property
    def available_slots(self):
        return self.max_students - self.enrolled_count

    def __repr__(self):
        return f'<Course {self.code}: {self.title}>'


class Module(db.Model):
    __tablename__ = 'modules'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    order = db.Column(db.Integer, default=0)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)

    lessons = db.relationship('Lesson', backref='module', lazy='dynamic',
                               order_by='Lesson.order')

    def __repr__(self):
        return f'<Module {self.title}>'


class Lesson(db.Model):
    __tablename__ = 'lessons'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=True)
    resource_url = db.Column(db.String(500), nullable=True)
    order = db.Column(db.Integer, default=0)
    module_id = db.Column(db.Integer, db.ForeignKey('modules.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Lesson {self.title}>'


class Enrollment(db.Model):
    __tablename__ = 'enrollments'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # pending, active, completed, dropped
    completion_date = db.Column(db.DateTime, nullable=True)
    grade = db.Column(db.String(5), nullable=True)
    progress = db.Column(db.Integer, default=0)  # percentage 0–100

    __table_args__ = (db.UniqueConstraint('student_id', 'course_id', name='uq_enrollment'),)

    def __repr__(self):
        return f'<Enrollment student={self.student_id} course={self.course_id}>'


class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    enrollment_id = db.Column(db.Integer, db.ForeignKey('enrollments.id'), nullable=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    method = db.Column(db.String(50), nullable=False)  # mpesa, bank, cash
    reference = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, failed
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    confirmed_at = db.Column(db.DateTime, nullable=True)
    confirmed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    enrollment = db.relationship('Enrollment', backref='payments')

    def __repr__(self):
        return f'<Payment {self.reference} KES {self.amount}>'


class Announcement(db.Model):
    __tablename__ = 'announcements'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=True)  # None = school-wide
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<Announcement {self.title}>'


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(200), nullable=False)
    resource = db.Column(db.String(100), nullable=True)
    resource_id = db.Column(db.Integer, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    details = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<AuditLog {self.action} by user {self.user_id}>'
