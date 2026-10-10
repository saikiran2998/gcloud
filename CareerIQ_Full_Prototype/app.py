import os, sqlite3
from functools import wraps
from pathlib import Path
from flask import Flask, g, session, request, redirect, url_for, flash, render_template, abort
from werkzeug.security import generate_password_hash, check_password_hash

ROOT = Path(__file__).resolve().parent
DB_PATH = os.environ.get('DATABASE_PATH', str(ROOT / 'careeriq.db'))
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'local-demo-secret-change-before-deployment')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['MAX_CONTENT_LENGTH'] = 3 * 1024 * 1024
CAREERS = {
 'Cloud Engineer': ['Linux','Networking','Python','Git','Cloud Fundamentals','Docker'],
 'Python Developer': ['Python','SQL','Git','REST APIs','Testing'],
 'Web Developer': ['HTML','CSS','JavaScript','Python','SQL','Git'],
 'Data Analyst': ['SQL','Python','Excel','Statistics','Data Visualization']
}

def conn():
    db = sqlite3.connect(DB_PATH); db.row_factory = sqlite3.Row; db.execute('PRAGMA foreign_keys=ON'); return db

def init_db():
    db = conn()
    db.executescript('''
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('student','faculty','company')));
    CREATE TABLE IF NOT EXISTS profiles(user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE, department TEXT DEFAULT 'Computer Science', year TEXT DEFAULT '3rd Year', target TEXT DEFAULT 'Cloud Engineer', skills TEXT DEFAULT '', score REAL DEFAULT 8.0, bio TEXT DEFAULT '');
    CREATE TABLE IF NOT EXISTS certificates(id INTEGER PRIMARY KEY, student_id INTEGER NOT NULL REFERENCES users(id), title TEXT NOT NULL, issuer TEXT DEFAULT '', status TEXT NOT NULL DEFAULT 'Pending' CHECK(status IN ('Pending','Verified','Rejected')));
    CREATE TABLE IF NOT EXISTS projects(id INTEGER PRIMARY KEY, student_id INTEGER NOT NULL REFERENCES users(id), title TEXT NOT NULL, description TEXT DEFAULT '');
    CREATE TABLE IF NOT EXISTS jobs(id INTEGER PRIMARY KEY, company_id INTEGER NOT NULL REFERENCES users(id), title TEXT NOT NULL, kind TEXT NOT NULL CHECK(kind IN ('Job','Internship')), description TEXT DEFAULT '', skills TEXT DEFAULT '', eligibility TEXT DEFAULT '', location TEXT DEFAULT 'Not specified', status TEXT NOT NULL DEFAULT 'Open' CHECK(status IN ('Open','Closed')));
    CREATE TABLE IF NOT EXISTS applications(id INTEGER PRIMARY KEY, job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE, student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, status TEXT NOT NULL DEFAULT 'Applied' CHECK(status IN ('Applied','Under Review','Shortlisted','Rejected','Selected')), created_at TEXT DEFAULT CURRENT_TIMESTAMP, UNIQUE(job_id,student_id));
    CREATE TABLE IF NOT EXISTS questions(id INTEGER PRIMARY KEY, topic TEXT, difficulty TEXT CHECK(difficulty IN ('Basic','Intermediate','Advanced')), question TEXT, a TEXT, b TEXT, c TEXT, d TEXT, answer TEXT, explanation TEXT);
    CREATE TABLE IF NOT EXISTS attempts(id INTEGER PRIMARY KEY, student_id INTEGER REFERENCES users(id), score REAL, correct_count INTEGER, total_count INTEGER, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    ''')
    if db.execute('SELECT COUNT(*) FROM users').fetchone()[0] == 0:
        db.executemany('INSERT INTO users(name,email,password_hash,role) VALUES(?,?,?,?)', [
          ('Aarav Student','student@careeriq.demo',generate_password_hash('Student@123'),'student'),
          ('Dr. Meera Faculty','faculty@careeriq.demo',generate_password_hash('Faculty@123'),'faculty'),
          ('Nova Tech HR','company@careeriq.demo',generate_password_hash('Company@123'),'company')])
        sid=db.execute("SELECT id FROM users WHERE email='student@careeriq.demo'").fetchone()['id']; cid=db.execute("SELECT id FROM users WHERE email='company@careeriq.demo'").fetchone()['id']
        db.execute('INSERT INTO profiles(user_id,department,year,target,skills,score,bio) VALUES(?,?,?,?,?,?,?)',(sid,'Computer Science','3rd Year','Cloud Engineer','Python, Git, Linux, HTML, CSS',8.4,'Interested in cloud platforms and practical software projects.'))
        db.executemany('INSERT INTO certificates(student_id,title,issuer,status) VALUES(?,?,?,?)',[(sid,'Python Fundamentals','Demo Learning Academy','Verified'),(sid,'Cloud Foundations','Demo Cloud Academy','Pending')])
        db.executemany('INSERT INTO projects(student_id,title,description) VALUES(?,?,?)',[(sid,'CareerIQ Prototype','A student-to-industry career platform.'),(sid,'Portfolio Website','A responsive personal portfolio.')])
        db.executemany('INSERT INTO jobs(company_id,title,kind,description,skills,eligibility,location) VALUES(?,?,?,?,?,?,?)',[
          (cid,'Cloud Support Intern','Internship','Assist with cloud labs, Linux basics and documentation.','Linux, Networking, Cloud Fundamentals','Basic Linux and networking knowledge','Hybrid'),
          (cid,'Python Developer Intern','Internship','Build and test small Python web features.','Python, SQL, Git','Basic Python and database knowledge','Remote'),
          (cid,'Junior Web Developer','Job','Help develop internal web tools.','HTML, CSS, JavaScript, Python','Portfolio or academic projects preferred','Vijayawada')])
        qs=[('Cloud','Basic','Which service model provides virtual machines?','SaaS','IaaS','FaaS','DaaS','b','IaaS provides infrastructure such as virtual machines.'),('Python','Basic','Which keyword defines a Python function?','func','define','def','function','c','Python functions are declared with def.'),('Web','Basic','Which HTML element creates a hyperlink?','<link>','<a>','<href>','<url>','b','The anchor element creates a hyperlink.'),('Database','Intermediate','Which SQL clause filters rows before grouping?','ORDER BY','HAVING','WHERE','LIMIT','c','WHERE filters rows before grouping.'),('Cloud','Intermediate','What is a cloud region?','A billing account','A geographic area containing cloud zones','A user role','A programming language','b','Regions are geographic locations containing zones.'),('Python','Intermediate','What does a Python dictionary store?','Only numbers','Key-value pairs','Only strings','Compiled classes','b','Dictionaries map keys to values.'),('Web','Advanced','Which HTTP status commonly indicates resource creation?','200','201','301','404','b','201 Created indicates a resource was created.'),('Cloud','Advanced','Which practice follows least privilege?','Give everyone admin','Share one account','Grant only necessary permissions','Disable logs','c','Least privilege limits permissions to what is needed.'),('Database','Advanced','What does a foreign key help enforce?','CSS layout','Referential integrity','Password hashing','HTTP caching','b','Foreign keys enforce valid record relationships.')]
        db.executemany('INSERT INTO questions(topic,difficulty,question,a,b,c,d,answer,explanation) VALUES(?,?,?,?,?,?,?,?,?)',qs)
    db.commit(); db.close()

@app.before_request
def open_db():
    g.db = conn()

@app.teardown_request
def close_db(error=None):
    db=g.pop('db',None)
    if db: db.close()

def login_required(fn):
    @wraps(fn)
    def wrapper(*args,**kwargs):
        if not session.get('uid'): flash('Please sign in first.','warning'); return redirect(url_for('login'))
        return fn(*args,**kwargs)
    return wrapper

def roles(*allowed):
    def dec(fn):
        @wraps(fn)
        def wrapper(*args,**kwargs):
            if not session.get('uid'): return redirect(url_for('login'))
            if session.get('role') not in allowed: abort(403)
            return fn(*args,**kwargs)
        return wrapper
    return dec

def user():
    return g.db.execute('SELECT id,name,email,role FROM users WHERE id=?',(session['uid'],)).fetchone() if session.get('uid') else None

@app.context_processor
def globals_for_templates(): return {'me':user()}

@app.after_request
def headers(response):
    response.headers['X-Content-Type-Options']='nosniff'; response.headers['X-Frame-Options']='SAMEORIGIN'; response.headers['Referrer-Policy']='strict-origin-when-cross-origin'; return response

@app.route('/')
def home(): return render_template('page.html', page='home')

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        email=request.form.get('email','').strip().lower(); password=request.form.get('password','')
        u=g.db.execute('SELECT * FROM users WHERE email=?',(email,)).fetchone()
        if u and check_password_hash(u['password_hash'],password):
            session.clear(); session['uid']=u['id']; session['role']=u['role']; flash('Welcome, '+u['name']+'!','success'); return redirect(url_for('dashboard'))
        flash('Invalid email or password.','danger')
    return render_template('page.html',page='login')

@app.post('/logout')
def logout(): session.clear(); flash('Signed out.','info'); return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    role=session['role']; uid=session['uid']; db=g.db
    if role=='student':
        p=db.execute('SELECT * FROM profiles WHERE user_id=?',(uid,)).fetchone()
        certs=db.execute('SELECT * FROM certificates WHERE student_id=? ORDER BY id DESC',(uid,)).fetchall()
        projects=db.execute('SELECT * FROM projects WHERE student_id=? ORDER BY id DESC',(uid,)).fetchall()
        jobs=db.execute("SELECT j.*,u.name company FROM jobs j JOIN users u ON u.id=j.company_id WHERE j.status='Open' ORDER BY j.id DESC").fetchall()
        apps=db.execute('SELECT a.*,j.title,j.kind,u.name company FROM applications a JOIN jobs j ON j.id=a.job_id JOIN users u ON u.id=j.company_id WHERE a.student_id=? ORDER BY a.id DESC',(uid,)).fetchall()
        attempts=db.execute('SELECT * FROM attempts WHERE student_id=? ORDER BY id DESC LIMIT 5',(uid,)).fetchall()
        roadmap=make_roadmap(p['target'],p['skills'])
        return render_template('page.html',page='student',p=p,certs=certs,projects=projects,jobs=jobs,apps=apps,attempts=attempts,roadmap=roadmap)
    if role=='faculty':
        students=db.execute("SELECT u.id,u.name,u.email,p.department,p.year,p.target,p.skills,p.score,(SELECT COUNT(*) FROM certificates c WHERE c.student_id=u.id) cert_count FROM users u JOIN profiles p ON p.user_id=u.id WHERE u.role='student' ORDER BY u.name").fetchall()
        pending=db.execute("SELECT c.*,u.name student FROM certificates c JOIN users u ON u.id=c.student_id WHERE c.status='Pending'").fetchall()
        return render_template('page.html',page='faculty',students=students,pending=pending)
    jobs=db.execute('SELECT * FROM jobs WHERE company_id=? ORDER BY id DESC',(uid,)).fetchall()
    apps=db.execute('SELECT a.*,j.title,u.name student,p.department,p.year,p.skills FROM applications a JOIN jobs j ON j.id=a.job_id JOIN users u ON u.id=a.student_id JOIN profiles p ON p.user_id=u.id WHERE j.company_id=? ORDER BY a.id DESC',(uid,)).fetchall()
    return render_template('page.html',page='company',jobs=jobs,apps=apps)

def make_roadmap(target,skills):
    required=CAREERS.get(target,CAREERS['Cloud Engineer']); have={x.strip().lower() for x in (skills or '').split(',') if x.strip()}
    matched=[s for s in required if s.lower() in have]; missing=[s for s in required if s.lower() not in have]
    return {'required':required,'matched':matched,'missing':missing,'milestones':[{'skill':s,'level':'Beginner' if i<2 else 'Intermediate' if i<4 else 'Advanced','project':f'Build a small {s} practice project'} for i,s in enumerate(missing)]}

@app.route('/profile',methods=['GET','POST'])
@roles('student')
def profile():
    uid=session['uid']; db=g.db
    if request.method=='POST':
        name=request.form.get('name','').strip()[:100]; department=request.form.get('department','').strip()[:100]; year=request.form.get('year','').strip()[:40]; target=request.form.get('target',''); skills=request.form.get('skills','').strip()[:1000]; bio=request.form.get('bio','').strip()[:1000]
        if not name or target not in CAREERS: flash('Enter a name and valid career goal.','danger')
        else:
            db.execute('UPDATE users SET name=? WHERE id=?',(name,uid)); db.execute('UPDATE profiles SET department=?,year=?,target=?,skills=?,bio=? WHERE user_id=?',(department,year,target,skills,bio,uid)); db.commit(); flash('Profile saved.','success'); return redirect(url_for('profile'))
    return render_template('page.html',page='profile',u=db.execute('SELECT * FROM users WHERE id=?',(uid,)).fetchone(),p=db.execute('SELECT * FROM profiles WHERE user_id=?',(uid,)).fetchone(),careers=list(CAREERS))

@app.post('/certificates')
@roles('student')
def add_certificate():
    title=request.form.get('title','').strip()[:150]; issuer=request.form.get('issuer','').strip()[:150]
    if not title: flash('Certificate title is required.','danger')
    else: g.db.execute('INSERT INTO certificates(student_id,title,issuer) VALUES(?,?,?)',(session['uid'],title,issuer)); g.db.commit(); flash('Certificate added for faculty review.','success')
    return redirect(url_for('dashboard'))

@app.post('/projects')
@roles('student')
def add_project():
    title=request.form.get('title','').strip()[:150]; desc=request.form.get('description','').strip()[:500]
    if title: g.db.execute('INSERT INTO projects(student_id,title,description) VALUES(?,?,?)',(session['uid'],title,desc)); g.db.commit(); flash('Project added.','success')
    else: flash('Project title is required.','danger')
    return redirect(url_for('dashboard'))

@app.post('/faculty/student/<int:sid>')
@roles('faculty')
def update_student(sid):
    try: score=float(request.form.get('score',''))
    except ValueError: score=-1
    if not 0<=score<=10: flash('Score must be between 0 and 10.','danger')
    elif not g.db.execute('SELECT id FROM users WHERE id=? AND role=\'student\'',(sid,)).fetchone(): abort(404)
    else: g.db.execute('UPDATE profiles SET score=? WHERE user_id=?',(score,sid)); g.db.commit(); flash('Academic score updated.','success')
    return redirect(url_for('dashboard'))

@app.post('/faculty/certificate/<int:cid>')
@roles('faculty')
def review_certificate(cid):
    status=request.form.get('status')
    if status not in ('Pending','Verified','Rejected'): abort(400)
    cur=g.db.execute('UPDATE certificates SET status=? WHERE id=?',(status,cid))
    if not cur.rowcount: abort(404)
    g.db.commit(); flash('Certificate status updated.','success'); return redirect(url_for('dashboard'))

@app.route('/opportunities')
@login_required
def opportunities():
    q=request.args.get('q','').strip()[:100]; kind=request.args.get('kind','')
    sql="SELECT j.*,u.name company FROM jobs j JOIN users u ON u.id=j.company_id WHERE j.status='Open'"; params=[]
    if q: sql+=' AND (j.title LIKE ? OR j.skills LIKE ? OR j.description LIKE ?)'; params += [f'%{q}%']*3
    if kind in ('Job','Internship'): sql+=' AND j.kind=?'; params.append(kind)
    rows=g.db.execute(sql+' ORDER BY j.id DESC',params).fetchall()
    return render_template('page.html',page='opportunities',jobs=rows,q=q,kind=kind)

@app.post('/apply/<int:jid>')
@roles('student')
def apply(jid):
    job=g.db.execute("SELECT id FROM jobs WHERE id=? AND status='Open'",(jid,)).fetchone()
    if not job: flash('Opportunity is not available.','danger')
    else:
        try: g.db.execute('INSERT INTO applications(job_id,student_id) VALUES(?,?)',(jid,session['uid'])); g.db.commit(); flash('Application submitted.','success')
        except sqlite3.IntegrityError: flash('You have already applied.','warning')
    return redirect(url_for('opportunities'))

@app.post('/company/job')
@roles('company')
def create_job():
    title=request.form.get('title','').strip()[:150]; kind=request.form.get('kind',''); desc=request.form.get('description','').strip()[:2000]; skills=request.form.get('skills','').strip()[:500]; eligibility=request.form.get('eligibility','').strip()[:500]; location=request.form.get('location','').strip()[:100]
    if not title or kind not in ('Job','Internship'): flash('Enter a title and type.','danger')
    else: g.db.execute('INSERT INTO jobs(company_id,title,kind,description,skills,eligibility,location) VALUES(?,?,?,?,?,?,?)',(session['uid'],title,kind,desc,skills,eligibility,location)); g.db.commit(); flash('Opportunity published.','success')
    return redirect(url_for('dashboard'))

@app.post('/company/job/<int:jid>/status')
@roles('company')
def job_status(jid):
    status=request.form.get('status')
    if status not in ('Open','Closed'): abort(400)
    cur=g.db.execute('UPDATE jobs SET status=? WHERE id=? AND company_id=?',(status,jid,session['uid']))
    if not cur.rowcount: abort(404)
    g.db.commit(); flash('Opportunity updated.','success'); return redirect(url_for('dashboard'))

@app.post('/company/application/<int:aid>')
@roles('company')
def app_status(aid):
    status=request.form.get('status')
    if status not in ('Under Review','Shortlisted','Rejected','Selected'): abort(400)
    cur=g.db.execute('UPDATE applications SET status=? WHERE id=? AND job_id IN (SELECT id FROM jobs WHERE company_id=?)',(status,aid,session['uid']))
    if not cur.rowcount: abort(404)
    g.db.commit(); flash('Application status updated.','success'); return redirect(url_for('dashboard'))

@app.route('/assessment',methods=['GET','POST'])
@roles('student')
def assessment():
    qs=g.db.execute('SELECT * FROM questions ORDER BY id').fetchall()
    if request.method=='POST':
        weights={'Basic':1,'Intermediate':2,'Advanced':3}; earned=total=correct=0; review=[]
        for q in qs:
            w=weights[q['difficulty']]; total+=w; chosen=request.form.get(f"q{q['id']}",''); ok=int(chosen==q['answer']); earned+=w if ok else 0; correct+=ok; review.append((q,chosen,ok))
        score=round(earned/total*100,2) if total else 0
        g.db.execute('INSERT INTO attempts(student_id,score,correct_count,total_count) VALUES(?,?,?,?)',(session['uid'],score,correct,len(qs))); g.db.commit()
        return render_template('page.html',page='result',score=score,earned=earned,total=total,correct=correct,review=review,total_count=len(qs))
    return render_template('page.html',page='assessment',questions=qs)

@app.route('/roadmap')
@roles('student')
def roadmap():
    p=g.db.execute('SELECT * FROM profiles WHERE user_id=?',(session['uid'],)).fetchone(); return render_template('page.html',page='roadmap',p=p,roadmap=make_roadmap(p['target'],p['skills']))

@app.get('/health')
def health(): return {'status':'ok','app':'CareerIQ'}

@app.errorhandler(403)
def forbidden(e): return render_template('page.html',page='error',code=403,message='You do not have permission to access this page.'),403
@app.errorhandler(404)
def not_found(e): return render_template('page.html',page='error',code=404,message='The requested page or record was not found.'),404

init_db()
if __name__=='__main__': app.run(debug=os.environ.get('FLASK_DEBUG')=='1')
