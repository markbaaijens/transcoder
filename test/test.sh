#!/bin/bash
# Presume: flacs are in $root/flac
# Note: all tests are idempotent

function given_all_files_when_remove_all_mp3-files_and_transcode_then_correct_logfile_and_mp3_filecount {
    echo "* ${FUNCNAME[0]}"
    source="$root/flac"
    destination="$root/mp3"
    python3 ../transcoder.py $source --mp3folder $destination --logfolder $root/
    rm -f $root/$log_file

    rm -rf $destination/*
    python3 ../transcoder.py $source --mp3folder $destination --logfolder $root/

    if cat $root/$log_file | grep -q "transcoded to mp3: $(find $source -type f -name "*.flac" | wc -l)"; then echo "(log) OK"; else echo "(log) Fail"; fi
    if find $destination -type f -name "*.mp3" | wc -l  | grep -q "$(find $source -type f -name "*.flac" | wc -l)"; then echo "(count) OK"; else echo "(count) Fail"; fi
}

function given_all_files_when_remove_all_ogg-files_and_transcode_then_correct_logfile_and_ogg_filecount {
    echo "* ${FUNCNAME[0]}"
    source="$root/flac"
    destination="$root/ogg"
    python3 ../transcoder.py $source --oggfolder $destination --logfolder $root/
    rm -f $root/$log_file

    rm -rf $destination/*
    python3 ../transcoder.py $source --oggfolder $destination --logfolder $root/
    
    if cat $root/$log_file | grep -q "transcoded to ogg: $(find $source -type f -name "*.flac" | wc -l)"; then echo "(log) OK"; else echo "(log) Fail"; fi
    if find $destination -type f -name "*.ogg" | wc -l  | grep -q "$(find $source -type f -name "*.flac" | wc -l)"; then echo "(count) OK"; else echo "(count) Fail"; fi
}

function given_all_files_when_remove_one_mp3-file_and_transcode_then_correct_logfile_and_mp3_filecount {
    echo "* ${FUNCNAME[0]}"
    source="$root/flac"
    destination="$root/mp3"
    python3 ../transcoder.py $source --mp3folder $destination --logfolder $root/
    rm -f $root/$log_file

    readarray -d '' mp3s < <(find $destination -type f -name "*.mp3" -print0)
    rm -rf "${mp3s[0]}"

    python3 ../transcoder.py $source --mp3folder $destination --logfolder $root/
    
    if cat $root/$log_file | grep -q "transcoded to mp3: 1"; then echo "(log) OK"; else echo "(log) Fail"; fi
    if find $destination -type f -name "*.mp3" | wc -l  | grep -q "$(find $source -type f -name "*.flac" | wc -l)"; then echo "(count) OK"; else echo "(count) Fail"; fi
}

function given_all_files_when_remove_cover-file_and_transcode_then_correct_logfile {
    echo "* ${FUNCNAME[0]}"
    source="$root/flac"
    destination="$root/mp3"
    python3 ../transcoder.py $source --mp3folder $destination --logfolder $root/
    rm -f $root/$log_file
    
    readarray -d '' images < <(find $destination -type f -name "cover.jpg" -print0)
    image="${images[0]}"
    rm -rf "$image"
    python3 ../transcoder.py $source --mp3folder $destination --logfolder $root/

    searchstringlog=${image/$destination/"\- copying to \[mp3_tree\]"}
    if cat $root/$log_file | grep -q "$searchstringlog"; then echo "(log) OK"; else echo "(log) Fail"; fi
}

function given_all_files_when_changed_to_newer_date_of_flac_then_retranscode {
    echo "* ${FUNCNAME[0]}"
    source="$root/flac"
    destination="$root/mp3"
    python3 ../transcoder.py $source --mp3folder $destination --logfolder $root/
    rm -f $root/$log_file

    readarray -d '' flacs < <(find $source -type f -name "*.flac" -print0)
    touch "${flacs[0]}"
    python3 ../transcoder.py $source --mp3folder $destination --logfolder $root/

    if cat $root/$log_file | grep -q "transcoded to mp3: 1"; then echo "(log) OK"; else echo "(log) Fail"; fi
}

function given_all_files_when_changed_to_newer_date_of_source_cover-jpg_then_re-embed {
    echo "* ${FUNCNAME[0]}"
    source="$root/flac"
    destination="$root/mp3"
    python3 ../transcoder.py $source --mp3folder $destination --logfolder $root/
    rm -f $root/$log_file

    readarray -d '' images < <(find $source -type f -name "cover.jpg" -print0)
    image="${images[0]}"
    touch "$image"
    python3 ../transcoder.py $source --mp3folder $destination --logfolder $root/

    if cat $root/$log_file | grep -q "\- cover files copied: 1"; then echo "(log) OK"; else echo "(log) Fail"; fi
    if cat $root/$log_file | grep -q "\- covers embedded in files: $(find "${image/"cover.jpg"/""}" -type f -name "*.flac" | wc -l)"; then echo "(log) OK"; else echo "(log) Fail"; fi
}

function given_all_files_when_delete_source_file_then_delete_lossy_file {
    echo "* ${FUNCNAME[0]}"
    source="$root/flac"
    python3 ../transcoder.py $source --mp3folder $root/mp3 --oggfolder $root/ogg --logfolder $root/
    rm -f $root/$log_file

    readarray -d '' flacs < <(find $source -type f -name "*.flac" -print0)
    rm -rf "${flacs[0]}"
    python3 ../transcoder.py $source --mp3folder $root/mp3 --oggfolder $root/ogg --logfolder $root/

    if find $root/mp3 -type f -name "*.mp3" | wc -l  | grep -q "$(find $source -type f -name "*.flac" | wc -l)"; then echo "(count mp3) OK"; else echo "(count mp3) Fail"; fi
    if find $root/ogg -type f -name "*.ogg" | wc -l  | grep -q "$(find $source -type f -name "*.flac" | wc -l)"; then echo "(count ogg) OK"; else echo "(count ogg) Fail"; fi
    if cat $root/$log_file | grep -q "\- obsolete files deleted: 2"; then echo "(log) OK"; else echo "(log) Fail"; fi
}

function given_all_files_when_create_folders_in_lossy_tree_and_transcode_then_delete_lossy_folders {
    echo "* ${FUNCNAME[0]}"
    source="$root/flac"
    python3 ../transcoder.py $source --mp3folder $root/mp3 --oggfolder $root/ogg --logfolder $root/
    rm -f $root/$log_file

    mkdir $root/ogg/Temp1
    mkdir $root/mp3/Temp2
    mkdir $root/mp3/Temp3
    python3 ../transcoder.py $source --mp3folder $root/mp3 --oggfolder $root/ogg --logfolder $root/

    if cat $root/$log_file | grep -q "\- empty folders deleted: 3"; then echo "(log) OK"; else echo "(log) Fail"; fi
}

function given_all_files_when_delete_lossy_file_and_transcode_then_check_if_tags_in_mp3_and_ogg_are_the_same_as_in_source
{
    echo "* ${FUNCNAME[0]}"
    source="$root/flac"
    python3 ../transcoder.py $source --mp3folder $root/mp3 --oggfolder $root/ogg --logfolder $root/
    rm -f $root/$log_file

    readarray -d '' flacs < <(find $source -type f -name "*.flac" -print0)
    mp3_file=$(echo "${flacs[0]}" | sed -e "s/\/flac\//\/mp3\//g" -e "s/\.flac$/.mp3/g") 
    ogg_file=$(echo "${flacs[0]}" | sed -e "s/\/flac\//\/ogg\//g" -e "s/\.flac$/.ogg/g")

    rm -f $mp3_file
    rm -f $ogg_file
    python3 ../transcoder.py $source --mp3folder $root/mp3 --oggfolder $root/ogg --logfolder $root/

    failure=0
    flac_tag=$(metaflac "${flacs[0]}" --show-tag=TITLE | cut -d"=" -f 2)
    ogg_tag=$(vorbiscomment -l "$ogg_file" | grep "TITLE" | cut -d"=" -f 2)
    mp3_tag=$(ffprobe "$mp3_file" -show_entries format_tags=title -of compact=p=0:nk=1 -v 0)
    if [[ "$flac_tag" != "$ogg_tag" ]]; then failure=1; fi
    if [[ "$flac_tag" != "$mp3_tag" ]]; then failure=1; fi

    flac_tag=$(metaflac "${flacs[0]}" --show-tag=ARTIST | cut -d"=" -f 2)
    ogg_tag=$(vorbiscomment -l "$ogg_file" | grep "ARTIST" | cut -d"=" -f 2)
    mp3_tag=$(ffprobe "$mp3_file" -show_entries format_tags=artist -of compact=p=0:nk=1 -v 0)
    if [[ "$flac_tag" != "$ogg_tag" ]]; then failure=1; fi
    if [[ "$flac_tag" != "$mp3_tag" ]]; then failure=1; fi
    
    flac_tag=$(metaflac "${flacs[0]}" --show-tag=ALBUM | cut -d"=" -f 2)
    ogg_tag=$(vorbiscomment -l "$ogg_file" | grep "ALBUM" | cut -d"=" -f 2)
    mp3_tag=$(ffprobe "$mp3_file" -show_entries format_tags=album -of compact=p=0:nk=1 -v 0)
    if [[ "$flac_tag" != "$ogg_tag" ]]; then failure=1; fi
    if [[ "$flac_tag" != "$mp3_tag" ]]; then failure=1; fi
    
    flac_tag=$(metaflac "${flacs[0]}" --show-tag=DATE | cut -d"=" -f 2)
    ogg_tag=$(vorbiscomment -l "$ogg_file" | grep "DATE" | cut -d"=" -f 2)
    mp3_tag=$(ffprobe "$mp3_file" -show_entries format_tags=date -of compact=p=0:nk=1 -v 0)
    if [[ "$flac_tag" != "$ogg_tag" ]]; then failure=1; fi
    if [[ "$flac_tag" != "$mp3_tag" ]]; then failure=1; fi
    
    flac_tag=$(metaflac "${flacs[0]}" --show-tag=TRACKNUMBER | cut -d"=" -f 2)
    ogg_tag=$(vorbiscomment -l "$ogg_file" | grep "TRACKNUMBER" | cut -d"=" -f 2)
    mp3_tag=$(ffprobe "$mp3_file" -show_entries format_tags=track -of compact=p=0:nk=1 -v 0)
    if [[ "$flac_tag" != "$ogg_tag" ]]; then failure=1; fi
    if [[ "$flac_tag" != "$mp3_tag" ]]; then failure=1; fi

    if [[ $failure == 0 ]]; then echo "(tags) OK"; else echo "(tags) Fail"; fi
}

function given_all_files_when_delete_cover_art_from_a_lossy_tree_and_transcode_then_check_if_copied_cover_art_is_the_same_as_the_source
{
    echo "* ${FUNCNAME[0]}"
    source="$root/flac"
    python3 ../transcoder.py $source --mp3folder $root/mp3 --logfolder $root/
    rm -f $root/$log_file

    readarray -d '' images < <(find $source -type f -name "cover.jpg" -print0)
    source_image="${images[0]}"
    lossy_image=$(echo "$source_image" | sed -e "s/\/flac\//\/mp3\//g")
    rm "$lossy_image"
    python3 ../transcoder.py $source --mp3folder $root/mp3 --logfolder $root/

    if [[ $(md5sum "$source_image" | cut -d" " -f 1) == $(md5sum "$lossy_image" | cut -d" " -f 1) ]]; then echo "(checksum) OK"; else echo "(checksum) Fail"; fi
}

function given_all_files_when_delete_lossy_file_and_transcode_then_check_if_copied_album_art_is_actually_embedded_in_the_music_file
{
    echo "* ${FUNCNAME[0]}"
    source="$root/flac"
    destination="$root/mp3"
    python3 ../transcoder.py $source --mp3folder $destination --logfolder $root/
    rm -f $root/$log_file

    readarray -d '' mp3s < <(find $destination -type f -name "*.mp3" -print0)
    mp3_file="${mp3s[0]}"
    rm "$mp3_file"
    python3 ../transcoder.py $source --mp3folder $destination --logfolder $root/

    mp3_dir=$(echo "$mp3_file" | rev | cut -d"/" -f2- | rev)
    ffmpeg -i "$mp3_file" "$mp3_dir/output.jpg" -y > /dev/null 2>&1
    if find "$mp3_dir" -type f -name "output.jpg" | wc -l | grep -q "1"; then echo "(embedded) OK"; else echo "(embedded) Fail"; fi
}

root="./files"
log_file="transcoder.log"

given_all_files_when_remove_all_mp3-files_and_transcode_then_correct_logfile_and_mp3_filecount
given_all_files_when_remove_all_ogg-files_and_transcode_then_correct_logfile_and_ogg_filecount
given_all_files_when_remove_one_mp3-file_and_transcode_then_correct_logfile_and_mp3_filecount
given_all_files_when_remove_cover-file_and_transcode_then_correct_logfile
given_all_files_when_changed_to_newer_date_of_flac_then_retranscode
given_all_files_when_changed_to_newer_date_of_source_cover-jpg_then_re-embed
given_all_files_when_delete_source_file_then_delete_lossy_file
given_all_files_when_create_folders_in_lossy_tree_and_transcode_then_delete_lossy_folders
given_all_files_when_delete_lossy_file_and_transcode_then_check_if_tags_in_mp3_and_ogg_are_the_same_as_in_source
given_all_files_when_delete_cover_art_from_a_lossy_tree_and_transcode_then_check_if_copied_cover_art_is_the_same_as_the_source
given_all_files_when_delete_lossy_file_and_transcode_then_check_if_copied_album_art_is_actually_embedded_in_the_music_file