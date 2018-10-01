#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import re
import sys
from datetime import datetime, timedelta, time, date
import icalendar
from hashlib import sha256
import time


# IMPORTANT! Replace this with a freshly-generated UUID!
PROGR_UUID = "8DC7A5B6-6CD4-401B-9852-D6ABF7537B41"


# Define holiday dates here, format "YYYY-MM-DD" (e.g. "2018-12-25")
HOLIDAYS = ["2018-11-01",
            "2018-11-02",
            "2018-11-05",
            "2018-11-06",
            "2018-11-07",
            "2018-11-10",
            "2018-12-07",
            "2018-12-08",
            "2018-12-09",
            "2019-04-15",
            "2019-04-16",
            "2019-04-17",
            "2019-04-18",
            "2019-04-19",
            "2019-04-22",
            "2019-04-23",
            "2019-04-24",
            "2019-04-25",
            "2019-04-26",
            "2019-05-01"]



REGEX_LESSON_NAME = r"([0-9]{6}) - (.*?)(?:  \(Docente: .*\)|$)"
REGEX_LESSON_DATES = r"Semestre: ([1-2]) Inizio lezioni: ([0-9]{2}\/[0-9]{2}\/[0-9]{4}) Fine lezioni: ([0-9]{2}\/[0-9]{2}\/[0-9]{4})"
REGEX_LESSON_DATA = r"(Lunedì|Martedì|Mercoledì|Giovedì|Venerdì|Sabato) dalle ([0-9]{2}:[0-9]{2}) alle ([0-9]{2}:[0-9]{2}), (.*?) (?:in|Aula)"
REGEX_LESSON_ROOM_TEST = r".*? Aula al momento non disponibile.*"
REGEX_LESSON_ROOM = r"in aula (.*?) \(.*? - .*? - (.*?) - .*"
REGEX_NO_LESSON_TEST = r"Nessun orario definito"
WEEKDAYS = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato"]


def capitalize(string):
    string = string.decode("utf-8")
    result = []
    for x in string.split(" "):
        if (x.lower() in ("e", "dei", "del", "della", "dello", "ed", "al", "a",
                          "ai", "ex", "degli", "delle", "di", "da", "in",
                          "con", "su", "per", "tra", "fra", "lo", "la", "il",
                          "gli", "le", "con", "senza", "un", "una", "uno")):
            result.append(x.lower())
        elif (x.lower().startswith("dell'")):
            result.append("dell'" + x[5:].title())
        elif (x.lower().startswith("l'")):
            result.append("l'" + x[2:].title())
        else:
            result.append(x.title())
    return (" ".join(result)).encode("utf-8")


output = []

text = sys.stdin.read().replace('\r', '')
courses = [x.strip() for x in text.split("\n\n\n")]
for course in courses:
    lines = course.split("\n")
    cod, name = re.findall(REGEX_LESSON_NAME, lines[0])[0]
    name = capitalize(name.strip())
    sem, from_str, to_str = re.findall(REGEX_LESSON_DATES, lines[1])[0]
    from_date = datetime.strptime(from_str, "%d/%m/%Y").date()
    to_date = (datetime.strptime(to_str, "%d/%m/%Y") + timedelta(days=1)).date()
    for line in lines[3:]:
        if re.match(REGEX_NO_LESSON_TEST, line):
            break
        dow, st, et, typ = re.findall(REGEX_LESSON_DATA, line)[0]
        if not re.match(REGEX_LESSON_ROOM_TEST, line):
            rm, bld = re.findall(REGEX_LESSON_ROOM, line)[0]
            location = "{} Aula {}".format(bld, rm)
        else:
            location = ""
        start_time = datetime.strptime(st, "%H:%M").time()
        end_time = datetime.strptime(et, "%H:%M").time()
        lesson_type = typ.strip()
        al_fr_date = from_date
        while al_fr_date.weekday() != WEEKDAYS.index(dow):
            al_fr_date += timedelta(days=1)
        uid_seed = "{}:{}:{}:{}:{}".format(
            cod,
            sem,
            datetime.strftime(al_fr_date, "%Y%m%d"),
            datetime.strftime(
                datetime.combine(datetime.now().date(), start_time),
                "%H%M"),
            PROGR_UUID)
        uid = sha256(uid_seed.encode()).hexdigest() + "@polimi.it"
        output.append({"name": name,
                       "from": al_fr_date,
                       "to": to_date,
                       "start": start_time,
                       "end": end_time,
                       "type": lesson_type,
                       "location": location,
                       "uid": uid})

cal = icalendar.Calendar()
cal.add("prodid", "Jacopo Jannone")
sequence = str(int(time.time() * 1000000))
last_upd_str = datetime.strftime(
    datetime.now(),
    "Generato il %d/%m/%Y alle %H:%M:%S")
last_upd = "{}\nID versione: {}".format(last_upd_str, sequence)
for element in output:
    event = icalendar.Event()
    start = datetime.combine(element["from"], element["start"])
    duration = (datetime.combine(date.min, element["end"])
                - datetime.combine(date.min, element["start"]))
    repeat = {"freq": "weekly", "until": element["to"]}
    skip_dates = [datetime.strptime(x, "%Y-%m-%d") for x in HOLIDAYS]
    skip_datetimes = [datetime.combine(x, element["start"]) for x in skip_dates]
    event.add("summary", "{} ({})".format(element["name"], element["type"]))
    event.add("location", element["location"])
    event.add("dtstart", start)
    event.add("duration", duration)
    event.add("uid", element["uid"])
    event.add("rrule", repeat)
    event.add("sequence", sequence)
    event.add("description", last_upd)
    event.add("exdate", skip_datetimes)
    cal.add_component(event)
calendar = cal.to_ical()

print calendar
