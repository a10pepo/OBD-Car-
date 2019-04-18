# -*- coding: utf-8 -*-
"""
Created on Thu Apr 18 09:13:43 2019

@author: PONO
"""

from wifi import Cell, Scheme
import obd
from obd import OBDStatus
import time


# INFO MESSAGES
INFO_000="INFO: Starting Connection"
INFO_001="INFO: ELM Connected"
INFO_002="INFO: Searching Wifi"
INFO_003="INFO: Wifi {} Connected"
INFO_004="INFO: Retrieving unpublished data"
INFO_005="INFO: Publishing stored data"
INFO_006="INFO: Gathering Data"
INFO_007="INFO: Connecting to Wifi {}"




# ERROR MESSAGES
ERROR_001="ERROR: Connection not established with ELM"
ERROR_002="ERROR: Connection not established with Wifi (Storing data)"
ERROR_003="ERROR: Connection Lost OBD2"
ERROR_004="ERROR: Connection Lost Wifi"





def show_message(message):
    print(message)


def setup_wifi():
    show_message(INFO_002)
    # get all cells from the air
    ssids = [cell.ssid for cell in Cell.all('wlan0')]
    schemes = list(Scheme.all())
    for scheme in schemes:
        ssid = scheme.options.get('wpa-ssid', scheme.options.get('wireless-essid'))
        if ssid in ssids:
            show_message(INFO_007.format(ssid))
            scheme.activate()
            break

def publish_data():
    return 0

def connect_bluetooth():
    connection = obd.OBD() # auto-connects to USB or RF port
    while connection.status() != OBDStatus.CAR_CONNECTED:
        if connection.status() == OBDStatus.ELM_CONNECTED:
            show_message(INFO_001)
            time.sleep(10)
        connection = obd.OBD() # auto-connects to USB or RF port
        if connection.status() != OBDStatus.CAR_CONNECTED:
            show_message(ERROR_001)
            time.sleep(10)
            
        time.sleep(100)
    
    
    
def collect_data():
    cmd = obd.commands.SPEED # select an OBD command (sensor)  
    response = connection.query(cmd) # send the command, and parse the response    
    print(response.value) # returns unit-bearing values thanks to Pint
    print(response.value.to("mph")) # user-friendly unit conversions







def main():
    show_message(INFO_000)
    setup_wifi()
    publish_data()
    

main()