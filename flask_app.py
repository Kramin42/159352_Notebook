
# using https://blog.pythonanywhere.com/121/ as a start point
from flask import Flask, redirect, render_template, request, url_for
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager, login_required, login_user, logout_user, current_user

app = Flask(__name__)
app.config["DEBUG"] = True

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

    def __init__(self , username ,password , email):
        self.username = username
        self.password = password

@app.route("/")
def index():
    return render_template("main_page.html", entries=Entry.query.all())

#    comment = Comment(content=request.form["contents"])
#    db.session.add(comment)
#    db.session.commit()
#    return redirect(url_for('index'))

if __name__ == '__main__':
    db.create_all()
