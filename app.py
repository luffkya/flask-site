from flask import Flask, render_template, request, redirect, session, jsonify
import json
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your-secret-key'

# Загрузка пользователей
if os.path.exists('users.json'):
    with open('users.json') as f:
        users = json.load(f)
else:
    users = {}

# Загрузка очков
if os.path.exists('scores.json'):
    with open('scores.json') as f:
        scores = json.load(f)
else:
    scores = []

# Сохраняем пользователей
def save_users():
    with open('users.json', 'w') as f:
        json.dump(users, f, indent=4)

# Сохраняем очки
def save_scores():
    with open('scores.json', 'w') as f:
        json.dump(scores, f, indent=4)

# Проверка входа
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'username' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return wrap

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users:
            return "Пользователь уже существует"
        users[username] = {'password': password, 'role': 'user'}
        save_users()
        return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users.get(username)
        if user and user['password'] == password:
            session['username'] = username
            return redirect('/')
        return "Неверный логин или пароль"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')

@app.route('/snake')
@login_required
def snake():
    return render_template('snake.html')

@app.route('/2048')
@login_required
def game_2048():
    return render_template('2048.html')

@app.route('/minesweeper')
@login_required
def minesweeper():
    return render_template('minesweeper.html')

@app.route('/platformer')
@login_required
def platformer():
    return render_template('platformer.html')


@app.route('/save_score', methods=['POST'])
@login_required
def save_score():
    data = request.get_json()
    scores.append({
        "username": session["username"],
        "game": data.get("game"),
        "score": data.get("score")
    })
    save_scores()
    return '', 204

@app.route('/leaderboard')
def leaderboard():
    filter_player = request.args.get('player', '').strip()
    categories = {"snake": [], "2048": [], "minesweeper": [], "platformer": []}

    for score in scores:
        game = score.get("game")
        if game in categories:
            categories[game].append(score)

    for game_scores in categories.values():
        game_scores.sort(key=lambda x: x["score"], reverse=True)

    return render_template("leaderboard.html", scores=categories, filter_player=filter_player)



# ----------- OWNER PANEL ----------------

@app.route('/owner')
@login_required
def owner_panel():
    username = session['username']
    if users.get(username, {}).get('role') != 'owner':
        return "Доступ запрещён", 403
    return render_template('owner.html', users=users, scores=scores)

@app.route('/owner/update_user', methods=['POST'])
@login_required
def update_user():
    if users[session['username']]['role'] != 'owner':
        return "Доступ запрещён", 403

    old_username = request.form['old_username']
    new_username = request.form['new_username']
    new_password = request.form['new_password']

    if old_username not in users:
        return "Пользователь не найден", 404

    user_data = users.pop(old_username)
    user_data['password'] = new_password
    users[new_username] = user_data
    save_users()
    return redirect('/owner')

@app.route('/owner/delete_user/<username>', methods=['POST'])
@login_required
def delete_user(username):
    if users[session['username']]['role'] != 'owner':
        return "Доступ запрещён", 403
    if users[username]['role'] == 'owner':
        return "Нельзя удалить владельца", 403
    users.pop(username)
    save_users()
    return redirect('/owner')

@app.route('/owner/update_score', methods=['POST'])
@login_required
def update_score():
    if users[session['username']]['role'] != 'owner':
        return "Доступ запрещён", 403

    index = int(request.form['index'])
    new_score = int(request.form['new_score'])

    if 0 <= index < len(scores):
        scores[index]['score'] = new_score
        save_scores()
    return redirect('/owner')

@app.route('/owner/delete_score', methods=['POST'])
@login_required
def delete_score():
    if users[session['username']]['role'] != 'owner':
        return "Доступ запрещён", 403

    index = int(request.form['index'])

    if 0 <= index < len(scores):
        scores.pop(index)
        save_scores()
    return redirect('/owner')

# ------------- RUN -----------------
if __name__ == '__main__':
    app.run(debug=True)
