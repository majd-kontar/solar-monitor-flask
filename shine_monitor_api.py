import hashlib
import time
from datetime import datetime, timedelta
import requests
import config
from database import Database


class ShineMonitor:
    def __init__(self):
        global f
        self.base_url = 'http://web.shinemonitor.com/public/'
        # Use token if exists
        self.token, self.secret, self.expire = '', '', ''
        try:
            f = open("token", "r")
            if config.debug == 1:
                print("Using tokenfile credentials")
            self.token = f.readline().strip()
            self.secret = f.readline().strip()
            self.expire = f.readline().strip()
            # Check if token expired
            d = datetime.now().today()
            e = datetime.strptime(self.expire, '%Y-%m-%d %H:%M:%S.%f')
            if config.debug == 1:
                print("Datetime now:  " + str(d))
                print("Expires:       " + str(e))
            if d > e:
                if config.debug == 1:
                    print("Expired")
                raise Exception
            else:
                if config.debug == 1:
                    print("Not expired")
        except:
            if config.debug == 1:
                print("Logging in using credentials")
            self.token, self.secret, self.expire = self.get_token(self.salt())
            f = open("token", "w")
            f.write(self.token + '\n')
            f.write(self.secret + '\n')
            f.write(str(self.expire))
        finally:
            f.close()

    def salt(self):
        return str(round(time.time() * 1000))

    def get_token(self, salt):
        # Build auth url
        pow_sha1 = hashlib.sha1()
        pow_sha1.update(config.pwd.encode('utf-8'))
        action = '&action=auth&usr=' + str(config.usr)
        pwd_action = salt + str(pow_sha1.hexdigest()) + action  # This complete string needs SHA1
        auth_sign = hashlib.sha1()
        auth_sign.update(pwd_action.encode('utf-8'))
        sign = str(auth_sign.hexdigest())
        solar_url = self.base_url + '?sign=' + sign + '&salt=' + salt + action
        # print(solar_url)
        r = requests.get(solar_url)
        self.token = r.json()['dat']['token']
        self.secret = r.json()['dat']['secret']
        self.expire = r.json()['dat']['expire']
        # Convert expire to datetime when expiring
        d = datetime.now().today()
        self.expire = d + timedelta(seconds=self.expire)
        return self.token, self.secret, self.expire

    def build_request_url(self, action, salt, secret, token, device_code, plant_id, pn, sn):
        if action == 'queryPlantCurrentData':
            action = '&action=queryPlantCurrentData&plantid=' + plant_id + '&par=ENERGY_TODAY,ENERGY_MONTH,ENERGY_YEAR,ENERGY_TOTAL,ENERGY_PROCEEDS,ENERGY_CO2,CURRENT_TEMP,CURRENT_RADIANT,BATTERY_SOC,ENERGY_COAL,ENERGY_SO2'
        elif action == 'queryPlantActiveOutputPowerOneDay':
            action = '&action=queryPlantActiveOuputPowerOneDay&plantid=' + plant_id + '&date=' + datetime.today().strftime(
                '%Y-%m-%d') + '&i18n=en_US&lang=en_US'
        elif action == 'queryDeviceDataOneDayPaging':
            action = '&action=queryDeviceDataOneDayPaging&devaddr=1&pn=' + pn + '&devcode=' + device_code + '&sn=' + sn + '&date=' + datetime.today().strftime(
                '%Y-%m-%d') + '&page=0&pagesize=50&i18n=en_US&lang=en_US'
        elif action == 'queryPlantDeviceDesignatedInformation':
            action = '&action=queryPlantDeviceDesignatedInformation&plantid=' + plant_id + '&devtype=512&i18n=en_US&parameter=energy_today,energy_total&i18n=en_US&lang=en_US '

        req_action = str(salt) + secret + token + action
        req_sign = hashlib.sha1()
        req_sign.update(req_action.encode('utf-8'))
        sign = str(req_sign.hexdigest())
        req_url = self.base_url + '?sign=' + sign + '&salt=' + str(salt) + '&token=' + token + action
        return req_url

    def get_all_data(self):
        # Get data
        req_url = self.build_request_url('queryPlantCurrentData', self.salt, self.secret, self.token, config.devcode, config.plantId, config.pn,
                                         config.sn)
        r = requests.get(req_url)

        errcode = r.json()['err']
        if errcode == 0:
            energy_today = r.json()['dat'][0]['val']
            energy_month = r.json()['dat'][1]['val']
            energy_year = r.json()['dat'][2]['val']
            energy_total = r.json()['dat'][3]['val']

            if config.debug == 1:
                print('Energy Today: ' + str(energy_today) + 'kWh')
                print('Energy Month: ' + str(energy_month) + 'kWh')
                print('Energy Year: ' + str(energy_year) + 'kWh')
                print('Energy Total: ' + str(energy_total) + 'kWh')
        else:
            print('Error code ' + str(errcode))
            print(r.json())

        req_url = self.build_request_url('queryDeviceDataOneDayPaging', self.salt, self.secret, self.token, config.devcode, config.plantId,
                                         config.pn, config.sn)
        r = requests.get(req_url)

        errcode = r.json()['err']
        if errcode == 0:
            timestamp = r.json()['dat']['row'][0]['field'][1]
            energy_now = r.json()['dat']['row'][0]['field'][5]

            if config.debug == 1:
                print('Timestamp: ' + str(timestamp))
                print('Energy Now: ' + str(energy_now) + 'W')
        else:
            print('Error code ' + str(errcode))
            print(r.json())

        req_url = self.build_request_url('queryPlantActiveOutputPowerOneDay', self.salt, self.secret, self.token, config.devcode, config.plantId,
                                         config.pn, config.sn)

        r = requests.get(req_url)

        errcode = r.json()['err']
        if errcode == 0:
            energy_over_day = r.json()['dat']['outputPower']
            energy_over_day = str(energy_over_day).replace(r'\'', '\"')

            if config.debug == 1:
                print(energy_over_day)
        else:
            print('Error code ' + str(errcode))
            print(r.json())

    def get_energy_now(self):
        req_url = self.build_request_url('queryDeviceDataOneDayPaging', self.salt, self.secret, self.token, config.devcode, config.plantId,
                                         config.pn, config.sn)
        r = requests.get(req_url)
        errcode = r.json()['err']

        if errcode == 0:
            fields = r.json()['dat']['row'][0]['field']
            to_return = dict()
            for (i, field) in enumerate(fields):
                to_return[r.json()['dat']['title'][i]['title']] = [field]
            fields = r.json()['dat']['row'][1]['field']
            for (i, field) in enumerate(fields):
                to_return[r.json()['dat']['title'][i]['title']].append(field)
            return to_return
        else:
            return {'Error code': str(errcode)}

    def get_data(self):
        req_url = self.build_request_url('queryDeviceDataOneDayPaging', self.salt, self.secret, self.token, config.devcode, config.plantId,
                                         config.pn, config.sn)
        r = requests.get(req_url)
        errcode = r.json()['err']

        if errcode == 0:
            to_return = []
            for row in r.json()['dat']['row']:
                data = []
                fields = row['field']
                for (i, field) in enumerate(fields):
                    data.append(field)
                to_return.append(data)
            return to_return
        else:
            return {'Error code': str(errcode)}

    def get_energy_summary(self):
        req_url = self.build_request_url('queryPlantCurrentData', self.salt, self.secret, self.token, config.devcode, config.plantId, config.pn,
                                         config.sn)
        r = requests.get(req_url)
        errcode = r.json()['err']

        if errcode == 0:
            energy_today = r.json()['dat'][0]['val']
            energy_month = r.json()['dat'][1]['val']
            energy_year = r.json()['dat'][2]['val']
            energy_total = r.json()['dat'][3]['val']
            r = '{"Today": ' + str(energy_today)
            r += ', "Month": ' + str(energy_month)
            r += ', "Year": ' + str(energy_year)
            r += ', "Total": ' + str(energy_total)
            r += ', "Unit": "kWh"}'
            return r
        else:
            print('{Error code: ' + str(errcode) + '}')
            print(r.json())

    def get_energy_timeline(self):
        req_url = self.build_request_url('queryPlantActiveOutputPowerOneDay', self.salt, self.secret, self.token, config.devcode, config.plantId,
                                         config.pn, config.sn)
        r = requests.get(req_url)
        errcode = r.json()['err']

        if errcode == 0:
            energy_over_day = r.json()['dat']['outputPower']
            energy_over_day = str(energy_over_day).replace(r'\'', '"')
            energy_over_day = str(energy_over_day).replace(r'("val":\ )"([\d\.]+)"', r'\1\2')
            energy_over_day = str(energy_over_day).replace(r'"val"', '"Value"', )
            energy_over_day = str(energy_over_day).replace(r'"ts"', '"TimeStamp"')
            # Add unit
            energy_over_day = str(energy_over_day).replace(r'}', ', "Unit": "kW"}')
            return energy_over_day
        else:
            print('Error code ' + str(errcode))
            print(r.json())


if __name__ == '__main__':
    shine_monitor = ShineMonitor()
    # endpoint = input('Enter an option: (energyNow, energySummary, energyTimeline):\n')
    # if endpoint == 'energyNow':
    #     while True:
    #         print(shine_monitor.get_energy_now())
    #         time.sleep(5 * 60)
    # elif endpoint == 'energySummary':
    #     print(shine_monitor.get_energy_summary())
    # elif endpoint == 'energyTimeline':
    #     print(shine_monitor.get_energy_timeline())
    # else:
    #     shine_monitor.get_all_data()
    data = shine_monitor.get_data()
    database = Database('identifier.sqlite')
    for d in data:
        database.insert_log(d)
