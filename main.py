from flask import Flask, render_template, url_for, request, redirect
from google.cloud import datastore
from datetime import datetime, timezone, timedelta, date
import pytz

app = Flask(__name__)
db = datastore.Client()

class Message():
    """Represents a chat message. This class does the heavy lifting of
    converting the date and time the message was sent to a more readible format
    for the frontend.
    """
    def __init__(self, content, datetime_sent):
        self.content = content
        self.datetime_sent = get_relational_datetime(datetime_sent)

def get_relational_datetime(dt_message):
    now = datetime.now(timezone.utc)
    time_since_message = now - dt_message
    # utc = pytz.timezone('UTC')
    # now = utc.localize(datetime.utcnow())
    tz = pytz.timezone("America/New_York") # TODO change this with user settings
    local_dt_message = dt_message.astimezone(tz)
    local_now = now.astimezone(tz)

    dt_10_seconds_ago = now - timedelta(seconds=10)
    dt_1_minute_ago = now - timedelta(minutes=1)
    dt_2_minutes_ago = now - timedelta(minutes=2)
    dt_1_hour_ago = now - timedelta(hours=1)
    dt_2_hours_ago = now - timedelta(hours=2)

    dt_beginning_of_today = datetime(local_now.year, local_now.month, local_now.day, tzinfo=tz)
    dt_beginning_of_yesterday = dt_beginning_of_today - timedelta(days=1)

    if dt_message > dt_10_seconds_ago:
        return "Now" + str(local_dt_message)
    if dt_message > dt_1_minute_ago:
        return "< 1 minute ago" + str(local_dt_message)
    if dt_message > dt_2_minutes_ago:
        return "1 minute ago" + str(local_dt_message)
    if dt_message > dt_1_hour_ago:
        return str(time_since_message.seconds // 60) + " minutes ago" + str(local_dt_message)
    if dt_message > dt_2_hours_ago:
        return "1 hour ago" + str(local_dt_message)
    
    if local_dt_message > dt_beginning_of_today:
        return str(time_since_message.seconds // 3600) + " hours ago" + str(local_dt_message)
    if local_dt_message > dt_beginning_of_yesterday:
        return "Yesterday"  + str(local_dt_message)
    else:
        return "old" + str(local_dt_message)

@app.route("/", methods=["POST", "GET"])
def index():
    if request.method == "POST":
        message_content = request.form["content"]
        if message_content.isspace() or message_content == "": return redirect("/")
        message = datastore.Entity(db.key("message"))
        message.update(
            {
                "content": message_content,
                "datetime_sent": datetime.now(timezone.utc),
            }
        )
        db.put(message)
    
        return redirect("/")
    else:
        query = db.query(kind="message")
        query.order = ["datetime_sent"]
        messages = list(query.fetch())
        formatted_messages = []
        for message in messages:
            formatted_message = Message(message["content"], message["datetime_sent"])
            formatted_messages.append(formatted_message)
        return render_template("index.html", messages=formatted_messages)
    
@app.route("/delete/<int:id>")
def delete(id):
    db.delete(db.key("message", id))
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True, port=8080)