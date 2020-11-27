#!/bin/bash

# Presume: flacs are in ./files/flac
# Note: all tests are idempotent

function given_all_files_when_remove_all_mp3-files_and_transcode_then_correct_logfile_and_filecount {
    echo "* ${FUNCNAME[0]}"
    rm -f ./files/mtranscoder.log
    rm -rf ./files/mp3/*
    python3 ~/source/transcoder/transcoder.py ./files/flac/ --mp3folder ./files/mp3 --logfolder ./files/
    if cat ./files/mtranscoder.log | grep -q "transcoded to mp3: 10"; then echo "(log) OK"; else echo "(log) Fail"; fi
    if find ./files/mp3 -type f | wc -l  | grep -q "13"; then echo "(count) OK"; else echo "(count) Fail"; fi
}

function given_all_files_when_remove_all_ogg-files_and_transcode_then_correct_logfile_and_filecount {
    echo "* ${FUNCNAME[0]}"
    rm -f ./files/mtranscoder.log
    rm -rf ./files/ogg/*
    python3 ~/source/transcoder/transcoder.py ./files/flac/ --oggfolder ./files/ogg --logfolder ./files/
    if cat ./files/mtranscoder.log | grep -q "transcoded to ogg: 10"; then echo "(log) OK"; else echo "(log) Fail"; fi
    if find ./files/ogg -type f | wc -l  | grep -q "13"; then echo "(count) OK"; else echo "(count) Fail"; fi
}

function given_all_files_when_remove_one_mp3-file_and_transcode_then_correct_logfile_and_filecount {
    echo "* ${FUNCNAME[0]}"
    python3 ~/source/transcoder/transcoder.py ./files/flac/ --mp3folder ./files/mp3 --logfolder ./files/
    rm -f ./files/mtranscoder.log
    rm -rf "./files/mp3/Nightwish/Human II Nature/02 - Noise.mp3"
    python3 ~/source/transcoder/transcoder.py ./files/flac/ --mp3folder ./files/mp3 --logfolder ./files/
    if cat ./files/mtranscoder.log | grep -q "transcoded to mp3: 1"; then echo "(log) OK"; else echo "(log) Fail"; fi
    if find ./files/mp3 -type f | wc -l  | grep -q "13"; then echo "(count) OK"; else echo "(count) Fail"; fi
}

function given_all_files_when_remove_cover-file_and_transcode_then_correct_logfile {
    echo "* ${FUNCNAME[0]}"
    python3 ~/source/transcoder/transcoder.py ./files/flac/ --mp3folder ./files/mp3 --logfolder ./files/
    rm -f ./files/mtranscoder.log
    rm -rf "./files/mp3/Nightwish/Human II Nature/cover.jpg"
    python3 ~/source/transcoder/transcoder.py ./files/flac/ --mp3folder ./files/mp3 --logfolder ./files/
    if cat ./files/mtranscoder.log | grep -q "embedding album art \[source_tree\]/Nightwish/Human II Nature/cover.jpg"; then echo "(log) OK"; else echo "(log) Fail"; fi
}

given_all_files_when_remove_all_mp3-files_and_transcode_then_correct_logfile_and_filecount
given_all_files_when_remove_all_ogg-files_and_transcode_then_correct_logfile_and_filecount
given_all_files_when_remove_one_mp3-file_and_transcode_then_correct_logfile_and_filecount
given_all_files_when_remove_cover-file_and_transcode_then_correct_logfile
