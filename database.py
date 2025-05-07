import sqlite3
import os
from kivy.app import App


class Database:
    def __init__(self, db_name='app_database.db'):

        try:
            app = App.get_running_app()
            self.db_path = os.path.join(app.user_data_dir, db_name)
        except:

            self.db_path = db_name


        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        self.conn = None
        self.cursor = None
        self.initialize_db()

    def initialize_db(self):
        """Инициализация базы данных и создание таблиц"""
        self.connect()

        # Таблица пользователей
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            email TEXT
        )
        ''')

        # Таблица мероприятий
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            date TEXT NOT NULL,
            short_desc TEXT NOT NULL,
            full_desc TEXT NOT NULL,
            image_path TEXT
        )
        ''')

        # Таблица регистраций
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            event_id INTEGER NOT NULL,
            registration_date TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (event_id) REFERENCES events (id),
            UNIQUE(user_id, event_id)
        )
        ''')

        self.conn.commit()


        if not self.get_events():
            self.add_test_events()

    def connect(self):

        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

    def close(self):

        if self.conn:
            self.conn.close()

    def add_user(self, username, password_hash, full_name="", email=""):

        try:
            self.cursor.execute(
                "INSERT INTO users (username, password_hash, full_name, email) VALUES (?, ?, ?, ?)",
                (username, password_hash, full_name, email)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def get_user(self, username):

        self.cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        return self.cursor.fetchone()

    def update_user(self, username, full_name, email):

        self.cursor.execute(
            "UPDATE users SET full_name=?, email=? WHERE username=?",
            (full_name, email, username)
        )
        self.conn.commit()

    def add_event(self, title, date, short_desc, full_desc, image_path=None):

        self.cursor.execute(
            "INSERT INTO events (title, date, short_desc, full_desc, image_path) VALUES (?, ?, ?, ?, ?)",
            (title, date, short_desc, full_desc, image_path)
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def get_events(self):

        self.cursor.execute("SELECT * FROM events ORDER BY date")
        return self.cursor.fetchall()

    def get_event(self, event_id):

        self.cursor.execute("SELECT * FROM events WHERE id=?", (event_id,))
        return self.cursor.fetchone()

    def register_for_event(self, user_id, event_id):

        try:
            self.cursor.execute(
                "INSERT INTO registrations (user_id, event_id) VALUES (?, ?)",
                (user_id, event_id)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def is_user_registered(self, user_id, event_id):

        self.cursor.execute(
            "SELECT 1 FROM registrations WHERE user_id=? AND event_id=?",
            (user_id, event_id)
        )
        return bool(self.cursor.fetchone())

    def get_user_events(self, user_id):

        self.cursor.execute('''
        SELECT e.* FROM events e
        JOIN registrations r ON e.id = r.event_id
        WHERE r.user_id = ?
        ORDER BY e.date
        ''', (user_id,))
        return self.cursor.fetchall()

    def add_test_events(self):

        test_events = [
            {
                "title": "IT-Конференция 2025",
                "date": "15-17 ноября 2025",
                "short_desc": "Ежегодная конференция для IT-специалистов",
                "full_desc": "Подробное описание мероприятия: лекции, воркшопы, нетворкинг с ведущими экспертами отрасли."
            },
            {
                "title": "Хакатон по разработке",
                "date": "10-12 декабря 2025",
                "short_desc": "Соревнования по программированию",
                "full_desc": "48 часов интенсивной работы в командах над реальными кейсами от компаний-партнеров."
            }
        ]

        for event in test_events:
            self.add_event(
                event["title"],
                event["date"],
                event["short_desc"],
                event["full_desc"]
            )