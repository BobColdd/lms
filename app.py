from __init__ import create_app, db
from models import User, Role, Category, Course
import os

app = create_app(os.environ.get('FLASK_ENV', 'development'))


@app.cli.command('seed')
def seed():
    """Seed the database with initial data."""
    with app.app_context():
        db.create_all()

        if not User.query.filter_by(email='admin@sfmcc.ac.ke').first():
            admin = User(
                full_name='System Administrator',
                email='admin@sfmcc.ac.ke',
                role=Role.ADMIN,
                is_active=True
            )
            admin.set_password('Admin@1234')
            db.session.add(admin)

        cats = ['Web Development', 'Computer Fundamentals', 'Networking',
                'Graphic Design', 'Database Management', 'Office Applications']
        for cname in cats:
            if not Category.query.filter_by(name=cname).first():
                db.session.add(Category(name=cname))

        db.session.commit()

        cat_web = Category.query.filter_by(name='Web Development').first()
        cat_net = Category.query.filter_by(name='Networking').first()
        cat_comp = Category.query.filter_by(name='Computer Fundamentals').first()
        cat_design = Category.query.filter_by(name='Graphic Design').first()
        cat_db = Category.query.filter_by(name='Database Management').first()
        cat_office = Category.query.filter_by(name='Office Applications').first()

        courses = [
            Course(title='Web Design & Development', code='WDD-101',
                   description='Learn HTML, CSS, JavaScript and build real websites from scratch.',
                   duration_months=3, price=12000, category_id=cat_web.id,
                   schedule='Mon/Wed/Fri 8:00–10:00AM', max_students=25),
            Course(title='Computer Packages', code='CP-101',
                   description='Microsoft Office Suite: Word, Excel, PowerPoint, and more.',
                   duration_months=2, price=7000, category_id=cat_office.id,
                   schedule='Daily 8:00–10:00AM', max_students=30),
            Course(title='Networking Fundamentals', code='NET-101',
                   description='CompTIA Network+ aligned. LAN/WAN, routers, switches.',
                   duration_months=4, price=15000, category_id=cat_net.id,
                   schedule='Tue/Thu 9:00–12:00PM', max_students=20),
            Course(title='Graphic Design', code='GD-101',
                   description='CorelDRAW & Photoshop for print and digital media.',
                   duration_months=3, price=13000, category_id=cat_design.id,
                   schedule='Mon/Wed 2:00–5:00PM', max_students=20),
            Course(title='Database Administration', code='DBA-101',
                   description='MySQL and PostgreSQL database design and management.',
                   duration_months=4, price=16000, category_id=cat_db.id,
                   schedule='Tue/Thu/Sat 8:00–11:00AM', max_students=20),
            Course(title='Introduction to Computers', code='IC-101',
                   description='Basic computer skills for beginners. Zero experience needed.',
                   duration_months=2, price=5000, category_id=cat_comp.id,
                   schedule='Daily 10:00AM–12:00PM', max_students=35),
            Course(title='Python Programming', code='PY-101',
                   description='Python from scratch: variables, loops, functions, OOP, projects.',
                   duration_months=6, price=20000, category_id=cat_web.id,
                   schedule='Mon/Wed/Fri 10:00AM–1:00PM', max_students=20),
            Course(title='Cybersecurity Essentials', code='CS-101',
                   description='Protect systems and networks. Ethical hacking fundamentals.',
                   duration_months=6, price=22000, category_id=cat_net.id,
                   schedule='Sat/Sun 8:00AM–2:00PM', max_students=15),
        ]
        for c in courses:
            if not Course.query.filter_by(code=c.code).first():
                db.session.add(c)

        db.session.commit()
        print("Database seeded successfully.")
        print("Admin login: admin@sfmcc.ac.ke / Admin@1234")


if __name__ == '__main__':
    app.run(debug=True)
