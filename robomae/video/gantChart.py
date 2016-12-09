#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import itertools
from video.videoGlobals import videoGlobals
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QSizePolicy


class videoGantChart(FigureCanvas):
    
    def __init__(self, parent=None,width=15,height=1,dpi=100):
        gantChart = Figure(figsize=(width, height), dpi=dpi)
        self.axes = gantChart.add_subplot(111)
        self.drawChart([], None)
        
        FigureCanvas.__init__(self, gantChart)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def drawChart(self):
        pass

#Class for the gantChart
class gantShow(videoGantChart):
    
    #Plot the chart
    def drawChart(self, videobox, framerate):
        temp_action = []
        self.timeWithId = []
        self.tickY = []
        self.tickX = []
        self.boxAtYaxes = []
        self.axes.hlines(0,0,0)

        for i in range(0, len(videobox)):
            frame_index = videobox[i]
            for i in range(len(frame_index.box_id)):
                boxIdx = frame_index.box_id[i]
                if boxIdx != -1:
                    for allactions in frame_index.annotation[i]:
                        if isinstance(allactions, list):
                            for action in allactions:
                                self.boxAtYaxes.append([boxIdx, action])
                                self.timeWithId.append([boxIdx, frame_index.timestamp, action])
                        else:
                            self.boxAtYaxes.append([boxIdx, allactions])
                            self.timeWithId.append([boxIdx, frame_index.timestamp, frame_index.annotation[frame_index.box_id.index(boxIdx)]])

        #Remove duplicates and sort the Y axes
        self.boxAtYaxes.sort()
        self.boxAtYaxes = list(k for k,_ in itertools.groupby(self.boxAtYaxes))

        for key in range(len(self.boxAtYaxes)):
            self.tickY.append(key)
        for index in range(len(self.timeWithId)):
            for action in self.timeWithId[index][2]:
                self.startTime, self.endTime = self.timeCalc(self.timeWithId, index, action)
                if self.timeWithId[index][1] == self.endTime:
                    self.color = self.getColor(action)
                    self.axes.hlines(self.boxAtYaxes.index([self.timeWithId[index][0],action]), self.startTime, self.endTime+(1/framerate),linewidth=10,color=self.color)
                else:
                    self.color = self.getColor(action)
                    self.axes.hlines(self.boxAtYaxes.index([self.timeWithId[index][0],action]), self.startTime,self.endTime,linewidth=10,color=self.color)

        for tick in self.axes.yaxis.get_major_ticks():
            tick.label.set_fontsize(9)

        self.axes.set_xticklabels([])
        self.axes.set_yticks(self.tickY)
        self.axes.set_ylim([-1,len(self.boxAtYaxes)])
        self.axes.set_yticklabels([str(index[0]) + "::" + str(index[1]).ljust(5) for index in self.boxAtYaxes])
        self.axes.grid(True)

    #Calculates the end time for each annotation to plot
    def timeCalc(self, time, curr, activity):
        temp_id = time[curr][0]
        startTime = time[curr][1]
        endTime = time[curr][1]
        while activity in time[curr][2] and temp_id in time[curr]:
            endTime = time[curr][1]
            curr += 1
            if curr > len(time)-1:
                break
        return startTime,endTime

    #Calculates the color for the gantChart and bound Boxes
    def getColor(self, label):
        if label == 'Clear':
                #color = 'Clear'
            return '#0000FF'
        elif label in videoGlobals.classLabels:
                #color = label
            return videoGlobals.annotationColors[videoGlobals.classLabels.index(label) % len(videoGlobals.classLabels)]
        elif label in videoGlobals.highLabels:
            return videoGlobals.eventColors[videoGlobals.highLabels.index(label) % len(videoGlobals.highLabels)]
