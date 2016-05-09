
# using https://blog.pythonanywhere.com/121/ as a start point
from flask import Flask, redirect, render_template, request, url_for, flash, abort, g
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from flask.ext.login import LoginManager
from flask.ext.login import login_user , logout_user , current_user , login_required
import re
import cgi

app = Flask(__name__)
app.config["DEBUG"] = True
app.secret_key = "super secret key"

SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
    username="Kramin42",
    password="pythonanywhere",
    hostname="Kramin42.mysql.pythonanywhere-services.com",
    databasename="Kramin42$comments",
)
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_POOL_RECYCLE"] = 299

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

class Comment(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(4096))

class Entry(db.Model):
    __tablename__ = "entries"

    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(4096))
    outline = db.Column(db.String(4096))
    timestamp = db.Column(db.TIMESTAMP(), server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    def __init__(self, topic, outline):
        self.topic = topic
        self.outline = outline

# https://blog.openshift.com/use-flask-login-to-add-user-authentication-to-your-python-application/
class User(db.Model):
    __tablename__ = "users"
    id = db.Column('user_id',db.Integer , primary_key=True)
    username = db.Column('username', db.String(20), unique=True , index=True)
    password = db.Column('password' , db.String(10))

    def __init__(self , username ,password):
        self.username = username
        self.password = password

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return '<User %r>' % (self.username)

@app.before_request
def before_request():
    g.user = current_user

@app.route('/',methods=['GET','POST'])
def index():
    if request.method == 'GET':
        return render_template("main_page.html", entries=Entry.query.all())

    s = request.form['searchstring']
    return render_template("main_page.html", entries=Entry.query.filter(Entry.topic.like('%'+s+'%') | Entry.outline.like('%'+s+'%')).all())

@app.route('/show')
def show():
    entry = Entry.query.filter_by(id=request.args.get('id')).first()
    outline = cgi.escape(entry.outline);
    print(outline)

    # break into alternating non-fixed and fixed parts
    split_outline = outline.split('#+BEGIN_FIXED')
    non_fixed = []
    fixed = []
    first=True
    for piece in split_outline:
        if first:
            first=False
            non_fixed.append(piece)
            continue
        split_piece = piece.split('#+END_FIXED')
        fixed.append(split_piece[0])
        if len(split_piece)>1:
            non_fixed.append('#+END_FIXED'.join(split_piece[1:]))
        else:
            non_fixed.append('')

    for i, piece in enumerate(non_fixed):
        piece = re.sub('(\n|^)\\s*[–-](.*)', '<li>\\2</li>', piece)
        piece = re.sub('((\\s*<li>[^<>]*<\\/li>)+)', '<ul>\\1</ul>', piece)# surround groups of <li></li> with <ul></ul>
        piece = re.sub('(\n|^)\\s*\\*([^\n*]+)', '<h2>\\2</h2>', piece)
        piece = re.sub('(\n|^)\\s*\\*\\*([^\n*]+)', '<h3>\\2</h3>', piece)
        piece = re.sub('\\[\\[(.*)\\]\\]', '<a href="\\1">\\1</a>', piece)
        piece = re.sub('\n\s*\n', '<br/>\n<br/>\n', piece) # double new line becomes new paragraph
        non_fixed[i] = piece

    outline = ""
    for i in range(len(non_fixed)):
        outline+= non_fixed[i]
        if i<len(fixed):
            outline+='<div class="container-fluid"><pre>'+fixed[i]+'</pre></div>'

    #outline = re.sub('#\\+BEGIN_FIXED((\n|.)*)#\\+END_FIXED', '<div class="container-fluid"><pre>\\2</pre></div>', outline)
    return render_template("show.html", entry=entry, formatted_outline=outline)

@app.route('/new',methods=['GET','POST'])
@login_required
def new():
    if request.method == 'GET':
        return render_template("edit.html", topic="New Topic", outline="")

    entry = Entry(request.form['topic'], request.form['outline'])
    db.session.add(entry)
    db.session.commit()
    flash('Added: '+entry.topic, 'success')
    return redirect(url_for('index'))

@app.route('/edit',methods=['GET','POST'])
@login_required
def edit():
    entry = Entry.query.filter_by(id=request.args.get('id')).first()
    if request.method == 'GET':
        return render_template("edit.html", topic=entry.topic, outline=entry.outline)
    entry.topic = request.form['topic']
    entry.outline = request.form['outline']
    db.session.commit()
    flash('Updated: '+entry.topic, 'success')
    return redirect(url_for('index'))

@app.route('/delete')
@login_required
def delete():
    entry = Entry.query.filter_by(id=request.args.get('id')).first()
    db.session.delete(entry)
    db.session.commit()
    flash('Deleted: '+entry.topic, 'success')
    return redirect(url_for('index'))

# disabled
# @app.route('/register' , methods=['GET','POST'])
# def register():
#     if request.method == 'GET':
#         return render_template('register.html')
#     user = User(request.form['username'] , request.form['password'])
#     db.session.add(user)
#     db.session.commit()
#     flash('User successfully registered')
#     return redirect(url_for('login'))

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    username = request.form['username']
    password = request.form['password']
    registered_user = User.query.filter_by(username=username,password=password).first()
    if registered_user is None:
        flash('Username or Password is invalid' , 'danger')
        return redirect(url_for('login'))
    login_user(registered_user)
    flash('Logged in successfully', 'success')
    return redirect(request.args.get('next') or url_for('index'))

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/status')
def about():
    return render_template('status.html')


# this code would normally not be here, but it is just to set up the db for the marker:
if __name__ == '__main__':
    db.create_all()
    f = User.query.first()
    if f is None:
        usr = User('admin','admin')
        db.session.add(usr)
        db.session.commit()

