call venv\Scripts\activate.bat
call platform-tools\adb start-server
call platform-tools\adb connect localhost:5556
call platform-tools\adb connect localhost:5555
call platform-tools\adb connect localhost:5554
call platform-tools\adb devices
call python "autoclicker.py"
call venv\Scripts\deactivate.bat
