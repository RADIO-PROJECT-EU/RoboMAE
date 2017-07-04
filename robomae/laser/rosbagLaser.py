#!/usr/bin/env python
import roslib
from sensor_msgs.msg import LaserScan
import rospy
from std_msgs.msg import String
import signal
import os
import sys
import rosbag
import yaml
import numpy as np
from clustering import AutoScannerAnnotator

global frequency
global duration
global wall

wall = None


def get_range_data(bag, input_topic, wall_limit):

    global frequency, wall

    info_dict = yaml.load(bag._get_yaml_info())
    topics =  info_dict['topics']

    try:
        topic = [t for t in topics if t['topic'] == input_topic][0]
        frequency = topic['frequency']

    except ValueError:
        print 'There is no topic with the specified name :: ',input_topic

    points_buff = []
    frames_array = []
    max_range = 0.0
    frame_count =0
    
    #Loop through the rosbag
    for top, msg, t in bag.read_messages(topics=[input_topic]):
        #Get the scan

        theta = np.arange(msg.angle_min, msg.angle_max, msg.angle_increment)
        max_range = msg.range_max

        
        if frame_count < wall_limit:
            wall_extract(msg.ranges,max_range)

        #convert wall from polar to cartesian
        elif frame_count == wall_limit:
            wall = (np.min(wall, axis=0))-0.1
            wall_buff = pol2cart(wall, theta)
        
        else:
            ranges = np.array(msg.ranges)
            
            filter = np.where(ranges < wall) 
            # filter out walls
            ranges = ranges[filter]
            theta = theta[filter]

            C = pol2cart(ranges, theta)

            points_buff.append(C)
            if not(len(ranges) == 0):
                frames_array.append(msg.header.seq)

        frame_count = frame_count + 1

        
    return points_buff, wall_buff, msg.scan_time, frames_array


def wall_extract(laser_ranges, range_limit):
    global wall

    wall_scan = np.array(laser_ranges)
    #get indexes of scans >= range_limit 
    filter=np.where(wall_scan >= range_limit)

    #set those scans to maximum range
    wall_scan[filter] = range_limit


    if wall is None:
        wall = wall_scan
    else:
        wall = np.vstack((wall,wall_scan ))

#convert polar coordinates to cartesian
def pol2cart(r,theta):
    x=np.multiply(r,np.cos(theta))
    y=np.multiply(r,np.sin(theta))

    C=np.array([x,y]).T
    return C


#Get the range data of the scanner, extract the walls of each scan and enable the <AutoScannerAnnotator> in order to produce the boxes autonomous.
def runMain(bag, laser_info):
    global frequency

    points_buff, wall_buff, t, frames_array = get_range_data(bag, laser_info.topic, laser_info.wall_limit)

    convertPoints(points_buff, wall_buff, laser_info)

    laser_info.time_increment = t
    laser_info.frames_array = frames_array

    auto = AutoScannerAnnotator(points_buff, laser_info.myradius)
    boxHandler = auto.cluster_procedure()

    laser_info.boxHandler = boxHandler

    return frequency

#Store the points as a list of [points_x],[pointsY] for each scan
def convertPoints(points_buff, wall_buff, laser_info):
    for scan in points_buff:
        x = [p[0] for p in scan]
        y = [p[1] for p in scan]

        la = LaserAnnotation(pointsX_=x, pointsY_=y)
        laser_info.raw_data.append(la)

    wX = []
    wY = []
    for wScan in wall_buff:
        wX.append(wScan[0])
        wY.append(wScan[1])

    laser_info.walls = [wX, wY]


#Better demostrastion of the X,Y points for each scan
class LaserAnnotation:
    def __init__(self, pointsX_=None, pointsY_=None):
        if pointsX_ is None:
            self.pointsX = []
        else:
            self.pointsX = pointsX_

        if pointsY_ is None:
            self.pointsY = pointsY_

        else:
            self.pointsY = pointsY_