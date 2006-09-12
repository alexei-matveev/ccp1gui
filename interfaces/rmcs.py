#!/usr/bin/env python

import SOAPpy

def group(lst, n):
    """
    Taken from http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/303060

    group([0,3,4,10,2,3], 2) => [(0,3), (4,10), (2,3)]
    
    Group a list into consecutive n-tuples. Incomplete tuples are
    discarded e.g.
    
    >>> group(range(10), 3)
    [(0, 1, 2), (3, 4, 5), (6, 7, 8)]
    """
    return zip(*[lst[i::n] for i in range(n)])

class RMCS(object):
    """

      Python wrapper around the web service provided by RMCS

    """
    version = '0.1-beta3'
    url = 'https://ebro.dl.ac.uk:8443/axis/services/rmcs?wsdl'

    def __init__(self, username, password):
        self.username = username
        self.password = password

        self.proxy = SOAPpy.WSDL.Proxy(self.url)

    def submitJob(self, MCSfile, myproxyUsername, myproxyPassword, jobName, notify):
        return self.proxy.submitJob(self.version, self.username, self.password, MCSfile, myproxyUsername, myproxyPassword, jobName, notify)

    def listJobs(self):
        result = []
        jobs = group(self.proxy.listJobs(self.version, self.username, self.password).data, 5)
        for job in jobs:
            job_dict = {}
            job_dict['jobID'] = job[0]
            job_dict['submitted'] = job[1]
            job_dict['jobState'] = job[2]
            job_dict['message'] = job[3]
            job_dict['jobName'] = job[4]
            result.append(job_dict)
        return result

    def listJobsByName(self, jobName):
        return self.proxy.listJobsByName(self.version, self.username, self.password, jobName)

    def cancelJob(self, jobID):
        return self.proxy.cancelJob(self.version, self.username, self.password, jobID)

    def removeJobDetails(self, jobID):
        return self.proxy.removeJobDetails(self.version, self.username, self.password, jobID)

    def compoundRemoveJobDetails(self, rangeString):
        return self.proxy.compoundRemoveJobDetails(self.version, self.username, self.password, rangeString)

    def getJobDetails(self, jobID):
        result = {}
        job = self.proxy.getJobDetails(self.version, self.username, self.password, jobID) 
        result['jobID'] = job[0]
        result['submitted'] = job[1]
        result['jobState'] = job[2]
        result['message'] = job[3]
        result['jobName'] = job[4]
        return result

    def updateProxy(self, myproxyUsername, myproxyPassword):
        return self.proxy.updateProxy(self.version, self.username, self.password, myproxyUsername, myproxyPassword)

    def changePassword(self, newPassword):
        oldPassword = self.password
        self.password = newPassword
        return self.proxy.changePassword(self.version, self.username, oldPassword, self.password)

    def getMachineList(self):
        return self.proxy.getMachineList(self.version, self.username, self.password)
