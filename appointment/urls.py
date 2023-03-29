from django.urls import path

from . import views

urlpatterns = [
    path("setup/", views.setup, name="setup"),
    path("calendarview/", views.calendarview, name="calendarview"),
    path("choose_treatments/", views.choose_treatments, name="choose_treatments"),
    path(
        "add_choose_treatment/", views.add_choose_treatment, name="add_choose_treatment"
    ),
    path("book_treatment/<chosen_slot>", views.book_treatment, name="book_treatment"),
]
