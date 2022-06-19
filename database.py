import psycopg2 as psycopg2
import config
from config import *


def connect():
    return psycopg2.connect(
        host=host,
        database=database,
        user=user,
        password=password)


def select_all_users():
    """
    Query all rows in the tasks table
    :param conn: the Connection object
    :return:
    """
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM shine_monitor.users")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_user(username):
    out = {}
    conn = connect()
    cur = conn.cursor()
    cur.execute('SELECT * From shine_monitor.accounts WHERE username=%(username)s', {'username': username.strip()})
    user = cur.fetchone()
    devices, device_names = get_devices(username)
    if user:
        out['username'] = user[0]
        out['password'] = user[1]
        out['plantid'] = user[2]
        out['token'] = user[3]
        out['secret'] = user[4]
        out['expire'] = user[5]
        out['devices'] = devices
        out['device_names'] = device_names
        # print(out)
    cur.close()
    conn.close()
    return out


def get_devices(user):
    devices = {}
    device_names = []
    conn = connect()
    cur = conn.cursor()
    cur.execute('SELECT * From shine_monitor.devices WHERE username=%(username)s', {'username': user.strip()})
    devices_query = cur.fetchall()
    for device in devices_query:
        devices[device[0]] = device
        device_names.append(device[0])
    return devices, device_names


def get_device(user, name):
    conn = connect()
    cur = conn.cursor()
    cur.execute('SELECT * From shine_monitor.devices WHERE username=%(username)s AND name=%(name)s',
                {'username': user['username'].strip(), 'name': name.strip()})
    devices_query = cur.fetchone()
    return devices_query


def add_user(data, pwd, token, secret, expire):
    conn = connect()
    cur = conn.cursor()
    cur.execute('INSERT INTO shine_monitor.accounts (username, password, plant_id, token, secret, expire)'
                'VALUES (%s, %s, %s, %s, %s, %s)',
                (data['username'].strip(), pwd.strip(), data['plantid'].strip(),
                 token.strip(), secret.strip(), expire))
    cur.execute('INSERT INTO shine_monitor.devices (username, sn, pn, devcode,name)'
                'VALUES (%s, %s, %s, %s, %s)',
                (data['username'].strip(), data['sn'].strip(), data['pn'].strip(), data['devcode'].strip(), data['devicename'].strip()))
    conn.commit()
    cur.close()
    conn.close()


def add_device(user, data):
    conn = connect()
    cur = conn.cursor()
    cur.execute('INSERT INTO shine_monitor.devices (username, sn, pn, devcode,name)'
                'VALUES (%s, %s, %s, %s, %s)',
                (user['username'].strip(), data['sn'].strip(), data['pn'].strip(), data['devcode'].strip(), data['devicename'].strip()))
    conn.commit()
    cur.close()
    conn.close()


def update_token(username, token, secret, expire):
    conn = connect()
    cur = conn.cursor()
    cur.execute('Update shine_monitor.accounts SET token=%s, secret=%s, expire=%s where username=%s',
                (token.strip(), secret.strip(), expire, username.strip()))
    conn.commit()
    cur.close()
    conn.close()


if __name__ == '__main__':
    print(select_all_users())
