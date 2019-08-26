@echo off
pushd %CD%
curl --header "Content-Type:text/plain" "https://www.kosphere.cn/server/replay.txt" > %CD%\server\replay.txt
popd