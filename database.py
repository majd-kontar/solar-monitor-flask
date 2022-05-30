import sqlite3
import matplotlib.pyplot as plt


class Database:
    def __init__(self, db_file):
        self.db_file = db_file
        self.conn = self.create_connection()
        self.cur = self.conn.cursor()

    def create_connection(self):
        """ create a database connection to the SQLite database
            specified by the db_file
        :return: Connection object or None
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_file)
        except Exception as e:
            print(e)
        return conn

    def select_all_logs(self):
        """
        Query all rows in the tasks table
        :param conn: the Connection object
        :return:
        """
        self.cur.execute("SELECT * FROM shine_monitor")
        rows = self.cur.fetchall()
        for row in rows:
            print(row)
        return rows

    def select_column(self, column):
        query = """SELECT time,""" + column + """ FROM shine_monitor ORDER BY sql DESC"""
        self.cur.execute(query)
        rows = self.cur.fetchall()
        time = []
        data = []
        for row in rows:
            time.append(float(row[0][row[0].index(' ')+1:row[0].rindex(':')].replace(':','.')))
            data.append(float(row[1]))
        print(time,data)
        return time, data

    def insert_log(self, data):
        sqlite_insert_query = """INSERT INTO shine_monitor(id,time, grid_voltage, pv_voltage, pv_power, battery_voltage, battery_capacity, 
        battery_charging_current, battery_discharging_current, output_voltage, output_power,output_percent, pv_current, total_generation, today_generation)
        VALUES  (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""
        count = self.cur.execute(sqlite_insert_query, data)
        self.conn.commit()


if __name__ == '__main__':
    database = Database('identifier.sqlite')
    # database.select_all_logs()
    time, data = database.select_column('output_power')
    plt.plot(time, data)
    plt.show()
