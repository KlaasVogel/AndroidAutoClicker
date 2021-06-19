call venv\Scripts\activate.bat
call platform-tools\adb start-server
call platform-tools\adb devices
call python "autoclicker.py"
call platform-tools\adb kill-server
call venv\Scripts\deactivate.bat
