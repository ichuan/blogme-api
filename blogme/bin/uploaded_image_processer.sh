#!/bin/bash
# deps:
#   convert
# https://github.com/ichuan/blogme-api/issues/3#issuecomment-566463033

# compress quality, 1~100
QUALITY=80
# output img pixels
MAX_WIDTH=1600

# https://stackoverflow.com/a/246128
SCRIPT_DIR="$(cd "`dirname "${BASH_SOURCE[0]}"`">/dev/null 2>&1 && pwd)"
API_LOG="${SCRIPT_DIR}/../../logs/api.log"

if ggrep -V >/dev/null 2>&1; then
  # macOS: brew install grep
  GREP=ggrep
else
  # Linux
  GREP=grep
fi


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
    convert "$img" -auto-orient -strip -interlace Plane -quality $QUALITY -resize "${MAX_WIDTH}>" "$img"
    time_cost=$(( `date +%s` - $start_at ))
    logit Cost ${time_cost}s
  }
}


tail -F "$API_LOG" | $GREP --color=never --line-buffered -oP '(?<=Uploaded file: ).+\.(jpe?g|png|gif)$' | while read line; do
  process_image "$line"
done;
