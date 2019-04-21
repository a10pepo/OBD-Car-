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
import csv
import os
from subprocess import check_output
import sys
import smbus
import math


# CONFIG PARAMS

OBD_RETRIES=1



# INFO MESSAGES
INFO_000="INFO: Starting Connection"
INFO_001="INFO: ELM Connected"
INFO_002="INFO: Searching Wifi"
INFO_003="INFO: Wifi {} Connected"
INFO_004="INFO: Retrieving unpublished data"
INFO_005="INFO: Publishing stored data"
INFO_006="INFO: Gathering Data"
INFO_007=""
INFO_008="INFO: CAR Connected on port {}"
INFO_009="INFO: Folder Created {}"
INFO_010="INFO: Connecting Wifi {}"



# ERROR MESSAGES
ERROR_001="ERROR: Connection not established with ELM"
ERROR_002="ERROR: Connection not established with Wifi (Storing data)"
ERROR_003="ERROR: Connection Lost OBD2"
ERROR_004="ERROR: Connection Lost Wifi"
ERROR_005="ERROR: Connection not established with CAR"
ERROR_006="ERROR: NOT Connected BYE"
ERROR_007="ERROR: Data Folder not created"
ERROR_008="ERROR: Telemetry Error: {}"


mode=0   # 0 Offline  1 Online
trip_timestamp=0
connection=None
# Register
power_mgmt_1 = 0x6b
power_mgmt_2 = 0x6c

bus = smbus.SMBus(1) # bus = smbus.SMBus(0) fuer Revision 1
address = 0x68       # via i2cdetect
        # Activate to be able to address the module
bus.write_byte_data(address, power_mgmt_1, 0)


#### HELPERS

def show_message(message):
    print(message)
    logging.info(message)


def scanForCells():
    # Scan using wlan0
    cells = Cell.all('wlan0')
    cells_dict={}
    # Loop over the available cells
    for cell in cells:
        if not cell.encrypted:
            cells_dict[cell.ssid]=cell.quality  
            scheme = Scheme.for_cell('wlan0', 'home', cell, passkey=None)
            print(INFO_010.format(cell.ssid))
    return cells

def read_byte(reg):
    return bus.read_byte_data(address, reg)
 
def read_word(reg):
    h = bus.read_byte_data(address, reg)
    l = bus.read_byte_data(address, reg+1)
    value = (h << 8) + l
    return value
 
def read_word_2c(reg):
    val = read_word(reg)
    if (val >= 0x8000):
        return -((65535 - val) + 1)
    else:
        return val
 
def dist(a,b):
    return math.sqrt((a*a)+(b*b))
 
def get_y_rotation(x,y,z):
    radians = math.atan2(x, dist(y,z))
    return -math.degrees(radians)
 
def get_x_rotation(x,y,z):
    radians = math.atan2(y, dist(x,z))
    return math.degrees(radians)

#### FUNCTIONS
    
def setup_wifi():
    show_message(INFO_002)
    # get all cells from the air    
    cells = scanForCells()
    host=check_output(['hostname', '-I'])
    wifi=check_output(['iwgetid'])
    logging.info("Connected to host: {}".format(host))
    logging.info("Connected to wifi: {}".format(wifi))
    if len(host)>4:
        show_message(INFO_003.format(wifi))
    else:       
        cells = scanForCells()
   

def publish_data(dict_data):
    with open(trip_timestamp+'.csv', 'w',newline='') as f:
        w = csv.DictWriter(f, dict_data.keys())
        w.writerow(dict_data)

def upload_previous():
    for filename in os.listdir("data"):
        if filename.endswith(".csv"):
            # upload f
            
            continue
        else:
            continue
    return 0

def connect_bluetooth():
    global connection
    retries = 0
    connection = obd.OBD() # auto-connects to USB or RF port 
    while ((connection.status() != OBDStatus.CAR_CONNECTED) and retries<OBD_RETRIES):
        if connection.status() == OBDStatus.ELM_CONNECTED:
            show_message(INFO_001)
            time.sleep(5)
        connection = obd.OBD() # auto-connects to USB or RF port
        if connection.status() != OBDStatus.CAR_CONNECTED:
            show_message(ERROR_005)
        time.sleep(5)
        print(retries)
        retries=retries+1

    if connection.status() != OBDStatus.CAR_CONNECTED:
        show_message(ERROR_005)
        ports = obd.scan_serial()# return list of valid USB or RF ports
        logging.info("Ports found:")
        logging.info(ports)
        for x in ports:
            connection = obd.OBD(x)
            if connection.status() == OBDStatus.CAR_CONNECTED:
                show_message(INFO_008.format(connection.port_name()))
                break
        show_message(ERROR_006)
        sys.exit(0)
    else:
        show_message(INFO_008.format(connection.port_name()))

def getgyroscope(): 
    gyroskop_xout = read_word_2c(0x43)
    gyroskop_yout = read_word_2c(0x45)
    gyroskop_zout = read_word_2c(0x47)
    acceleration_xout = read_word_2c(0x3b)
    acceleration_yout = read_word_2c(0x3d)
    acceleration_zout = read_word_2c(0x3f)
    return {'gyroskop_xout':gyroskop_xout,
            'gyroskop_yout':gyroskop_yout,
            'gyroskop_zout':gyroskop_zout,
            'acceleration_xout':acceleration_xout,
            'acceleration_yout':acceleration_yout,
            'acceleration_zout':acceleration_zout}
   
def collect_data():
    while True:
        try:
            payload_temp={}
            result_xyz=getgyroscope()
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
            payload_temp['gyroskop_x'] = result_xyz['gyroskop_xout']
            payload_temp['gyroskop_y'] = result_xyz['gyroskop_yout']
            payload_temp['gyroskop_z'] = result_xyz['gyroskop_zout']
            payload_temp['gyroskop_x_scaled'] = result_xyz['gyroskop_xout'] / 131
            payload_temp['gyroskop_y_scaled'] = result_xyz['gyroskop_yout'] / 131
            payload_temp['gyroskop_z_scaled'] = result_xyz['gyroskop_zout'] / 131
            payload_temp['acceleration_x'] = result_xyz['acceleration_xout']
            payload_temp['acceleration_y'] = result_xyz['acceleration_yout']
            payload_temp['acceleration_z'] = result_xyz['acceleration_zout']
            payload_temp['acceleration_x_scaled'] = result_xyz['acceleration_xout'] / 16384.0
            payload_temp['acceleration_y_scaled'] = result_xyz['acceleration_yout'] / 16384.0
            payload_temp['acceleration_z_scaled'] = result_xyz['acceleration_zout'] / 16384.0
            payload_temp['capturetime']=str(datetime.datetime.now())
            publish_data(payload_temp)
        except Exception as error:
            logging.info(str(error))
            show_message(ERROR_008.format(str(error)))

def query_value(cmd,field):   
    response = connection.query(cmd) # send the command, and parse the response    
    if field == "":
        return response.value
    else:
        return response.value.to(field) 


def init_setup():
    try:
        if not os.path.exists("data"):
            os.mkdir("data")
    except OSError:  
        show_message(ERROR_007)
    else:  
        show_message(INFO_009.format("data"))

def main():
    global trip_timestamp
    logging.basicConfig(filename='car_log.log', level=logging.INFO)
    trip_timestamp=datetime.datetime.now()
    show_message(INFO_000)
    init_setup()
    setup_wifi()
    connect_bluetooth()
    upload_previous()
    collect_data()
    

main()