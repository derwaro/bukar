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
from urllib.parse import urlencode, quote_plus, parse_qs
import pytz
import json

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
    timeMax = timeMin + timedelta(days=2)
    timeMax_iso = timeMax.isoformat()

    day_start = datetime.strptime("08:00", "%H:%M")
    day_end = datetime.strptime("16:00", "%H:%M")

    slot_duration = timedelta(minutes=30)

    # retrieve the selected treatments from the session and parse them into a dictionary
    # for example:
    # {'t0': ["['Lipo Sin Bisturi', 325, datetime.timedelta(seconds=1800)]"]}
    selection = json.loads(request.session.get("selection", {}))
    print(selection)

    # retrieve calender from google calendar api
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
        curr_day = curr_day_start.strftime("%Y-%m-%d")
        slots[curr_day] = {}

        curr_slot = datetime.combine(curr_day_start, day_start.time())
        curr_slot = curr_slot.replace(tzinfo=cdmx)

        curr_day_end = datetime.combine(curr_day_start, day_end.time())
        curr_day_end = curr_day_end.replace(tzinfo=cdmx)

        slot_num = 1
        while curr_slot < curr_day_end:
            curr_slot = curr_slot.replace(tzinfo=cdmx)
            tmp = {
                "start": curr_slot,
                "end": curr_slot + slot_duration,
                "available": True,
            }
            for bslot in blocked_slots:
                if bslot[1][3] >= 2 and bslot[0] == curr_slot:
                    tmp["available"] = False
                    tmp["status"] = "blocked"
                    break

            slots[curr_day][f"slot{slot_num}"] = tmp
            curr_slot += slot_duration
            slot_num += 1

    return render(
        request,
        "appointment/calendarview.html",
        {"calendar": slots},
    )


def choose_treatments(request):
    if request.method == "POST":
        form = ChooseTreatmentsForm(request.POST)
        if form.is_valid():
            treatments = []
            print(form.cleaned_data.items())
            for form_field_name, value in form.cleaned_data.items():
                treatments.append([value.name, value.price, value.duration])

            chosen_treatments = {}

            for i, t in enumerate(treatments):
                chosen_treatments["t" + str(i)] = t

            request.session["selection"] = json.dumps(chosen_treatments, default=str)
            return redirect("calendarview")
    else:
        form = ChooseTreatmentsForm()
    return render(request, "appointment/choose_treatments.html", {"form": form})


def add_choose_treatment(request):
    form = ChooseTreatmentsForm()
    html = render_to_string("appointment/add_choose_treatment.html", {"form": form})
    return HttpResponse(html)


def session_writer(request, chosen_slot, endpoint):
    request.session["chosen_slot"] = json.dumps(chosen_slot)
    return redirect(endpoint)


def book_treatment(request):
    chosen_slot = json.loads(request.session.get("chosen_slot", {}))
    print(f"DATA!!!!!: {chosen_slot}")
    selection = json.loads(request.session.get("selection", {}))
    print(f"SELECTION: {selection}")

    # set up json data for api
    # start time
    chosen_slot = datetime.strptime(chosen_slot, "%Y-%m-%dT%H-%M")
    chosen_slot = chosen_slot.replace(tzinfo=cdmx)
    start_slot = chosen_slot.isoformat()
    print(start_slot)
    # end time
    duration_str = "0:15:00"
    hours, minutes, seconds = map(int, duration_str.split(":"))
    duration = datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds)

    # START FROM HERE, calculate end of slot by adding the total of timedelta (needs to be converted from string e.g. "00:15:00") to the start slot
    # end_slot = chosen_slot +
    service = setup_service()

    event = {
        "summary": "Test Appointment",
        "location": "Calle Test 100, Ciuadad Prueba",
        "description": "",
        "start": {
            "dateTime": "2015-05-28T09:00:00-07:00",
            "timeZone": "America/Mexico_City",
        },
        "end": {
            "dateTime": "2015-05-28T17:00:00-07:00",
            "timeZone": "America/Mexico_City",
        },
        "attendees": [
            {"email": "lpage@example.com"},
            {"email": "sbrin@example.com"},
        ],
    }

    event = service.events().insert(calendarId=cid, body=event).execute()

    return render(request, "appointment/book_treatment_success.html")
    # return redirect("book_treatment_success", chosen_slot=chosen_slot)
