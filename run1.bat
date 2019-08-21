@echo off


sleep 5s
ping -n 3 127.0.0.1>null

pushd %CD%
cd /d "ai"
start /min gameclient.bat 1111 127.0.0.1 6001
popd

pushd %CD%
cd /d "client"
start /min gameclient.bat 6666 127.0.0.1 6001
popd

