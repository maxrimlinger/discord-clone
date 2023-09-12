from flask import Flask, render_template, url_for, request, redirect
from google.cloud import datastore
from datetime import datetime

app = Flask(__name__)
db = datastore.Client()

next_task_id = 0

@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        task_content = request.form['content']
        task = db.Entity(db.key("task", next_task_id))
        next_task_id += 1
        task.update(
            {
                "content": task_content,
                "date_created": datetime.datetime.utcnow(),
            }
        )
    
        return redirect('/')
    else:
        query = db.query(kind="task")
        query.order = ["date"]
        tasks = list(query.fetch())
        return render_template('index.html', tasks=tasks)
    
@app.route('/delete/<int:id>')
def delete(id):
    db.delete(db.key("task", id))
    return redirect('/')
    
@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    task = Todo.query.get_or_404(id)

    if request.method == 'POST':
        task.content = request.form['content']

        try:
            db.session.commit()
            return redirect('/')
        except:
            return 'There was an error updating your task'
    else:
        return render_template('update.html', task=task)

if __name__ == "__main__":
    app.run(debug=True)