import json
from datetime import datetime, timezone, timedelta
import pytz

month_to_str = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December"
}

def get_client_secrets():
    with open("auth\client_secrets.json") as file:
        data = json.load(file)
    return data["web"]

def get_relational_datetime(dt_message):
    now = datetime.now(timezone.utc)
    time_since_message = now - dt_message
    tz = pytz.timezone("America/New_York") # this could potentially be changed
    local_dt_message = dt_message.astimezone(tz)
    local_now = now.astimezone(tz)

    dt_10_seconds_ago = now - timedelta(seconds=10)
    dt_1_minute_ago = now - timedelta(minutes=1)
    dt_2_minutes_ago = now - timedelta(minutes=2)
    dt_1_hour_ago = now - timedelta(hours=1)
    dt_2_hours_ago = now - timedelta(hours=2)

    # local to user
    dt_beginning_of_today = datetime(local_now.year, local_now.month, local_now.day, tzinfo=tz)
    dt_beginning_of_yesterday = dt_beginning_of_today - timedelta(days=1)
    days_since_message = dt_beginning_of_today - local_dt_message + timedelta(days=1)

    if dt_message > dt_10_seconds_ago:
        return "Now"
    if dt_message > dt_1_minute_ago:
        return "< 1 minute ago"
    if dt_message > dt_2_minutes_ago:
        return "1 minute ago"
    if dt_message > dt_1_hour_ago:
        return str(time_since_message.seconds // 60) + " minutes ago"
    if dt_message > dt_2_hours_ago:
        return "1 hour ago"
    
    if local_dt_message > dt_beginning_of_today:
        return str(time_since_message.seconds // 3600) + " hours ago"
    if local_dt_message > dt_beginning_of_yesterday:
        return "Yesterday" 
    else:
        return str(days_since_message.days) + " days ago"
    
def get_day_suffix(day_num):
    if day_num % 10 == 1:
        return "st"
    elif day_num % 10 == 2:
        return "nd"
    elif day_num % 10 == 3:
        return "rd"
    else:
        return "th"
    
def to_12hr(hour):
    """Converts a 24-hour clock hour to a 12-hour clock hour."""
    if hour == 0:
        return 12
    elif hour <= 12:
        return hour
    else:
        return hour - 12
    
def get_formatted_time(dt):
    tz = pytz.timezone("America/New_York") # this could potentially be changed
    local_dt = dt.astimezone(tz) # localize
    time = "{hour}:{minute} {am_pm}".format(
        hour=to_12hr(local_dt.hour),
        minute=f"{local_dt.minute:02}",
        am_pm = "AM" if local_dt.hour < 12 else "PM"
    )
    return time

def get_formatted_datetime(dt):
    tz = pytz.timezone("America/New_York") # this could potentially be changed
    local_dt = dt.astimezone(tz) # localize
    now = datetime.now(timezone.utc)
    time = "{month} {day}{day_suffix}{year}, {hour}:{minute}:{second} {am_pm}".format(
        month=month_to_str[local_dt.month],
        day=local_dt.day,
        day_suffix=get_day_suffix(local_dt.day),
        year=f" {local_dt.year}" if now.year != local_dt.year else "",
        hour=to_12hr(local_dt.hour),
        minute=f"{local_dt.minute:02}",
        second=f"{local_dt.second:02}",
        am_pm="AM" if local_dt.hour < 12 else "PM"
    )
    return time