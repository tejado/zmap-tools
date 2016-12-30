#!/usr/bin/env bash

INPUT_FILE=$1
OUTPUT_FILE=$2
OUTPUT_ERROR_FILE=$2.err

STATE_FILE=.zscan_state_$$
rm -f $STATE_FILE 2> /dev/null

#PORTS_HTTP="80 8080 18080 28080 38080 48080 58080"
PORTS_HTTP="80 8080"
#PORTS_HTTPS="443 8443 18443 28443 38443 48443 58443"
PORTS_HTTPS="443 8443"

if [ ! -f $INPUT_FILE ]; then
    echo "Error: Input file '$INPUT_FILE' not found!"
    exit 1
fi

if [ -f $OUTPUT_FILE ]; then
    echo "Error: Output file '$OUTPUT_FILE' must not exist!"
    exit 2
fi

touch "$STATE_FILE" 2> /dev/null || { echo "Cannot write to $STATE_FILE" >&2; exit 3; }
touch "$OUTPUT_FILE" 2> /dev/null || { echo "Cannot write to $OUTPUT_FILE" >&2; exit 3; }
touch "$OUTPUT_ERROR_FILE" 2> /dev/null || { echo "Cannot write to $OUTPUT_ERROR_FILE" >&2; exit 3; }

while read NETWORK; do
  OUTPUT_PREFIX=$(echo $NETWORK | sed 's/\/..//').

  # http
  for PORT in $PORTS_HTTP
  do
    STEP=${NETWORK}:${PORT}
    if grep -Fxq "$STEP" $STATE_FILE
    then
      continue
    fi

    sudo zmap -p $PORT $NETWORK -r 1000000 --output-field=* | ztee ${OUTPUT_PREFIX}_${PORT}.out | zgrab --port $PORT --http="/" >> $OUTPUT_FILE 2>> $OUTPUT_ERROR_FILE

    echo $STEP >> $STATE_FILE
    rm ${OUTPUT_PREFIX}_${PORT}.out
  done

  # https
  for PORT in $PORTS_HTTPS
  do
    STEP=${NETWORK}:${PORT}
    if grep -Fxq "$STEP" $STATE_FILE
    then
      continue
    fi

    sudo zmap -p $PORT $NETWORK -r 1000000 --output-field=* | ztee ${OUTPUT_PREFIX}_${PORT}.out | zgrab --port $PORT --http="/" --tls >> $OUTPUT_FILE 2>> $OUTPUT_ERROR_FILE

    echo $STEP >> $STATE_FILE
    rm ${OUTPUT_PREFIX}_${PORT}.out
  done

done < $INPUT_FILE

rm -f $STATE_FILE 2> /dev/null
