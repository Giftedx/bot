from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask import request, jsonify  # Added imports for request, jsonify
import os


app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = \
    'sqlite:///' + os.path.join(basedir, 'tasks.db')
db = SQLAlchemy(app)

class Task(db.Model): # type: ignore
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    is_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Task {self.id}>'

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/tasks', methods=['POST'])
def create_task():
    data = request.get_json()
    if not data or 'title' not in data:
        return jsonify({'message': 'Title is required'}), 400

    new_task = Task(title=data['title'], description=data.get('description', ''))
    db.session.add(new_task)
    db.session.commit()

    return jsonify({
        'id': new_task.id,
        'title': new_task.title,
        'description': new_task.description,
        'is_completed': new_task.is_completed,
        'created_at': new_task.created_at.isoformat(),
        'updated_at': new_task.updated_at.isoformat()
    }), 201

@app.route('/tasks')
def list_tasks():
    tasks = Task.query.all()
    output = 'Tasks:<br>'
    for task in tasks:
        output += f'ID: {task.id}, Title: {task.title}, Completed: {task.is_completed}<br>'
    return output

@app.route('/test_task') # Simple route for quick testing
def test_task():
    new_task = Task(title='Test Task', description='A sample task')
    db.session.add(new_task)
    db.session.commit()
    return jsonify({'message': 'Test task created!'}), 201


if __name__ == '__main__':
    with app.app_context(): # type: ignore
        db.create_all()
    app.run(debug=True, port=8080)