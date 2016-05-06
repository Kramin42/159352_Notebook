
# using https://blog.pythonanywhere.com/121/ as a start point
from flask import Flask, redirect, render_template, request, url_for, flash, abort, g
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask.ext.login import login_user , logout_user , current_user , login_required

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
    timestamp = db.Column(db.DateTime())

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

@app.route("/")
def index():
    return render_template("main_page.html", entries=Entry.query.all())

#    comment = Comment(content=request.form["contents"])
#    db.session.add(comment)
#    db.session.commit()
#    return redirect(url_for('index'))

@app.route('/delete')
@login_required
def delete():
    entry = Entry.query.filter_by(id=request.args.get('id')).first()
    db.session.delete(entry)
    db.session.commit()
    flash('Deleted: '+entry.topic)
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
        flash('Username or Password is invalid' , 'error')
        return redirect(url_for('login'))
    login_user(registered_user)
    flash('Logged in successfully')
    return redirect(request.args.get('next') or url_for('index'))

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    db.create_all()
