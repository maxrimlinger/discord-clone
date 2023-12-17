import requests
import cachecontrol
from flask import Flask, render_template, url_for, request, redirect, session, abort
from google.cloud import datastore
from google_auth_oauthlib.flow import Flow
import google.auth.transport.requests
from google.oauth2 import id_token
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from datetime import datetime, timezone, timedelta, date
import pytz

app = Flask(__name__)
app.secret_key = "SECRET"
db = datastore.Client()

GOOGLE_CLIENT_ID = "325587338034-lr4ha1j1hkj8ba9h1qdrp8u3gcoc03oc.apps.googleusercontent.com"

flow = Flow.from_client_secrets_file(
    client_secrets_file="auth\client_secrets.json",
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"], 
    redirect_uri="https://127.0.0.1:8080/callback"
)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

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

def channel_query():
    query = db.query(kind="channel")
    query.order = ["name"]
    return list(query.fetch())

@app.route("/")
def index():
    return render_template("/login.html")

@app.route("/login")
def login():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)

    if not session["state"] == request.args["state"]:
        abort(500)

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )
    
    session["google_id"] = id_info.get("sub")
    session["name"] = id_info.get("name")
    return redirect("/channel")

@app.route("/channel/")
def channel_index():
    if "google_id" not in session:
            return abort(401)
    first_channel = channel_query()[0]
    return redirect("/channel/" + first_channel["name"])

@app.route("/channel/<selected_channel_name>/", methods=["POST", "GET"])
def channel(selected_channel_name):
    if "google_id" not in session:
            return abort(401)
    if request.method == "POST":
        message_content = request.form["content"]
        if message_content.isspace() or message_content == "": 
            return redirect("/channel/" + selected_channel_name)
        
        message = datastore.Entity(db.key("message"))
        message.update(
            {
                "channel": selected_channel_name,
                "content": message_content,
                "datetime_sent": datetime.now(timezone.utc),
            }
        )
        db.put(message)
    
        return redirect("/channel/" + selected_channel_name)
    else:
        channels = channel_query()
        channel_names = [channel["name"] for channel in channels]
        if selected_channel_name not in channel_names:
            return render_template("404.html")

        message_query = db.query(kind="message")
        message_query.add_filter("channel", "=", selected_channel_name)
        message_query.order = ["datetime_sent"]
        messages = list(message_query.fetch())
        formatted_messages = []
        for message in messages:
            formatted_message = Message(message["channel"],
                                        message["content"], 
                                        message["datetime_sent"], 
                                        message.id)
            formatted_messages.append(formatted_message)
            
        return render_template("index.html", selected_channel_name=selected_channel_name, channels=channels, messages=formatted_messages)

@app.route("/add-channel", methods=["POST", "GET"])
def add_channel(): # TODO currently doesn't check if channel name already exists, just overwrites
    if "google_id" not in session:
            return abort(401)
    if request.method == "POST":
        channel_name = request.form["channel-name"]

        # don't recreate already existing channels
        channels = channel_query()
        channel_names = [channel["name"] for channel in channels]
        if channel_name in channel_names:
            return redirect("/channel/" + channel_name)

        channel = datastore.Entity(db.key("channel"))
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
    
@app.route("/delete-message/<int:id>")
def delete_message(id):
    if "google_id" not in session:
            return abort(401)
    db.delete(db.key("message", id))
    redirect_channel = request.args.get("redirect")
    print(type(redirect_channel))
    return redirect("/channel/" + redirect_channel)

@app.route("/delete-channel/<int:id>/")
def delete_channel(id):
    if "google_id" not in session:
            return abort(401)
    print(id)
    print(db.key("channel", id))
    db.delete(db.key("channel", id)) 
    return redirect("/")

if __name__ == "__main__":
    context = ("ssl/server.crt", "ssl/server.key")
    app.run(debug=True, port=8080, ssl_context=context)