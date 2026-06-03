import os
import uuid
from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, send_file, abort, current_app)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, Course, CourseMaterial, Enrollment
from utils import instructor_or_admin_required, log_action

instructor_bp = Blueprint('instructor', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'mp4'}
MAX_FILE_MB = 100


def _allowed(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _save_file(file):
    ext = file.filename.rsplit('.', 1)[1].lower()
    stored_name = f"{uuid.uuid4().hex}.{ext}"
    upload_dir = os.path.join(current_app.root_path, 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    path = os.path.join(upload_dir, stored_name)
    file.save(path)
    size = os.path.getsize(path)
    return stored_name, ext, size


# ── Materials list ─────────────────────────────────────────────────────────────
@instructor_bp.route('/materials')
@login_required
@instructor_or_admin_required
def materials():
    # Instructors see only their courses; admins see all
    if current_user.is_admin():
        courses = Course.query.filter_by(is_active=True).order_by(Course.title).all()
    else:
        courses = Course.query.filter_by(
            instructor_id=current_user.id, is_active=True).order_by(Course.title).all()

    course_id = request.args.get('course_id', '')
    mtype     = request.args.get('type', '')

    query = CourseMaterial.query
    if not current_user.is_admin():
        query = query.join(Course).filter(Course.instructor_id == current_user.id)
    if course_id:
        query = query.filter(CourseMaterial.course_id == int(course_id))
    if mtype:
        query = query.filter(CourseMaterial.material_type == mtype)

    materials_list = query.order_by(CourseMaterial.created_at.desc()).all()

    return render_template('instructor/materials.html',
                           materials=materials_list,
                           courses=courses,
                           selected_course=course_id,
                           selected_type=mtype)


# ── Upload ─────────────────────────────────────────────────────────────────────
@instructor_bp.route('/materials/upload', methods=['GET', 'POST'])
@login_required
@instructor_or_admin_required
def upload_material():
    if current_user.is_admin():
        courses = Course.query.filter_by(is_active=True).order_by(Course.title).all()
    else:
        courses = Course.query.filter_by(
            instructor_id=current_user.id, is_active=True).order_by(Course.title).all()

    if request.method == 'POST':
        title       = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        course_id   = request.form.get('course_id', '')
        mtype       = request.form.get('material_type', '')
        file        = request.files.get('file')

        # Validation
        if not all([title, course_id, mtype, file and file.filename]):
            flash('All fields including the file are required.', 'danger')
            return render_template('instructor/upload_material.html', courses=courses)

        if not _allowed(file.filename):
            flash('Only PDF and MP4 files are allowed.', 'danger')
            return render_template('instructor/upload_material.html', courses=courses)

        # Check file size
        file.seek(0, 2)
        size_mb = file.tell() / (1024 * 1024)
        file.seek(0)
        if size_mb > MAX_FILE_MB:
            flash(f'File too large. Maximum allowed is {MAX_FILE_MB} MB.', 'danger')
            return render_template('instructor/upload_material.html', courses=courses)

        stored_name, ext, size = _save_file(file)

        material = CourseMaterial(
            course_id=int(course_id),
            uploaded_by=current_user.id,
            title=title,
            description=description,
            material_type=mtype,
            filename=stored_name,
            original_filename=secure_filename(file.filename),
            file_type=ext,
            file_size=size,
        )
        db.session.add(material)
        db.session.commit()
        log_action('upload_material', 'course_material', material.id,
                   details=f'{mtype}: {title}')
        flash(f'"{title}" uploaded successfully.', 'success')
        return redirect(url_for('instructor.materials'))

    return render_template('instructor/upload_material.html', courses=courses)


# ── Delete ─────────────────────────────────────────────────────────────────────
@instructor_bp.route('/materials/<int:mat_id>/delete', methods=['POST'])
@login_required
@instructor_or_admin_required
def delete_material(mat_id):
    mat = CourseMaterial.query.get_or_404(mat_id)
    # Instructors can only delete their own uploads
    if not current_user.is_admin() and mat.uploaded_by != current_user.id:
        abort(403)
    # Remove file from disk
    path = os.path.join(current_app.root_path, 'uploads', mat.filename)
    if os.path.exists(path):
        os.remove(path)
    db.session.delete(mat)
    db.session.commit()
    flash('Material deleted.', 'success')
    return redirect(url_for('instructor.materials'))


# ── View (stream — no download header) ────────────────────────────────────────
@instructor_bp.route('/materials/<int:mat_id>/view')
@login_required
def view_material(mat_id):
    mat = CourseMaterial.query.get_or_404(mat_id)

    # Students must be enrolled in the course
    if current_user.is_student():
        enrolled = Enrollment.query.filter_by(
            student_id=current_user.id,
            course_id=mat.course_id
        ).filter(Enrollment.status.in_(['active', 'completed'])).first()
        if not enrolled:
            abort(403)

    path = os.path.join(current_app.root_path, 'uploads', mat.filename)
    if not os.path.exists(path):
        abort(404)

    mime = 'application/pdf' if mat.file_type == 'pdf' else 'video/mp4'
    return send_file(path, mimetype=mime, as_attachment=False)
