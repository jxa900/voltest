#!/bin/bash
# this script parses iozone output, calculates average and maximum iops values and prints it all out in a form that's easy to graph and read
# written by Kuba C at NCI on 9/11/2012

# go where the resultssets are
cd results/out;

# Average IOPS
echo "Avg_IOPS"
# grab the first one to get headers 
FIRST_FILE=$(ls 10.* | sort -n | head -1)
cat $FIRST_FILE | grep report\" | awk '{ printf "%s ", $0 }';
# add a newline
echo "";
# now go through all and extract the data
for i in $(ls 10.*); do
cat $i | 
# get the line with numbers - two lines down from the header - and get rid of the odd line
awk '/report/ { getline; getline; print $0}' |  grep -v Output |
# calculate averages
awk '{sum=0; n=0; for(i=1;i<=NF;i++) {sum+=$i; ++n}; print sum/(n-1)}' | 
# turn columns to rows for easier processing and graphing
awk '{ for (i = 1; i <= NF; i++) f[i] = f[i] " " $i ; if (NF > n) n = NF } END { for (i = 1; i <= n; i++) sub(/^  */, "", f[i]) ; for (i = 1; i <= n; i++) print f[i] }';
done

# Maximum IOPS
echo "MAX_IOPS"
# grab the first one to get headers 
FIRST_FILE=$(ls 10.* | sort -n | head -1)
cat $FIRST_FILE | grep report\" | awk '{ printf "%s ", $0 }';
# add a newline
echo "";
# now go through all and extract the data
for i in $(ls 10.*); do
cat $i | 
# get the line with numbers - two lines down from the header - and get rid of the odd line
awk '/report/ { getline; getline; print $0}' |  grep -v Output |
# calculate maximums
awk '{max=$2; for(i=2;i<=NF;i++) if( $i > max) max=$i; print max}' |
# turn columns to rows for easier processing and graphing
awk '{ for (i = 1; i <= NF; i++) f[i] = f[i] " " $i ; if (NF > n) n = NF } END { for (i = 1; i <= n; i++) sub(/^  */, "", f[i]) ; for (i = 1; i <= n; i++) print f[i] }';
done

# Throughput
echo "IO_Throughput"
#grab the first one to get the headers; use awk to match the content between opening and closing strings
cat $FIRST_FILE | awk '/iozone test complete./{p=0};p;/Record size = 4 Kbytes /{p=1}' |
#remove one odd line that gets in the way
grep -v Output | awk '{$NF=""}1' |
# remove newlines and spaces inside quotes
awk '{ printf "%s ", $0 }' | sed 's/" /"/g; s/ "/"/g' 
# add a newline
echo "";
# now go through all the host-specific files and extract the information
for i in $(ls 10.*); do
# use awk to match the content between the opening and closing strings
awk '/iozone test complete./{p=0};p;/Record size = 4 Kbytes /{p=1}' $i |
# remove the odd line
grep -v Output | awk '{print $NF}' |
# print out as a row, not a column
awk '{ printf "%s ", $0 }' |
# remove the whitespace at the beginning of the output and any repeated spaces (drives libre calc nuts)
tr -s ' ' | sed 's/^ \(.*\)/\1/g'
# add a closing newline
echo "";
#
done
# and that's it
