pushd %CD%
python -m ballclient.main %1 %2 %3 > ballclient/log/server.txt
popd

EXIT