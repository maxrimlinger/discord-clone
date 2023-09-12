from flask import Flask, render_template, url_for, request, redirect
from google.cloud import datastore
from datetime import datetime

app = Flask(__name__)
db = datastore.Client()

@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        task_content = request.form['content']
        task = datastore.Entity(db.key("task"))
        task.update(
            {
                "content": task_content,
                "date_created": datetime.utcnow(),
            }
        )
        db.put(task)
        print(task.id)
    
        return redirect('/')
    else:
        query = db.query(kind="task")
        query.order = ["-date_created"]
        tasks = list(query.fetch())
        print(tasks)
        return render_template('index.html', tasks=tasks)
    
@app.route('/delete/<int:id>')
def delete(id):
    db.delete(db.key("task", id))
    return redirect('/')
    
@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    task = db.get(db.key("task", id))

    if request.method == 'POST':
        task['content'] = request.form['content']
        db.put(task)
        return redirect('/')
    else:
        return render_template('update.html', task=task)

if __name__ == "__main__":
    app.run(debug=True, port=8080)