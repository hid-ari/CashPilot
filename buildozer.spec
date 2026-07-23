[app]
title = CashPilot
package.name = cashpilot
package.domain = com.cashpilot
source.dir = .
source.include_exts = py,json,md,png,jpg,jpeg,svg
version = 1.0
requirements = python3,streamlit,pandas,plotly
orientation = portrait
fullscreen = 0

# WebView bootstrap opens an embedded browser while `main.py` starts Streamlit on localhost.
p4a.bootstrap = webview
android.permissions = INTERNET
android.api = 34
android.minapi = 24
android.archs = arm64-v8a, armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1
