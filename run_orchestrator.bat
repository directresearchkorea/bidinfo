@echo off
cd /d "%~dp0"
echo Running Automatic Bid Collection at %date% %time% >> collection_log.txt
py execution\update_calendar_bids.py >> collection_log.txt 2>&1
echo Finished at %date% %time% >> collection_log.txt
