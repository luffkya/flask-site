from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = 'some_secret_key'
USERS_FILE = 'users.json'

def load_users():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f:
            json.dump({"owneruser": {"password": "ownerpass", "role": "owner"}}, f, indent=4)
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'username' not in session:
            flash('Пожалуйста, войдите в систему')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') not in ('admin', 'owner'):
            flash('Доступ запрещён')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        users = load_users()
        if username in users:
            flash('Пользователь уже существует')
            return redirect(url_for('register'))
        users[username] = {'password': password, 'role': 'user'}
        save_users(users)
        flash('Регистрация успешна')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        users = load_users()
        user = users.get(username)
        if user and user['password'] == password:
            session['username'] = username
            session['role'] = user.get('role', 'user')
            return redirect(url_for('index'))
        flash('Неверный логин или пароль')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы')
    return redirect(url_for('index'))

@app.route('/admin')
@admin_required
def admin_panel():
    users = load_users()
    return render_template('admin.html', users=users)

@app.route('/admin/delete/<username>', methods=['POST'])
@admin_required
def admin_delete_user(username):
    users = load_users()
    if username in users and users[username]['role'] != 'owner':
        users.pop(username)
        save_users(users)
        flash(f'{username} удалён')
    else:
        flash('Нельзя удалить владельца или несуществующего пользователя')
    return redirect(url_for('admin_panel'))

@app.route('/admin/change_role/<username>', methods=['POST'])
@admin_required
def admin_change_role(username):
    users = load_users()
    if username in users and users[username]['role'] != 'owner':
        current = users[username]['role']
        users[username]['role'] = 'admin' if current == 'user' else 'user'
        save_users(users)
        flash(f'Роль {username} обновлена')
    else:
        flash('Нельзя изменить владельца')
    return redirect(url_for('admin_panel'))

@app.route('/save_score', methods=['POST'])
@login_required
def save_score():
    data = request.get_json()
    game = data.get('game')
    score = int(data.get('score'))

    if not os.path.exists('scores.json'):
        with open('scores.json', 'w') as f:
            json.dump([], f)

    with open('scores.json', 'r') as f:
        scores = json.load(f)

    scores.append({
        "username": session['username'],
        "game": game,
        "score": score
    })

    with open('scores.json', 'w') as f:
        json.dump(scores, f, indent=4)

    return '', 204


@app.route('/snake')
@login_required
def snake():
    return render_template('snake.html')

@app.route('/game_2048')
@login_required
def game_2048():
    return render_template('2048.html')

@app.route('/minesweeper')
@login_required
def minesweeper():
    return render_template('minesweeper.html')

@app.route('/leaderboard')
@login_required
def leaderboard():
    if os.path.exists('scores.json'):
        with open('scores.json') as f:
            scores = json.load(f)
    else:
        scores = []

    games = {'snake': [], '2048': [], 'minesweeper': []}
    for s in scores:
        games[s['game']].append(s)

    for game in games:
        games[game] = sorted(games[game], key=lambda x: x['score'], reverse=True)[:10]

    return render_template('leaderboard.html', games=games)


if __name__ == '__main__':
    app.run(debug=True)
