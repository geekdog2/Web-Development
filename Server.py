from flask import Flask, redirect, request, render_template, abort, flash, url_for, jsonify, make_response, session, send_file
import sqlite3
import io
import csv
from datetime import datetime

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
DATABASE = 'AATData.db'

app = Flask(__name__)

app.secret_key = 'your_secret_key_here'

# define function connect the sql(data1)

def get_db_conn():
    conn = sqlite3.connect('AATData.db')
    conn.row_factory = sqlite3.Row
    return conn


def get_st(get_id):
    conn = get_db_conn()
    assessment = conn.execute('Select * from Assessments where id = ?', (get_id,)).fetchall()
    conn.close()
    return assessment


# A function to count the number of clicks.(data)
def get_link_clicks(link):
    conn = sqlite3.connect('AATData.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM LinkClicks WHERE link = ?", (link,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[2]  # back to hit
    else:
        return 0  # Returns 0 if the link does not exist


def record_link_click(link):
    conn = sqlite3.connect('AATData.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM LinkClicks WHERE link = ?", (link,))
    row = cursor.fetchone()
    if row:
        clicks = row[2] + 1
        cursor.execute("UPDATE LinkClicks SET clicks = ? WHERE link = ?", (clicks, link))
    else:
        cursor.execute("INSERT INTO LinkClicks (link, clicks) VALUES (?, 1)", (link,))
    conn.commit()
    conn.close()

@app.route("/", methods=['GET', 'POST'])
def Redirect():
    return redirect("/Home")

@app.route("/Home", methods=['GET'])
def Home():
    if request.method == 'GET':
        return render_template('Home.html')


@app.route("/Login", methods=['GET', 'POST'])
def Login():
    if request.method == 'GET':
        return render_template('Login.html')
    elif request.method == 'POST':
        usertype = request.form.get('UserType')
        username = request.form.get('Username') 
        password = request.form.get('Password')

        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        try:
            cur.execute("SELECT usertype, username, password FROM Users WHERE usertype=? AND username=? AND password=?;",
                        (usertype, username, password))
            data = cur.fetchone()
            if data:
                session['username'] = data[1]  # Store username in session for later use
                session['usertype'] = data[0]  # Store usertype in session
                if usertype == 'Student':
                    return redirect(url_for('Student', username=data[1]))  # Redirect with username in URL
                else:
                    return redirect("/Teaching-staff")  # Adjust as necessary for teaching staff
            else:
                flash("Invalid username or password. Please try again.")  # Provide user-friendly error message
                return redirect(url_for('Login'))  # Redirect back to login page
        except Exception as e:
            print(f"Error in retrieval operation: {str(e)}")
            conn.rollback()
            abort(500)  # Internal server error
        finally:
            conn.close()

@app.route("/Student/<string:username>", methods=['GET'])
def Student(username):
    conn = sqlite3.connect('AATData.db')
    conn.row_factory = sqlite3.Row
    try:
        assessments = conn.execute('SELECT * FROM Assessments').fetchall()
        question = conn.execute('SELECT * FROM Questions').fetchall()
        return render_template('Student.html', data=assessments, data1=question, username=username)
    finally:
        conn.close()

# A function to record the number of clicks
def record_click():
    link = request.args.get('link')
    if link:
        record_link_click(link)
        clicks = get_link_clicks(link)
        return render_template('Student.html', data=clicks)
    else:
        return "No link provided."

# Student sees very first questions of assessment
# Tracker information is reset on the start of each attempt
@app.route("/Student/<string:username>/<int:get_id>", methods=['GET', 'POST'])
def StudentSpecificassessment(get_id, username):
    assessment = get_st(get_id)
    conn = get_db_conn()
    name = conn.execute("SELECT name FROM Assessments WHERE id =?;", [get_id]).fetchall()
    name = str(name[0][0])
    conn.execute("DELETE FROM studentAttempts WHERE username=?", ( (username,)) )
    conn.execute( "INSERT INTO studentAttempts (assessmentid,username) VALUES (?,?)", (get_id, username)) # reset tracker
    questions = conn.execute("SELECT * FROM Questions WHERE assessmentid=?", [get_id] ).fetchone()
    conn.commit()
    conn.close()
    return render_template('Assessment.html', data1=assessment, data2 = name, data3=questions, data4=get_id, username=username)

# checks if answer is correct
# if it is, updates counter in database
# returns feedback
@app.route("/Student/result/<string:username>/<int:get_id>/<int:ques_id>", methods=['GET', 'POST'])
def studentResults(get_id, ques_id, username):
    assessment = get_st(get_id)
    conn = get_db_conn()
    name = conn.execute("SELECT name FROM Assessments WHERE id =?;", [get_id]).fetchall()
    name = str(name[0][0])
    questions = conn.execute("SELECT * FROM Questions WHERE id=?", [ques_id] ).fetchone()
    if request.method == 'POST':
        feedback =""
        answer = request.form['ans']
        if answer == conn.execute("SELECT answer FROM Questions WHERE id=?", [ques_id] ).fetchone()[0]:
            feedback = "Correct"
            counter = conn.execute("SELECT count FROM studentAttempts WHERE username=?",(username,)).fetchone()[0]
            counter += 1
            conn.execute("UPDATE studentAttempts SET count=? WHERE assessmentid=? AND username=?", (counter, get_id,username) )
            conn.commit()
        else:
            feedback = "Incorrect"
        assType = conn.execute("SELECT type FROM Assessments WHERE id=?", ([get_id])).fetchall()[0][0]
        conn.close()
        return render_template('Assessment.html', data1=assessment, data2 = name, data3=questions, data4=get_id, data5=feedback, data6=assType, username=username)
    flash("error")
    conn.close()
    return redirect(url_for('Student'))

# checks previous questions, and returns the next
@app.route("/Student/<string:username>/<int:get_id>/<int:ques_id>", methods=['GET', 'POST'])
def nextQuestion(get_id, ques_id, username):
    assessment = get_st(get_id)
    conn = get_db_conn()
    name = conn.execute("SELECT name FROM Assessments WHERE id =?;", [get_id]).fetchall()
    name = str(name[0][0])
    qlist = conn.execute("SELECT id FROM Questions WHERE assessmentid=?", [get_id]).fetchall()
    preques = conn.execute("SELECT id FROM Questions WHERE id=?", [ques_id]).fetchall()
    j=0
    b = 0
    question = 0
    for i in qlist: # select all question id's and find the next one
        j+=1
        if j < len(qlist):
            if preques[0][0] < qlist[j][0]:
                question = qlist[j][0]
                questions = conn.execute("SELECT * FROM Questions WHERE id=?", [question] ).fetchone()
                return render_template('Assessment.html', data1=assessment, data2 = name, data3=questions, data4=get_id, username=username)
    counter = conn.execute("SELECT count FROM studentAttempts WHERE username=?", (username,)).fetchone()[0]
    total = round((counter/len(qlist))*100, 2)
    time = datetime.now()
    conn.execute("UPDATE studentAttempts SET mark=? WHERE username=?", (total, username) )
    conn.execute("UPDATE studentAttempts SET completed=? WHERE assessmentid=? AND username=?", (str(time), get_id,username) ) #date
    assType = conn.execute("SELECT type FROM Assessments WHERE id =?;", [get_id]).fetchall()[0][0]
    conn.commit()
    if assType == 'summative':
        alldata = conn.execute("SELECT * FROM studentAttempts WHERE username=?", (username,)).fetchone()
        assid,stuid,time,count,mark = alldata[0],alldata[1],alldata[2],alldata[3],alldata[4]
        conn.execute("INSERT INTO allAttempts (assessmentid,username,completed,count,mark) VALUES (?,?,?,?,?)", (assid,stuid,time,count,mark)) # insert into all data
        conn.execute("DELETE FROM studentAttempts WHERE username=?", ( (username,)) ) #delete row
        conn.commit()
        conn.close()
        return redirect(url_for('Student',username=username))
    conn.close()
    return redirect(url_for('results',get_id=get_id,username=username))

@app.route("/Student/results/<string:username>/<int:get_id>", methods=["GET"])
def results(get_id, username):
    conn = get_db_conn()
    alldata = conn.execute("SELECT * FROM studentAttempts WHERE username=?", (username,)).fetchone()
    if alldata:
        name = conn.execute("SELECT name FROM Assessments WHERE id =?", [get_id]).fetchall()
        name = str(name[0][0])
        assid,stuid,time,count,mark = alldata[0],alldata[1],alldata[2],alldata[3],alldata[4]
        conn.execute("INSERT INTO allAttempts (assessmentid,username,completed,count,mark) VALUES (?,?,?,?,?)", (assid,stuid,time,count,mark)) # insert into all data
        conn.execute("DELETE FROM studentAttempts WHERE username=?", ( (username,)) ) #delete row
        conn.commit()
        conn.close()
        return render_template('results.html', data1=count,data2=mark,data3=name, username=username)
    alldata = conn.execute("SELECT * FROM allAttempts WHERE id=?", [get_id]).fetchone()
    qid = conn.execute("SELECT assessmentid FROM allAttempts WHERE id=?", [get_id]).fetchone()[0]
    allques = conn.execute("SELECT * FROM Questions WHERE assessmentid=?", [qid]).fetchall()
    return render_template('results.html', alldata=alldata, allques=allques, username=username, res=True)

@app.route("/Student/AssessmentResults/<string:username>", methods=['GET'])
def StudentAss(username):
    conn = get_db_conn()
    assessments = conn.execute("SELECT * FROM allAttempts WHERE username =?", (username,)).fetchall()
    conn.close()
    return render_template('Student-AssResults.html',username=username,ass=assessments)

# student review section:
@app.route("/Statistics/<string:username>", methods=['GET'])
def Statistics(username):
    conn = get_db_conn()
    students = conn.execute(
        'SELECT username, assessment_type, attempt, engagement, performance, rank, attempt_date, comment FROM students WHERE username = ?', (username,)).fetchall()

    assessment_types = conn.execute('SELECT DISTINCT assessment_type FROM students ORDER BY assessment_type').fetchall()
    conn.close()
    return render_template('Student-Statistics.html',students=students,assessment_types=assessment_types,username=username)

 # export personal specific data
@app.route("/export_personal_data/<string:username>/<string:assessment_type>", methods=['GET'])
def export_personal_data(username, assessment_type):
    conn = get_db_conn()
    student_personal_data = conn.execute("SELECT * FROM students WHERE username = ? AND assessment_type = ?", (username, assessment_type)).fetchall()
    filename = f"{username}_data_{assessment_type}.csv"
    if student_personal_data:
        with open(filename, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['username', 'assessment_type', 'attempt', 'engagement', 'performance', 'rank', 'attempt_date', 'comment'])
            for student_data in student_personal_data:
                writer.writerow([student_data['username'], student_data['assessment_type'], student_data['attempt'], student_data['engagement'], 
                                student_data['performance'], student_data['rank'], student_data['attempt_date'], student_data['comment']])
        conn.close()   
        return send_file(filename, as_attachment=True)
    else:
        return jsonify({"message": "No relevant data found!!"})

# export personal all data
@app.route("/export_personal_all_data/<string:username>", methods=['GET'])
def export_personal_all_data(username):
    conn = get_db_conn()
    student_personal_all_data = conn.execute("SELECT * FROM students WHERE username = ? ", (username,)).fetchall()
    filename = f"{username}_all_data.csv"
    if student_personal_all_data:
        with open(filename, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['username', 'assessment_type', 'attempt', 'engagement', 'performance', 'rank', 'attempt_date', 'comment'])
            for student_data in student_personal_all_data:
                writer.writerow([student_data['username'], student_data['assessment_type'], student_data['attempt'], student_data['engagement'], 
                                student_data['performance'], student_data['rank'], student_data['attempt_date'], student_data['comment']])    
        conn.close()
        return send_file(filename, as_attachment=True)
    else:
        return jsonify({"message": "No relevant data found!"})

@app.route("/Teaching-staff", methods=['GET',])
def Teachingstaff():
    if request.method == 'GET':
        conn = get_db_conn()
        assessments = conn.execute('Select * from Assessments').fetchall()
        return render_template('Teaching-staff.html', data=assessments)

# Shows set of questions for specific assessment
@app.route("/Teaching-Assessment/<int:get_id>", methods=['GET'])
def StaffSpecificassessment(get_id):
    assessment = get_st(get_id)
    conn = get_db_conn()
    name = conn.execute("SELECT name FROM Assessments WHERE id =?;", [get_id]).fetchall()
    name = str(name[0][0])
    questions = conn.execute("SELECT * FROM Questions WHERE assessmentid =?;", [get_id]).fetchall()
    return render_template('StaffAssessment.html', data=assessment, data1 = questions, Aname = name, data2 = get_id)

# editQuestions function used to edit questions for all assessments
@app.route("/Teaching-Assessment/edit/<int:get_id>", methods=['POST', 'GET'])
def editQuestions(get_id):
    post = get_st(get_id)
    conn = get_db_conn()
    if request.method == 'POST':
        questionid = request.form['id']
        question = request.form['quest']
        answer = request.form['ans']
        check1 = request.form['check1']
        check2 = request.form['check2']
        check3 = request.form['check3']
        feedback = request.form['feed']
        comment = request.form['comm']
        total = []
        total.append(questionid)
        total.append(question)
        total.append(answer)
        total.append(check1)
        total.append(check2)
        total.append(check3)
        total.append(feedback)
        total.append(comment)
        while ("" in total):
            total.remove("")
        a = conn.execute("SELECT id FROM Questions").fetchall()
        for row in a:
            if int(questionid) == row[0] and len(total) > 1:
                if question:
                    conn.execute("UPDATE Questions SET question=? WHERE id=? AND assessmentid=?", (question, questionid, get_id))
                if answer:
                    conn.execute("UPDATE Questions SET answer=? WHERE id=? AND assessmentid=?", (answer, questionid, get_id))
                if check1:
                    conn.execute("UPDATE Questions SET check1=? WHERE id=? AND assessmentid=?", (check1, questionid, get_id))
                if check2:
                    conn.execute("UPDATE Questions SET check2=? WHERE id=? AND assessmentid=?", (check2, questionid, get_id))
                if check3:
                    conn.execute("UPDATE Questions SET check3=? WHERE id=? AND assessmentid=?", (check3, questionid, get_id))
                if feedback:
                    conn.execute("UPDATE Questions SET feedback=? WHERE id=? AND assessmentid=?", (feedback, questionid, get_id))
                if comment:
                    conn.execute("UPDATE Questions SET comment=? WHERE id=? AND assessmentid=?", (comment, questionid, get_id))
                data3 = 'Edit Successful'
                conn.commit()
                name = conn.execute("SELECT name FROM Assessments WHERE id =?;", [get_id]).fetchall()
                name = str(name[0][0])
                questions = conn.execute("SELECT * FROM Questions WHERE assessmentid =?;", [get_id]).fetchall()
                conn.close()
                return render_template('StaffAssessment.html', data=post, data1 = questions, Aname = name, data2 = get_id, error=data3)
        data3 ='Error - id not in table or added no new data'
        name = conn.execute("SELECT name FROM Assessments WHERE id =?;", [get_id]).fetchall()
        name = str(name[0][0])
        questions = conn.execute("SELECT * FROM Questions WHERE assessmentid =?;", [get_id]).fetchall()
        conn.close()
        return render_template('StaffAssessment.html', data=post, data1 = questions, Aname = name, data2 = get_id, error=data3)
    data3 ='error'
    name = conn.execute("SELECT name FROM Assessments WHERE id =?;", [get_id]).fetchall()
    name = str(name[0][0])
    questions = conn.execute("SELECT * FROM Questions WHERE assessmentid =?;", [get_id]).fetchall()
    conn.close()
    return render_template('StaffAssessment.html', data=post, data1 = questions, Aname = name, data2 = get_id, error=data3)

# teaching-staff review section:
def get_db_connection():
    conn = sqlite3.connect('AATData.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/Staff-Statistics", methods=['GET'])
def StaffStatistics():
    conn = get_db_connection()
    students = conn.execute(
        '''
        SELECT u.id as id, u.username, u.cohort, u.module, 
               b.name as assessment_name, a.count as attempt, a.mark as performance,
               CASE 
                   WHEN a.count > 3 AND a.mark >= 75 THEN 'High'
                   WHEN a.count > 1 AND a.mark >= 50 THEN 'Medium'
                   ELSE 'Low'
               END as engagement
        FROM Users u
        JOIN allAttempts a ON u.id = a.id
        JOIN Assessments b ON a.assessmentid = b.id
        WHERE u.usertype = "Student"
        '''
    ).fetchall()

    cohorts = conn.execute(
        'SELECT DISTINCT cohort FROM Users WHERE usertype = "Student" ORDER BY cohort'
    ).fetchall()


    modules = conn.execute(
        'SELECT DISTINCT module FROM Users WHERE usertype = "Student" ORDER BY module'
    ).fetchall()

    assessment_types = conn.execute(
        'SELECT DISTINCT b.name as assessment_name FROM Assessments b '
        'JOIN allAttempts a ON b.id = a.assessmentid '
        'JOIN Users u ON u.id = a.id '
        'WHERE u.usertype = "Student" '
        'ORDER BY b.name'
    ).fetchall()

    conn.close()
    return render_template('Staff-Statistics.html', students=students, cohorts=cohorts, modules=modules,
                           assessment_types=assessment_types)

@app.route('/filter', methods=['POST'])
def filter():
    data = request.get_json()
    student_id = data.get('student_id', '')
    cohort = data.get('cohort', 'All Cohorts')
    module = data.get('module', 'All Modules')
    assessment_name = data.get('assessment_name', 'All Assessments')

    conn = get_db_connection()
    query = '''
    SELECT 
        u.id as student_id, u.name, u.cohort, u.module, 
        b.name as assessment_name, a.count as attempt, a.mark as performance,
        CASE 
            WHEN a.count > 3 AND a.mark >= 75 THEN 'High'
            WHEN a.count > 1 AND a.mark >= 50 THEN 'Medium'
            ELSE 'Low'
        END as engagement
    FROM Users u
    JOIN allAttempts a ON u.id = a.studentid
    JOIN Assessments b ON a.assessmentid = b.id
    WHERE u.usertype = "Student"
    '''
    params = []

    if student_id:
        query += ' AND u.id = ?'
        params.append(student_id)
    if cohort != 'All Cohorts':
        query += ' AND u.cohort = ?'
        params.append(cohort)
    if module != 'All Modules':
        query += ' AND u.module = ?'
        params.append(module)
    if assessment_name != 'All Assessments':
        query += ' AND b.name = ?'
        params.append(assessment_name)

    students = conn.execute(query, params).fetchall()
    conn.close()

    students_list = [dict(student) for student in students]
    return jsonify(students_list)


@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    student_id = data.get('student_id')

    conn = get_db_connection()
    query = '''
    SELECT 
        u.id as student_id, u.name, u.cohort, u.module,
        b.name as assessment_name, a.count as attempt, a.mark as performance,
        CASE 
            WHEN a.count > 3 AND a.mark >= 75 THEN 'High'
            WHEN a.count > 1 AND a.mark >= 50 THEN 'Medium'
            ELSE 'Low'
        END as engagement  
    FROM Users u
    JOIN allAttempts a ON u.id = a.studentid
    JOIN Assessments b ON a.assessmentid = b.id
    WHERE u.usertype = "Student" AND u.id = ?
    '''

    students = conn.execute(query, (student_id,)).fetchall()
    conn.close()

    students_list = [dict(student) for student in students]
    return jsonify(students_list)



@app.route('/export')
def export_data():
    student_id = request.args.get('student_id', default=None)
    cohort = request.args.get('cohort', default='All Cohorts')
    module = request.args.get('module', default='All Modules')
    assessment_name = request.args.get('assessment_name', default='All Assessments')

    conn = get_db_connection()

    query = '''
    SELECT 
        u.id as student_id, u.name, u.cohort, u.module, 
        b.name as assessment_name, a.count as attempt, a.mark as performance,
        CASE 
            WHEN a.count > 3 AND a.mark >= 75 THEN 'High'
            WHEN a.count > 1 AND a.mark >= 50 THEN 'Medium'
            ELSE 'Low'
        END as engagement
    FROM Users u
    JOIN allAttempts a ON u.id = a.studentid
    JOIN Assessments b ON a.assessmentid = b.id
    WHERE u.usertype = "Student"
    '''
    params = []

    if student_id:
        query += ' AND u.id = ?'
        params.append(student_id)
    if cohort != 'All Cohorts':
        query += ' AND u.cohort = ?'
        params.append(cohort)
    if module != 'All Modules':
        query += ' AND u.module = ?'
        params.append(module)
    if assessment_name != 'All Assessments':
        query += ' AND b.name = ?'
        params.append(assessment_name)

    students = conn.execute(query, params).fetchall()
    conn.close()


    si = io.StringIO()
    cw = csv.writer(si)

    cw.writerow(['Student ID', 'Name', 'Cohort', 'Module', 'Assessment Name', 'Attempts', 'Performance', 'Engagement'])
    for student in students:
        cw.writerow([
            student['student_id'], student['name'], student['cohort'], student['module'],
            student['assessment_name'], student['attempt'], student['performance'], student['engagement']
        ])

    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=filtered_data_export.csv"
    output.headers["Content-type"] = "text/csv"
    return output

# newQuestion function to create new questions for specific assessment, no more than 10 per assessment
@app.route("/Teaching-Assessment/new/<int:get_id>", methods=['POST', 'GET'])
def newQuestion(get_id):
    post = get_st(get_id)
    conn = get_db_conn()
    a = conn.execute("SELECT * FROM Questions WHERE assessmentid=?",[get_id]).fetchall()
    if request.method == 'POST':
        if len(a) != 10:
            question = request.form['addquest']
            answer = request.form['addans']
            check1 = request.form['addcheck1']
            check2 = request.form['addcheck2']
            check3 = request.form['addcheck3']
            feedback = request.form['addfeed']
            comment = request.form['addcomm']
            if check3 and not comment:
                conn.execute("INSERT INTO Questions (assessmentid,question,answer,check1,check2,check3,feedback) values (?,?,?,?,?,?,?)", (get_id, question, answer,check1,check2,check3,feedback ))
            elif check3 and comment:
                conn.execute("INSERT INTO Questions (assessmentid,question,answer,check1,check2,check3,feedback,comment) values (?,?,?,?,?,?,?,?)", (get_id, question, answer,check1,check2,check3,feedback,comment ))
            elif comment and not check3:
                conn.execute("INSERT INTO Questions (assessmentid,question,answer,check1,check2,feedback,comment) values (?,?,?,?,?,?,?)", (get_id, question, answer,check1,check2,feedback,comment ))
            else:
                conn.execute("INSERT INTO Questions (assessmentid,question,answer,check1,check2,feedback) values (?,?,?,?,?,?)", (get_id, question, answer,check1,check2,feedback ))
            name = conn.execute("SELECT name FROM Assessments WHERE id =?;", [get_id]).fetchall()
            name = str(name[0][0])
            questions = conn.execute("SELECT * FROM Questions WHERE assessmentid =?;", [get_id]).fetchall()
            conn.commit()
            conn.close()
            data3 ='Add Successful'
            return render_template('StaffAssessment.html', data=post, data1 = questions, Aname = name, data2 = get_id, error=data3)
        else:
            data3 = 'Questions capacity reached (10)'
            name = conn.execute("SELECT name FROM Assessments WHERE id =?;", [get_id]).fetchall()
            name = str(name[0][0])
            questions = conn.execute("SELECT * FROM Questions WHERE assessmentid =?;", [get_id]).fetchall()
            conn.close()
            return render_template('StaffAssessment.html', data=post, data1 = questions, Aname = name, data2 = get_id, error = data3)
    data3 = "error"
    name = conn.execute("SELECT name FROM Assessments WHERE id =?;", [get_id]).fetchall()
    name = str(name[0][0])
    questions = conn.execute("SELECT * FROM Questions WHERE assessmentid =?;", [get_id]).fetchall()
    return render_template('StaffAssessment.html', data=post, data1 = questions, Aname = name, data2 = get_id, error=data3)

# Delete questions
@app.route("/Teaching-Assessment/delete/<int:get_id>", methods=['POST', ])
def deleteQuestion(get_id):
    post = get_st(get_id)
    conn = get_db_conn()
    deleteid = request.form['deleteid']
    a = conn.execute("SELECT id FROM Questions").fetchall()
    b = []
    for row in a:
        b.append(row[0])
    print(b)
    if int(deleteid) in b:
        conn.execute("DELETE FROM Questions WHERE id = ?", (deleteid,))
        name = conn.execute("SELECT name FROM Assessments WHERE id =?;", [get_id]).fetchall()
        name = str(name[0][0])
        questions = conn.execute("SELECT * FROM Questions WHERE assessmentid =?;", [get_id]).fetchall()
        conn.commit()
        conn.close()
        data3 ='Delete Successful'
        return render_template('StaffAssessment.html', data=post, data1 = questions, Aname = name, data2 = get_id, error=data3)
    else:
        name = conn.execute("SELECT name FROM Assessments WHERE id =?;", [get_id]).fetchall()
        name = str(name[0][0])
        questions = conn.execute("SELECT * FROM Questions WHERE assessmentid =?;", [get_id]).fetchall()
        conn.commit()
        conn.close()
        data3 ='Error - incorrect id. There are no questions with that id'
        return render_template('StaffAssessment.html', data=post, data1 = questions, Aname = name, data2 = get_id, error=data3)

#A add function is used to create new assessment
@app.route('/Teaching-staff/new',methods=['POST','GET'])
def new():
   if request.method=='POST' or request.method == 'GET':
       id=request.form['id']
       name=request.form['name']
       content=request.form['content']
       type=request.form['type']
       if not id:
           flash('Id cannot be null')
       elif not content:
           flash('Content cannot be null')
       elif not  name:
           flash('Name cannot be null')
       else:
           conn=get_db_conn()
           conn.execute('insert into Assessments (id,name,content,type) values (?,?,?,?)',(id,name,content,type))
           conn.commit()
           conn.close()
           flash('Save Successful')
           return redirect(url_for('Teachingstaff'))
   return render_template('Teaching-staff.html')
   conn = get_db_conn()
   c = conn.cursor()
   c.execute("SELECT type FROM Assessments")
   types = [row[0] for row in c.fetchall()]
   app.logger.debug("Types from database: %s", types)  # 添加调试日志
   conn.close()
   return render_template('Teaching-staff.html',types=types)

# A delete function is used to delete the contents of the sql(data1) in teaching-staff page
@app.route("/Teaching-staff/<int:get_id>/delete", methods=['POST', ])
def delete(get_id):
    post = get_st(get_id)
    conn = get_db_conn()
    conn.execute('DELETE FROM Assessments WHERE id = ?', (get_id,))
    conn.execute('DELETE FROM Questions WHERE assessmentid = ?', (get_id,))
    conn.commit()
    conn.close()
    flash(' delete successful')
    return redirect(url_for('Teachingstaff'))


# An edit function to change the contents of the sql(data1) library in teaching-staff page
@app.route('/Teaching-staff/edit/<int:get_id>', methods=['POST', 'GET',])
def edit(get_id):
    post = get_st(get_id)
    if request.method == 'POST':
        # Here I only change the title（“content” in data1）, you can add other fields to modify the subsequent if it needed
        #I'm using the studentsdata database here, if someone needs to call it they can add it to what they need
        content = request.form['content']
        if not content:
            flash('WARING! There is no content')
        else:
            conn = get_db_conn()
            conn.execute('update Assessments set name=? WHERE id = ?', (content,get_id))
            conn.commit()
            conn.close()
        return redirect(url_for('Teachingstaff'))
    return render_template('Teaching-staff.html', post=post)

@app.route("/Comment/<string:username>/<int:get_id>", methods=['GET', 'POST'])
def Comment(get_id, username):
    if request.method == 'POST':
        assessment_id = get_id
        username = request.form['username']
        usertype = request.form['usertype']
        content = request.form['content']
        if not content:
            flash('Content cannot be null')
        else:
            conn = get_db_conn()
            conn.execute('insert into Comments (assessment_id,usertype,username,content) values (?,?,?,?)',
                         (assessment_id, usertype, username, content))
            conn.commit()
            conn.close()
            flash('Save Successful')
            return redirect(url_for("Student", username=username))
    assessment_id = get_id
    username = session.get('username')
    usertype = session.get('usertype')
    return render_template('Comment.html', assessment_id=assessment_id, username=username, usertype=usertype)


@app.route('/ViewComment/<string:username>/<int:get_id>', methods=['GET'])
def ViewComment(get_id, username):
    conn = get_db_conn()
    conn.row_factory = sqlite3.Row
    comments = conn.execute("select * from Comments WHERE assessment_id =?;", [get_id]).fetchall()

    if 'username' in session:
        deletable_comments = [comment for comment in comments if comment['username'] == session.get('username', None)]
        return render_template('ViewComment.html', data=comments, data1=deletable_comments, username=username)
    else:
        return redirect(url_for("Login", username=username))

@app.route("/Delete_Comment/<string:username>/<int:get_id>/<int:get_assId>", methods=['GET'])
def Delete_Comment(get_id,get_assId, username):
    conn = get_db_conn()
    conn.execute('DELETE FROM Comments WHERE id = ?', (get_id,))
    conn.commit()
    conn.close()
    flash(' delete successful')
    return redirect(url_for("ViewComment", get_id=get_assId, username=username))

if __name__ == "__main__":
    app.run(debug=True)