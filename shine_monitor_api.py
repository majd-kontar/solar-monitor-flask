import hashlib
import time
import urllib.parse
from datetime import datetime, timedelta
import pytz
import requests
import database


class ShineMonitor:
    def __init__(self):
        self._debug = 1
        self.timezone = 'Asia/Beirut'
        self.base_url = 'http://web.shinemonitor.com/public/'
        self.headers = {
            "User-Agent": "Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.141 Safari/537.36"}

    def salt(self):
        return str(round(time.time() * 1000))

    def check_token(self, user):
        d = datetime.now(tz=pytz.timezone(self.timezone)).replace(tzinfo=None)
        e = datetime.strptime(user[8], '%Y-%m-%d %H:%M:%S.%f')
        try:
            if self._debug == 1:
                print("Datetime now:  " + str(d))
                print("Expires:       " + str(e))
            if d > e:
                if self._debug == 1:
                    print("Expired")
                raise Exception
            elif self._debug == 1:
                print("Not expired")
        except:
            if self._debug == 1:
                print("Logging in using credentials")
            _, token, secret, expire = self.login(user[0], user[1])
            database.update_token(user[0], token, secret, expire)

    def build_request_url(self, action, salt=None, secret=None, token=None, device_code=None, plant_id=None, pn=None, sn=None, usr=None, pwd=None,
                          field=None, page=0):
        date = datetime.now(tz=pytz.timezone(self.timezone)).replace(tzinfo=None)
        if action == 'queryPlantCurrentData':
            action = '&action=queryPlantCurrentData&plantid=' + plant_id + '&par=ENERGY_TODAY,ENERGY_MONTH,ENERGY_YEAR,ENERGY_TOTAL,ENERGY_PROCEEDS,ENERGY_CO2,CURRENT_TEMP,CURRENT_RADIANT,BATTERY_SOC,ENERGY_COAL,ENERGY_SO2'
        elif action == 'queryPlantActiveOutputPowerOneDay':
            action = '&action=queryPlantActiveOuputPowerOneDay&plantid=' + plant_id + '&date=' + date.strftime(
                '%Y-%m-%d') + '&i18n=en_US&lang=en_US'
        elif action == 'queryDeviceDataOneDayPaging':
            action = '&action=queryDeviceDataOneDayPaging&devaddr=1&pn=' + pn + '&devcode=' + device_code + '&sn=' + sn + '&date=' + date.strftime(
                '%Y-%m-%d') + '&page=' + str(page) + '&pagesize=500&i18n=en_US&lang=en_US'
        elif action == 'queryPlantDeviceDesignatedInformation':
            action = '&action=queryPlantDeviceDesignatedInformation&plantid=' + plant_id + '&devtype=512&i18n=en_US&parameter=energy_today,energy_total&i18n=en_US&lang=en_US '
        elif action == 'queryDeviceChartFieldDetailData':
            action = '&action=queryDeviceChartFieldDetailData&pn=' + pn + '&devcode=' + device_code + "&sn=" + sn + "&field=" + field + "&devaddr=" + '1' + "&precision=" + '5' + "&sdate=" + str(
                urllib.parse.quote(str(date.replace(hour=0, minute=0, second=0, microsecond=0)).encode('utf-8'))) + "&edate=" + str(
                urllib.parse.quote(str(date.replace(hour=23, minute=59, second=59, microsecond=0)).encode('utf-8')))
        elif action == 'login':
            action = "&action=auth&usr=" + usr.replace('+', '%2B') + "&company-key=bnrl_frRFjEz8Mkn"
            req_action = str(salt) + pwd + action
            req_sign = hashlib.sha1()
            req_sign.update(req_action.encode('utf-8'))
            sign = str(req_sign.hexdigest())
            req_url = self.base_url + '?sign=' + sign + '&salt=' + str(salt) + action
            return req_url

        req_action = str(salt) + secret + token + action
        req_sign = hashlib.sha1()
        req_sign.update(req_action.encode('utf-8'))
        sign = str(req_sign.hexdigest())
        req_url = self.base_url + '?sign=' + sign + '&salt=' + str(salt) + '&token=' + token + action
        return req_url

    def login(self, usr, pwd):
        req_url = self.build_request_url('login', self.salt(), usr=usr, pwd=pwd)
        r = requests.get(req_url).json()
        if r['err'] == 0:
            token = r['dat']['token']
            secret = r['dat']['secret']
            expire = r['dat']['expire']
            d = datetime.now(tz=pytz.timezone(self.timezone)).replace(tzinfo=None)
            expire = d + timedelta(seconds=expire)
            return r['err'] == 0, token, secret, expire
        return r['err'] == 0, None, None, None

    def get_energy_now(self, user):
        self.check_token(user)
        req_url = self.build_request_url('queryDeviceDataOneDayPaging', self.salt(), user[7], user[6], user[5], user[2], user[3], user[4])
        r = requests.get(req_url)
        errcode = r.json()['err']
        if errcode == 0:
            fields = r.json()['dat']['row'][0]['field']
            to_return = dict()
            to_return['dat'] = fields
            return to_return
        else:
            return {'Error code': str(errcode)}

    def get_data(self, user):
        to_return = dict()
        self.check_token(user)
        stime = time.time()
        for page in range(6):
            print(page)
            req_url = self.build_request_url('queryDeviceDataOneDayPaging', self.salt(), user[7], user[6], user[5], user[2], user[3], user[4],
                                             page=page)
            r = requests.get(req_url)
            errcode = r.json()['err']
            if errcode == 0:
                if page == 0:
                    for title in r.json()['dat']['title']:
                        to_return[title['title']] = []
                for fields in r.json()['dat']['row']:
                    for (i, field) in enumerate(fields['field']):
                        to_return[r.json()['dat']['title'][i]['title']].append(field)
            elif errcode == 12:
                print(time.time() - stime)
                return to_return
            else:
                return {'Error code': str(errcode)}
        return to_return

    def get_energy_summary(self, user):
        req_url = self.build_request_url('queryPlantCurrentData', self.salt(), user[7], user[6], user[5], user[2], user[3], user[4])
        r = requests.get(req_url).json()
        if r['err'] == 0:
            # print(r['dat'])
            return r['dat']
        else:
            errcode = r['err']
            return {'Error code': str(errcode)}

    def get_graph_data(self, user, field):
        req_url = self.build_request_url('queryDeviceChartFieldDetailData', self.salt(), user[7], user[6], user[5], user[2], user[3], user[4],
                                         field=field)
        r = requests.get(req_url)
        return r.json()

    def get_source_time(self, user, fields):
        response = self.get_data(user)
        if 'err' not in response:
            to_return = []
            for i, field in enumerate(fields):
                logs = response[field]
                count = sum(map(lambda log: float(log) > 200, logs))
                to_return.append(count * 5 / 60)
                to_return[i] = str(int(to_return[i])) + ':' + str(int(to_return[i] % 1 * 60))
            return to_return[0], to_return[1]
        else:
            errcode = response['err']
            return {'Error code': str(errcode)}

    def get_source_summary(self, user):
        grid_time, pv_time = self.get_source_time(user, ['Grid Voltage', 'PV1 Input Voltage'])
        if 'Error code' in grid_time or 'Error code' in pv_time:
            return grid_time
        else:
            return {'grid': grid_time, 'pv': pv_time}

    def get_status(self, log):
        to_return = dict()
        if 'Error code' not in log:
            battery_status = 'Charging' if (float(log['dat'][7]) > 0) else 'Discharging'
            to_return['battery'] = {
                'voltage': log['dat'][5],
                'status': battery_status,
                'capacity': log['dat'][6]
            }
            to_return['grid'] = {
                'status': float(log['dat'][2]) > 0,
                'voltage': log['dat'][2]
            }
            to_return['pv'] = {
                'status': float(log['dat'][3]) > 200,
                'power': log['dat'][4],
                'voltage': log['dat'][3],
                'current': log['dat'][12]
            }
            to_return['output'] = {
                'current': str(round(float(log['dat'][10]) / float(log['dat'][9]), 2)),
                'power': log['dat'][10],
                'voltage': log['dat'][9]
            }
        return to_return
