@echo off
7z a halite.zip MyBot.py command_center.py flow_field.py hlt
.\hlt_client\client.py bot -b halite.zip