import astral
import config
import datetime
import mysql.connector
import sched
import time

connection = mysql.connector.connect(
    host=config.host,
    user=config.user,
    passwd=config.passwd,
    database=config.database
)

scheduler = sched.scheduler(time.time, time.sleep)
weekday = datetime.datetime.today().weekday() + 1



def mainloop(sc):
    # Begin
    sun = astral.Location(("Brussels", "Belgium", 51.02261, 4.54714, "Europe/Brussels", 0)).sun(datetime.datetime.today().date(), True)
    sunrise = str(sun["sunrise"])[11:19]
    sunset = str(sun["sunset"])[11:19]
    print(sunrise + " - " + sunset)
    weekday = datetime.datetime.today().weekday() + 1
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM chacon_info")
    result = cursor.fetchall()
    for row1 in result:
        if row1[2] == 1:  # If trigger enabled continue
            cursor.execute("SELECT * FROM chacon_times WHERE triggerId= " + row1[0])
            result = cursor.fetchall()  # Get more information about timings
            for row2 in result:

                if str(weekday) in row2[1] and row1[2]:
                    print("It's time to die")

    # End
    scheduler.enter(20, 1, mainloop, (sc,))


scheduler.enter(1, 1, mainloop, (scheduler,))
scheduler.run()
