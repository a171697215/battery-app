[app]
title = 电池追溯
package.name = batterytrace
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,otf
version = 1.0.0
requirements = python3,kivy,requests,plyer,pyjnius,android,kivy_garden.xcamera,Pillow,opencv,numpy
orientation = portrait
android.permissions = INTERNET,CAMERA,VIBRATE
android.accept_sdk_license = True
android.api = 33
android.minapi = 24
android.ndk = 25c
android.sdk = 33

[buildozer]
log_level = 2
