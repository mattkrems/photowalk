#!/bin/bash 

directory='/home/mkrems/Flickr_complete/'
tgz_base='I3_part_'
bz2_base='yfcc100m_dataset-'


tar zxvf $directory$tgz_base"1.tgz" -C $directory
num='0'
bzip2 -d $directory$bz2_base$num".bz2"
python flickr_db.py $directory$bz2_base$num
rm -f $directory$bz2_base$num
num='1'
bzip2 -d $directory$bz2_base$num".bz2"
python flickr_db.py $directory$bz2_base$num
rm -f $directory$bz2_base$num
 

tar zxvf $directory$tgz_base"2.tgz" -C $directory
num='2'
bzip2 -d $directory$bz2_base$num".bz2"
python flickr_db.py $directory$bz2_base$num
rm -f $directory$bz2_base$num
num='3'
bzip2 -d $directory$bz2_base$num".bz2"
python flickr_db.py $directory$bz2_base$num
rm -f $directory$bz2_base$num
num='4'
bzip2 -d $directory$bz2_base$num".bz2"
python flickr_db.py $directory$bz2_base$num
rm -f $directory$bz2_base$num
 

tar zxvf $directory$tgz_base"3.tgz" -C $directory
num='5'
bzip2 -d $directory$bz2_base$num".bz2"
python flickr_db.py $directory$bz2_base$num
rm -f $directory$bz2_base$num
num='6'
bzip2 -d $directory$bz2_base$num".bz2"
python flickr_db.py $directory$bz2_base$num
rm -f $directory$bz2_base$num
num='7'
bzip2 -d $directory$bz2_base$num".bz2"
python flickr_db.py $directory$bz2_base$num
rm -f $directory$bz2_base$num


tar zxvf $directory$tgz_base"4.tgz" -C $directory
num='8'
bzip2 -d $directory$bz2_base$num".bz2"
python flickr_db.py $directory$bz2_base$num
rm -f $directory$bz2_base$num
num='9'
bzip2 -d $directory$bz2_base$num".bz2"
python flickr_db.py $directory$bz2_base$num
rm -f $directory$bz2_base$num
