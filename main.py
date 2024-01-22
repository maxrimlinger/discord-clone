import os
import json
import requests
from flask import Flask, render_template, request, redirect
import utils
import pytz

# Google authentication
from google.cloud import datastore
from oauthlib.oauth2 import WebApplicationClient
from flask_login import LoginManager, current_user, login_required, login_user, logout_user

# handling datetime sent for messages
from datetime import datetime, timezone, timedelta

app = Flask(__name__)
app.secret_key = os.urandom(12).hex() # needed for SSL
db = datastore.Client()

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    db_user = db.get(db.key("user", user_id))
    user = User(
        user_id,
        db_user["first_name"],
        db_user["last_name"],
        db_user["email"],
        db_user["picture"],
        db_user["last_login"],
    )
    return user

@login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect('/')

# globals for various google auth references
client_secrets = utils.get_client_secrets()
auth_client = WebApplicationClient(client_secrets["client_id"])
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
USERINFO_ENDPOINT = requests.get(GOOGLE_DISCOVERY_URL).json()["userinfo_endpoint"]

class User():
    """
    For use with Flask-Login which holds on to an object as the `current_user`.
    """
    def __init__(self, id, first_name, last_name, email, profile_picture, last_login):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.profile_picture = profile_picture
        self.last_login = last_login

        # required for flask_login
        self.is_anonymous = False
        self.is_authenticated = True
        self.is_active = True

    def get_id(self):
        return str(self.id)

class Message():
    """
    Represents a chat message. This class does the heavy lifting of
    converting the date and time the message was sent to a more readible format
    for the front end.
    """
    def __init__(self, content, datetime_sent, message_id, author_id, author_first_name, author_last_name, author_profile_picture):
        self.content = content
        self.relational_datetime = utils.get_relational_datetime(datetime_sent)
        self.time = utils.get_formatted_time(datetime_sent)
        self.datetime = utils.get_formatted_datetime(datetime_sent)
        self.id = message_id
        self.author_id = author_id
        self.author_first_name = author_first_name
        self.author_last_name = author_last_name
        self.author_profile_picture = author_profile_picture

class Space():
    """Represents a space in between messages marking the next day."""
    def __init__(self, space_date):
        self.space_date = space_date

def channel_query():
    query = db.query(kind="channel")
    query.order = ["name"]
    return list(query.fetch())

# routes

@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect("/channel")
    else:
        return render_template("/login.html")

@app.route("/login")
def login():
    request_uri = auth_client.prepare_request_uri(
        client_secrets["auth_uri"],
        redirect_uri="https://127.0.0.1:8080/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)

@app.route("/logout")
def logout():
    logout_user()
    return redirect("/")


@app.route("/callback")
def callback():
    code = request.args.get("code")
    token_url, headers, body = auth_client.prepare_token_request(
        client_secrets["token_uri"],
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code,
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(client_secrets["client_id"], client_secrets["client_secret"]),
    )
    auth_client.parse_request_body_response(json.dumps(token_response.json()))
    
    uri, headers, body = auth_client.add_token(USERINFO_ENDPOINT)
    userinfo_response = requests.get(uri, headers=headers, data=body).json()

    if not userinfo_response.get("email_verified"):
        return "User email not available or not verified by Google.", 400

    now = datetime.now(timezone.utc)

    user = User(
        userinfo_response["sub"], userinfo_response["given_name"], 
        userinfo_response["family_name"], userinfo_response["email"], 
        userinfo_response["picture"], now
    )

    user_entity = datastore.Entity(db.key("user", user.id))
    user_entity.update(
        {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "picture": user.profile_picture,
            "last_login": now
        }
    )
    db.put(user_entity)

    login_user(user)

    return redirect("/channel")

@app.route("/channel/")
@login_required
def channel_index():
    first_channel = channel_query()[0]
    return redirect("/channel/" + first_channel["name"])

@app.route("/channel/<selected_channel_name>/", methods=["POST", "GET"])
@login_required
def channel(selected_channel_name):
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
                "author": current_user.id
            }
        )
        db.put(message)
    
        return redirect("/channel/" + selected_channel_name)
    else:
        channels = channel_query()
        channel_names = [channel["name"] for channel in channels]
        if selected_channel_name not in channel_names:
            return "Channel not found"

        message_query = db.query(kind="message")
        message_query.add_filter("channel", "=", selected_channel_name)
        message_query.order = ["datetime_sent"]
        db_messages = list(message_query.fetch())

        # saves already known author info to speed up load times
        # dict of info inside a dict of authors
        author_cache = {}

        formatted_messages = []
        prev_author = None
        prev_datetime = None
        tz = pytz.timezone("America/New_York") # this could potentially be changed
        for message in db_messages:
            if message["author"] not in author_cache:
                db_author = db.get(db.key("user", message["author"]))
                author_cache[message["author"]] = db_author
            local_message_dt = message["datetime_sent"].astimezone(tz)
            if prev_datetime != None:
                local_prev_dt = prev_datetime.astimezone(tz)
                if local_message_dt.day != local_prev_dt.day:
                    # add spaces that tell the date when the day changes
                    formatted_messages.append(Space(utils.get_formatted_date(local_message_dt)))
            else:
                formatted_messages.append(Space(utils.get_formatted_date(local_message_dt)))
            if (
                message["author"] != prev_author or
                message["datetime_sent"] - prev_datetime > timedelta(minutes=10)
            ):
                formatted_message = Message(
                    message["content"], 
                    message["datetime_sent"], 
                    message.id,
                    message["author"],
                    author_cache[message["author"]]["first_name"],
                    author_cache[message["author"]]["last_name"],
                    author_cache[message["author"]]["picture"]
                )
            else:
                # no author info in the object tells the template to render the 
                # message grouped with previous messages
                formatted_message = Message(
                    message["content"], 
                    message["datetime_sent"], 
                    message.id,
                    message["author"],
                    None,
                    None,
                    None
                )
            formatted_messages.append(formatted_message)
            prev_author = message["author"]
            prev_datetime = message["datetime_sent"]
        return render_template(
            "index.html", 
            selected_channel_name=selected_channel_name, 
            channels=channels, 
            messages=formatted_messages, 
            current_user=current_user.id,
            # user_first_name=current_user.first_name,
            # user_last_name=current_user.last_name,
            # user_profile_picture=current_user.profile_picture
        )

@app.route("/add-channel", methods=["POST", "GET"])
@login_required
def add_channel():
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
@login_required
def delete_message(id):
    message = db.get(db.key("message", id))
    if message["author"] != current_user.id:
        return "You do not have permission to delete this message.", 403
    db.delete(db.key("message", id))
    
    redirect_channel = request.args.get("redirect")
    return redirect("/channel/" + redirect_channel)

@app.route("/delete-channel/<int:id>/")
@login_required
def delete_channel(id):
    db.delete(db.key("channel", id)) 
    return redirect("/")

if __name__ == "__main__":
    context = ("ssl/server.crt", "ssl/server.key")
    app.run(debug=True, port=8080, ssl_context=context)