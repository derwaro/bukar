# Bukar
## custom appointment booking platform in Django

The idea is to make a simple selfhostable platform, for taking reservations.
It integrates with Google Calendar through the API.

**Obviously work in progress. No guarantees. Use at your own risk. Feedback and improvements welcome!**

### to-do
- confirmation page for client
- create downloadable calendar file for client
- notify client for upcoming appointments
- only show slots, which really fit the chosen treatments (check for duration of treatment and neighboring future occupied slots. e.g. slots taken 9.00-10.00 and 9.30-10.00. if client chooses a treatment with duration of 1 hour, the only available slot between 8 and 10 should be 8.00 and 8.30. Not available: 9.00 (since the second 30 minutes of the treatment are already double occupied))