@echo off

python agentWinService.py --startup auto install

python agentWinService.py start

echo. & pause
exit
