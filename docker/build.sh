# Must be executed as sudo
# sudo chmod +x build.sh
cp ../transcoder.py .
docker build -t transcoder .
rm transcoder.py