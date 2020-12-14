#!/bin/bash
# Presume: flacs are in $root/flac

root="./files"
python3 ../transcoder.py --verbose $root/flac/ --mp3folder $root/mp3 --oggfolder $root/ogg