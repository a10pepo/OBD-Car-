# -*- coding: utf-8 -*-
"""
Created on Thu Apr 18 09:13:43 2019

@author: PONO
"""

from wifi import Cell, Scheme
import obd
from obd import OBDStatus
import datetime
import time
import logging
import json
import csv
import os

# INFO MESSAGES
INFO_000="INFO: Starting Connection"
INFO_001="INFO: ELM Connected"
INFO_002="INFO: Searching Wifi"
INFO_003="INFO: Wifi {} Connected"
INFO_004="INFO: Retrieving unpublished data"
INFO_005="INFO: Publishing stored data"
INFO_006="INFO: Gathering Data"
INFO_007="INFO: Connecting to Wifi {}"
INFO_008="INFO: CAR Connected on port {}"
INFO_009="INFO: Folder Created"



# ERROR MESSAGES
ERROR_001="ERROR: Connection not established with ELM"
ERROR_002="ERROR: Connection not established with Wifi (Storing data)"
ERROR_003="ERROR: Connection Lost OBD2"
ERROR_004="ERROR: Connection Lost Wifi"
ERROR_005="ERROR: Connection not established with CAR"
ERROR_006="ERROR: NOT Connected BYE"
ERROR_007="ERROR: Data Folder not created"


mode=0   # 0 Offline  1 Online
trip_timestamp=0

def show_message(message):
    print(message)
    logging.info(message)


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

def publish_data(dict_data):
    with open(trip_timestamp+'.csv', 'w',newline='') as f:
        w = csv.DictWriter(f, dict_data.keys())
        w.writerow(dict_data)

def upload_previous():

def connect_bluetooth():
    global connection
    retries = 0
    connection = obd.OBD() # auto-connects to USB or RF port
    while ((connection.status() != OBDStatus.CAR_CONNECTED) & retries<5):
        if connection.status() == OBDStatus.ELM_CONNECTED:
            show_message(INFO_001)
            time.sleep(10)
        connection = obd.OBD() # auto-connects to USB or RF port
        if connection.status() != OBDStatus.CAR_CONNECTED:
            show_message(ERROR_005)
            time.sleep(10)
        time.sleep(100)
        retries=retries+1
    
    if connection.status() != OBDStatus.CAR_CONNECTED:
        show_message(ERROR_005)       
        ports = obd.scan_serial()      # return list of valid USB or RF ports
        for x in range(0,3):
            connection = obd.OBD(ports[x])
            if connection.status() == OBDStatus.CAR_CONNECTED:
                show_message(INFO_008.format(connection.port_name()))
                break
        show_message(INFO_006)
    else:
        show_message(INFO_008.format(connection.port_name()))
    
def collect_data():
    payload_temp={}
    payload_temp['PIDS_A']=query_value(obd.commands.PIDS_A,"")
    payload_temp['STATUS']=query_value(obd.commands.STATUS,"")
    payload_temp['FREEZE_DTC']=query_value(obd.commands.FREEZE_DTC,"")
    payload_temp['FUEL_STATUS']=query_value(obd.commands.FUEL_STATUS,"")
    payload_temp['ENGINE_LOAD']=query_value(obd.commands.ENGINE_LOAD,"")
    payload_temp['COOLANT_TEMP']=query_value(obd.commands.COOLANT_TEMP,"")
    payload_temp['SHORT_FUEL_TRIM_1']=query_value(obd.commands.SHORT_FUEL_TRIM_1,"")
    payload_temp['LONG_FUEL_TRIM_1']=query_value(obd.commands.LONG_FUEL_TRIM_1,"")
    payload_temp['SHORT_FUEL_TRIM_2']=query_value(obd.commands.SHORT_FUEL_TRIM_2,"")
    payload_temp['LONG_FUEL_TRIM_2']=query_value(obd.commands.LONG_FUEL_TRIM_2,"")
    payload_temp['FUEL_PRESSURE']=query_value(obd.commands.FUEL_PRESSURE,"")
    payload_temp['INTAKE_PRESSURE']=query_value(obd.commands.INTAKE_PRESSURE,"")
    payload_temp['RPM']=query_value(obd.commands.RPM,"")
    payload_temp['SPEED']=query_value(obd.commands.SPEED,"")
    payload_temp['TIMING_ADVANCE']=query_value(obd.commands.TIMING_ADVANCE,"")
    payload_temp['INTAKE_TEMP']=query_value(obd.commands.INTAKE_TEMP,"")
    payload_temp['MAF']=query_value(obd.commands.MAF,"")
    payload_temp['THROTTLE_POS']=query_value(obd.commands.THROTTLE_POS,"")
    payload_temp['AIR_STATUS']=query_value(obd.commands.AIR_STATUS,"")
    payload_temp['O2_SENSORS']=query_value(obd.commands.O2_SENSORS,"")
    payload_temp['O2_B1S1']=query_value(obd.commands.O2_B1S1,"")
    payload_temp['O2_B1S2']=query_value(obd.commands.O2_B1S2,"")
    payload_temp['O2_B1S3']=query_value(obd.commands.O2_B1S3,"")
    payload_temp['O2_B1S4']=query_value(obd.commands.O2_B1S4,"")
    payload_temp['O2_B2S1']=query_value(obd.commands.O2_B2S1,"")
    payload_temp['O2_B2S2']=query_value(obd.commands.O2_B2S2,"")
    payload_temp['O2_B2S3']=query_value(obd.commands.O2_B2S3,"")
    payload_temp['O2_B2S4']=query_value(obd.commands.O2_B2S4,"")
    payload_temp['OBD_COMPLIANCE']=query_value(obd.commands.OBD_COMPLIANCE,"")
    payload_temp['O2_SENSORS_ALT']=query_value(obd.commands.O2_SENSORS_ALT,"")
    payload_temp['AUX_INPUT_STATUS']=query_value(obd.commands.AUX_INPUT_STATUS,"")
    payload_temp['RUN_TIME']=query_value(obd.commands.RUN_TIME,"")
    payload_temp['PIDS_B']=query_value(obd.commands.PIDS_B,"")
    payload_temp['DISTANCE_W_MIL']=query_value(obd.commands.DISTANCE_W_MIL,"")
    payload_temp['FUEL_RAIL_PRESSURE_VAC']=query_value(obd.commands.FUEL_RAIL_PRESSURE_VAC,"")
    payload_temp['FUEL_RAIL_PRESSURE_DIRECT']=query_value(obd.commands.FUEL_RAIL_PRESSURE_DIRECT,"")
    payload_temp['O2_S1_WR_VOLTAGE']=query_value(obd.commands.O2_S1_WR_VOLTAGE,"")
    payload_temp['O2_S2_WR_VOLTAGE']=query_value(obd.commands.O2_S2_WR_VOLTAGE,"")
    payload_temp['O2_S3_WR_VOLTAGE']=query_value(obd.commands.O2_S3_WR_VOLTAGE,"")
    payload_temp['O2_S4_WR_VOLTAGE']=query_value(obd.commands.O2_S4_WR_VOLTAGE,"")
    payload_temp['O2_S5_WR_VOLTAGE']=query_value(obd.commands.O2_S5_WR_VOLTAGE,"")
    payload_temp['O2_S6_WR_VOLTAGE']=query_value(obd.commands.O2_S6_WR_VOLTAGE,"")
    payload_temp['O2_S7_WR_VOLTAGE']=query_value(obd.commands.O2_S7_WR_VOLTAGE,"")
    payload_temp['O2_S8_WR_VOLTAGE']=query_value(obd.commands.O2_S8_WR_VOLTAGE,"")
    payload_temp['COMMANDED_EGR']=query_value(obd.commands.COMMANDED_EGR,"")
    payload_temp['EGR_ERROR']=query_value(obd.commands.EGR_ERROR,"")
    payload_temp['EVAPORATIVE_PURGE']=query_value(obd.commands.EVAPORATIVE_PURGE,"")
    payload_temp['FUEL_LEVEL']=query_value(obd.commands.FUEL_LEVEL,"")
    payload_temp['WARMUPS_SINCE_DTC_CLEAR']=query_value(obd.commands.WARMUPS_SINCE_DTC_CLEAR,"")
    payload_temp['DISTANCE_SINCE_DTC_CLEAR']=query_value(obd.commands.DISTANCE_SINCE_DTC_CLEAR,"")
    payload_temp['EVAP_VAPOR_PRESSURE']=query_value(obd.commands.EVAP_VAPOR_PRESSURE,"")
    payload_temp['BAROMETRIC_PRESSURE']=query_value(obd.commands.BAROMETRIC_PRESSURE,"")
    payload_temp['O2_S1_WR_CURRENT']=query_value(obd.commands.O2_S1_WR_CURRENT,"")
    payload_temp['O2_S2_WR_CURRENT']=query_value(obd.commands.O2_S2_WR_CURRENT,"")
    payload_temp['O2_S3_WR_CURRENT']=query_value(obd.commands.O2_S3_WR_CURRENT,"")
    payload_temp['O2_S4_WR_CURRENT']=query_value(obd.commands.O2_S4_WR_CURRENT,"")
    payload_temp['O2_S5_WR_CURRENT']=query_value(obd.commands.O2_S5_WR_CURRENT,"")
    payload_temp['O2_S6_WR_CURRENT']=query_value(obd.commands.O2_S6_WR_CURRENT,"")
    payload_temp['O2_S7_WR_CURRENT']=query_value(obd.commands.O2_S7_WR_CURRENT,"")
    payload_temp['O2_S8_WR_CURRENT']=query_value(obd.commands.O2_S8_WR_CURRENT,"")
    payload_temp['CATALYST_TEMP_B1S1']=query_value(obd.commands.CATALYST_TEMP_B1S1,"")
    payload_temp['CATALYST_TEMP_B2S1']=query_value(obd.commands.CATALYST_TEMP_B2S1,"")
    payload_temp['CATALYST_TEMP_B1S2']=query_value(obd.commands.CATALYST_TEMP_B1S2,"")
    payload_temp['CATALYST_TEMP_B2S2']=query_value(obd.commands.CATALYST_TEMP_B2S2,"")
    payload_temp['PIDS_C']=query_value(obd.commands.PIDS_C,"")
    payload_temp['STATUS_DRIVE_CYCLE']=query_value(obd.commands.STATUS_DRIVE_CYCLE,"")
    payload_temp['CONTROL_MODULE_VOLTAGE']=query_value(obd.commands.CONTROL_MODULE_VOLTAGE,"")
    payload_temp['ABSOLUTE_LOAD']=query_value(obd.commands.ABSOLUTE_LOAD,"")
    payload_temp['COMMANDED_EQUIV_RATIO']=query_value(obd.commands.COMMANDED_EQUIV_RATIO,"")
    payload_temp['RELATIVE_THROTTLE_POS']=query_value(obd.commands.RELATIVE_THROTTLE_POS,"")
    payload_temp['AMBIANT_AIR_TEMP']=query_value(obd.commands.AMBIANT_AIR_TEMP,"")
    payload_temp['THROTTLE_POS_B']=query_value(obd.commands.THROTTLE_POS_B,"")
    payload_temp['THROTTLE_POS_C']=query_value(obd.commands.THROTTLE_POS_C,"")
    payload_temp['ACCELERATOR_POS_D']=query_value(obd.commands.ACCELERATOR_POS_D,"")
    payload_temp['ACCELERATOR_POS_E']=query_value(obd.commands.ACCELERATOR_POS_E,"")
    payload_temp['ACCELERATOR_POS_F']=query_value(obd.commands.ACCELERATOR_POS_F,"")
    payload_temp['THROTTLE_ACTUATOR']=query_value(obd.commands.THROTTLE_ACTUATOR,"")
    payload_temp['RUN_TIME_MIL']=query_value(obd.commands.RUN_TIME_MIL,"")
    payload_temp['TIME_SINCE_DTC_CLEARED']=query_value(obd.commands.TIME_SINCE_DTC_CLEARED,"")
    payload_temp['MAX_MAF']=query_value(obd.commands.MAX_MAF,"")
    payload_temp['FUEL_TYPE']=query_value(obd.commands.FUEL_TYPE,"")
    payload_temp['ETHANOL_PERCENT']=query_value(obd.commands.ETHANOL_PERCENT,"")
    payload_temp['EVAP_VAPOR_PRESSURE_ABS']=query_value(obd.commands.EVAP_VAPOR_PRESSURE_ABS,"")
    payload_temp['EVAP_VAPOR_PRESSURE_ALT']=query_value(obd.commands.EVAP_VAPOR_PRESSURE_ALT,"")
    payload_temp['SHORT_O2_TRIM_B1']=query_value(obd.commands.SHORT_O2_TRIM_B1,"")
    payload_temp['LONG_O2_TRIM_B1']=query_value(obd.commands.LONG_O2_TRIM_B1,"")
    payload_temp['SHORT_O2_TRIM_B2']=query_value(obd.commands.SHORT_O2_TRIM_B2,"")
    payload_temp['LONG_O2_TRIM_B2']=query_value(obd.commands.LONG_O2_TRIM_B2,"")
    payload_temp['FUEL_RAIL_PRESSURE_ABS']=query_value(obd.commands.FUEL_RAIL_PRESSURE_ABS,"")
    payload_temp['RELATIVE_ACCEL_POS']=query_value(obd.commands.RELATIVE_ACCEL_POS,"")
    payload_temp['HYBRID_BATTERY_REMAINING']=query_value(obd.commands.HYBRID_BATTERY_REMAINING,"")
    payload_temp['OIL_TEMP']=query_value(obd.commands.OIL_TEMP,"")
    payload_temp['FUEL_INJECT_TIMING']=query_value(obd.commands.FUEL_INJECT_TIMING,"")
    payload_temp['FUEL_RATE']=query_value(obd.commands.FUEL_RATE,"")
    publish_data(payload_temp)



def query_value(cmd,field):   
    response = connection.query(cmd) # send the command, and parse the response    
    if field == "":
        return response.value
    else:
        return response.value.to(field) 


def init_setup():
    try:  
        os.mkdir("data")
    except OSError:  
        show_message(ERROR_007)
    else:  
        show_message(INFO_009)

def main():
    global trip_timestamp
    logging.basicConfig(filename='car_log.log', level=logging.INFO)
    trip_timestamp=datetime.datetime.now()
    show_message(INFO_000)
    init_setup()
    setup_wifi()
    upload_previous()
    collect_data()
    

main()