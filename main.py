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
    def __init__(self, channel, content, datetime_sent, message_id):
        self.channel = channel
        self.content = content
        self.datetime_sent = get_relational_datetime(datetime_sent)
        self.id = message_id

def get_relational_datetime(dt_message):
    now = datetime.now(timezone.utc)
    time_since_message = now - dt_message
    tz = pytz.timezone("America/New_York") # TODO change this with user settings
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

@app.route("/")
def index():
    return redirect("/channel/no_channel") # TODO redirect to "first" channel

@app.route("/channel/")
def channel_index():
    return redirect("/channel/no_channel") # TODO redirect to "first" channel

@app.route("/channel/<selected_channel>/", methods=["POST", "GET"])
def channel(selected_channel):
    if request.method == "POST":
        message_content = request.form["content"]
        if message_content.isspace() or message_content == "": 
            return redirect("/channel/" + selected_channel)
        
        message = datastore.Entity(db.key("message"))
        message.update(
            {
                "channel": selected_channel,
                "content": message_content,
                "datetime_sent": datetime.now(timezone.utc),
            }
        )
        db.put(message)
    
        return redirect("/channel/" + selected_channel)
    else:
        channel_query = db.query(kind="channel")
        channel_query.order = ["name"]
        channels = list(channel_query.fetch())
        for channel in channels: # debugging for overwite bug
            print(channel)
            # print(channel["datetime_created"])

        channel_names = [channel["name"] for channel in channels]
        if selected_channel not in channel_names:
            return render_template("404.html")

        message_query = db.query(kind="message")
        message_query.add_filter("channel", "=", selected_channel)
        message_query.order = ["datetime_sent"]
        messages = list(message_query.fetch())
        formatted_messages = []
        for message in messages:
            formatted_message = Message(message["channel"],
                                        message["content"], 
                                        message["datetime_sent"], 
                                        message.id)
            formatted_messages.append(formatted_message)
            
        return render_template("index.html", selected_channel=selected_channel, channels=channels, messages=formatted_messages)

@app.route("/add-channel", methods=["POST", "GET"])
def add_channel(): # TODO currently doesn't check if channel name already exists, just overwrites
    if request.method == "POST":
        channel_name = request.form["channel-name"]
        channel = datastore.Entity(db.key("channel", channel_name))
        channel.update(
            {
                "name": channel_name,
                "datetime_created": datetime.now(timezone.utc),
            }
        )
        db.put(channel)

        return redirect("/channel/" + channel_name)
    else:
        return redirect("/")
    
@app.route("/delete-message/<int:id>/")
def delete_message(id):
    db.delete(db.key("message", id))
    return redirect("/")

@app.route("/delete-channel/<channel>/")
def delete_channel(channel):
    db.delete(db.key("channel", channel)) 
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True, port=8080)