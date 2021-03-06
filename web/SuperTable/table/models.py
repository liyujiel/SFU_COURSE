from django.db import models
from collections import OrderedDict
import datetime
import sqlite3
import json

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


# Create your models here.
class SearchRequest(models.Model):
    year = models.TextField()
    semester = models.TextField()
    preference = models.TextField()
    department = models.TextField()
    courseNum = models.TextField()

    def __str__(self):
        return self.department+str(self.courseNum) 

    def __init__(self, year, semester, preference, department, courseNum,courseTimes):
        self.year = year
        self.semester = semester
        self.preference = preference
        self.department = department
        self.courseNum = courseNum
        self.courseTimes = courseTimes
        
        self.connectDB = None
        self.cursor = None
        self.rtnDict = OrderedDict()
        

    def searchFromDB(self):
        dbName = str(self.year) + self.semester.lower() + ".db"
        self.connectDB = sqlite3.connect(dbName)
        self.connectDB.row_factory = dict_factory
        
        if self.courseNum[-1] == "w":
            self.courseNum = self.courseNum[:-1] + "W"

        query = "SELECT * FROM " + (self.department+ "x") + " WHERE course=(?) AND sectionCode='LEC'"
        self.cursor = self.connectDB.execute(query,(self.courseNum,))
    
    def parseMonth(self,abbr):
        monthDict = {"Jan":"01", "Feb":"02", "Mar":"03", "Apr":"04",
                    "May":"05", "June":"06", "July":"07", "Aug":"08",
                    "Sep":"09", "Oct":"10", "Nov":"11", "Dec":"12",}
        return monthDict[abbr]

    def parseWeekday(self, abbr):
        weekdayDict = {"Mo":1, "Tu":2,
                        "We":3, "Th":4,
                        "Fr":5, "Sa":6, "Su":7}
        return weekdayDict[abbr]

    def backgroundColor(self, times):
        colorDict = {0:"#DDDDDD",1:"#FFDC00 ", 2:"#0074D9", 3:"pink", 4:"dark",5:" #AAAAAA", 6:"#001f3f", 7:" #01FF70 ",
                    8:" #85144b ", 9:" #F012BE ",10:"#3D9970"}
        return colorDict[times]

    def parseDate(self, row, colName):
        dateFormList = [part.strip() for part in row[colName].split(" ")]
        return dateFormList[3] + "-" + self.parseMonth(dateFormList[1]) +"-" + dateFormList[2]

    def parseDictRow(self,row):
        classRow = {}
        # row for final exam
        finalRow = {}
        if row["startTime1"]:
            classRow["title"] = self.department.upper() + self.courseNum + " " + row["section"]
            startDate = self.parseDate(row,"startDate")
            endDate = self.parseDate(row,"endDate")
            classRow["start"] = row["startTime1"]
            classRow["end"] =  row["endTime1"]
            classRow["ranges"] = [{"start":startDate,"end":endDate}]
            classRow["dow"] = [self.parseWeekday(day.strip()) for day in row["days1"].split(",")]
            classRow["backgroundColor"] = self.backgroundColor(self.courseTimes)
            self.rtnDict[self.courseTimes] = classRow
            classRow = {}
            self.courseTimes += 1

            if row["startTime2"]:
                classRow["title"] = self.department.upper() + self.courseNum + " "  + row["section"]
                classRow["start"] = row["startTime2"]
                classRow["end"] = row["endTime2"]
                classRow["ranges"] = [{"start":startDate,"end":endDate}]
                classRow["dow"] = [self.parseWeekday(day.strip()) for day in row["days2"].split(",")]
                classRow["backgroundColor"] = self.backgroundColor(self.courseTimes-1)
                self.rtnDict[self.courseTimes] = classRow
                classRow = {}
                self.courseTimes += 1

                if row["startTime3"]:
                    classRow["title"] = self.department.upper() + self.courseNum + " " + row["section"]
                    classRow["ranges"] = [{"start":startDate,"end":endDate}]
                    classRow["start"] = row["startTime3"]
                    classRow["end"] = row["endTime3"]
                    classRow["dow"] = [self.parseWeekday(day.strip()) for day in row["days3"].split(",")]
                    classRow["backgroundColor"] = self.backgroundColor(self.courseTimes-2)
                    self.rtnDict[self.courseTimes] = classRow
                    classRow = {}
                    self.courseTimes += 1

        if row["examDate"]:
            dateFormList =[part.strip() for part in row["examDate"].split(" ")]
            dateForm = dateFormList[3] + "-" + self.parseMonth(dateFormList[1]) +"-" + dateFormList[2]
            examEndDate = dateFormList[3] + "-" + self.parseMonth(dateFormList[1]) +"-" + str(int(dateFormList[2]) + 1)
            finalRow["title"] = self.department.upper() + self.courseNum + " Final"
            finalRow["ranges"] = [{"start":dateForm,"end":examEndDate}]
            finalRow["dow"] = [datetime.date(int(dateFormList[3]), int(self.parseMonth(dateFormList[1])),int(dateFormList[2])).isoweekday()]
            finalRow["start"] = row["examstartTime"] + ":00"
            finalRow["end"] = row["examEndTime"] + ":00"
            finalRow["backgroundColor"] =  "#FF4136"
            self.rtnDict[self.courseTimes] = finalRow
            self.courseTimes += 1


    def filterPrefer(self):
        if self.preference == "All":
            for row in self.cursor:
                self.parseDictRow(row)
        elif self.preference == "Morning":
            for row in self.cursor:
                if int(row["endTime1"].split(":")[0]) <= 14:
                    self.parseDictRow(row)
        elif self.preference == "Afternoon":
            for row in self.cursor:
                if int(row["startTime1"].split(":")[0]) >= 14:
                    self.parseDictRow(row) 

    def get_rtnVal(self):
        self.searchFromDB()
        self.filterPrefer()
        self.connectDB.rollback()
        self.connectDB.close()
        return self.rtnDict

    def get_courseTimes(self):
        return self.courseTimes

        

class SearchResult(models.Model): 
    department = models.TextField()
    courseNum = models.TextField()
    courseCampus = models.TextField()
    courseRoom = models.TextField()
    courseStarTime = models.TimeField()
    courseEndTime = models.TimeField()
    courseDays = models.TextField()
    courseExamTime = models.TimeField()
    courseExamDate = models.DateField()

    def __str__(self):
        return self.department+str(self.courseNum) 