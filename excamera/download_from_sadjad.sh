#!/bin/bash

for i in {00000000..00000879}
  do 
     # aws s3 cp s3://excamera-us-west-2/sintel-1k-y4m_06/$i.y4m .
     # aws s3 cp s3://excamera-us-west-2/sintel-1k-y4m_06/$i.y4m s3://excamera-input-6frames-16chunks
     # aws s3 cp s3://excamera-us-west-2/sintel-4k-y4m_06/$i.y4m .
     aws s3 cp s3://sintel-4k-y4m-6frames-880/$i.y4m s3://excamera-input-6frames-16chunks
 done
