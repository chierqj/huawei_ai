pushd %CD%
python -m ballclient.main %1 %2 %3 > ../log/client.txt
popd

EXIT