import astral
import config
import datetime
import mysql.connector
import sched
import time
import re
from rpi_rf import RFDevice

connection = mysql.connector.connect(
    host=config.host,
    user=config.user,
    passwd=config.passwd,
    database=config.database
)

scheduler = sched.scheduler(time.time, time.sleep)  # loop setup
rfdevice = RFDevice(17)  # radio sender setup
rfdevice.enable_tx()  # enable transmission


def mainloop(sc):
    # Begin
    sun = astral.Location(("Brussels", "Belgium", 51.02261, 4.54714, "Europe/Brussels", 0)).sun(
        datetime.datetime.today().date(), True)
    sunrise = int(str(sun["sunrise"])[11:13]) * 3600 \
              + int(str(sun["sunrise"])[14:16]) * 60 \
              + int(str(sun["sunrise"])[17:19])  # turn full sunrise datetime into sunrise seconds since midnight
    sunset = int(str(sun["sunset"])[11:13]) * 3600 \
             + int(str(sun["sunset"])[14:16]) * 60 \
             + int(str(sun["sunset"])[17:19])  # same here

    weekday = datetime.datetime.today().weekday() + 1  # Check what day of the week it is mon= 1, tue= 2, wed= 3, ...
    cursor = connection.cursor()  # Mysql cursor

    cursor.execute("SELECT * FROM chacon_info")  # Execute information query
    result = cursor.fetchall()  # Fetch all data
    for row1 in result:  # loop thru all results
        if row1[2] == 1:  # If trigger enabled continue
            cursor.execute("SELECT * FROM chacon_times WHERE triggerId= " + row1[0])  # execute more info query
            result = cursor.fetchall()  # Fetch more information about timings
            for row2 in result:  # Lets go through all enabled rows in chacon_times to check if the time for execution
                #  has come
                if row2 == "sunrise":  # Replace the sunrise placeholder with the current sunrise time
                    row2 = sunrise
                elif row2 == "sunset":  # same here
                    row2 = sunset

                now = datetime.datetime.now()
                seconds_since_midnight = (now - now.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
                if str(weekday) in row2[1] and seconds_since_midnight + 30 > int(row1[2]) > seconds_since_midnight - 30:
                    for code in re.split(", ", row1[1]):
                        rfdevice.tx_code(code, 1, 430)  # code, protocol, pulselength

    scheduler.enter(20, 1, mainloop, (sc,))  # rescheduled 20 seconds from now


scheduler.enter(1, 1, mainloop, (scheduler,))  # scheduled 1 second from now
scheduler.run()  # start scheduler
