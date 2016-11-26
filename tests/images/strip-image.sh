#!/usr/bin/env bash

# Albumin Image Metadata Remover
# Copyright (C) 2016 Alper Nebi Yasak
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

name=$(basename "$1")
ext="${name##*.}"
name="${name%.*}"
new="${name}.meta.${ext}"

convert "$1" -resize 1x1 "$new"
exiftool -overwrite_original_in_place -ThumbnailImage= -PreviewImage= "$new"
touch "$new" --reference="$1"

diff <(exiftool "$1" | sort) <(exiftool "$new" | sort) -U 0