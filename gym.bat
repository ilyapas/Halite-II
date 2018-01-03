@echo off
if "%1"=="" echo Usage^: gym.bat ^<number of runs^> & goto :eof
del /s /q *.log *.hlt
python .\hlt_client\client.py gym -r "python MyBot.py" -r "python MyBot.1.py" -b "halite.exe" -i %1 -H 160 -W 240