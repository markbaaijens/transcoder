# Transcoder
Transcode lossless music files (flac) into lossy ones (mp3/ogg).

## Description
Script for transcoding lossless audio files (flac) to lossy formats like mp3 or ogg. When transcoding, tags are derived 
from the lossless file. Also album art is embedded in the lossy file. In the end, the lossy tree exactly resembles the
lossless tree: (lossy) files which do not have a lossless source, are deleted. Script can be run in a headless environment, 
logging to a predefined logfolder.

## Requirements
- python3

## Installation
`sudo apt install vorbis-tools  # oggenc`<br/> 
`sudo apt install lame`<br/>
`sudo apt install flac`<br/>
`sudo apt install python3-mutagen # alternative $ pip3 install mutagen`<br/>
`sudo apt install python3-pil  # alternative $ pip3 install pillow`<br/>

`wget https://raw.githubusercontent.com/markbaaijens/transcoder/master/transcoder.py -O transcoder.py`<br/>
`chmod +x transcoder.py`<br/>

## Usage
`python3 transcoder.py --help`<br/>
(using python3 as a prefix is optional, ./transcoder.py also works)

## Tools needed for testing
`sudo apt install ffmpeg`<br/> 

## Example(s)
`python3 transcoder.py --verbose <music folder>/flac --mp3folder <music folder>/mp3 --logfolder .`<br/>
show output to console, transcoding to mp3 (default to 128 kbs), log to current folder

`python3 transcoder.py <music folder>/flac --mp3folder <music folder>/mp3 --mp3bitrate 256`<br/>
transcoding to mp3 at bitrate 256 kbs (default = 128 kbs), no output

`python3 transcoder.py --dry-run --verbose <music folder>/flac --oggfolder <music folder>/ogg --oggquality 3`<br/>
test run, show output to console, transcoding to ogg at level 3 (default = 1)

`python3 transcoder.py --verbose <music folder>/flac/ --mp3folder <music folder>/mp3 --oggfolder <music folder>/ogg`<br/>
transcode simultaneously to mp3 and ogg

## Notes
- if no value is given to mp3folder, no transcoding to mp3 will take place
- if no value is given to oggfolder, no transcoding to ogg will take place
- note that lossy folders *must* exist before transcoding
- when given --logfolder, operations will be logged to transcoder.log
  - watch log: tail -f <logfolder>transcoder.log
- for embedding album art in the transcoded files, the script expects a file cover.jpg 
  in the lossless (flac) folder; otherwise no embedding can take place
- transcoded files won't be checked on there current compression (MP3 bitrate / OGG quality level) and will be ignored
