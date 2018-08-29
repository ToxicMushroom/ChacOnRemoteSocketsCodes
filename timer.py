from rpi_rf import RFDevice
import astral
import config
import datetime
import mysql.connector
import sched
import time
import re

scheduler = sched.scheduler(time.time, time.sleep)  # loop setup
 # enable transmission
def mainloop(sc):
    # Begin
    connection = mysql.connector.connect(
        host=config.host,
        user=config.user,
        passwd=config.passwd,
        database=config.database
    )

    rfdevice = RFDevice(17)  # radio sender setup
    rfdevice.enable_tx() 

    sun = astral.Location(("Brussels", "Belgium", 51.02261, 4.54714, "Europe/Brussels", 0)).sun(
        datetime.datetime.today().date(), True)
    sunrise = int(str(sun["sunrise"])[11:13]) * 3600 \
              + int(str(sun["sunrise"])[14:16]) * 60 \
              + int(str(sun["sunrise"])[17:19])  # turn full sunrise datetime into sunrise seconds since midnight
    sunset = int(str(sun["sunset"])[11:13]) * 3600 \
             + int(str(sun["sunset"])[14:16]) * 60 \
             + int(str(sun["sunset"])[17:19]) - 1800# same here (-1800 Is 30 minutes less because I want my lights on before it is dark outside)

    weekday = datetime.datetime.today().weekday() + 1  # Check what day of the week it is mon= 1, tue= 2, wed= 3, ...
    cursor = connection.cursor()  # Mysql cursor

    cursor.execute("SELECT * FROM chacon_info")  # Execute information query
    result = cursor.fetchall()  # Fetch all data

    print(sunset);
    print(str(datetime.datetime.now())[11:19]);
    for row in result:  # loop thru all results
        if row[4] == 1:  # If trigger enabled continue
            #  has come
            now = datetime.datetime.now()
            seconds_since_midnight = (now - now.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
            if row[3] == "sunrise":  # Replace the sunrise placeholder with the current sunrise time
                if str(weekday) in row[2] and seconds_since_midnight + 30 > sunrise > seconds_since_midnight - 30:
                    for code in re.split(",", row[1]):
                        rfdevice.tx_code(int(code), 1, 430)
                        print(code);
            elif row[3] == "sunset":  # same here
                if str(weekday) in row[2] and seconds_since_midnight + 30 > sunset > seconds_since_midnight - 30:
                    for code in re.split(",", row[1]):
                        rfdevice.tx_code(int(code), 1, 430)
                        print(code);
            else:
                if str(weekday) in row[2] and seconds_since_midnight + 30 > int(row[3]) > seconds_since_midnight - 30:
                    for code in re.split(",", row[1]):
                        rfdevice.tx_code(int(code), 1, 430)  # code, protocol, pulselength
                        print(code);

    scheduler.enter(20, 1, mainloop, (sc,))  # rescheduled 20 seconds from now


scheduler.enter(1, 1, mainloop, (scheduler,))  # scheduled 1 second from now
scheduler.run()  # start scheduler
