########################################################
#MEDFORD GLX: Generated Language Extension
#Code to generate MEDFORD and 
# process parsed MEDFORD JSON files
#
#######################################################
import json
import sys
import os
import pprint
import requests
from urllib.request import urlretrieve
import gzip, shutil
import subprocess
import pandas as pd
import numpy as np
from datetime import datetime
import threading
import psutil
import time
from collections import deque
import os.path
import jmespath as jp

class GLXstats():
        
    def __str__(self):
        self.thread=0
        self.curAVG=0
        self.curN=0
        self.curRAM=0
        self.totN=0
        self.keepRunning = False
        return "GLX stats object: time elapsed "+ str(self.totN)

    def start(self, speed=1):
        # create thread and start it
        self.speed = speed
        self.thread = threading.Thread(target=self.track, args=(self,))
        self.thread.start()
        self.keepRunning = True
        
    def stop(self):

        # use `keepRunning` to stop loop in thread so thread will end
        self.keepRunning = False

        # wait for thread's end
        self.thread.join()
        return

    #modified from stack overflow
    def track(self,hmm):
        self.startTime = time.time()
        self.curAVG=0
        self.curN=0
        self.curRAM=0
        self.totN=0
        self.localTime=0
        self.maxRAM=0
        print("tracking...")
        print(self.speed)
        self.currentProcess = psutil.Process()

        # start loop
        while self.keepRunning:
            time.sleep(1)
            self.localTime=self.localTime+1
            self.totN=self.totN+1

            if(self.localTime>=self.speed):
                temp=self.currentProcess.cpu_percent(interval=1)
                self.curAVG=(self.curAVG*self.curN+temp)/(self.curN+1)
                temp=self.currentProcess.memory_info().rss / (1024 * 1024)
                self.maxRAM=max(self.maxRAM,temp)
                self.curRAM=(self.curRAM*self.curN+temp)/(self.curN+1)
                self.curN=self.curN+1
                print(temp)
                self.localTime=0
        self.endTime = time.time()
        self.totN=self.endTime-self.startTime
    
class mBlock():
    majorTag=""
    majorName=""
    minorTags=dict()

    def __init__(self, majorTag,majorName):
        self.majorName=majorName
        self.majorTag=majorTag

    def add(self,minorTag,value):
        self.minorTags[minorTag]=value

    def __str__(self):
        return "MEDFORD block for "+self.majorTag+" named "+self.majorName+" with minor tags "+ ",".join(self.minorTags.keys())

    def medfordLog(self,fname,append=True):
        if not append:
            f=open(fname, "w")
            f.write("@MEDFORD GLXGeneratedMEDFORD\n")
            f.write("@MEDFORD-Version 1.0\n\n")
        else:
            f=open(fname,"a")

        f.write("@"+self.majorTag+ " "+self.majorName+"\n")
        for key in self.minorTags.keys():
            f.write("@"+self.majorTag+"-"+key+" "+str(self.minorTags[key])+"\n")
        f.close()
    def addStats(self,statsOb):
        self.add("runTime",statsOb.totN)
        self.add("meanRAM",statsOb.curRAM)
        self.add("maxRAM",statsOb.maxRAM)
        self.add("meanCPU",statsOb.curAVG)

def getEntities(med):
    blocks=med.keys()
    names=list()
    for block in blocks:
        temp=med[block]
        for line in temp:
            names.append((block,line["value"]))
    return(names)

def getEdges(med,ents):
    blocks=med.keys()
    edges=list()
    for block in blocks:
        temp=med[block]
        #temp here is a medford block
        #print(temp)
        for line in temp:
            #for each minor tag
            #print(line)
            for ent in ents:
                #check each top level tag
                #print(ent[0])
                if ent[0] in line:
                    #if the major tag is in the key set
                    #print(ent)
                    for ele in range(len(line[ent[0]])):
                        if line[ent[0]][ele]==ent[1]:
                            edges.append((block,line["value"],ent[0],ent[1]))
    return(edges)

def graphMedford(ents,edges):
    import sys
    import networkx as nx 
    import matplotlib.pyplot as plt
    G = nx.Graph()
    for ent in ents:
        G.add_node(ent[0]+"-"+ent[1])
    for edge in edges:
        G.add_edge(edge[0]+"-"+edge[1],edge[2]+"-"+edge[3])
    spring_pos = nx.drawing.layout.spring_layout(G)
    circ_pos = nx.circular_layout(G) 
    kk_pos = nx.drawing.layout.kamada_kawai_layout(G)

    nx.draw_networkx(G,circ_pos)


def spellCheck(d):
    allFine=1
    from Levenshtein import ratio
    entDict=dict()
    ents=getEntities(d)
    for i in range(len(ents)):
        mykey=ents[i][0]
        if mykey in entDict:
            entDict[mykey].append(ents[i][1])
        else:
            entDict[mykey]=list()
            entDict[mykey].append(ents[i][1])
    for mykey in entDict.keys():
        vals=entDict[mykey]
        for i in range(len(vals)):
            for j in range(len(vals)):
                if i==j:
                    pass
                else:
                    myrat=ratio(vals[i],vals[j])
                    if myrat>.9:
                        print("Warning: major tag "+mykey+" has similar minor tags: "+vals[i]+" and "+vals[j])
                        allFine=0
    if allFine==1:
        print("No minor tags are within .9 Levenshtein ratio for any associated Major tag")





