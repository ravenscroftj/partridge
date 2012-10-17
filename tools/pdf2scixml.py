#!/usr/bin/python2 

'''
 Python tooling for working with annotated XML papers

 @author James Ravenscroft
 @date 17/12/2012
'''

from pyPdf import PdfFileReader

f = open("test.pdf","rb")

p = PdfFileReader(f)

print p.getPage(0).extractText()
