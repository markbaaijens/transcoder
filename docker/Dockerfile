FROM ubuntu
RUN apt update
RUN apt install vorbis-tools -y
RUN apt install lame -y
RUN apt install flac -y
RUN apt install python3 -y
RUN apt install python3-mutagen -y 
RUN apt install python3-pil  -y
RUN apt install wget -y
RUN wget https://raw.githubusercontent.com/markbaaijens/transcoder/master/transcoder.py -O /usr/local/bin/transcoder.py
RUN chmod +x /usr/local/bin/transcoder.py
RUN mkdir /source