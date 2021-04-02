FROM ubuntu
RUN apt-get update
RUN apt-get install vorbis-tools -y
RUN apt-get install vorbis-tools -y
RUN apt-get install vorbis-tools -y
RUN apt-get install vorbis-tools -y
RUN apt-get install lame -y
RUN apt-get install flac -y
RUN apt-get install python3 -y
RUN apt-get install python3-mutagen -y 
RUN apt-get install python3-pil  -y
RUN apt-get install wget -y
RUN wget https://raw.githubusercontent.com/markbaaijens/transcoder/master/transcoder.py -O /usr/local/bin/transcoder.py
RUN chmod +x /usr/local/bin/transcoder.py
RUN mkdir /source
RUN apt-get autoremove -y 
RUN apt-get clean 
RUN rm -rf /var/lib/apt/lists/*