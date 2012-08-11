#!/usr/bin/python2
import csv
import os

filenames = os.listdir("./subjects")
results = [f[:-4].split('-') for f in filenames if f[-3:] == 'wav']

w = csv.writer(open('results.csv', 'w'))
w.writerows(results)





