Example: <br/> 
`sudo docker run --user "$(id -u):$(id -g)" -v <location for flac files>:/zone transcoder transcoder.py --verbose --mp3folder ./mp3 ./flac`<br/> 
 
 Note(s):<br/>
 
 - by setting --user, transcoded files will be created in the context of the user who executes the command instead of root

  