import unittest
import os  # Added import for os module
from app import app, db, Task


class TestDatabase(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app_context = app.app_context()
        print("setUp: App context created")  # VERBOSE
        self.app_context.push()
        current_dir = os.getcwd()  # Get current working directory
        print(f"setUp: Current working directory: {current_dir}")  # VERBOSE
        print("setUp: App context pushed")  # VERBOSE
        db.create_all()
        print("setUp: Database created")  # VERBOSE
        self.client = app.test_client()
        print("setUp: Test client initialized")  # VERBOSE

    def tearDown(self):
        print("tearDown: Starting")  # VERBOSE
        db.session.remove()
        print("tearDown: DB session removed")  # VERBOSE
        db.drop_all()
        print("tearDown: DB dropped")  # VERBOSE
        self.app_context.pop()
        print("tearDown: App context popped")  # VERBOSE

    def test_task_creation(self):
        print("test_task_creation: Starting")  # VERBOSE
        try:
            task = Task(title="Test Task", description="Test Description")
            db.session.add(task)
            db.session.commit()

            retrieved_task = Task.query.filter_by(title="Test Task").first()
            self.assertIsNotNone(retrieved_task)
            self.assertEqual(retrieved_task.description, "Test Description")
            print("test_task_creation: Task created and ")
            print("retrieved successfully")  # VERBOSE
        except Exception as e:
            print(f"test_task_creation: Exception occurred: {e}")  # VERBOSE
            raise  # Re-raise the exception to fail the test


if __name__ == '__main__':

    unittest.main()
    print("Database tests PASSED.")