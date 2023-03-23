from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import reverse
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from datetime import datetime, timedelta, timezone, time
import os.path
from dotenv import load_dotenv, find_dotenv
from zoneinfo import ZoneInfo
from dateutil.parser import parse
from urllib.parse import urlencode, quote_plus
import pytz

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .forms import ChooseTreatmentsForm, ChooseTreatmentsFormSet


# load the .env file
load_dotenv(find_dotenv())

# set timezone, since google api wants timezone offset in dateTime fields in json
cdmx = ZoneInfo("America/Mexico_City")

# set up the calendarId fron the .env file
cid = os.getenv("CALENDAR_ID")

# link up to credentials.json necessary to get token.json file and oauth to Google API
cred_file = "./credentials.json"

# this sets up the SCOPES for the Calendar API
# If modifying these scopes, delete the file token.json, which triggers new oauth login.
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
]


def setup_service():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            flow = InstalledAppFlow.from_client_secrets_file(cred_file, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    service = build("calendar", "v3", credentials=creds)
    return service


def setup(request):
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            flow = InstalledAppFlow.from_client_secrets_file(cred_file, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("calendar", "v3", credentials=creds)
        return HttpResponse("Successfully authenticated at Google API")

    except HttpError as error:
        print("An error occurred: %s" % error)
        return HttpResponse("An error occurred: %s" % error)


def calendarview(request):
    service = setup_service()
    timeMin = datetime.now().astimezone(cdmx)
    timeMin_iso = timeMin.isoformat()
    timeMax = timeMin + timedelta(days=7)
    timeMax_iso = timeMax.isoformat()

    day_start = datetime.strptime("08:00", "%H:%M")
    day_end = datetime.strptime("18:00", "%H:%M")

    slot_duration = timedelta(minutes=15)

    events_results = (
        service.events()
        .list(
            calendarId=cid,
            timeMax=timeMax_iso,
            timeMin=timeMin_iso,
        )
        .execute()
    )
    events = events_results.get("items", [])
    if not events:
        event_list = []
        return HttpResponse(event_list)

    # print(events)

    # prepare blocked slots according to data fetched from calendar API
    blocked_slots = []
    for event in events:
        slot_start = parse(event["start"]["dateTime"])
        slot_end = parse(event["end"]["dateTime"])
        curr_slot = slot_start
        while curr_slot < slot_end:
            curr_slot = curr_slot.replace(tzinfo=cdmx)
            tmp = [curr_slot, ["blocked", curr_slot, curr_slot + slot_duration, 0]]
            blocked_slots.append(tmp)
            curr_slot += slot_duration

    for slot in blocked_slots:
        slot[1][3] = blocked_slots.count(slot)

    # prepare all possible slots for the next seven days
    slots = {}
    for day in range(0, 8):
        curr_day_start = timeMin.date() + timedelta(days=day)

        curr_slot = datetime.combine(curr_day_start, day_start.time())
        curr_slot = curr_slot.replace(tzinfo=cdmx)

        curr_day_end = datetime.combine(curr_day_start, day_end.time())
        curr_day_end = curr_day_end.replace(tzinfo=cdmx)

        slots[curr_day_start] = []

        while curr_slot < curr_day_end:
            curr_slot = curr_slot.replace(tzinfo=cdmx)
            tmp = [curr_slot, ["available", curr_slot, curr_slot + slot_duration, 0]]
            slots[curr_day_start].append(tmp)
            curr_slot += slot_duration

    # consolidate blocked_slots and slots into result
    for bslot in blocked_slots:
        if bslot[1][3] >= 2:
            for oslot in slots[bslot[0].date()]:
                if bslot[0] == oslot[0]:
                    # print(f"found! {oslot[0]}")
                    oslot[1][1] = "blocked"

    return render(request, "appointment/calendarview.html", {"slots": slots})


"""
def calendarview(request):
    service = setup_service()
    timeMin = datetime.now().astimezone(cdmx)
    timeMin_iso = timeMin.isoformat()
    timeMax = timeMin + timedelta(days=7)
    timeMax_iso = timeMax.isoformat()

    day_start = datetime.strptime("08:00", "%H:%M")
    day_end = datetime.strptime("16:00", "%H:%M")

    events_results = (
        service.events()
        .list(
            calendarId=cid,
            timeMax=timeMax_iso,
            timeMin=timeMin_iso,
        )
        .execute()
    )
    events = events_results.get("items", [])
    if not events:
        event_list = []
        return HttpResponse(event_list)

    """
"""
    event_list = []
    for day in range(0, 8):
        date = (timeMin + timedelta(days=day)).date()
        tmp = []
        for e in events:
            if parse(e["start"]["dateTime"]).date() == date:
                start = datetime.strptime(e["start"]["dateTime"], "%Y-%m-%dT%H:%M:%S%z")
                end = datetime.strptime(e["end"]["dateTime"], "%Y-%m-%dT%H:%M:%S%z")
                tz_start = pytz.FixedOffset(start.utcoffset().total_seconds() // 60)
                tz_end = pytz.FixedOffset(end.utcoffset().total_seconds() // 60)
                start = start.replace(tzinfo=tz_start)
                end = end.replace(tzinfo=tz_end)
                tmp.append(["blocked", start, end])
                # events.pop(e)
        event_list.append({date: tmp})
"""
"""
    event_list = []
    slot_size = 15  # slot size in minutes
    for day in range(0, 8):
        date = (timeMin + timedelta(days=day)).date()
        tmp = []
        for e in events:
            if parse(e["start"]["dateTime"]).date() == date:
                start = datetime.strptime(e["start"]["dateTime"], "%Y-%m-%dT%H:%M:%S%z")
                end = datetime.strptime(e["end"]["dateTime"], "%Y-%m-%dT%H:%M:%S%z")
                tz_start = pytz.FixedOffset(start.utcoffset().total_seconds() // 60)
                tz_end = pytz.FixedOffset(end.utcoffset().total_seconds() // 60)
                start = start.replace(tzinfo=tz_start)
                end = end.replace(tzinfo=tz_end)

                # split up existing appointments into 15 minutes slots.
                slots = []
                curr_slot_start = start

                while curr_slot_start < end:
                    curr_slot_end = curr_slot_start + timedelta(minutes=slot_size)
                    slots.append(["blocked", curr_slot_start, curr_slot_end])
                    curr_slot_start = curr_slot_end
                tmp.extend(slots)
        event_list.append({date: tmp})

    # print(event_list)

    # Define the start and end times of your schedule

    start_time = time(hour=9, minute=0, tzinfo=pytz.FixedOffset(-360))
    end_time = time(hour=17, minute=0, tzinfo=pytz.FixedOffset(-360))

    # Define the duration of each time slot
    duration = timedelta(minutes=15)

    # Define the number of clients you can serve at the same time
    num_clients = 2

    # Loop through each day in event_list
    for day in event_list:
        date = list(day.keys())[0]
        events = day[date]
        start_datetime = datetime.combine(date, start_time)
        end_datetime = datetime.combine(date, end_time)

        # Add two available slots at the beginning of the day if there are no events yet
        if not events:
            for i in range(num_clients):
                slot_start = start_datetime + i * duration
                slot_end = slot_start + duration
                events.append(["available", slot_start, slot_end])

        # Add one available slot at the beginning of the day if there is only one event
        elif len(events) == 1:
            first_event = events[0]
            if first_event[1] > start_datetime:
                for i in range(num_clients):
                    slot_start = start_datetime + i * duration
                    slot_end = slot_start + duration
                    events.insert(0, ["available", slot_start, slot_end])

        # Add available slots in between events if there is room for them
        for i in range(len(events) - 1):
            current_event = events[i]
            next_event = events[i + 1]
            if next_event[1] - current_event[2] >= duration:
                for j in range(num_clients):
                    slot_start = current_event[2] + j * duration
                    slot_end = slot_start + duration
                    events.insert(i + 1, ["available", slot_start, slot_end])

        # Add one available slot at the end of the day if there is only one event
        if len(events) == 1:
            last_event = events[0]
            if last_event[2] < end_datetime:
                for i in range(num_clients):
                    slot_start = last_event[2] + i * duration
                    slot_end = slot_start + duration
                    events.append(["available", slot_start, slot_end])

        # Add two available slots at the end of the day if there are no events yet
        elif not events[-1]:
            for i in range(num_clients):
                slot_start = end_datetime - (num_clients - i) * duration
                slot_end = slot_start + duration
                events[-1] = ["available", slot_start, slot_end]
                events.append(["available", slot_end, end_datetime])

    return render(request, "appointment/calendarview.html", {"event_list": event_list})
"""


def choose_treatments(request):
    if request.method == "POST":
        form = ChooseTreatmentsForm(request.POST)
        if form.is_valid():
            treatments = []
            for field_name, value in form.cleaned_data.items():
                if value:
                    treatments.append([value.name, value.price, value.duration])
            selection = {"treatments": treatments}

            print(selection)
            selection = urlencode(selection, quote_via=quote_plus)
            return redirect(reverse("calendarview"), selection)
    else:
        form = ChooseTreatmentsForm()
    return render(request, "appointment/choose_treatments.html", {"form": form})


def add_choose_treatment(request):
    form = ChooseTreatmentsForm()
    html = render_to_string("appointment/add_choose_treatment.html", {"form": form})
    return HttpResponse(html)
