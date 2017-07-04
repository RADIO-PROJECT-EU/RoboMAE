import json
import os.path

"""
Keeps basic information of the LaserScanner as given from the rosbag, its the raw data, the status of the LaserWidget etc.
"""
class LaserCredentials(object):
    
    def __init__(self):
        self.timer = None           #the timer of the LaserWidget
        self.wall_limit = 10        #how many scans are used to set the walls
        self.walls = []             #points that represent the walls 
        self.boxHandler = None      #<BBoxHandler> which contains the bounding boxes and the data
        self.time_increment = 0.0   #the time of between two scans 
        self.frames_array = []      #array with the sequence IDs of the frames (only the frames that contain the raw_data) in the rosbag
        self.raw_data = []          #set of points <LaserAnnotation> for each scan (the walls are not included)
        self.status = None          #defines the state of the Laser widget. Possible options: "Loaded"->the rosbag is loaded, "Play","Stop","Pause","Next","Previous","SetBox"->sets the previous boxes to the current frame/scan
        self.bag_file = ""
        self.csv_file = ""
        self.topic = None           #the topic where the laserScanner of the rosbag publishes
        self.counter = 0            #the number of the frame/scan
        self.myradius = 0.07        #the radious of a point in the plot -> ease the drawing of the rectangle and circles

        self.headlines = ["Timestamp", "Rect_id", "Rect_x", "Rect_y", "Rect_W", "Rect_H", "Class", "Points", "Frame_id"]

        self.basicLabel = []
        self.highLabel = []
        self.annotationColors = []
        self.eventColors = []

        self.parseJson()

    def setFile(self, filename):
        self.bag_file = filename
        self.csv_file = filename.split(".bag")[0] + "_laser.csv"    #the csv file has the same prefix name with the bag file

    def setTopic(self, topicName):
        self.topic = topicName
    
    #Read the labels and the colors of the json files and store them
    def parseJson(self):
        with open("labels.json") as json_file:
            json_data = json.load(json_file)
            json_label = []
            for i in json_data['basiclabels'] :
                self.basicLabel.append(i)
            for i in json_data['highlevellabels']:
                self.highLabel.append(i)
            for i in json_data['annotationColors'] :
                self.annotationColors.append(i)
            for i in json_data['eventColors']:
                self.eventColors.append(i)


