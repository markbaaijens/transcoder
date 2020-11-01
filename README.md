# Transcoder
Transcode lossless music files (flac) into lossy ones (mp3/ogg)

## Description
Script for transcoding lossless audio files (flac) to lossy formats like mp3 or ogg. When transcoding, tags are derived 
from the lossless file. Also album art is embedded in the lossy file. In the end, the lossy tree exactly resembles the
lossless tree: (lossy) files which do not have a lossless source, are deleted. Script can be run in a headless environment, 
logging to a predefined logfolder.

## Installation 
- install dependencies (Ubuntu 16.04+):
  sudo apt install vorbis-tools  # oggenc
  sudo apt install lame 
  sudo apt install flac 
  sudo apt install python-mutagen
- wget https://sourceforge.net/p/aaa/code/HEAD/tree/trunk/transcoder/mtranscoder.py?format=raw -O mtranscoder.py
- chmod +x mtranscoder.py

## Usage
python transcoder.py --help
(using python is as a prefix optional, ./mtranscoder.py also works)

## Example(s)
python transcoder.py --verbose <music folder>/flac --mp3folder <music folder>/mp3 --logfolder .
- show output to console, transcoding to mp3 (default to 128 kbs), log to current folder
python transcoder.py <music folder>/flac --mp3folder <music folder>/mp3 --mp3bitrate 256
- transcoding to mp3 at bitrate 256 kbs (default = 128 kbs), no output
python transcoder.py --dry-run --verbose <music folder>/flac --oggfolder <music folder>/ogg --oggquality 3
- test run, show output to console, transcoding to ogg at level 3 (default = 1) 

## Notes
- if no value is given to mp3folder, no transcoding to mp3 will take place
- if no value is given to oggfolder, no transcoding to ogg will take place
- note that lossy folders *must* exist before transcoding
- when given --logfolder, operations will be logged to mtranscoder.log
  - watch log: tail -f <logfolder>mtranscoder.log   
- for embedding album art in the transcoded files, the script expects a file cover.jpg 
  in the lossless (flac) folder; otherwise no embedding can take place
