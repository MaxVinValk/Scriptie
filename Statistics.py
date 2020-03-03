import pickle
import inspect
import numpy as np
import matplotlib.pyplot as plt
import os

from ConsoleMessages import ConsoleMessages as cm

MAX_NUM_TO_FILE = 1_000_000

class ClassCollector():

    def __init__(self, owner):
        self.owner = owner
        self.statistics = {}

    def addStatistic(self, name, title):
        if name not in self.statistics:
            self.statistics[name] = {"title" : title, "data" : []}

    def updateStatistic(self, name, value):
        if name in self.statistics:
            self.statistics[name]["data"].append(value)
        else:
            print(f"{cm.WARNING} attempted update of unknown statistic" +
            f"{name} by {calledBy}")

    def getStatistics(self):
        return self.statistics

    def save(self, dirName):

        dirName = dirName + "/" + self.owner

        #TODO: Error handling needs to be more robust here

        try:
            os.mkdir(dirName)
        except OSError:
            print(f"{cm.WARNING} Failed to create directory for data. Data is lost...")

        for key, value in self.statistics.items():

            localDir = dirName + "/" + key

            try:
                os.mkdir(localDir)
            except OSError:
                print(f"{cm.WARNING} Failed to create directory for data. Data is lost...")

            data = value["data"]
            chunks = int(len(data) / MAX_NUM_TO_FILE)
            fileCtr = 0
            filePrefix = localDir + "/d_"

            for i in range(0, chunks):
                fileName = filePrefix + str(fileCtr)

                with open(fileName, "wb") as f:
                    pickle.dump(data[i*MAX_NUM_TO_FILE : (i+1)*MAX_NUM_TO_FILE], f)
                fileCtr += 1

            rem = len(data) % MAX_NUM_TO_FILE

            if (rem):
                fileName = filePrefix + str(fileCtr)
                with open(fileName, "wb") as f:
                    pickle.dump(data[-rem:], f)


            #Create information file which tells us the title/could hold other info
            with open(localDir + "/" + "infoFile", "wb") as f:
                pickle.dump(value["title"], f)


    def _unpack(self, dirPath, dirName):

        self.statistics[dirName] = {}
        self.statistics[dirName]["data"] = []

        with open(dirPath + "/" + "infoFile", "rb") as f:
            self.statistics[dirName]["title"] = pickle.load(f)

        for file in os.listdir(dirPath):
            if "infoFile" not in file:

                with open(dirPath + "/" + file, "rb") as f:
                    self.statistics[dirName]["data"].extend(pickle.load(f))


    def load(self, dirName):
        for folder in os.listdir(dirName):
            self._unpack(dirName + "/" + folder, folder)


    def _averageStatOver(self, name, averageOver):

        localAverageOver = averageOver
        avg = []
        data = self.statistics[name]["data"]

        if (len(data) < localAverageOver):
            print(f"{cm.WARNING} averageOver is larger than the data averaged over," +
            f"defaulting it to 1. Plot titles will be incorrect as a result.")
            localAverageOver = 1
        elif (len(data) % localAverageOver):
            print(f"{cm.WARNING} averageOver {localAverageOver} does not divide data of length " +
            f"{len(data)} wholly, plots may be incorrect as a result.]")

        chunks = int(len(data) / localAverageOver)

        for i in range(0, chunks):
            avg.append(np.average(data[i*localAverageOver:(i+1)*localAverageOver]))

        return avg




    def readyPlot(self, averageOver, plots):

        avgData = {}

        for key, value in self.statistics.items():
            avgData[value["title"]] = self._averageStatOver(key, averageOver)

        plt.figure(plots)
        plotCtr = 1

        for title, data in avgData.items():

            plt.subplot(2, 2, plotCtr)
            plt.plot(data)

            plt.title(title + f", averaged over {averageOver} runs")
            plotCtr += 1

            #We allow at most 4 plots per subplot
            if (plotCtr > 4):
                plotCtr = 1
                plots += 1
                plt.figure(plots)



        if (plotCtr == 1):
            return plots
        else:
            return plots + 1



#
#   This class is concerned with storing data from all over the program
#   It is a singleton class, so that all data gets collected at one point
#
#   It also has functionality for plotting the data collected and providing info on it

class StatCollector():

    __instance = None

    @staticmethod
    def getInstance():
        if StatCollector.__instance == None:
            StatCollector()
        return StatCollector.__instance

    def __init__(self):
        if StatCollector.__instance != None:
            raise Exception("This class is a singleton - access with getInstance() instead")
        else:
            StatCollector.__instance = self
            self.collectors = {}
            self.statistics = {}


    def getClassCollector(self):
        calledBy = inspect.stack()[1][0].f_locals["self"].__class__.__name__

        if calledBy not in self.collectors:
            self.collectors[calledBy] = ClassCollector(calledBy)

        return self.collectors[calledBy]



    def save(self, dirName):

        #TODO: Error handling needs to be more robust here
        try:
            os.mkdir(dirName)
        except OSError:
            print(f"{cm.WARNING} Failed to create directory for data. Data is lost...")

        for key, value in self.collectors.items():
            value.save(dirName)


    def load(self, dirName):

        for folder in os.listdir(dirName):
            self.collectors[folder] = ClassCollector(folder)
            self.collectors[folder].load(dirName + "/" + folder)


    def summarize(self):

        print(  "\n\n"                              +
                "----------------------------\n"    +
                " Overview of data collected \n"    +
                "----------------------------\n"
        )

        for key, value in self.collectors.items():
            print(f"Data found for: {key}")

            for k2, v2 in value.getStatistics().items():
                print(f"statistic: {v2['title']}")
                print(f"values recorded: {len(v2['data'])}")
                print("-----\n")
            print("######\n")

    def plot(self, averageOver = 1):
        plots = 0

        for key, value in self.collectors.items():
            plots = value.readyPlot(averageOver, plots)

        plt.show()
