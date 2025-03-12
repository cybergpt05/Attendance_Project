from flask import render_template,url_for,flash,redirect,request,abort,jsonify,Response
from AttendanceProject import app,db
from AttendanceProject.models import User,Course,Attendance,QRToken
from flask_login import login_user,logout_user,current_user,login_required
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Message
from werkzeug.utils import secure_filename
from AttendanceProject.forms import DoctorRemoveStudent,DoctorAddCourseForm,StudentCoursesForm,ChangePasswordForm,DoctorAddStudent,AddUserForm,LoginForm,AddCourseForm,ManageCoursesForm,DoctorCoursesForm
from werkzeug.exceptions import NotFound
from datetime import datetime
import os,qrcode,time,secrets,pytz,csv,io

jordan_tz = pytz.timezone('Asia/Amman')
def generate_qr(course_id):
    token = secrets.token_urlsafe(16)
    expiration_time = time.time() + 20
    existing_token = QRToken.query.filter_by(course_id=course_id).first()
    
    if existing_token:
        existing_token.token = token
        existing_token.expiration_time = expiration_time
        db.session.commit()
    else:
        new_token = QRToken(course_id=course_id, token=token, expiration_time=expiration_time)
        db.session.add(new_token)
        db.session.commit()
    
    attendance_url = url_for('scan_qr_attendance', course_id=course_id, token=token, _external=True)
    qr = qrcode.make(attendance_url)

    base_dir = os.path.dirname(os.path.abspath(__file__))  
    static_folder = os.path.join(base_dir, "static", "qr_codes")
    os.makedirs(static_folder, exist_ok=True)
    qr_path = os.path.join(static_folder, f"course_{course_id}.png")
    qr.save(qr_path)
    
    return token

@app.route("/")
@app.route("/home",methods=["GET"])
def home():
    return render_template("home.html",title="Home Page")

@app.route('/login',methods=["GET","POST"])
def login():
    form = LoginForm()
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password,password):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Incorrect email or password!','danger')
    return render_template('login.html', title="Login Page", form=form)

@app.route('/logout',methods=["GET"])
def logout():
    if current_user.is_authenticated:
        logout_user()
        return redirect(url_for('home'))
    else:
        flash('You are already logged out!','info')
        return redirect(url_for('home'))
    return redirect(url_for('home'))

@app.route('/profile',methods=["GET","POST"])
@login_required
def profile():
    form = ChangePasswordForm()
    name = current_user.first_name
    if form.validate_on_submit():
        user = User.query.filter_by(id=current_user.id).first()
        current_password = form.current_password.data
        new_password = form.new_password.data
        if check_password_hash(user.password,current_password):
            user.password = generate_password_hash(new_password, method='pbkdf2:sha256')
            db.session.commit()
            flash('Password was changed successfully!','success')
        else:
            flash('current password is incorrect!','danger')
            return redirect(url_for('profile'))
    return render_template('profile.html', title=f'{name} Dashboard',form=form)

@app.route('/superadmin/add_course',methods=["GET","POST"])
@login_required
def add_course():
    user = current_user
    if user.account_type != 'admin':
        return abort(403)
    form = AddCourseForm()
    if form.validate_on_submit():
        try:
            course_name = form.name.data
            doc_name = form.author_id.data.split()
            doctor = User.query.filter_by(first_name=doc_name[0],last_name=doc_name[1]).first_or_404()
            new_course = Course(course_name=course_name + f' - {form.author_id.data}',doctor_id=doctor.id)
            db.session.add(new_course)
            db.session.commit()
            flash(f'{course_name} Course was added successfully to dr.{doctor.first_name} {doctor.last_name} courses list.','success')
        except NotFound:
            flash('No doctors assigned with this name.','danger')
    return render_template('add_course.html',title='Add New Course',form=form)

@app.route('/superadmin/add_user',methods=["GET","POST"])
@login_required
def add_user():
    user = current_user
    if user.account_type != 'admin':
        return abort(403)
    form = AddUserForm()
    if form.validate_on_submit():
        first_name = form.first_name.data
        last_name = form.last_name.data
        uni_number = form.uni_number.data
        email = form.email.data
        password = form.password.data
        account_type = form.account_type.data
        old_user = User.query.filter_by(email=email).first()
        if old_user:
            flash('There exists a user with this email!','danger')
            return redirect(url_for('add_user'))
        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")
        newUser = User(first_name=first_name,last_name=last_name,email=email,password=hashed_password,account_type=account_type,uni_number=uni_number)
        db.session.add(newUser)
        db.session.commit()
        flash('User added successfully!','info')
    return render_template('add_user.html',title='Add User',form=form)

@app.route('/doctor/course/<int:course_id>',methods=["GET","POST"])
@login_required
def course_details(course_id):
    if current_user.account_type != 'doctor':
        return abort(403)
    course = Course.query.get_or_404(course_id)
    course_name = course.course_name
    doctor_id = course.doctor_id
    if current_user.id != doctor_id:
        return abort(403)
    enrolled_students = course.enrolled_students
    student_statuses = {}
    token = generate_qr(course_id)
    if course and enrolled_students:
        for student in enrolled_students:
            today = datetime.now(jordan_tz).date()
            attendance_record = Attendance.query.filter_by(student_id=student.id, course_id=course_id).filter(db.func.date(Attendance.attend_time) == today).first()
            if attendance_record:
                student_statuses[student.id] = 'حاضر'
            else:
                student_statuses[student.id] = 'غائب'
    return render_template('course_details.html', title=course_name, course=course, students=enrolled_students,student_statuses=student_statuses)

@app.route('/doctor/course/check_attendance/<int:course_id>',methods=["POST"])
@login_required
def check_attendance(course_id):
    if current_user.account_type != 'doctor':
        return abort(403)
    course = Course.query.get_or_404(course_id)
    student_statuses = {}
    if course:
        enrolled_students = course.enrolled_students
        doctor_id = course.doctor_id
        if current_user.id != doctor_id:
            abort(403)
        if enrolled_students:
            for student in enrolled_students:
                today = datetime.now(jordan_tz).date()
                attendance_record = Attendance.query.filter_by(student_id=student.id, course_id=course_id).filter(db.func.date(Attendance.attend_time) == today).first()
                if attendance_record:
                    student_statuses[student.id] = 'حاضر'
                else:
                    student_statuses[student.id] = 'غائب'
    else:
        return abort(403)
    return jsonify(student_statuses)

@app.route('/doctor/course/generate_qr/<int:course_id>', methods=["GET","POST"])
@login_required
def generate_qr_api(course_id):
    if current_user.account_type != 'doctor':
        return abort(403)
    course = Course.query.get_or_404(course_id)
    if current_user.id != course.doctor_id:
        abort(403)
    token = generate_qr(course_id)
    return jsonify({"qr_url": url_for('static', filename=f'qr_codes/course_{course_id}.png')})


@app.route("/scan_qr/<int:course_id>",methods=["GET","POST"])
@login_required
def scan_qr_attendance(course_id):
    token = request.args.get("token")
    course = Course.query.filter_by(id=course_id).first()
    user = User.query.filter_by(id=current_user.id).first()
    if course:
        enrollments = course.enrolled_students
        if enrollments:
            if user not in enrollments:
                return abort(403)
        else:
            return abort(403)
        if token:
            qr_token = QRToken.query.filter_by(token=token, course_id=course_id).first()
            if not qr_token or time.time() > qr_token.expiration_time:
                flash('Invalid QR Code format or the code has been expired!','danger')
                return redirect(url_for('home'))
        else:
            flash('Token is missing!','danger')
            return redirect(url_for('home'))
        attendance = Attendance.query.filter_by(student_id=user.id, course_id=course_id).first()
        if attendance:
            attendance.attend_time = datetime.now(jordan_tz)
        else:
            attendance = Attendance(student_id=user.id, course_id=course_id, attend_time=datetime.now(jordan_tz))
            db.session.add(attendance)
        db.session.commit()
        flash('تم تسجيل الحضور بنجاح!','success')
        return redirect(url_for('home'))
    else:
        return abort(403)

@app.route("/mark_attendance", methods=["POST"])
@login_required
def mark_attendance():
    if current_user.account_type != 'doctor':
        return abort(403)
    data = request.get_json()
    student_id = data.get("student_id")
    course_id = data.get("course_id")
    if current_user.id != Course.query.filter_by(id=course_id).first().doctor_id:
        return abort(403)
    if not student_id or not course_id:
        return jsonify({"success": False, "message": "بيانات غير صحيحة"}), 400

    attendance = Attendance.query.filter_by(student_id=student_id, course_id=course_id).first()

    if attendance:
        attendance.attend_time = datetime.now(jordan_tz)
    else:
        attendance = Attendance(student_id=student_id, course_id=course_id, attend_time=datetime.now(jordan_tz))
        db.session.add(attendance)

    db.session.commit()

    return jsonify({"success": True, "message": "تم تسجيل الحضور بنجاح!"})

@app.route("/mark_absent", methods=["POST"])
@login_required
def mark_absent():
    if current_user.account_type != 'doctor':
        return abort(403)
    data = request.get_json()
    student_id = data.get("student_id")
    course_id = data.get("course_id")
    if current_user.id != Course.query.filter_by(id=course_id).first().doctor_id:
        return abort(403)
    if not student_id or not course_id:
        return jsonify({"success": False, "message": "بيانات غير صحيحة"}), 400

    attendance = Attendance.query.filter_by(student_id=student_id, course_id=course_id).first()

    if attendance:
        db.session.delete(attendance)
        db.session.commit()

    return jsonify({"success": True, "message": "تم تسجيل الغياب بنجاح!"})

@app.route('/doctor/add_student/<int:course_id>', methods=["GET", "POST"])
@login_required
def add_student(course_id):
    if current_user.account_type != 'doctor':
        return abort(403)
    user = current_user
    course = Course.query.filter_by(id=course_id).first()
    if course:
        if user.id != course.doctor_id:
            return abort(403)
        form = DoctorAddStudent()
        if form.validate_on_submit():
            student_id = form.student_id.data
            student = User.query.filter_by(uni_number=student_id).first()
            course = Course.query.filter_by(id=course_id).first()
            if student:
                if student not in course.enrolled_students:
                    course.enrolled_students.append(student)
                    try:
                        db.session.commit()
                        flash(f'{student.first_name} {student.last_name} was added successfully!','success')
                    except:
                        flash('Error was happend!','danger')
                else:
                    flash('Student already enrolled in this course!','info')
            else:
                flash('Error in student number or course was not found!','danger')
    else:
        return abort(403)
    return render_template('enroll_student.html', title='Enroll a student', form=form, course=course)

@app.route('/superadmin/manage_courses', methods=["GET", "POST"])
@login_required
def manage_courses():
    user = current_user
    if user.account_type != 'admin':
        abort(403)
    form = ManageCoursesForm()
    courses = db.session.query(Course, User).join(User, Course.doctor_id == User.id).all()
    if form.validate_on_submit():
        course_name = form.name.data
        doctor_name = form.author_id.data.split()
        doctor_id = User.query.filter_by(first_name=doctor_name[0],last_name=doctor_name[1]).first()
        course = Course.query.filter_by(course_name=course_name,doctor_id=doctor_id.id).first()
        course_qr_token = QRToken.query.filter_by(course_id=course.id).first()
        if course_qr_token:
            db.session.delete(course_qr_token)
        course_attendances = Attendance.query.filter_by(course_id=course.id).all()
        if course_attendances:
            for attend in course_attendances:
                db.session.delete(attend)
        db.session.delete(course)
        db.session.commit()
        return redirect(url_for('manage_courses'))
    return render_template('admin_manage_courses.html', title='Manage Courses', form=form, courses=courses)

@app.route('/doctor/courses', methods=["GET", "POST"])
@login_required
def doctor_courses():
    user = current_user
    if user.account_type != 'doctor':
        abort(403)
    form = DoctorCoursesForm()
    courses = user.courses
    courses_data = []
    for course in courses:
        enrolled_students = [student.id for student in course.enrolled_students]
        course_info = f"{course.id};{course.course_name};{','.join(map(str, enrolled_students))}"
        courses_data.append(course_info)
    return render_template('doctor_courses.html', title='My Courses', form=form, courses=courses_data)

@app.route('/student/courses', methods=["GET", "POST"])
@login_required
def student_courses():
    user = current_user
    if user.account_type != 'student':
        abort(403)
    form = StudentCoursesForm()
    courses = user.enrolled_courses
    return render_template('student_courses.html', title='My Courses', form=form, courses=courses)

@app.route('/student/course/<int:course_id>' , methods=["GET",'POST'])
@login_required
def student_course_details(course_id):
    user = current_user
    if user.account_type != 'student':
        abort(403)
    student_courses = user.enrolled_courses
    is_attended = False
    for course in student_courses:
        if course.id == course_id:
            is_attended = True
        else:
            pass
    if is_attended:
        attendances = Attendance.query.filter_by(student_id=user.id,course_id=course_id).all()
        course = Course.query.filter_by(id=course_id).first()
    else:
        flash('Course is not in your attended courses list!','danger')
        return redirect(url_for('home'))
    if request.method == "POST":
        form_name = request.form.get('form_type')
        if form_name == "download_history":
            attendances = Attendance.query.filter_by(student_id=user.id,course_id=course_id).all()
            output = []
            output.append(["Student ID", "Student Name", "Attendance Time"])

            for record in attendances:
                formatted_time = record.attend_time.strftime('%Y-%m-%d %I:%M:%S %p')
                output.append([current_user.uni_number, f"{current_user.first_name} {current_user.last_name}", formatted_time])

            si = "\n".join([",".join(map(str, row)) for row in output])
            response = Response(si, content_type="text/csv")
            response.headers["Content-Disposition"] = f"attachment; filename=attendance_course_{course_id}.csv"
            return response
    return render_template('student_course_details.html', title='My Attendance', attendances=attendances, course_name=course.course_name)

@app.route('/doctor/course/<int:course_id>/attendance', methods=["GET", "POST"])
@login_required
def course_attendance(course_id):
    if current_user.account_type != 'doctor':
        abort(403)
    course = Course.query.get_or_404(course_id)
    students = course.enrolled_students
    doctor_id = course.doctor_id
    if current_user.id != doctor_id:
        abort(403)

    attendance_records = Attendance.query.filter_by(course_id=course_id).all()
    attendance_data = [
        {
            "student_id": record.student_id,
            "student_name": f"{record.student.first_name} {record.student.last_name}",
            "uni_number": record.student.uni_number,
            "date": record.attend_time.strftime('%Y-%m-%d %I:%M:%S %p')
        }
        for record in attendance_records
    ]

    if request.method == "POST":
        student_id = request.form.get("student_id")
        filtered_records = [record for record in attendance_records if student_id == "all" or str(record.student_id) == student_id]

        if not filtered_records:
            flash("لا يوجد بيانات حضور لتنزيلها!", "warning")
            return redirect(url_for('course_attendance', course_id=course_id))

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["اسم الطالب", "الرقم الجامعي", "التاريخ والوقت"])

        for record in filtered_records:
            student = User.query.get(record.student_id)
            writer.writerow([f"{student.first_name} {student.last_name}", student.uni_number, record.attend_time.strftime('%Y-%m-%d %I:%M:%S %p')])

        output.seek(0)
        
        response = Response(output, content_type="text/csv")
        response.headers["Content-Disposition"] = f"attachment; filename={course.course_name}_attendance.csv"
        return response

    return render_template("course_attendance.html", title="Students Attendances", course=course, students=students, attendance_data=attendance_data)

@app.route('/doctor/add_course', methods=["GET", "POST"])
@login_required
def doctor_add_course():
    form = DoctorAddCourseForm()
    user = current_user
    if user.account_type != 'doctor':
        abort(403)
    if form.validate_on_submit():
        name = form.course_name.data
        course_name = name + f' - {user.first_name} {user.last_name}'
        new_course = Course(course_name=course_name,doctor_id=user.id)
        db.session.add(new_course)
        db.session.commit()
        flash(f'{name} Course was added successfully!','success')
        return redirect(url_for('doctor_courses'))
    return render_template('doctor_add_course.html',title="Add New Course",form=form)


@app.route('/doctor/remove_student/<int:course_id>', methods=["GET", "POST"])
@login_required
def remove_student(course_id):
    user = current_user
    if user.account_type != 'doctor':
        abort(403)
    course = Course.query.filter_by(id=course_id).first()
    if course:
        if user.id != course.doctor_id:
            abort(403)
        form = DoctorRemoveStudent()
        if form.validate_on_submit():
            student_id = form.student_id.data
            student = User.query.filter_by(uni_number=student_id).first()
            course = Course.query.filter_by(id=course_id).first()
            if student:
                attendance_history = Attendance.query.filter_by(course_id=course_id,student_id=student.id).all()
                if student not in course.enrolled_students:
                    flash('Student is not enrolled in this course!','info')
                    return redirect(url_for('remove_student',course_id=course_id))
                else:
                    course.enrolled_students.remove(student)
                    for attendance_history_item in attendance_history:
                        db.session.delete(attendance_history_item)
                    db.session.commit()
                    flash(f'{student.first_name} {student.last_name} was removed successfully!','info')
            else:
                flash('Error in student number or course was not found!','danger')
    else:
        return abort(403)
    return render_template('remove_student.html', title='Remove a student', form=form, course=course)

@app.route('/scan_qr', methods=["GET", "POST"])
@login_required
def sca_a_qr():
    return render_template("scan_qr.html")
