# -*- coding: utf-8 -*-
"""
Created on Wed Jan 26 21:23:40 2022

@author: iraco
"""

from PyPDF2 import PdfFileWriter, PdfFileReader
import csv, os, re
import xml.etree.ElementTree as ET
import copy
from xml.dom import minidom

pages = {}
pages['Germany'] = 44

# Split des pages 

inputpdf = PdfFileReader(open("atlas.pdf", "rb"))

for i in range(inputpdf.numPages):
    output = PdfFileWriter()
    output.addPage(inputpdf.getPage(i))
    with open("Atlas/atlas%s.pdf" % i, "wb") as outputStream:
        output.write(outputStream)
