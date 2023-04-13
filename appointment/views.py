from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import reverse
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.core.mail import send_mail

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
    timeMax = timeMin + timedelta(days=7)
    timeMax_iso = timeMax.isoformat()

    day_start = datetime.strptime("08:00", "%H:%M")
    day_end = datetime.strptime("16:00", "%H:%M")

    slot_duration = timedelta(minutes=30)

    # retrieve the selected treatments from the session and parse them
    selection = json.loads(request.session.get("selection", {}))
    # example output
    # treatmentname, duration, price, client_count
    # ['Hot Stone Massage', '0:15:00', 200, 1]

    # retrieve calender from google calendar api
    events_results = (
        service.events()
        .list(
            calendarId=cid,
            timeMax=timeMax_iso,
            timeMin=timeMin_iso,
            showDeleted=True,
        )
        .execute()
    )
    events = events_results.get("items", [])

    # check for recurring events in result and add the instances to the events object
    for event in events:
        if "recurrence" in event:
            # Query instances endpoint and get all instances of recurring event
            instances = (
                service.events()
                .instances(
                    calendarId=cid,
                    eventId=event["id"],
                    timeMin=timeMin_iso,
                    timeMax=timeMax_iso,
                )
                .execute()
            )
            # Add the instances to the list of events
            events.extend(instances.get("items", []))

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
            key, value = list(form.cleaned_data.items())[0]
            chosen_treatments = [
                value.name,
                value.duration,
                value.price,
                value.client_count,
            ]

            client_details = list(form.cleaned_data.items())[1:]

            request.session["selection"] = json.dumps(chosen_treatments, default=str)
            request.session["clientDetails"] = json.dumps(client_details, default=str)

            return redirect("calendarview")
    else:
        form = ChooseTreatmentsForm()
    return render(request, "appointment/choose_treatments.html", {"form": form})


# STUB, meant to add a new field to the initial form on choose_treatments
def add_choose_treatment(request):
    form = ChooseTreatmentsForm()
    html = render_to_string("appointment/add_choose_treatment.html", {"form": form})
    return HttpResponse(html)


def session_writer(request, chosen_slot, endpoint):
    request.session["chosen_slot"] = json.dumps(chosen_slot)
    return redirect(endpoint)


def book_treatment(request):
    chosen_slot = json.loads(request.session.get("chosen_slot", {}))
    # print(f"DATA!!!!!: {chosen_slot}")
    selection = json.loads(request.session.get("selection", {}))
    # print(f"SELECTION: {selection}")
    client_details = json.loads(request.session.get("clientDetails", {}))
    # print(f"CLIENT: {client_details}")

    # set up json data for api
    # start time
    chosen_slot = datetime.strptime(chosen_slot, "%Y-%m-%dT%H-%M")
    chosen_slot = chosen_slot.replace(tzinfo=cdmx)
    start_slot = chosen_slot.isoformat()
    # end time
    duration_str = selection[1]
    hours, minutes, seconds = map(int, duration_str.split(":"))
    duration = timedelta(hours=hours, minutes=minutes, seconds=seconds)

    # START FROM HERE, calculate end of slot by adding the total of timedelta (needs to be converted from string e.g. "00:15:00") to the start slot
    end_slot = chosen_slot + duration
    end_slot = end_slot.replace(tzinfo=cdmx)
    end_slot = end_slot.isoformat()

    # summary string
    summary = selection[0] + " " + client_details[0][1] + " " + client_details[1][1]

    # setup service instance for api
    service = setup_service()

    event = {
        "summary": summary,
        "location": os.getenv("ADDRESS"),
        "description": "",
        "start": {
            "dateTime": start_slot,
            "timeZone": "America/Mexico_City",
        },
        "end": {
            "dateTime": end_slot,
            "timeZone": "America/Mexico_City",
        },
        "attendees": [
            {"email": os.getenv("MAIL_COMPANY")},
            {"email": client_details[2][1]},
        ],
    }

    event = service.events().insert(calendarId=cid, body=event).execute()

    # delete session elements
    request.session.flush()

    return render(
        request,
        "appointment/book_treatment_success.html",
        {"client_details": client_details},
    )
    # return redirect("book_treatment_success", chosen_slot=chosen_slot)
