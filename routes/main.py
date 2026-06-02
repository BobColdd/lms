from flask import Blueprint, render_template
from models import Course, Announcement, Category

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    courses = Course.query.filter_by(is_active=True).order_by(Course.price).limit(6).all()
    announcements = Announcement.query.filter_by(is_active=True, course_id=None)\
                                      .order_by(Announcement.created_at.desc()).limit(3).all()
    categories = Category.query.all()
    return render_template('main/index.html',
                           courses=courses,
                           announcements=announcements,
                           categories=categories)


@main_bp.route('/courses')
def courses():
    all_courses = Course.query.filter_by(is_active=True).order_by(Course.title).all()
    categories = Category.query.all()
    return render_template('main/courses.html', courses=all_courses, categories=categories)


@main_bp.route('/courses/<int:course_id>')
def course_detail(course_id):
    course = Course.query.get_or_404(course_id)
    return render_template('main/course_detail.html', course=course)


@main_bp.app_errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403


@main_bp.app_errorhandler(404)
def not_found(e):
    return render_template('errors/404.html'), 404


@main_bp.app_errorhandler(500)
def server_error(e):
    return render_template('errors/500.html'), 500
