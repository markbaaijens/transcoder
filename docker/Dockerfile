FROM ubuntu
RUN apt-get update
RUN apt-get install vorbis-tools -y
RUN apt-get install lame -y
RUN apt-get install flac -y
RUN apt-get install python3 -y
RUN apt-get install python3-mutagen -y 
RUN apt-get install python3-pil  -y
COPY ./transcoder.py  /usr/local/bin/transcoder.py
RUN chmod +x /usr/local/bin/transcoder.py
RUN mkdir /zone
WORKDIR /zone
RUN apt-get autoremove -y 
RUN apt-get clean 
RUN rm -rf /var/lib/apt/lists/*