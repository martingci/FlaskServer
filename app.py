from flask import Flask, request, render_template, redirect, url_for, send_file, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import json
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

    def __init__(self, username, password):
        self.username = username
        self.password = password

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_json(inv, filename):
    with open(filename, "w") as file:
        json.dump(inv, file, indent=4)

def read_json(filename):
    if not os.path.exists(filename):
        return {}
    with open(filename, "r") as file:
        return json.load(file)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('home'))
        flash('Nombre de usuario o contraseña incorrectos')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Nombre de usuario ya existe')
        else:
            new_user = User(username=username, password=password)
            db.session.add(new_user)
            db.session.commit()
            flash('Usuario registrado exitosamente')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/')
@login_required
def home():
    return render_template('index.html')

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        isbn = request.form['isbn']
        filename = f"{current_user.id}.json"
        inv = read_json(filename)
        if isbn in inv:
            return "El libro ya se encuentra registrado.", 400
        title = request.form['title']
        author = request.form['author']
        year = request.form['year']
        pages = int(request.form['pages'])
        done = int(request.form['done'])
        progress = int((done * 100) / pages) if pages != 0 else 0
        comments = request.form['comments'] or "---"
        inv[isbn] = {"Title": title, "Author": author, "Year": year, "Pages": pages, "Done": done, "Progress": progress, "Comments": comments}
        create_json(inv, filename)
        return redirect(url_for('home'))
    return render_template('add.html')

@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    if request.method == 'POST':
        isbn = request.form['isbn']
        filename = f"{current_user.id}.json"
        inv = read_json(filename)
        book = inv.get(isbn)
        if book:
            return render_template('search.html', book=book)
        else:
            return "El libro no se encuentra en el inventario.", 404
    return render_template('search.html')

@app.route('/update', methods=['GET', 'POST'])
@login_required
def update():
    if request.method == 'POST':
        isbn = request.form['isbn']
        filename = f"{current_user.id}.json"
        inv = read_json(filename)
        if isbn not in inv:
            return "El libro no se encuentra en el inventario.", 404
        book = inv[isbn]
        book["Title"] = request.form['title']
        book["Author"] = request.form['author']
        book["Year"] = request.form['year']
        book["Pages"] = int(request.form['pages'])
        book["Done"] = int(request.form['done'])
        book["Progress"] = int((book["Done"] * 100) / book["Pages"]) if book["Pages"] != 0 else 0
        book["Comments"] = request.form['comments'] or "---"
        create_json(inv, filename)
        return redirect(url_for('home'))
    return render_template('update.html')

@app.route('/delete', methods=['GET', 'POST'])
@login_required
def delete():
    if request.method == 'POST':
        isbn = request.form['isbn']
        filename = f"{current_user.id}.json"
        inv = read_json(filename)
        if isbn in inv:
            del inv[isbn]
            create_json(inv, filename)
            return "El libro ha sido eliminado.", 200
        else:
            return "El libro no se encuentra en el inventario.", 404
    return render_template('delete.html')

@app.route('/view', methods=['GET'])
@login_required
def view():
    filename = f"{current_user.id}.json"
    inv = read_json(filename)
    return render_template('view.html', inventory=inv)

@app.route('/export', methods=['GET'])
@login_required
def export():
    filename = f"{current_user.id}.json"
    inv = read_json(filename)
    with open(f"{current_user.id}.csv", "w") as invn:
        s = []
        s.append("ISBN,Título,Autor,Año de publicación,Páginas totales,Páginas leídas,Porcentaje de lectura,Comentarios")
        invn.write(f"{s[0]}\n")
        for isbn, data in inv.items():
            invn.write(f"{isbn},{data['Title']},{data['Author']},{data['Year']},{data['Pages']},{data['Done']},{data['Progress']}%,{data['Comments']}\n")
    try:
        return send_file(f"{current_user.id}.csv", as_attachment=True)
    except Exception as e:
        return str(e)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=80)
