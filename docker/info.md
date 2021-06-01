# Example bash command line<br/> 
`sudo docker run --user "$(id -u):$(id -g)" -v <location for flac files>:/zone transcoder transcoder.py --verbose --mp3folder ./mp3 ./flac`<br/> 
 
Note(s):<br/>
 
 - by setting --user, transcoded files will be created in the context of the user who executes the command instead of root

# Examples docker-compose.yml<br />

## Enviroment tags<br />

```
transcoder:
  image: transcoder
  container_name: transcoder2
  volumes:
    - <location for flac files>:/zone
  command: transcoder.py
  user: <PUID>:<PGID>
  environment:
    - mp3-folder=./mp3
    - ogg-folder=./ogg
    - ./flac
    - verbose
```

## Arguments in command line<br/>

```
transcoder:
  image: transcoder
  container_name: transcoder2
  volumes:
    - <location for flac files>:/zone
  command: transcoder.py --mp3-folder=./mp3 --ogg-folder=./ogg ./flac --verbose
  user: <PUID>:<PGID>
```