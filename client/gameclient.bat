pushd %CD%
python -m ballclient.main %1 %2 %3 > ballclient/log/server.txt
sleep 10s
popd

EXIT