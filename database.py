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
    conn = connect()
    cur = conn.cursor()
    cur.execute('SELECT * From shine_monitor.users WHERE username=%(username)s', {'username': username.strip()})
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user


def add_user(data, pwd, token, secret, expire):
    conn = connect()
    cur = conn.cursor()
    cur.execute('INSERT INTO shine_monitor.users (username, password, plant_id, pn, sn, devcode, token, secret, expire)'
                'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
                (data['username'].strip(), pwd.strip(), data['plantid'].strip(), data['pn'].strip(), data['sn'].strip(), data['devcode'].strip(),
                 token.strip(), secret.strip(), expire))
    conn.commit()
    cur.close()
    conn.close()


def update_token(username, token, secret, expire):
    conn = connect()
    cur = conn.cursor()
    cur.execute('Update shine_monitor.users SET token=%s, secret=%s, expire=%s where username=%s',
                (token.strip(), secret.strip(), expire, username.strip()))
    conn.commit()
    cur.close()
    conn.close()


if __name__ == '__main__':
    print(select_all_users())
