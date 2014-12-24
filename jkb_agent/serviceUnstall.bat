@echo off

python agentWinService.py stop
python agentWinService.py remove

echo. & pause
exit
