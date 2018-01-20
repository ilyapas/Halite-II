@echo off
7z a halite.zip MyBot.py command_center.py vector.py flow_field.py pathfinding.py hlt
python hlt_client\client.py bot -b halite.zip