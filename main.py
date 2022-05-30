import time

from shine_monitor_api import ShineMonitor
from twilio_api import TwilioApi


def main():
    shine_monitor = ShineMonitor()
    twilio = TwilioApi()
    start_time = 0
    while True:
        if time.time() - start_time >= 5 * 60:
            start_time = time.time()
            data = shine_monitor.get_energy_now()
            print(data)
            if float(data['Battery Voltage'][0]) <= 22:
                twilio.send_message('Battery Low!')
            if float(data['Battery Voltage'][0]) == 27.2 and float(data['Battery Voltage'][1]) != 27.2:
                twilio.send_message('Battery is charged')
            if float(data['PV1 Input Voltage'][0]) <= 120 and float(data['PV1 Input Voltage'][1]) > 120:
                twilio.send_message('There is no sun!')
            if float(data['PV1 Input Voltage'][0]) >= 200 and float(data['PV1 Input Voltage'][1]) < 200:
                twilio.send_message('The sun is shining')
            if float(data['Grid Voltage'][0]) > 0 and float(data['Grid Voltage'][1]) == 0:
                twilio.send_message('EDL is available')
            if float(data['Grid Voltage'][0]) == 0 and float(data['Grid Voltage'][1]) > 0:
                twilio.send_message('EDL is no longer available')
            if float(data['Output Load Percent'][0]) >= 50:
                load = data['Output Load Percent'][0]
                consumption = data['AC Output Active Power'][0]
                twilio.send_message(f'Load is high {load}%\nConsumption is: {consumption} W')


if __name__ == '__main__':
    main()
