from kivy.lang import Builder
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivymd import app
from kivy.app import App
from kivymd.app import MDApp
from kivy.core.window import Window
from kivy.properties import StringProperty
from kivy.animation import Animation
from kivy.clock import Clock
import hashlib
import json
import os
import kivymd
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from database import Database
from kivymd.uix.snackbar import Snackbar


Window.size = (360, 640)

Builder.load_string("""
<MenuButton@MDFloatingActionButton>:
    size_hint: None, None
    size: dp(56), dp(56)
    pos_hint: {'center_x': 0.5}
    elevation: 10

<NavigationDrawerItem@MDNavigationDrawerItem>:
    icon_color: app.theme_cls.primary_color
    text_color: app.theme_cls.primary_color
    ripple_color: app.theme_cls.primary_light
    selected_color: app.theme_cls.primary_light
""")


class LoginScreen(Screen):
    error_message = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self.animate_logo, 0.5)

    def animate_logo(self, dt):
        if hasattr(self, 'ids') and 'logo_image' in self.ids:
            Animation(opacity=1, duration=1.5).start(self.ids.logo_image)

    def on_login(self):
        username = self.ids.username.text.strip()
        password = self.ids.password.text

        if not username or not password:
            self.error_message = "Заполните все поля!"
            Animation(opacity=1, duration=0.5).start(self.ids.error_label)
            Clock.schedule_once(lambda dt: Animation(opacity=0, duration=0.5).start(self.ids.error_label), 3)
            return

        app = MDApp.get_running_app()
        password_hash = self.hash_password(password)

        user = app.db.get_user(username)

        if user:
            if user[2] == password_hash:
                app.logged_in_user = username
                app.logged_in_user_id = user[0]  # Устанавливаем ID пользователя
                self.manager.current = "main"
            else:
                self.error_message = "Неверный пароль!"
                Animation(opacity=1, duration=0.5).start(self.ids.error_label)
                Clock.schedule_once(lambda dt: Animation(opacity=0, duration=0.5).start(self.ids.error_label), 3)
        else:
            if app.db.add_user(username, password_hash):
                app.logged_in_user = username
                new_user = app.db.get_user(username)
                app.logged_in_user_id = new_user[0]  # Устанавливаем ID нового пользователя
                self.manager.current = "main"
            else:
                self.error_message = "Ошибка при создании пользователя!"
                Animation(opacity=1, duration=0.5).start(self.ids.error_label)
                Clock.schedule_once(lambda dt: Animation(opacity=0, duration=0.5).start(self.ids.error_label), 3)

        self.ids.username.text = ""
        self.ids.password.text = ""
        self.error_message = ""

    def show_error(self, message):
        self.error_message = message
        Animation(opacity=1, duration=0.5).start(self.ids.error_label)
        Clock.schedule_once(lambda dt: Animation(opacity=0, duration=0.5).start(self.ids.error_label), 3)

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

class MainScreen(Screen):
    def on_enter(self):
        app = MDApp.get_running_app()
        if hasattr(app, 'logged_in_user'):
            self.ids.welcome_label.text = f"Добро пожаловать,\n{app.logged_in_user}!"

        # Обновляем список мероприятий
        events_screen = app.root.get_screen('events')
        events_screen.load_events(0)

    def open_menu(self):
        self.ids.nav_drawer.set_state("open")


class ProfileScreen(Screen):
    def on_enter(self):
        app = MDApp.get_running_app()
        user = app.db.get_user(app.logged_in_user)

        if user:
            self.ids.username.text = app.logged_in_user
            self.ids.full_name.text = user[3] if user[3] else ""  # full_name
            self.ids.email.text = user[4] if user[4] else ""  # email

    def save_profile(self):
        app = MDApp.get_running_app()
        app.db.update_user(
            app.logged_in_user,
            self.ids.full_name.text,
            self.ids.email.text
        )
        app.root.current = "main"


class SettingsScreen(Screen):
    pass


class ContentNavigationDrawer(Screen):
    pass

class PartnersScreen(Screen):
    def open_link(self, url):
        import webbrowser
        webbrowser.open(url)


class EventsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_expanded = None
        self.events_loaded = False
        Clock.schedule_once(self.load_events, 0.5)

    def toggle_description(self, event_id):
        if self.current_expanded == event_id:
            self.current_expanded = None
        else:
            self.current_expanded = event_id
        self.load_events(0)

    def register_for_event(self, event_id):
        """Обработка регистрации на мероприятие"""
        app = MDApp.get_running_app()
        if app.logged_in_user_id:
            try:
                success = app.db.register_for_event(app.logged_in_user_id, event_id)
                if success:
                    self.show_snackbar("Вы успешно зарегистрированы на мероприятие!")
                else:
                    self.show_snackbar("Вы уже зарегистрированы на это мероприятие")
                self.load_events(0)
            except Exception as e:
                print(f"Ошибка регистрации: {e}")
                self.show_snackbar("Ошибка регистрации")

    def show_snackbar(self, text):
        snackbar = Snackbar()
        snackbar.text = text  
        snackbar.size_hint_x = 0.9
        snackbar.pos_hint = {'center_x': 0.5, 'y': 0.1}
        snackbar.open()

    def load_events(self, dt):
        try:
            if not hasattr(self, 'ids') or not hasattr(self.ids, 'events_container'):
                Clock.schedule_once(self.load_events, 0.5)
                return

            self.ids.events_container.clear_widgets()
            app = MDApp.get_running_app()

            if not app.db:
                print("База данных не инициализирована")
                return

            events_data = app.db.get_events()

            for event in events_data:
                self.add_event_card({
                    "id": event[0],
                    "title": event[1],
                    "date": event[2],
                    "short_desc": event[3],
                    "full_desc": event[4]
                }, app.theme_cls)

        except Exception as e:
            print(f"Ошибка при загрузке мероприятий: {e}")

    def add_event_card(self, event, theme_cls):
        app = MDApp.get_running_app()

        is_registered = False
        if hasattr(app, 'logged_in_user_id') and app.logged_in_user_id:
            is_registered = app.db.is_user_registered(app.logged_in_user_id, event["id"])

        card = MDCard(
            size_hint=(1, None),
            height=dp(200) if self.current_expanded != event["id"] else dp(350),
            padding=dp(15),
            elevation=5,
            radius=[15, ]
        )

        box = BoxLayout(orientation="vertical", spacing=dp(10))

        # Заголовок и дата
        box.add_widget(MDLabel(
            text=event["title"],
            font_style="H6",
            size_hint_y=None,
            height=dp(30)
        ))

        box.add_widget(MDLabel(
            text=event["date"],
            theme_text_color="Secondary",
            size_hint_y=None,
            height=dp(25)
        ))

        # Краткое описание
        box.add_widget(MDLabel(
            text=event["short_desc"],
            size_hint_y=None,
            height=dp(60),
            text_size=(Window.width - dp(40), None)
        ))

        # Кнопки
        btn_box = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))

        # Кнопка "Подробнее"
        btn_more = MDFlatButton(
            text="Свернуть" if self.current_expanded == event["id"] else "Подробнее",
            theme_text_color="Primary",
            on_release=lambda x, eid=event["id"]: self.toggle_description(eid)
        )
        btn_box.add_widget(btn_more)


        if self.current_expanded == event["id"]:
            if is_registered:
                btn_status = MDLabel(
                    text="Вы зарегистрированы",
                    theme_text_color="Secondary",
                    halign="center",
                    size_hint_x=0.7
                )
                btn_box.add_widget(btn_status)
            else:
                btn_register = MDRaisedButton(
                    text="Зарегистрироваться",
                    theme_text_color="Custom",
                    text_color=(1, 1, 1, 1),
                    md_bg_color=theme_cls.primary_color,
                    on_release=lambda x, eid=event["id"]: self.register_for_event(eid)
                )
                btn_box.add_widget(btn_register)

        box.add_widget(btn_box)

        # Полное описание (если раскрыто)
        if self.current_expanded == event["id"]:
            box.add_widget(MDLabel(
                text=event["full_desc"],
                size_hint_y=None,
                height=dp(120),
                text_size=(Window.width - dp(40), None)
            ))

        card.add_widget(box)
        self.ids.events_container.add_widget(card)


class AboutScreen(Screen):
    def open_link(self, url):
        import webbrowser
        webbrowser.open(url)

    def open_document(self, doc_type):
        # Здесь можно реализовать открытие PDF-документов
        docs = {
            "position": "https://docs.google.com/document/d/1YAqKyFY_VOZTBxsA670cDaus6KhktzB1/edit?usp=sharing&ouid=105593740821813587290&rtpof=true&sd=true",
        }
        self.open_link(docs.get(doc_type))

class MyApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = None
        self.logged_in_user = None
        self.logged_in_user_id = None




    def build(self):
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Indigo"
        self.theme_cls.primary_hue = "500"
        self.theme_cls.primaryColor = "#DAB707"
        self.theme_cls.backgroundColor = "#FFFFFF"
        self.theme_cls.accent_palette = "Amber"
        self.db = Database()

        try:
            self.db = Database()
        except Exception as e:
            print(f"Ошибка инициализации базы данных: {e}")
            raise

        sm = ScreenManager()
        sm = ScreenManager(transition=FadeTransition(duration=0.2))
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(ProfileScreen(name='profile'))
        sm.add_widget(SettingsScreen(name='settings'))
        sm.add_widget(AboutScreen(name='about'))
        sm.add_widget(PartnersScreen(name='partners'))
        sm.add_widget(EventsScreen(name='events'))

        self.screens = {
            'login': LoginScreen(name='login'),
            'main': MainScreen(name='main'),
            'profile': ProfileScreen(name='profile'),
            'settings': SettingsScreen(name='settings'),
            'about': AboutScreen(name='about'),
            'partners': PartnersScreen(name='partners'),
            'events': EventsScreen(name='events')
        }

        for screen in self.screens.values():
            sm.add_widget(screen)

        return sm

    def switch_screen(self, screen_name):

        if screen_name in self.screens:
            self.root.current = screen_name

    def toggle_theme(self, dark_mode):

        self.theme_cls.theme_style = "Dark" if dark_mode else "Light"
        self.theme_cls.primary_palette = "Indigo"
        self.theme_cls.primaryColor = "#DAB707"

    def on_stop(self):

        if self.db:
            self.db.close()



if __name__ == "__main__":
    MyApp().run()

