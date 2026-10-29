[app]
title = GreenCAT AI Camera
package.name = greencat
package.domain = org.greencat

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 0.1
# Фиксируем python3.10 и добавляем openssl с cryptography
requirements = python3==3.10.12,kivy==2.3.1,openssl,cryptography,requests,pillow,pyjnius==1.6.1,setuptools,cython

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
