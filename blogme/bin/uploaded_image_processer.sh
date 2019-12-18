#!/bin/bash
# deps:
#   fswatch
#   convert
# https://github.com/ichuan/blogme-api/issues/3#issuecomment-566463033

# compress quality, 1~100
QUALITY=80
# output img pixels
MAX_WIDTH=1600

# https://stackoverflow.com/a/246128
SCRIPT_DIR="$(cd "`dirname "${BASH_SOURCE[0]}"`">/dev/null 2>&1 && pwd)"
UPLOAD_DIR="`dirname ${SCRIPT_DIR}`/public/upload"

logit() {
  echo "[`date '+%F %T'`] $*"
}


process_image() {
  img="$1"
  flag="${img}.__PROCESSED__"
  [ ! -f "$img" ] && return
  [ -f "$flag" ] || {
    touch "$flag"
    logit Processing $img
    start_at=`date +%s`
    convert "$img" -auto-orient -strip -quality $QUALITY -resize "${MAX_WIDTH}>" "$img"
    time_cost=$(( `date +%s` - $start_at ))
    logit Cost ${time_cost}s
  }
}


fswatch -0 --event Renamed --event Updated --extended --insensitive --exclude ".*" \
  --include "\.(jpg|jpeg|png|webp|bmp)$" ${UPLOAD_DIR} | while read -d "" event; \
  do process_image "$event"; done
