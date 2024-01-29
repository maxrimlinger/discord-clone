# Discord Clone
This is a basic chat app with some visual inspiration from the popular chat app Discord. I created this to learn backend web development, and more specifically the Flask framework.
## Installation and Running
### Setting up Google Services
>*Warning:* This project relies on multiple Google services for functionality. In order to run this locally, you must set up these Google services to work with your local instance.

As data is stored in a Google Datastore database, you will need to have a Google Cloud Platform project with the Datastore API enabled. This project also uses Google authentication, so you must create an OAuth Client ID with an application type of Web Application for sign-in to function. Download the OAuth client JSON file, place it in a directory called `auth` and rename the file `client_secrets.json`. OAuth requires traffic be sent over HTTPS, so you must generate/obtain an SSL certificate and place it in a directory called `ssl`. Name the certificate and key files `server.crt` and `server.key` respectively.

To link your GCP project with your local instance, run this command: `gcloud auth login` then login with your Google account that owns the project.
### Installing Python Dependencies (Windows)
```
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r .\requirements.txt
```
### Running Discord Clone
```
python main.py
```
The application will now be running at https://127.0.0.1:8080.
