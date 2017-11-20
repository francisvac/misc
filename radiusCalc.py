#!/usr/bin/python
import argparse
import os
from os.path import basename
import numpy as np
import cPickle as p
from lqCircle import leastsq_circle
import utm


# Steering wheel angle vs speed analysis
# Input: directory path for (angle, speed, ts) pickle files

class LogAnalyzer:
    def __init__(self, args):
        # self.path = args.path
        self.path = args
        self.speeds = []
        self.angles = []
        self.cmd_angles = []
        self.time = []
        self.utm_x = []
        self.utm_y = []
        self.lat = []
        self.lon = []
        self.gps_time = []
        self.gps_index = []
        self.critical_points = []
        self.lower_bound = -1
        self.sample_length = 5
        self.bag_name = ''
    def process(self):
        i = 0
        for fname in os.listdir(self.path):
            if fname.endswith(".p"):
                if "_gps.p" in fname:
                    continue
                self.bag_name = os.path.splitext(basename(fname))[0]
                i = i + 1
                try:
                    file = self.path + self.bag_name + ".p"
                    print 'loading file ', file
                    data = p.load(open(file, "rb"))
                    for angle, cmd, speed, ts in data:
                        if speed <= 0.0001:
                            continue
                        self.speeds.append(speed)
                        self.angles.append(angle)
                        self.cmd_angles.append(cmd)
                        self.time.append(ts)
                except Exception as e:
                    print(e)

                try:
                    file = self.path + self.bag_name + "_gps.p"
                    print 'loading file ', file
                    data = p.load(open(self.path + self.bag_name + "_gps.p", "rb"))
                    for lat, lon, ts, temp in data:
                        self.lat.append(lat)
                        self.lon.append(lon)
                        self.gps_time.append(ts)
                except Exception as e:
                    print(e)

            self.dump()
            self.reset()
            print i


    def dump(self):
        for i in range(len(self.lat)):
            utmXY = utm.from_latlon(self.lat[i], self.lon[i])
            self.utm_x.append(utmXY[0])
            self.utm_y.append(utmXY[1])
        m = 0
        len_gps_time = len(self.gps_time)
        if len_gps_time:
            for i in range(len_gps_time):
                self.gps_index.append(len(self.time))
            for j in range(len(self.time)):
                if self.time[j] > self.gps_time[m]:
                    self.gps_index[m] = max(0,j - 1)
                    if m == (len_gps_time - 1):
                        break
                    m = m + 1
            print "completed 2D frame"
            self.consolidate()
            print "completed consolidation"
            zipped_info = zip(self.critical_points)
            p.dump(zipped_info, open('./critical_data/'+self.bag_name+".p", "wb"), p.HIGHEST_PROTOCOL)
            print "done"

    def reset(self):
        self.speeds = []
        self.angles = []
        self.cmd_angles = []
        self.time = []
        self.utm_x = []
        self.utm_y = []
        self.lat = []
        self.lon = []
        self.gps_time = []
        self.gps_index = []
        self.critical_points = []
        self.lower_bound = -1

    def consolidate(self):
        tpts = len(self.speeds)
        for i in range(tpts):
            try:
                trad, c, sample_lbd, sample_ubd = self.sampleExtract(i, 1)
                trad2, c2, sample_lbd, sample_ubd = self.sampleExtract(i, 2)
                if trad == 0:
                    continue
                if abs(trad - trad2) > 100:
                    continue
                if self.lower_bound == sample_lbd:
                    continue
                self.lower_bound = sample_lbd
                print str(i), ' of ', tpts
                temp_speed = np.average(self.speeds[sample_lbd:sample_ubd])
                temp_angle = np.average((self.angles[sample_lbd:sample_ubd]))
                self.critical_points.append(temp_speed)
                self.critical_points.append(temp_angle)
                self.critical_points.append(trad)
                self.critical_points.append(c)
                self.critical_points.append(self.time[i])
            except:
                pass

        self.critical_points = np.reshape(self.critical_points,[(len(self.critical_points)/5),5])
        print np.shape(self.critical_points)

    def calcDistance(self, x1, y1, x2, y2):
        return abs(((x1-x2)**2 + (y1-y2)**2)**0.5)

    def sampleExtract(self, index, multiply):
        t = self.time[index]
        fwd_dist = 1.3 * multiply
        t_fwd_dist = 0.
        pts = len(self.utm_x)
        i = 0;
        for j in range(pts):
            if self.gps_time[j] >= t:
                i = i + 1
                if fwd_dist <= t_fwd_dist:
                    i = i + i * 2/3
                    lb = j - int(round(i))
                    lower_bound = max(0,lb)
                    upper_bound = min(pts ,j)
                    sample_x = self.utm_x[lower_bound:upper_bound]
                    sample_y = self.utm_y[lower_bound:upper_bound]
                    sample_lbd = self.gps_index[lower_bound]
                    sample_ubd = self.gps_index[upper_bound - 1]
                    rad = 0
                    if len(sample_x):
                        try:
                            _, _, rad, c = leastsq_circle(sample_x, sample_y)
                            return rad, c, sample_lbd, sample_ubd
                        except:
                            return 0, 0, [], []
                else:
                    t_fwd_dist = t_fwd_dist + self.calcDistance(self.utm_x[j],self.utm_y[j],self.utm_x[j-1],self.utm_y[j-1])
        return 0,0, [],[]

if __name__ == "__main__":
    # parser = argparse.ArgumentParser(description='analyzer for steering angle data')
    # parser.add_argument('path', help='directory to parse')
    # args = parser.parse_args()
    la = LogAnalyzer('all_data/')
    la.process()