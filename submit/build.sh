rm -rf chier*
mkdir chier

cp -r ../client ./chier
cp gameclient.sh ./chier
cp config.py chier/client/ballclient/auth/

cd chier

rm -rf client/gameclient.bat


zip -r chier.zip *
mv chier.zip ../