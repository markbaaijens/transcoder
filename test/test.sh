#!/bin/bash
# Presume: flacs are in $root/flac
# Note: all tests are idempotent

function given_all_files_when_remove_all_mp3-files_and_transcode_then_correct_logfile_and_filecount {
    echo "* ${FUNCNAME[0]}"
    rm -f $root/$log_file
    rm -rf $root/mp3/*
    python3 ../transcoder.py $root/flac/ --mp3folder $root/mp3 --logfolder $root/
    if cat $root/$log_file | grep -q "transcoded to mp3: 10"; then echo "(log) OK"; else echo "(log) Fail"; fi
    if find $root/mp3 -type f | wc -l  | grep -q "13"; then echo "(count) OK"; else echo "(count) Fail"; fi
}

function given_all_files_when_remove_all_ogg-files_and_transcode_then_correct_logfile_and_filecount {
    echo "* ${FUNCNAME[0]}"
    rm -f $root/$log_file
    rm -rf $root/ogg/*
    python3 ../transcoder.py $root/flac/ --oggfolder $root/ogg --logfolder $root/
    if cat $root/$log_file | grep -q "transcoded to ogg: 10"; then echo "(log) OK"; else echo "(log) Fail"; fi
    if find $root/ogg -type f | wc -l  | grep -q "13"; then echo "(count) OK"; else echo "(count) Fail"; fi
}

function given_all_files_when_remove_one_mp3-file_and_transcode_then_correct_logfile_and_filecount {
    echo "* ${FUNCNAME[0]}"
    python3 ../transcoder.py $root/flac/ --mp3folder $root/mp3 --logfolder $root/
    rm -f $root/$log_file
    rm -rf "$root/mp3/Nightwish/Human II Nature/02 - Noise.mp3"
    python3 ../transcoder.py $root/flac/ --mp3folder $root/mp3 --logfolder $root/
    if cat $root/$log_file | grep -q "transcoded to mp3: 1"; then echo "(log) OK"; else echo "(log) Fail"; fi
    if find $root/mp3 -type f | wc -l  | grep -q "13"; then echo "(count) OK"; else echo "(count) Fail"; fi
}

function given_all_files_when_remove_cover-file_and_transcode_then_correct_logfile {
    echo "* ${FUNCNAME[0]}"
    python3 ../transcoder.py $root/flac/ --mp3folder $root/mp3 --logfolder $root/
    rm -f $root/$log_file
    rm -rf "$root/mp3/Nightwish/Human II Nature/cover.jpg"
    python3 ../transcoder.py $root/flac/ --mp3folder $root/mp3 --logfolder $root/
    if cat $root/$log_file | grep -q "embedding album art \[source_tree\]/Nightwish/Human II Nature/cover.jpg"; then echo "(log) OK"; else echo "(log) Fail"; fi
}

root="./files"
log_file="mtranscoder.log"

given_all_files_when_remove_all_mp3-files_and_transcode_then_correct_logfile_and_filecount
given_all_files_when_remove_all_ogg-files_and_transcode_then_correct_logfile_and_filecount
given_all_files_when_remove_one_mp3-file_and_transcode_then_correct_logfile_and_filecount
given_all_files_when_remove_cover-file_and_transcode_then_correct_logfile
