#!/usr/bin/env bash

name=$(basename "$1")
ext="${name##*.}"
name="${name%.*}"
new="${name}.meta.${ext}"

convert "$1" -resize 1x1 "$new"
exiftool -overwrite_original_in_place -ThumbnailImage= -PreviewImage= "$new"
touch "$new" --reference="$1"

diff <(exiftool "$1" | sort) <(exiftool "$new" | sort) -U 0