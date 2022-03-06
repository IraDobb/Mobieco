# -*- coding: utf-8 -*-
"""
Created on Tue Mar  1 09:20:28 2022

@author: iraco
"""

import csv, re

manualDataInOperationPath = 'C:\\Users\\iraco\\Documents\\S9_EC-Lyon\\MOS\\MOS 5.5 Visualisation Interactive de données\\Projet\\AtlasDataProcess\\manualDataInOperation.csv'
processedDataInOperationPath = 'C:\\Users\\iraco\\Documents\\S9_EC-Lyon\\MOS\\MOS 5.5 Visualisation Interactive de données\\Projet\\AtlasDataProcess\\processedDataInOperation.csv'

manualDataInOperationFile = open(manualDataInOperationPath, 'r', encoding='utf-8', errors='ignore')
manualDataInOperationReader = csv.reader(manualDataInOperationFile, delimiter = ';')

processedDataInOperationFile = open(processedDataInOperationPath, 'w', encoding='utf-8', newline = '')
processedDataInOperationWriter = csv.writer(processedDataInOperationFile)

processedDataInOperationWriter.writerow(['Area', 'Country/Region', 'Status', 'Section' , 'Max.Speed(km/h)' , 'Year', 'Length(km)'])

for line in manualDataInOperationReader : 
    area = line[0]
    country = line[1]
    status = line[2]
    array = line[3].split(' ')
    res = []
    
    for i in range(len(array) -1 , -1, -1):
        if(array[i].split('.')[0].isnumeric()):
            res.append(array[i])
        if(len(res) == 3):
            name = ''
            for j in range(i):
                name += array[j] + ' '
            name = name.strip(' ')
            res.append(name)
            break
        
    print(array, res)
    
    processedDataInOperationWriter.writerow([area, country, status, res[3], res[2], res[1], res[0]])
    
    
manualDataInOperationFile.close()
processedDataInOperationFile.close()

