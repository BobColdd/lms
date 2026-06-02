from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime
from models import db, User, Course, Enrollment, Payment, Announcement, Category, AuditLog
from forms import (CourseForm, UserForm, EnrollmentForm, PaymentForm,
                   AnnouncementForm, CategoryForm)
from utils import admin_required, instructor_or_admin_required, log_action
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__)


# ── Dashboard ──────────────────────────────────────────────────────────────────
@admin_bp.route('/dashboard')
@login_required
@instructor_or_admin_required
def dashboard():
    total_students = User.query.filter_by(role='student').count()
    total_courses = Course.query.filter_by(is_active=True).count()
    total_enrollments = Enrollment.query.filter_by(status='active').count()
    revenue = db.session.query(func.sum(Payment.amount))\
                        .filter_by(status='confirmed').scalar() or 0

    recent_enrollments = (Enrollment.query
                          .order_by(Enrollment.enrolled_at.desc()).limit(10).all())
    recent_payments = (Payment.query
                       .order_by(Payment.created_at.desc()).limit(5).all())
    announcements = (Announcement.query.filter_by(is_active=True)
                     .order_by(Announcement.created_at.desc()).limit(5).all())

    return render_template('admin/dashboard.html',
                           total_students=total_students,
                           total_courses=total_courses,
                           total_enrollments=total_enrollments,
                           revenue=revenue,
                           recent_enrollments=recent_enrollments,
                           recent_payments=recent_payments,
                           announcements=announcements)


# ── Users ──────────────────────────────────────────────────────────────────────
@admin_bp.route('/users')
@login_required
@admin_required
def users():
    role_filter = request.args.get('role', '')
    search = request.args.get('search', '')
    query = User.query
    if role_filter:
        query = query.filter_by(role=role_filter)
    if search:
        query = query.filter(User.full_name.ilike(f'%{search}%') |
                             User.email.ilike(f'%{search}%'))
    users_list = query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users_list,
                           role_filter=role_filter, search=search)


@admin_bp.route('/users/new', methods=['GET', 'POST'])
@login_required
@admin_required
def user_new():
    form = UserForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return render_template('admin/user_form.html', form=form, title='New User')
        user = User(
            full_name=form.full_name.data.strip(),
            email=email,
            phone=form.phone.data,
            national_id=form.national_id.data,
            role=form.role.data,
            is_active=form.is_active.data,
        )
        if form.password.data:
            user.set_password(form.password.data)
        else:
            user.set_password('Temp@1234')
        db.session.add(user)
        db.session.commit()
        log_action('create_user', 'user', user.id)
        flash(f'User {user.full_name} created.', 'success')
        return redirect(url_for('admin.users'))
    return render_template('admin/user_form.html', form=form, title='New User')


@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def user_edit(user_id):
    user = User.query.get_or_404(user_id)
    form = UserForm(obj=user)
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        existing = User.query.filter_by(email=email).first()
        if existing and existing.id != user.id:
            flash('Email already in use.', 'danger')
            return render_template('admin/user_form.html', form=form, title='Edit User', user=user)
        user.full_name = form.full_name.data.strip()
        user.email = email
        user.phone = form.phone.data
        user.national_id = form.national_id.data
        user.role = form.role.data
        user.is_active = form.is_active.data
        if form.password.data:
            user.set_password(form.password.data)
        db.session.commit()
        log_action('update_user', 'user', user.id)
        flash('User updated.', 'success')
        return redirect(url_for('admin.users'))
    return render_template('admin/user_form.html', form=form, title='Edit User', user=user)


@admin_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def user_toggle(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot deactivate your own account.', 'warning')
        return redirect(url_for('admin.users'))
    user.is_active = not user.is_active
    db.session.commit()
    log_action('toggle_user', 'user', user.id)
    status = 'activated' if user.is_active else 'deactivated'
    flash(f'User {user.full_name} {status}.', 'success')
    return redirect(url_for('admin.users'))


# ── Courses ────────────────────────────────────────────────────────────────────
@admin_bp.route('/courses')
@login_required
@instructor_or_admin_required
def courses():
    courses_list = Course.query.order_by(Course.title).all()
    return render_template('admin/courses.html', courses=courses_list)


@admin_bp.route('/courses/new', methods=['GET', 'POST'])
@login_required
@admin_required
def course_new():
    form = CourseForm()
    form.category_id.choices = [(0, '-- Select Category --')] + \
        [(c.id, c.name) for c in Category.query.order_by(Category.name).all()]
    form.instructor_id.choices = [(0, '-- Assign Instructor --')] + \
        [(u.id, u.full_name) for u in User.query.filter_by(role='instructor').all()]
    if form.validate_on_submit():
        if Course.query.filter_by(code=form.code.data.upper()).first():
            flash('Course code already exists.', 'danger')
            return render_template('admin/course_form.html', form=form, title='New Course')
        course = Course(
            title=form.title.data.strip(),
            code=form.code.data.upper().strip(),
            description=form.description.data,
            duration_months=form.duration_months.data,
            price=form.price.data,
            max_students=form.max_students.data,
            category_id=form.category_id.data or None,
            instructor_id=form.instructor_id.data or None,
            schedule=form.schedule.data,
            prerequisites=form.prerequisites.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            is_active=form.is_active.data,
        )
        db.session.add(course)
        db.session.commit()
        log_action('create_course', 'course', course.id)
        flash(f'Course {course.code} created.', 'success')
        return redirect(url_for('admin.courses'))
    return render_template('admin/course_form.html', form=form, title='New Course')


@admin_bp.route('/courses/<int:course_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def course_edit(course_id):
    course = Course.query.get_or_404(course_id)
    form = CourseForm(obj=course)
    form.category_id.choices = [(0, '-- Select Category --')] + \
        [(c.id, c.name) for c in Category.query.order_by(Category.name).all()]
    form.instructor_id.choices = [(0, '-- Assign Instructor --')] + \
        [(u.id, u.full_name) for u in User.query.filter_by(role='instructor').all()]
    if form.validate_on_submit():
        existing = Course.query.filter_by(code=form.code.data.upper()).first()
        if existing and existing.id != course.id:
            flash('Course code already in use.', 'danger')
            return render_template('admin/course_form.html', form=form,
                                   title='Edit Course', course=course)
        course.title = form.title.data.strip()
        course.code = form.code.data.upper().strip()
        course.description = form.description.data
        course.duration_months = form.duration_months.data
        course.price = form.price.data
        course.max_students = form.max_students.data
        course.category_id = form.category_id.data or None
        course.instructor_id = form.instructor_id.data or None
        course.schedule = form.schedule.data
        course.prerequisites = form.prerequisites.data
        course.start_date = form.start_date.data
        course.end_date = form.end_date.data
        course.is_active = form.is_active.data
        db.session.commit()
        log_action('update_course', 'course', course.id)
        flash('Course updated.', 'success')
        return redirect(url_for('admin.courses'))
    return render_template('admin/course_form.html', form=form, title='Edit Course', course=course)


# ── Enrollments ────────────────────────────────────────────────────────────────
@admin_bp.route('/enrollments')
@login_required
@instructor_or_admin_required
def enrollments():
    status_filter = request.args.get('status', '')
    query = Enrollment.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    enrolments_list = query.order_by(Enrollment.enrolled_at.desc()).all()
    return render_template('admin/enrollments.html',
                           enrollments=enrolments_list,
                           status_filter=status_filter)


@admin_bp.route('/enrollments/new', methods=['GET', 'POST'])
@login_required
@admin_required
def enrollment_new():
    form = EnrollmentForm()
    form.student_id.choices = [(u.id, f'{u.full_name} ({u.email})')
                                for u in User.query.filter_by(role='student').order_by(User.full_name).all()]
    form.course_id.choices = [(c.id, f'{c.code} – {c.title}')
                               for c in Course.query.filter_by(is_active=True).order_by(Course.title).all()]
    if form.validate_on_submit():
        existing = Enrollment.query.filter_by(
            student_id=form.student_id.data,
            course_id=form.course_id.data).first()
        if existing:
            flash('Student already enrolled in this course.', 'warning')
        else:
            e = Enrollment(student_id=form.student_id.data,
                           course_id=form.course_id.data,
                           status=form.status.data)
            db.session.add(e)
            db.session.commit()
            log_action('create_enrollment', 'enrollment', e.id)
            flash('Enrollment created.', 'success')
        return redirect(url_for('admin.enrollments'))
    return render_template('admin/enrollment_form.html', form=form, title='New Enrollment')


@admin_bp.route('/enrollments/<int:enr_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def enrollment_edit(enr_id):
    enr = Enrollment.query.get_or_404(enr_id)
    form = EnrollmentForm(obj=enr)
    form.student_id.choices = [(u.id, f'{u.full_name} ({u.email})')
                                for u in User.query.filter_by(role='student').order_by(User.full_name).all()]
    form.course_id.choices = [(c.id, f'{c.code} – {c.title}')
                               for c in Course.query.order_by(Course.title).all()]
    if form.validate_on_submit():
        enr.student_id = form.student_id.data
        enr.course_id = form.course_id.data
        enr.status = form.status.data
        if form.status.data == 'completed' and not enr.completion_date:
            enr.completion_date = datetime.utcnow()
        db.session.commit()
        log_action('update_enrollment', 'enrollment', enr.id)
        flash('Enrollment updated.', 'success')
        return redirect(url_for('admin.enrollments'))
    return render_template('admin/enrollment_form.html', form=form, title='Edit Enrollment', enr=enr)


# ── Payments ───────────────────────────────────────────────────────────────────
@admin_bp.route('/payments')
@login_required
@instructor_or_admin_required
def payments():
    status_filter = request.args.get('status', '')
    query = Payment.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    payments_list = query.order_by(Payment.created_at.desc()).all()
    total = sum(p.amount for p in payments_list if p.status == 'confirmed')
    return render_template('admin/payments.html',
                           payments=payments_list,
                           total=total,
                           status_filter=status_filter)


@admin_bp.route('/payments/new', methods=['GET', 'POST'])
@login_required
@admin_required
def payment_new():
    form = PaymentForm()
    students = User.query.filter_by(role='student').order_by(User.full_name).all()
    form.student_id.choices = [(u.id, f'{u.full_name} ({u.email})') for u in students]
    form.enrollment_id.choices = [(0, '-- Select Enrollment --')] + \
        [(e.id, f'{e.course.code} – {e.course.title}')
         for e in Enrollment.query.filter_by(status='active').all()]
    if form.validate_on_submit():
        payment = Payment(
            student_id=form.student_id.data,
            enrollment_id=form.enrollment_id.data or None,
            amount=form.amount.data,
            method=form.method.data,
            reference=form.reference.data,
            notes=form.notes.data,
            status=form.status.data,
        )
        if form.status.data == 'confirmed':
            payment.confirmed_at = datetime.utcnow()
            payment.confirmed_by = current_user.id
        db.session.add(payment)
        db.session.commit()
        log_action('create_payment', 'payment', payment.id)
        flash('Payment recorded.', 'success')
        return redirect(url_for('admin.payments'))
    return render_template('admin/payment_form.html', form=form, title='Record Payment')


@admin_bp.route('/payments/<int:pay_id>/confirm', methods=['POST'])
@login_required
@admin_required
def payment_confirm(pay_id):
    payment = Payment.query.get_or_404(pay_id)
    payment.status = 'confirmed'
    payment.confirmed_at = datetime.utcnow()
    payment.confirmed_by = current_user.id
    # Activate enrollment if pending
    if payment.enrollment_id:
        enr = Enrollment.query.get(payment.enrollment_id)
        if enr and enr.status == 'pending':
            enr.status = 'active'
    db.session.commit()
    log_action('confirm_payment', 'payment', payment.id)
    flash('Payment confirmed.', 'success')
    return redirect(url_for('admin.payments'))


# ── Announcements ──────────────────────────────────────────────────────────────
@admin_bp.route('/announcements')
@login_required
@instructor_or_admin_required
def announcements():
    anns = Announcement.query.order_by(Announcement.created_at.desc()).all()
    return render_template('admin/announcements.html', announcements=anns)


@admin_bp.route('/announcements/new', methods=['GET', 'POST'])
@login_required
@instructor_or_admin_required
def announcement_new():
    form = AnnouncementForm()
    form.course_id.choices = [(0, 'School-wide')] + \
        [(c.id, c.title) for c in Course.query.filter_by(is_active=True).order_by(Course.title).all()]
    if form.validate_on_submit():
        ann = Announcement(
            title=form.title.data.strip(),
            body=form.body.data,
            author_id=current_user.id,
            course_id=form.course_id.data or None,
            is_active=form.is_active.data,
        )
        db.session.add(ann)
        db.session.commit()
        log_action('create_announcement', 'announcement', ann.id)
        flash('Announcement posted.', 'success')
        return redirect(url_for('admin.announcements'))
    return render_template('admin/announcement_form.html', form=form, title='New Announcement')


@admin_bp.route('/announcements/<int:ann_id>/delete', methods=['POST'])
@login_required
@instructor_or_admin_required
def announcement_delete(ann_id):
    ann = Announcement.query.get_or_404(ann_id)
    db.session.delete(ann)
    db.session.commit()
    flash('Announcement deleted.', 'success')
    return redirect(url_for('admin.announcements'))


# ── Categories ─────────────────────────────────────────────────────────────────
@admin_bp.route('/categories')
@login_required
@admin_required
def categories():
    cats = Category.query.order_by(Category.name).all()
    return render_template('admin/categories.html', categories=cats)


@admin_bp.route('/categories/new', methods=['GET', 'POST'])
@login_required
@admin_required
def category_new():
    form = CategoryForm()
    if form.validate_on_submit():
        cat = Category(name=form.name.data.strip(), description=form.description.data)
        db.session.add(cat)
        db.session.commit()
        flash('Category created.', 'success')
        return redirect(url_for('admin.categories'))
    return render_template('admin/category_form.html', form=form, title='New Category')


# ── Audit Log ──────────────────────────────────────────────────────────────────
@admin_bp.route('/audit-log')
@login_required
@admin_required
def audit_log():
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(200).all()
    return render_template('admin/audit_log.html', logs=logs)
