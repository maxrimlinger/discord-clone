from flask import Flask, render_template, url_for, request, redirect
from google.cloud import datastore
from datetime import datetime

app = Flask(__name__)
db = datastore.Client()

@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        message_content = request.form['content']
        message = datastore.Entity(db.key("message"))
        message.update(
            {
                "content": message_content,
                "datetime_sent": datetime.utcnow(),
            }
        )
        print(message)
        db.put(message)
    
        return redirect('/')
    else:
        query = db.query(kind="message")
        query.order = ["date_created"]
        messages = list(query.fetch())
        return render_template('index.html', messages=messages)
    
@app.route('/delete/<int:id>')
def delete(id):
    db.delete(db.key("message", id))
    return redirect('/')

if __name__ == "__main__":
    app.run(debug=True, port=8080)