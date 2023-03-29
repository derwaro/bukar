from django.urls import path

from . import views

urlpatterns = [
    path("setup/", views.setup, name="setup"),
    path("calendarview/", views.calendarview, name="calendarview"),
    path("choose_treatments/", views.choose_treatments, name="choose_treatments"),
    path(
        "add_choose_treatment/", views.add_choose_treatment, name="add_choose_treatment"
    ),
    path("book_treatment/", views.book_treatment, name="book_treatment"),
    path(
        "session_writer/<chosen_slot>/<endpoint>",
        views.session_writer,
        name="session_writer",
    ),
]
