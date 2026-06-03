from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, abort
from flask_login import login_required, current_user
from datetime import datetime
from models import db, User, Enrollment, Course
from utils import admin_required, log_action
from certificate import generate_certificate
import uuid

cert_bp = Blueprint('cert', __name__)


@cert_bp.route('/certificates')
@login_required
@admin_required
def certificate_list():
    """Show all completed enrollments eligible for certificates."""
    search = request.args.get('search', '')
    course_id = request.args.get('course_id', '')

    query = Enrollment.query.filter(
        Enrollment.status.in_(['active', 'completed'])
    )
    if course_id:
        query = query.filter_by(course_id=int(course_id))
    if search:
        query = query.join(User, Enrollment.student_id == User.id).filter(
            User.full_name.ilike(f'%{search}%') |
            User.email.ilike(f'%{search}%')
        )

    enrollments = query.order_by(Enrollment.enrolled_at.desc()).all()
    courses = Course.query.filter_by(is_active=True).order_by(Course.title).all()

    return render_template('admin/certificates.html',
                           enrollments=enrollments,
                           courses=courses,
                           search=search,
                           selected_course=course_id)


@cert_bp.route('/certificates/generate/<int:enr_id>')
@login_required
@admin_required
def generate(enr_id):
    """Generate and stream a single certificate PDF."""
    enr = Enrollment.query.get_or_404(enr_id)
    student = enr.student
    course = enr.course

    completion_date = enr.completion_date or datetime.utcnow()
    cert_no = f'SFMCC/{course.code}/{student.id:04d}/{completion_date.year}'
    instructor_name = course.instructor.full_name if course.instructor else ''

    buf = generate_certificate(
        student_name=student.full_name,
        course_title=course.title,
        course_code=course.code,
        duration_months=course.duration_months,
        completion_date=completion_date,
        certificate_no=cert_no,
        instructor_name=instructor_name,
        grade=enr.grade or '',
    )

    log_action('generate_certificate', 'enrollment', enr.id,
               details=f'Certificate for {student.full_name} – {course.code}')

    filename = f"Certificate_{student.full_name.replace(' ', '_')}_{course.code}.pdf"
    return send_file(
        buf,
        mimetype='application/pdf',
        as_attachment=False,       # opens in browser tab for review before printing
        download_name=filename,
    )


@cert_bp.route('/certificates/generate-bulk', methods=['POST'])
@login_required
@admin_required
def generate_bulk():
    """Generate certificates for multiple selected enrollments (zip)."""
    import zipfile
    from io import BytesIO

    ids = request.form.getlist('enr_ids')
    if not ids:
        flash('No students selected.', 'warning')
        return redirect(url_for('cert.certificate_list'))

    zip_buf = BytesIO()
    with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for enr_id in ids:
            enr = Enrollment.query.get(int(enr_id))
            if not enr:
                continue
            student = enr.student
            course = enr.course
            completion_date = enr.completion_date or datetime.utcnow()
            cert_no = f'SFMCC/{course.code}/{student.id:04d}/{completion_date.year}'
            instructor_name = course.instructor.full_name if course.instructor else ''

            pdf_buf = generate_certificate(
                student_name=student.full_name,
                course_title=course.title,
                course_code=course.code,
                duration_months=course.duration_months,
                completion_date=completion_date,
                certificate_no=cert_no,
                instructor_name=instructor_name,
                grade=enr.grade or '',
            )
            fname = f"Certificate_{student.full_name.replace(' ', '_')}_{course.code}.pdf"
            zf.writestr(fname, pdf_buf.read())
            log_action('generate_certificate', 'enrollment', enr.id)

    zip_buf.seek(0)
    flash(f'{len(ids)} certificate(s) generated and downloaded.', 'success')
    return send_file(
        zip_buf,
        mimetype='application/zip',
        as_attachment=True,
        download_name='SFMCC_Certificates.zip',
    )
