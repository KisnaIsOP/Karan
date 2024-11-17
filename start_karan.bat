@echo off
echo Starting Karan AI...
ipconfig | findstr "IPv4" | findstr "192"
echo.
echo Copy your local IP address from above (like 192.168.x.x)
echo Then on your phone, open browser and go to: http://YOUR_IP:2000
echo For example: http://192.168.1.5:2000
echo.
python -m flask run --debug --port 2000 --host 0.0.0.0
pause
