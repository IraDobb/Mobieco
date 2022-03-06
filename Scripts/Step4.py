# -*- coding: utf-8 -*-
"""
Created on Sun Feb 20 15:14:56 2022

@author: iraco
"""

import xml.etree.ElementTree as ET
import csv 
import numpy as np
import requests
import urllib.parse
from scipy.optimize import minimize
from geojson import LineString, MultiLineString, FeatureCollection, Feature, dump
import json

# Parameters

labelCsvFilePath = 'Label.csv'
xmlns = '{http://www.w3.org/2000/svg}'
floatArray = np.vectorize(float)

# Functions definition

def importCsvLabelisationFile(csvLabelPath):
    
    res = {}

    file = open(csvLabelPath, 'r', encoding = 'utf-8')
    reader = csv.reader(file, delimiter = ';')
    next(reader, None) # To skip the header
    
    for line in reader:
        
        if(not line[0] in res.keys()):
            res[line[0]] = {}
            
        if(not line[1] in res[line[0]].keys()):
            res[line[0]][line[1]] = {}
            
        res[line[0]][line[1]][line[2]] = {'name' : line[3]}
    
    file.close()
    return res

def getTransformationMatrixFromStr(transformationStr):
    
    if(transformationStr.startswith('matrix')):
        coordinates = floatArray(transformationStr.split('(')[1].strip(')').split(','))
        return np.array([[coordinates[0], coordinates[2], coordinates[4]],
                         [coordinates[1], coordinates[3], coordinates[5]],
                         [0., 0., 1.]])
    
    elif(transformationStr.startswith('translate')):
        coordinates = floatArray(transformationStr.split('(')[1].strip(')').split(','))
        return np.array([[1., 0., coordinates[0]],
                         [0., 1., coordinates[1]],
                         [0., 0., 1.]])
    
def getLocalCoordinatesOfCities(pageNumber, label, logLevel = False):
    
    svgRoot = ET.parse(pageNumber + '.svg').getroot()

    # Get SVG city coordinates
    for gId in label[pageNumber]['CITY'].keys():
        
        # Let's find it the SVG 
        for it in svgRoot.findall('.//' + xmlns + 'g' + '[@id="' + gId + '"]'):
            
            # Get the local -> svg base transformation
            
            localToSvgBaseTransformation = getTransformationMatrixFromStr(it.get('transform'))
            
            # Assuming the circle definition always begin at the bottom of the shape
            path = it.find(xmlns + 'path')
            localCoordinate = np.vstack([0., float(path.get('d').split(' ')[5].split(',')[1]), 1.])
            
            # Compute svg based coordinates
            svgCoordinate = np.dot(localToSvgBaseTransformation, localCoordinate)
            
            if(logLevel):
                print('Traitement du groupe ' + str(label[pageNumber]['CITY'][gId]['name']) + ' ; coordonnées svg calculées : ')
                print(svgCoordinate)
            
            # Write it in the dict
            label[pageNumber]['CITY'][gId]['svgCoordinates'] = svgCoordinate
            
    return label

def getRealCoordinatesOfCities(pageNumber, label, logLevel = False):
    
    file = open('OfflineCoordinates.csv', 'r', encoding = 'utf-8')
    reader = csv.reader(file, delimiter = ';')
    next(reader, None) # To skip the header
    loadedDic = {}
    
    for line in reader:
        loadedDic[line[0]] = np.vstack([float(line[2]), float(line[3]), 1.])
        
    file.close()
    
    file = open('OfflineCoordinates.csv', 'a', encoding = 'utf-8', newline = '')
    writer = csv.writer(file, delimiter = ';')
    
    for gId, dic in label[pageNumber]['CITY'].items():
        
        if(gId in loadedDic.keys()):
            print('Already charged ' + dic['name'])
            label[pageNumber]['CITY'][gId]['realCoordinates'] = loadedDic[gId]
        
        else:
            response = requests.get('https://nominatim.openstreetmap.org/search/' + urllib.parse.quote(dic['name']) +'?format=json').json()[0]
            realCoordinates = np.vstack([float(response['lon']), float(response['lat']), 1.])
            if(logLevel):
                print('Coordonnées réelles de ' + str(dic['name']))
            label[pageNumber]['CITY'][gId]['realCoordinates'] = realCoordinates
            
            # Write in the OfflineCoordinates
            writer.writerow([gId, dic['name'], realCoordinates[0,0], realCoordinates[1,0]])
            
    file.close()
            
    return label

def loss(transformationMatrix, pageNumber, label):
    loss = 0
    transformationMatrix = np.array([[transformationMatrix[0], transformationMatrix[2], transformationMatrix[4]],
                                     [transformationMatrix[1], transformationMatrix[3], transformationMatrix[5]],
                                     [0., 0., 1.]])
    for gId, dic in label[pageNumber]['CITY'].items():
        calculatedCoordinates = np.dot(transformationMatrix, dic['svgCoordinates'])
        loss += (calculatedCoordinates[0,0] - dic['realCoordinates'][0,0]) ** 2 + (calculatedCoordinates[1,0] - dic['realCoordinates'][1,0]) ** 2
    print(loss)
    return loss / 10

def getTransformationMatrixSvgToReal(pageNumber, label):
    transformationMatrix = minimize(loss, np.ones(6), args = (pageNumber, label), tol = 1e-6).x
    label[pageNumber]['TransformationMatrix'] = np.array([[transformationMatrix[0], transformationMatrix[2], transformationMatrix[4]],
                                                          [transformationMatrix[1], transformationMatrix[3], transformationMatrix[5]],
                                                          [0., 0., 1.]])
    return label

def getAbsolutePathFromRelative(localPathStr, digit = 3):
    
    elements = localPathStr.split(' ')
    lastCoordinate = [0., 0.]
    lastElement = ''
    lastType = ''
    resPath = ''
    cCounter = 0
    
    for it in elements:
        
        if(it.isalpha()):
            if(it.isupper()):
                lastType = 'absolute'
            else:
                lastType = 'relative'
            lastElement = it.upper()
            resPath += it.upper() + ' '
            if(lastElement == 'C'):
                cCounter = 0
            
        else:
            if(lastType == 'relative'):
                if(lastElement == 'H'):
                    lastCoordinate = [float(it) + lastCoordinate[0], lastCoordinate[1]]
                    resPath += str(round(lastCoordinate[0], digit)) + ' '
                elif(lastElement == 'V'):
                    lastCoordinate = [lastCoordinate[0], float(it) + lastCoordinate[1]]
                    resPath += str(round(lastCoordinate[1], digit)) + ' '
                elif(lastElement == 'C' and cCounter != 2):
                    x, y = it.split(',')
                    resPath += str(round(float(x) + lastCoordinate[0], digit)) + ',' + str(round(float(y) + lastCoordinate[1], digit)) + ' '
                    cCounter += 1
                else:
                    x, y = it.split(',')    
                    lastCoordinate = [float(x) + lastCoordinate[0], float(y) + lastCoordinate[1]]
                    resPath += str(round(lastCoordinate[0], digit)) + ',' + str(round(lastCoordinate[1], digit)) + ' '
                    cCounter = 0
            else:
                if(lastElement == 'H'):
                    lastCoordinate = [float(it), lastCoordinate[1]]
                    resPath += str(round(lastCoordinate[1], digit)) + ' '
                elif(lastElement == 'V'):
                    lastCoordinate[lastCoordinate[0], float(it)] + ' '
                elif(lastElement == 'C' and cCounter != 2):
                    x, y = it.split(',')
                    resPath += str(round(float(x), digit)) + ',' + str(round(float(y), digit)) + ' '
                    cCounter += 1
                else:
                    x, y = it.split(',')
                    lastCoordinate = [float(x), float(y)]
                    resPath += str(round(lastCoordinate[0], digit)) + ',' + str(round(lastCoordinate[1], digit)) + ' '
                    cCounter = 0
                    
    return resPath.strip(' ')

def applyTransformationMatrixtoPath(localTransformation, absolutePath, digit = 3):
    
    # Assuming we have an absolute path
    
    elements = absolutePath.split(' ')
    lastElement = ''
    resPath = ''
    
    for it in elements:
        
        if(it.isalpha()):
            lastElement = it
            resPath += it + ' '
            
        else:
            if(lastElement == 'H'):
                coordinates = np.vstack([float(it), 0., 1.])    
                coordinates = np.dot(localTransformation, coordinates)
                resPath += str(round(coordinates[0, 0], digit)) + ' '
            elif(lastElement == 'V'):
                coordinates = np.vstack([0., float(it), 1.])    
                coordinates = np.dot(localTransformation, coordinates)
                resPath += str(round(coordinates[1, 0], digit)) + ' '
            else:
                coordinates = np.vstack(np.append(floatArray(np.array(it.split(','))), [1.]))    
                coordinates = np.dot(localTransformation, coordinates)
                resPath += str(round(coordinates[0, 0], digit)) + ',' + str(round(coordinates[1, 0], digit)) + ' '
                    
    return resPath.strip(' ')

def processGeoJsonFromSvgPath(svgBasedPath, digit = 3):
    
    # Assuming we have an absolute path
    
    elements = svgBasedPath.split(' ')
    lastCoordinate = [0., 0.]
    lastElement = ''
    coordinatesList = []
    cCounter = 0
    
    for it in elements:
        
        if(it.isalpha()):
            lastElement = it
            if(lastElement == 'C'):
                cCounter = 0
            
        else:
            if(lastElement == 'H'):
                lastCoordinate = [round(float(it), digit), lastCoordinate[1]]
                coordinatesList.append(tuple(lastCoordinate))
            elif(lastElement == 'V'):
                lastCoordinate = [lastCoordinate[0], round(float(it), digit)]
                coordinatesList.append(tuple(lastCoordinate))
            elif(lastElement == 'C' and cCounter != 2):
                # Ignoring theses values (approximating curves by lines)
                cCounter += 1
            else:
                x, y = it.split(',')    
                lastCoordinate = [round(float(x), digit), round(float(y), digit)]
                coordinatesList.append(tuple(lastCoordinate))
                cCounter = 0
                    
    return coordinatesList

def processPath(pageNumber, label):
    
    svgRoot = ET.parse(pageNumber + '.svg').getroot()
    
    featureCollectionArray = []

    # Get SVG city coordinates
    for gId, dic in label[pageNumber]['LGV'].items():
        
        # Let's find it the SVG 
        for it in svgRoot.findall('.//' + xmlns + 'g' + '[@id="' + gId + '"]'):
            print('ok')
            
    return featureCollectionArray

def processLGV(pageNumber, label):
    
    svgRoot = ET.parse(pageNumber + '.svg').getroot()
    
    featureCollectionArray = []
    lgvAlreadyDone = []

    # Get SVG city coordinates
    for gId, dic in label[pageNumber]['LGV'].items():
        
        print(dic['name'])
    
        # Let's find it the SVG 
        for it in svgRoot.findall('.//' + xmlns + 'g' + '[@id="' + gId + '"]'):
            relativePath = it.find(xmlns + 'path').get('d')

            absolutePath = getAbsolutePathFromRelative(relativePath)

            localTransformation = getTransformationMatrixFromStr(it.get('transform'))
            realBasedPath = applyTransformationMatrixtoPath(np.dot(label[pageNumber]['TransformationMatrix'],localTransformation), absolutePath)
            coordinatesList = processGeoJsonFromSvgPath(realBasedPath)
            if(not dic['name'] in lgvAlreadyDone):
                featureCollectionArray.append(Feature(geometry = MultiLineString([coordinatesList]), properties ={'name' : dic['name']}))
                lgvAlreadyDone.append(dic['name'])
            else:
                for i in range(len(featureCollectionArray)):
                    if(featureCollectionArray[i]['properties']['name'] == dic['name']):
                        featureCollectionArray[i]['geometry']['coordinates'].append(coordinatesList)
                        break
            
    return featureCollectionArray
        
# Main Run 

atlasIndex = ['32', '34', '36', '40', '42', '44', '46', '48', '51', '52', '54', '56', '118', '120', '122', '124', '126', '128', '158', '169', '179', ]

label = importCsvLabelisationFile(labelCsvFilePath)

featureCollectionArray = []

for pageNumber in atlasIndex :
    
    # Compute the calibration matrix
    label = getLocalCoordinatesOfCities(pageNumber, label)
    label = getRealCoordinatesOfCities(pageNumber, label, logLevel = False)
    label = getTransformationMatrixSvgToReal(pageNumber, label)
    
    # Now, the paths
    featureCollectionArray += processLGV(pageNumber, label)
    
featureCollection = FeatureCollection(featureCollectionArray)

# Write to output file
file = open('output.geojson', 'w')
dump(featureCollection, file)
file.close()

# For each group Path of the file :
    # Get the path in the local base
    # Apply relative to absolute transformation
    # Apply the transformation to get the path in the svg base
    # Apply the transformation svg --> real to get the path in the real base 
    # Compute and simplify path to GeoJSON format 