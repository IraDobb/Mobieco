# -*- coding: utf-8 -*-
"""
Created on Fri Feb  4 17:06:16 2022

@author: iraco
"""

import csv, subprocess , re

# Parameters

countryPageIndexPath = 'atlasPages.csv'
countryAtlasPagesFolder = 'atlas'
path = 'C:\\Users\\iraco\\Documents\\S9_EC-Lyon\MOS\\MOS 5.5 Visualisation Interactive de données\\Projet\\AtlasProcess\\atlas'

# Functions definitions

def fromPdfToSvg(pageIndex):
    subprocess.check_call('inkscape --export-filename=' + pageIndex + '.svg atlas' + pageIndex + '.pdf', cwd = path)
    firstSvg = open(path + '\\' + pageIndex + '.svg')
    firstSvgText = firstSvg.read()
    firstSvg.close()
    firstSvg = open(path + '\\' + pageIndex + '.svg','w', newline='')
    firstSvgText = re.sub(u"[\x00-\x08\x0b-\x0c\x0e-\x1f]+", u"", firstSvgText) # Texte décodé des charactères problématiques
    firstSvg.write(firstSvgText)
    firstSvg.close()

# Loop across countries

countryPageIndexFile = open(countryPageIndexPath,'r', encoding='utf-8')
countryPageIndexReader = csv.reader(countryPageIndexFile, delimiter=';')
next(countryPageIndexReader)

for country in countryPageIndexReader:
    print('atlas' + country[0] + '.pdf')
    fromPdfToSvg(country[0])
    
countryPageIndexFile.close()

