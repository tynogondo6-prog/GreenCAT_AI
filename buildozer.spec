[app]
title = GreenCAT AI Camera
package.name = greencat
package.domain = org.greencat

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 0.1
# Возвращаем фиксированные версии, которые ожидает Docker-образ ArtemSBulgakov
requirements = python3==3.10.12,kivy==2.3.0,requests,pillow,pyjnius==1.5.0,setuptools,cython

orientation = portrait
fullscreen = 0

android.permissions = CAMERA,FLASHLIGHT,INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a

android.accept_sdk_license = True

p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 1
