[app]
title = 电池追溯
package.name = batterytrace
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,otf
version = 1.0.0
requirements = python3,kivy,requests,plyer
android.permissions = INTERNET,CAMERA,VIBRATE
android.accept_sdk_license = True
android.api = 33
android.minapi = 21
android.ndk = 23b
pypi_mirror = https://pypi.tuna.tsinghua.edu.cn/simple

# 以下为可选优化项，防止 gradle 额外下载
android.gradle_dependencies =

[buildozer]
log_level = 2
