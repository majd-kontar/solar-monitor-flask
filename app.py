import hashlib
import string
import random
from flask import Flask, request, render_template, redirect, url_for, make_response, session, jsonify
import database
from shine_monitor_api import ShineMonitor

app = Flask(__name__)
app.secret_key = 'aj;lfja;lfaj=wir['
shine_monitor = ShineMonitor()


def get_random_string(length):
    letters = string.ascii_lowercase
    while True:
        to_return = ''.join(random.choice(letters) for _ in range(length))
        if to_return not in session:
            return to_return


@app.route('/home-<id>', methods=['GET'])
def home(id):
    if id in session:
        # print(session)
        usr = session[id]
        user = database.get_user(usr)
        data = shine_monitor.get_energy_now(user)
        summary = shine_monitor.get_energy_summary(user)
        source_time = shine_monitor.get_source_summary(user)
        status = shine_monitor.get_status(data)
        # print(data)
        return render_template('home_page.html', data=data, status=status, summary=summary, source_time=source_time)
    else:
        response = make_response(redirect(url_for('login')))
        response.set_cookie('session_id', '', expires=0)
        return response


@app.route('/logs-<id>', methods=['GET'])
def get_logs(id):
    if id in session:
        # print(session)
        usr = session[id]
        user = database.get_user(usr)
        data = shine_monitor.get_data(user)
        return render_template('logs_page.html', data=data)
    else:
        return redirect(url_for('login'))


@app.route('/summary-<id>', methods=['GET'])
def get_summary(id):
    if id in session:
        # print(session)
        usr = session[id]
        user = database.get_user(usr)
        summary = shine_monitor.get_energy_summary(user)
        source_time = shine_monitor.get_source_summary(user)
        return render_template('summary_page.html', summary=summary, source_time=source_time)
    else:
        return redirect(url_for('login'))


@app.route('/status-<id>')
def get_status(id):
    if id in session:
        # print(session)
        usr = session[id]
        user = database.get_user(usr)
        data = shine_monitor.get_energy_now(user)
        status = shine_monitor.get_status(data)
        # print(data)
        return render_template('status_page.html', status=status)
    else:
        return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    err = None
    # print(session)
    if request.method == 'POST':
        usr = request.form['username'].strip()
        pwd = request.form['password'].strip()
        pwd = str(hashlib.sha1(pwd.encode('utf-8')).hexdigest())
        user_db = database.get_user(usr)
        if user_db and pwd == user_db[1]:
            key = get_random_string(20)
            session[key] = usr
            response = make_response(redirect('/home-' + key))
            response.set_cookie('session_id', key)
            return response
        elif not user_db:
            err = 'User doesn\'t exist.'
        else:
            err = 'Invalid Credentials. Please try again.'
    elif request.cookies.get('session_id'):
        return redirect('/home-' + request.cookies.get('session_id'))
    return render_template('login.html', error=err)


@app.route('/logout-<id>', methods=['GET'])
def logout(id):
    response = make_response(redirect(url_for('login')))
    if id in session:
        session.pop(id)
    if request.cookies.get('session_id'):
        response.set_cookie('session_id', '', expires=0)
    return response


@app.route('/register', methods=['GET', 'POST'])
def register():
    err = None
    if request.method == 'POST':
        usr = request.form['username'].strip()
        pwd = request.form['password']
        pwd = str(hashlib.sha1(pwd.encode('utf-8')).hexdigest())
        user_db = database.get_user(usr)
        valid, token, secret, expire = shine_monitor.login(usr, pwd)
        if valid and not user_db:
            database.add_user(request.form, pwd, token, secret, expire)
            key = get_random_string(20)
            session[key] = usr
            response = make_response(redirect('/home-' + key))
            response.set_cookie('session_id', key)
            return response
        elif user_db:
            err = 'User already exists.'
        else:
            err = 'Invalid Credentials. Please try again.'
    return render_template('register.html', error=err)


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    if request.cookies.get('session_id'):
        return redirect('/home-' + request.cookies.get('session_id'))
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(port=5000)
