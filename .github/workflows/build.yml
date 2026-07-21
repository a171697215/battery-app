name: Build APK

on:
  push:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Cache buildozer dependencies
        uses: actions/cache@v3
        with:
          path: ~/.buildozer
          key: ${{ runner.os }}-buildozer-${{ hashFiles('buildozer.spec') }}
          restore-keys: |
            ${{ runner.os }}-buildozer-

      - name: Install system dependencies
        run: |
          sudo apt update
          sudo apt install -y \
            git zip unzip openjdk-17-jdk \
            autoconf libtool pkg-config \
            zlib1g-dev libncurses-dev \
            cmake libffi-dev libssl-dev python3-dev

      - name: Install buildozer
        run: pip install buildozer

      - name: Build APK
        env:
          ANDROID_NDK_HOME: ${{ github.workspace }}/.buildozer/android/platform/android-ndk-r25c
        run: buildozer -v android debug

      - name: Upload APK
        uses: actions/upload-artifact@v4
        with:
          name: battery-apk
          path: ${{ github.workspace }}/bin/*.apk
