import numpy as np
from matplotlib.patches import Rectangle, Circle
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import QtCore, QtWidgets, QtGui
import matplotlib.pyplot as plt
import csv

from guiChangeBox import changeBoxId
from laserBox import BoundingBox, BBoxHandler


current_rect = None #the rectangle that the user draws at the moment
openMode = False    #whether the user chose to open a CSV file with the boxes or not

"""
Plot Canvas for the laser scan points, that extends <FigureCanvas>. 
It receives the mouse and keyboard events on the plot, draws the Rectangles and the Circles as well as the colors respectively.
It also contains the <BBoxHandler> of the rosbag laserscanner topic, where the bounding boxes and their info exist.
"""
class PlotCanvas(FigureCanvas):


    def __init__(self, parent=None, width=10, height=3, dpi=100):
        

        fig = Figure(figsize=(width, height), dpi=dpi)
        #fig,axes= plt.subplots()

        self.axes = fig.add_subplot(111)


        self.axes.set_title('Top View of Laser Data Points')
        self.axes.set_xlim((-2, 9))
        self.axes.set_ylim((-5, 5))


        self.point1 = []  # the active vert point where the user clicked on the plot
        
        self.rectangles = None #BBoxHandler() #contains all the bounding boxes so far, and their info
        
        self.addPoint = False
        self.nextSet = False

        self.canvas = fig.canvas

        FigureCanvas.__init__(self, fig)
        self.setParent(parent)


        FigureCanvas.setSizePolicy(self, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        self.canvas = fig.canvas
        self.scat = None
        self.laserCr = None

        self.canvas.setFocusPolicy( QtCore.Qt.ClickFocus )
        self.canvas.setFocus()

        
        plt.show()


    def connectAll(self):
        #MouseEvent occurs
        self.canvas.mpl_connect('button_press_event', self.onPress)
        self.canvas.mpl_connect('button_release_event', self.onRelease)
        self.canvas.mpl_connect('motion_notify_event', self.onMotion)
        self.canvas.mpl_connect('key_press_event', self.onKeyPress)
        self.canvas.mpl_connect('key_release_event', self.onKeyRelease)
        

        self.canvas.mpl_connect('draw_event', self.onDraw)
    
    def onPress(self, event):
        if event.inaxes is None:
            return

        #Left click -> the user is about to draw a rectangle, sett he first point where the rectangle begins
        if event.button == Qt.LeftButton:
            self.point1 = [event.xdata, event.ydata]

        #Right click -> the user should click into a rectangle-box. If yes, a menu is displayed 
        else:
            box = self.rectangles.getInvolvedBox(self.laserCr.counter, event.xdata, event.ydata)

            if not (box == None):
                menu = QMenu()

                changeId = menu.addAction('Change Id')
                changeNextId = menu.addAction('Change Next Ids')

                changeNextStates = menu.addMenu('Change Next States')
                changeState = menu.addMenu('Change State')

                stateList = []
                for basic in self.laserCr.basicLabel:
                    stateList.append(''+basic)
                    changeNextStates.addAction(''+basic)
                    changeState.addAction(''+basic)


                menu.addSeparator()
                delete = menu.addMenu('Delete')
                #add a submenu for delete option
                deleteBox = delete.addAction('Delete Box')
                deleteAllBoxes = delete.addAction('Delete All Boxes')
                delete.addSeparator()
                deleteAllBoxesId = delete.addAction('Delete All Boxes with this Id')

                action = menu.exec_(self.mapToGlobal(QtCore.QPoint(event.x, event.y)))

                if action is not None:
                    if action.parent() == delete:
                        #delete the single rectangle-box
                        if action == deleteBox:
                            self.rectangles.removeBox(box)

                            self.canvas.restore_region(self.background)
                            self.drawRectangles()
                            self.canvas.blit(self.axes.bbox)
                        #delete the rectangles of the specific scan/frame
                        elif action == deleteAllBoxes:
                            self.rectangles.removeAllBoxes(self.laserCr.counter)

                            self.canvas.restore_region(self.background)
                            self.drawRectangles()
                            self.canvas.blit(self.axes.bbox)
                        #delete all the rectangles of the rosbag that have the same id
                        elif action == deleteAllBoxesId:
                            self.rectangles.removeAllBoxesId(box.uId)

                            self.canvas.restore_region(self.background)
                            self.drawRectangles()
                            self.canvas.blit(self.axes.bbox)
                    #change the state of the specific rectangle-box as well as its color
                    elif action.parent() == changeState:
                        box.condition = str(action.text())
                        index = stateList.index(box.condition)
                        colorState = self.laserCr.annotationColors[index]

                        box.setColor(colorState)

                        self.canvas.restore_region(self.background)
                        self.drawRectangles()
                        self.canvas.blit(self.axes.bbox)

                    #change the state of the specific rectangle-box and of all the next scans' rectangles with the specific id, as well as their color
                    elif action.parent() == changeNextStates:
                        box.condition = str(action.text())
                        index = stateList.index(box.condition)
                        colorState = self.laserCr.annotationColors[index]

                        box.setColor(colorState)

                        self.rectangles.updateNextStates(box, colorState)

                        self.canvas.restore_region(self.background)
                        self.drawRectangles()
                        self.canvas.blit(self.axes.bbox)    
                    #checnhe the id of the rectangle in the specific scan (changeId) or every next rectangles with the specific id (changeNextId)
                    if action == changeId or action == changeNextId:
                        frame_boxes = self.rectangles.getByFrame(self.laserCr.counter)

                        if action == changeNextId:
                            self.newBoxId = changeBoxId(box, frame_boxes, self, True)
                        else:
                            self.newBoxId = changeBoxId(box, frame_boxes, self, False)

                        self.newBoxId.setGeometry(QRect(800, 100, 250, 100))
                        self.newBoxId.show()
                
    #When the user realeases the right click -> draw the final rectangle on the plot
    def onRelease(self, event):
        global current_rect

        if not (current_rect == None):
            self.addRectangle()
            self.drawRectangles()

            current_rect = None
            self.point1 = []

    #While the user presses the right click and moves the mouse -> have an instance of the current rectangle
    def onMotion(self, event):
        global current_rect

        if len(self.point1) == 0:
            return
        if event.inaxes is None:
            return
        
        if not self.addPoint:
            if event.xdata > self.point1[0]:
                x = self.point1[0]
            else:
                x = event.xdata

            if event.ydata > self.point1[1]:
                y = self.point1[1]
            else:
                y = event.ydata

            
            w = abs(event.xdata - self.point1[0])
            h = abs(event.ydata - self.point1[1])    
            current_rect = Rectangle( (x , y), width=w, height=h, fill=True, edgecolor='black', facecolor=(0.7,0.7,0.7,0.2))

            self.axes.add_patch(current_rect)

            self.canvas.restore_region(self.background)

            #draw the other rectangles of this scan too
            self.drawRectangles()

            self.axes.draw_artist(current_rect)
            self.canvas.blit(self.axes.bbox)

    #When the 'A' key is presses -> denotes that the user wants to add a point to the last rectangle
    def onKeyPress(self, event):
        if event.key == 'a':
            self.addPoint = True 

    #Draws a circle on the plot, which represents the added point
    def onKeyRelease(self, event):
        if not (len(self.point1) == 0):
            self.canvas.restore_region(self.background)
            
            current_circle = Circle((self.point1[0], self.point1[1]), radius=self.laserCr.myradius, color='red')
            self.axes.add_patch(current_circle)

            self.rectangles.addPoint(current_circle)

            self.axes.draw_artist(current_circle)

            self.drawRectangles()
            
            self.canvas.blit(self.axes.bbox)

        self.addPoint = False
        self.point1 = []



    def onDraw(self, event):

        self.background = self.canvas.copy_from_bbox(self.axes.bbox)
        
        if self.rectangles == None:
            return 
            
        if not self.rectangles.empty():
            if not (self.laserCr.status == 'Stop'):
                self.drawRectangles()
        

        self.canvas.blit(self.axes.bbox)

    #Draws:
    # - the rectangles, with the specified colors
    # - the circles, which represent the extra points
    # - an id for each rectangle, which represents the user id
    def drawRectangles(self):
        recsToShow = self.rectangles.getByFrame(self.laserCr.counter)
                
        if not (recsToShow == None):
            for box in recsToShow:
            
                self.axes.add_patch(box.rectangle)
                self.axes.draw_artist(box.rectangle)

                #draw the user id of the rectangle
                t = self.axes.text(box.rectangle.get_x(), box.rectangle.get_y()+ box.rectangle.get_height() + 0.1, box.uId,  animated=True) 
                self.axes.draw_artist(t)

                for c in box.extraPoints:
                    self.axes.add_patch(c)
                    self.axes.draw_artist(c)
                    

    #Adds the current rectangle as a <BoundingBox> to the list of all boxes and draws the id of the rectangle.
    #Called from onRealease() function
    def addRectangle(self):
        global current_rect

        bbox = BoundingBox(current_rect)
        bbox.frameCount = self.laserCr.counter

        t = self.axes.text(bbox.rectangle.get_x(), bbox.rectangle.get_y()+ bbox.rectangle.get_height() + 0.1, bbox.uId,  animated=True) 
        self.axes.draw_artist(t)
        self.canvas.blit(self.axes.bbox)


        self.rectangles.append(bbox)


"""
The Widget of the Laser Scanner, which extends <PlotCanvas> class.
It sets, stores and handles the laser scanner points.
"""
class LaserWidget(PlotCanvas):

    def __init__(self):
        PlotCanvas.__init__(self)


    def setInfo(self, laser_info):
        self.laserCr = laser_info

    def setConnections(self):
        self.connectAll()

    def deleteAllBoxes(self):
        if not (self.rectangles == None):
            self.rectangles.reset()

    #Draws the appropriate scan points, depending on the status (play, next, previous etc)
    def drawLaserScan(self):
        global openMode

        self.axes.clear()
        self.axes.set_xlim((-2, 9))
        self.axes.set_ylim((-5, 5))

        if not (self.laserCr.status == 'Stop'):
            #Init the <BBoxHandler> when the user presses Play button. 
            if (self.rectangles == None and (self.laserCr.status == 'Play' or self.laserCr.status == 'Loaded')):

                #If the system didn't create the b.boxes automatically, initialise a <BBoxHandler>
                if self.laserCr.boxHandler == None:
                    self.rectangles = BBoxHandler()
                else:
                    self.rectangles = self.laserCr.boxHandler

            if (self.laserCr.status == 'Next') or (self.laserCr.status == 'SetBox'):

                if openMode == True:
                    prev_cnt = self.laserCr.counter
                else:
                    prev_cnt = self.laserCr.counter - 1

                #If the user presses the button <SetBox>, the system copies the rectangles of the previous scan in the current one
                if (self.laserCr.status == 'SetBox'):
                    nextBoxes = self.rectangles.getByFrame(prev_cnt+1)
                    if nextBoxes == None:
                        self.rectangles.copyPrevious(prev_cnt) 

                else:
                    self.setAnnotations(prev_cnt)

            try:
                xdata = self.laserCr.raw_data[self.laserCr.counter].pointsX
                ydata = self.laserCr.raw_data[self.laserCr.counter].pointsY

                self.axes.scatter(np.array(self.laserCr.walls[0]), np.array(self.laserCr.walls[1]), marker='_', s=20, color='black')
                self.scat = self.axes.scatter(np.array(xdata), np.array(ydata), marker='o', s=60, edgecolor='navy', facecolor='blue') 
            except IndexError: 
                self.laserCr.status = 'Stop'
                self.laserCr.timer = 0
                self.laserCr.counter = 0
                self.axes.clear()

        self.draw()

    #Set the points as annotations of the previous scan, depending on the rectangles/circles plotted
    def setAnnotations(self, frameCount):

        boxes = self.rectangles.getByFrame(frameCount)
        annotX = self.laserCr.raw_data[frameCount].pointsX
        annotY = self.laserCr.raw_data[frameCount].pointsY

        if boxes == None:
            return

        for box in boxes:
            intersect = self.inRectangle(box, annotX, annotY)

            annot = zip((annotX[x] for x in intersect), (annotY[y] for y in intersect))
 
            #add some extra points that the user marked separately
            for circle in box.extraPoints:
                center = circle.center
                radius = circle.get_radius()

                pointx = [i for i,v in enumerate(annotX) if v==center[0] or abs(v-center[0])<=radius]
                pointy = [i for i,v in enumerate(annotY) if v==center[1] or abs(v-center[1])<=radius]
                intersectP = list(set(pointx).intersection(pointy))

                if len(intersectP) == 0:
                    continue

                for i in intersectP:
                    if i in intersect:
                        continue
                    annot.append((annotX[i], annotY[i]))  
            
            #replace the data of the current box, with the new annotation points
            box.data = annot[:]

    #Gets all the points that underlie into a rectangle
    def inRectangle(self, box, pointsX, pointsY):
        minX = box.rectangle.get_x()
        maxX = box.rectangle.get_x() + box.rectangle.get_width()
        minY = box.rectangle.get_y()
        maxY = box.rectangle.get_y() + box.rectangle.get_height()

        #(x,y) points that are located into each rectangle
        x_ = [i for i,v in enumerate(pointsX) if v>=minX and v<=maxX]
        y_ = [i for i,v in enumerate(pointsY) if v>=minY and v<=maxY]

        return list(set(x_).intersection(y_))


    #Save all the data/annotations of the <BoundinBox>es into a csv file
    def saveCSV(self):
        #set the annotations for the current frame too
        self.setAnnotations(self.laserCr.counter)

        with open(self.laserCr.csv_file, 'w+') as file:
            csv_writer = csv.writer(file, delimiter='\t')

            #if not exists:
            csv_writer.writerow(self.laserCr.headlines)
            rowList = []

            for box in self.rectangles.boxes:
                timestamp = self.laserCr.time_increment*box.frameCount
                rect = box.rectangle

                row = [timestamp, box.uId, rect.get_x(), rect.get_y(), rect.get_width(), rect.get_height(), box.condition, box.data]
                rowList.append(row)

            sortedlist = sorted(rowList, key=lambda r: float(r[0]), reverse=False)


            prev_time = -1.0
            frameIndex = 0
            for row in sortedlist:
                if float(row[0]) > prev_time:
                    fid = self.laserCr.frames_array[frameIndex]
                    frameIndex = frameIndex + 1
                    prev_time = float(row[0])

                row.append(fid)
                csv_writer.writerow(row)


        print ("Csv for scanner written at: ", self.laserCr.csv_file) 

        
    #Loads all the information of the csv file, to a set of <BoundingBox>es
    def openCSV(self):

        try:
            with open(self.laserCr.csv_file, 'r') as file:
                csv_reader = csv.reader(file, delimiter='\t')
                headlines = self.associateHeadlines(next(csv_reader))

                self.rectangles = BBoxHandler()

                for row in csv_reader:
                    box = self.createBox(row, headlines)
                    self.rectangles.append(box)
        except Exception as ex:
            print ('Error ',ex)
            raise Exception


    #rewrite a written csv by sorting it and inserting the frame_id information
    def rewriteCSV(self):
        output_file = None

        try:
            output_file = self.laserCr.csv_file.split(".csv")[0]+"_RW.csv"

            with open(self.laserCr.csv_file, 'r') as rfile, open(output_file, 'w+') as wfile:
                csv_reader = csv.reader(rfile, delimiter='\t')
                csv_reader.next()

                #sort the csv by the timestamp
                sortedlist = sorted(csv_reader, key=lambda row: float(row[0]), reverse=False)

                csv_writer = csv.writer(wfile, delimiter='\t')

                csv_writer.writerow(self.laserCr.headlines)

                prev_time = -1.0
                frameIndex = 0
                for row in sortedlist:
                    try:
                        if float(row[0]) > prev_time:
                            fid = self.laserCr.frames_array[frameIndex]
                            frameIndex = frameIndex + 1
                            prev_time = float(row[0])
                    except ValueError:
                        continue

                    rowNew = [row[0],row[1], row[2], row[3], row[4], row[5], row[6], row[7], fid]
                    csv_writer.writerow(rowNew)

        except Exception as ex:
            print ('Error ',ex)
            raise Exception 

        print ("Csv for scanner rewritten at: ",output_file)


    #Creates a <BoundingBox> with its information, by taking into account the information of a csv row
    def createBox(self, row, headlines):
        try:
            #initialize a box with the rectangle
            rect = Rectangle( (float(row[headlines['Rect_x']]) , float(row[headlines['Rect_y']]) ), 
                width=float(row[headlines['Rect_W']]), height=float(row[headlines['Rect_H']]), fill=True, edgecolor='black', facecolor=(0.7,0.7,0.7,0.2))

            box = BoundingBox(rect)

            #set the frame/scan depending on the timestamp
            box.frameCount = int(float(row[headlines['Timestamp']])/self.laserCr.time_increment) 

            #set the condition and the respective color of the box
            box.condition = row[headlines['Class']].strip()
            index = self.laserCr.basicLabel.index(box.condition)
            colorState = self.laserCr.annotationColors[index]
            box.setColor(colorState)

            #set the data points of the bounding box
            box.data = eval(row[headlines['Points']])

            self.createCircles(box)

            #set the user id of the box
            box.uId = row[headlines['Rect_id']]

            return box

        except Exception:
            raise Exception('Error in handling CSV file')


    def associateHeadlines(self, headlines):
        association = {}

        for i in range(0, len(headlines)):
            association[str(headlines[i])] = i

        return association

    #Adds and draws the extra points of the <BoundingBox>
    def createCircles(self, box): 

        pointsX = [x[0] for x in box.data]
        pointsY = [y[1] for y in box.data]

        indexIn = self.inRectangle(box, pointsX, pointsY)

        extraX = [x for i,x in enumerate(pointsX) if i not in indexIn]
        extraY = [y for i,y in enumerate(pointsY) if i not in indexIn]

        for i in range(0, len(extraX)):
            circle = Circle((extraX[i], extraY[i]), radius=self.laserCr.myradius, color='red')
            box.appendPoint(circle)
