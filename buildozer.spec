[app]

# Основные параметры приложения
title = MyApp
package.name = myapp
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,ttf,json
version = 0.1
requirements = python3==3.9.6,kivy==2.1.0,kivymd,openssl,sqlite3

# Настройки Android
android.ndk = 25b
android.sdk = 33
android.api = 33  # Минимальная рекомендуемая версия для Google Play
android.minapi = 21
android.arch = arm64-v8a  # Современная архитектура


# Графические настройки
orientation = portrait
fullscreen = 0
log_level = 2

# Разрешения
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# Дополнительные настройки
android.bootstrap = webview
android.accept_sdk_license = True
p4a.branch = master