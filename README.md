# CashPilot

CashPilot is a Streamlit app reorganized into layers:

- `cashpilot/data_access.py`: file and JSON persistence
- `cashpilot/business.py`: authentication, profile, and financial logic
- `app.py`: Streamlit presentation layer and entry point

## Run

```bash
streamlit run app.py
```

## Android APK (Buildozer)

This repository now includes `buildozer.spec` and `main.py` so you can package the app as an APK using Buildozer (webview bootstrap).

```bash
./scripts/build_apk.sh
```

The generated APK will be under:

```bash
bin/*.apk
```

Notes:
- APK build requires Linux with Android SDK/NDK and Java available for Buildozer.
- The Android entrypoint (`main.py`) starts Streamlit locally and the APK uses a WebView bootstrap.
