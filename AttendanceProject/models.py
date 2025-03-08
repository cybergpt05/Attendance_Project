from AttendanceProject import app, db, login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    account_type = db.Column(db.String(16), nullable=False)
    first_name = db.Column(db.String(16), nullable=False)
    uni_number = db.Column(db.String(20), nullable=True)
    last_name = db.Column(db.String(16), nullable=False)
    email = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(60), nullable=False)
    courses = db.relationship('Course', backref='doctor', lazy=True)
    attendances = db.relationship('Attendance', backref='student', lazy=True)
    def __repr__(self):
        return f"{self.id};{self.first_name};{self.last_name}"

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_name = db.Column(db.String(100), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # Students enrolled in this course (many-to-many)
    enrolled_students = db.relationship('User', 
                                         secondary='enrollments', 
                                         backref='enrolled_courses',
                                         lazy=True)
    def __repr__(self):
        return f"{self.doctor_id};{self.course_name};{self.enrolled_students}"

# Enrollment Table (Association Table for many-to-many: students <-> courses)
enrollments = db.Table('enrollments',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('course_id', db.Integer, db.ForeignKey('course.id'), primary_key=True)
)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    attend_time = db.Column(db.DateTime, nullable=False)
    # Course relationship (for convenience)
    course = db.relationship('Course', backref='attendance_records')
class QRToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    token = db.Column(db.String(64), nullable=False, unique=True)
    expiration_time = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"<QRToken {self.token}>"
