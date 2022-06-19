import hashlib
import string
import random
from datetime import datetime, timedelta
import pytz
from flask import Flask, request, render_template, redirect, url_for, make_response, session
import database
from shine_monitor_api import ShineMonitor

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.secret_key = 'aj;lfja;lfaj=wir['
shine_monitor = ShineMonitor()


def get_random_string(length):
    letters = string.ascii_lowercase
    while True:
        to_return = ''.join(random.choice(letters) for _ in range(length))
        if to_return not in session:
            return to_return


def get_expire_date():
    expire_date = datetime.now(tz=pytz.timezone('Asia/Beirut')).replace(tzinfo=None)
    expire_date = expire_date + timedelta(days=90)
    return expire_date


@app.route('/home', methods=['GET'])
def home():
    id = request.cookies.get('session_id')
    if id in session:
        # print(session)
        user = session[id]
        data = shine_monitor.get_energy_now(user)
        devices = user['device_names']
        device = user['device']
        print(device)
        # summary = shine_monitor.get_energy_summary(user)
        # source_time = shine_monitor.get_source_summary(user)
        status = shine_monitor.get_status(data)
        # print(data)
        return render_template('home_page.html', data=data, status=status, device=device, devices=devices)
    else:
        response = make_response(redirect(url_for('login')))
        response.set_cookie('session_id', '', expires=0)
        return response


@app.route('/logs', methods=['GET'])
def get_logs():
    id = request.cookies.get('session_id')
    today = datetime.now(tz=pytz.timezone(shine_monitor.timezone)).replace(tzinfo=None)
    today = today.strftime('%Y-%m-%d')
    day = request.args.get('day', default=today)
    day = datetime.strptime(day, '%Y-%m-%d')
    print(f'Day: {day.strftime("%Y-%m-%d")}\tToday: {today}')
    prev = day - timedelta(days=1)
    prev = prev.strftime('%Y-%m-%d')
    next = day + timedelta(days=1)
    next = next.strftime('%Y-%m-%d')
    if day.strftime('%Y-%m-%d') == today:
        today = None
    if id in session:
        # print(session)
        user = session[id]
        data = shine_monitor.get_data(user, day.strftime('%Y-%m-%d'))
        devices = user['device_names']
        device = user['device']
        return render_template('logs_page.html', data=data, today=today, prev=prev, next=next, device=device, devices=devices)
    else:
        return redirect(url_for('login'))


@app.route('/summary', methods=['GET'])
def get_summary():
    id = request.cookies.get('session_id')
    today = datetime.now(tz=pytz.timezone(shine_monitor.timezone)).replace(tzinfo=None)
    today = today.strftime('%Y-%m-%d')
    day = request.args.get('day', default=today)
    day = datetime.strptime(day, '%Y-%m-%d')
    print(f'Day: {day.strftime("%Y-%m-%d")}\tToday: {today}')
    prev = day - timedelta(days=1)
    prev = prev.strftime('%Y-%m-%d')
    next = day + timedelta(days=1)
    next = next.strftime('%Y-%m-%d')
    if day.strftime('%Y-%m-%d') == today:
        today = None
    if id in session:
        # print(session)
        user = session[id]
        summary = shine_monitor.get_energy_summary(user)
        source_time = shine_monitor.get_source_summary(user, day.strftime('%Y-%m-%d'))
        device = user['device']
        devices = user['device_names']
        return render_template('summary_page.html', summary=summary, source_time=source_time, today=today, next=next, prev=prev, device=device,
                               devices=devices)
    else:
        return redirect(url_for('login'))


@app.route('/status')
def get_status():
    id = request.cookies.get('session_id')
    if id in session:
        # print(session)
        user = session[id]
        data = shine_monitor.get_energy_now(user)
        status = shine_monitor.get_status(data)
        device = user['device']
        devices = user['device_names']
        # print(data)
        return render_template('status_page.html', status=status, device=device, devices=devices)
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
        if user_db and pwd == user_db['password']:
            user_db['device'] = user_db['device_names'][0]
            key = get_random_string(20)
            session[key] = user_db
            response = make_response(redirect('/home-' + key))
            response.set_cookie('session_id', key, expires=get_expire_date())
            return response
        elif not user_db:
            err = 'User doesn\'t exist.'
        else:
            err = 'Invalid Credentials. Please try again.'
    elif request.cookies.get('session_id') in session:
        return redirect('/home')
    return render_template('login.html', error=err)


@app.route('/logout', methods=['GET'])
def logout():
    response = make_response(redirect(url_for('login')))
    id = request.cookies.get('session_id')
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
            session[key] = user_db
            response = make_response(redirect('/home'))
            response.set_cookie('session_id', key, expires=get_expire_date())
            return response
        elif user_db:
            err = 'User already exists.'
        else:
            err = 'Invalid Credentials. Please try again.'
    return render_template('register.html', error=err)


@app.route('/add_device', methods=['GET', 'POST'])
def add_device():
    err = None
    id = request.cookies.get('session_id')
    if id in session:
        if request.method == 'POST':
            try:
                user = session[id]
                if database.get_device(user, request.form['devicename'].strip()):
                    err = 'Device already exists!'
                elif shine_monitor.invalid_device(user, request.form):
                    err = 'Check device parameters!'
                else:
                    database.add_device(user, request.form)
                    user_db = database.get_user(user['username'])
                    user_db['device'] = user_db['device_names'][0]
                    session[id] = user_db
                    return redirect('/home')
            except:
                err = 'Failed to add device. Please try again.'
        return render_template('add_device.html', error=err)
    else:
        return redirect(url_for('login'))


@app.route('/change_device/<device>')
def set_device(device):
    id = request.cookies.get('session_id')
    if id in session:
        user = session[id]
        user['device'] = device
        session[id] = user
        return redirect(request.referrer)
    else:
        return redirect(url_for('login'))


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    if request.cookies.get('session_id'):
        return redirect('/home')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(port=5000)
