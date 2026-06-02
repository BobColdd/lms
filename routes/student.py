from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from models import db, Course, Enrollment, Payment, Announcement

student_bp = Blueprint('student', __name__)


def student_only(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ('student',):
            abort(403)
        return f(*args, **kwargs)
    return decorated


@student_bp.route('/dashboard')
@login_required
def dashboard():
    enrollments = (Enrollment.query
                   .filter_by(student_id=current_user.id)
                   .order_by(Enrollment.enrolled_at.desc()).all())
    payments = (Payment.query
                .filter_by(student_id=current_user.id)
                .order_by(Payment.created_at.desc()).limit(5).all())
    # School-wide + course announcements for enrolled courses
    enrolled_course_ids = [e.course_id for e in enrollments]
    announcements = (Announcement.query
                     .filter(
                         Announcement.is_active == True,
                         db.or_(
                             Announcement.course_id == None,
                             Announcement.course_id.in_(enrolled_course_ids)
                         )
                     )
                     .order_by(Announcement.created_at.desc()).limit(5).all())
    return render_template('student/dashboard.html',
                           enrollments=enrollments,
                           payments=payments,
                           announcements=announcements)


@student_bp.route('/courses')
@login_required
def browse_courses():
    courses = Course.query.filter_by(is_active=True).order_by(Course.title).all()
    # Map enrolled course IDs
    enrolled_ids = {e.course_id for e in
                    Enrollment.query.filter_by(student_id=current_user.id).all()}
    return render_template('student/browse_courses.html',
                           courses=courses, enrolled_ids=enrolled_ids)


@student_bp.route('/courses/<int:course_id>/enroll', methods=['POST'])
@login_required
def enroll(course_id):
    course = Course.query.get_or_404(course_id)
    if not course.is_active:
        flash('This course is not currently accepting enrollments.', 'warning')
        return redirect(url_for('student.browse_courses'))
    existing = Enrollment.query.filter_by(
        student_id=current_user.id, course_id=course_id).first()
    if existing:
        flash('You are already enrolled in this course.', 'info')
        return redirect(url_for('student.dashboard'))
    if course.available_slots <= 0:
        flash('This course is full. Please contact admin.', 'warning')
        return redirect(url_for('student.browse_courses'))
    enrollment = Enrollment(student_id=current_user.id,
                            course_id=course_id, status='pending')
    db.session.add(enrollment)
    db.session.commit()
    flash(f'Enrollment request for {course.title} submitted. '
          f'Please complete payment (KES {course.price:,.0f}) to activate.', 'success')
    return redirect(url_for('student.dashboard'))


@student_bp.route('/my-courses')
@login_required
def my_courses():
    enrollments = (Enrollment.query
                   .filter_by(student_id=current_user.id)
                   .order_by(Enrollment.enrolled_at.desc()).all())
    return render_template('student/my_courses.html', enrollments=enrollments)


@student_bp.route('/payments')
@login_required
def payments():
    payments_list = (Payment.query
                     .filter_by(student_id=current_user.id)
                     .order_by(Payment.created_at.desc()).all())
    return render_template('student/payments.html', payments=payments_list)


@student_bp.route('/profile')
@login_required
def profile():
    return render_template('student/profile.html')
