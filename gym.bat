@echo off
if "%1"=="" echo Usage^: gym.bat ^<number of runs^> & goto :eof
del *.log *.hlt
.\hlt_client\client.py gym -r "python MyBot.py" -r "python MyBot.1.py" -b "halite.exe" -i %1 -H 384 -W 256