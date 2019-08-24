@echo off

pushd %CD%
cd /d "server"
start /min gameserver.bat .\map_r2m1.txt 127.0.0.1 6001 
popd



pushd %CD%
cd /d "client"
start /min gameclient.bat 6666 127.0.0.1 6001 
popd

rem sleep 3s
ping -n 3 127.0.0.1>null


pushd %CD%
cd /d "ai"
start /min gameclient.bat 1111 127.0.0.1 6001 
popd

REM pushd %CD%
REM cd /d "ui"
REM start nw.bat
REM popd
