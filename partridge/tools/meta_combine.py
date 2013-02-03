""" This is a small utility that combines ART papers with their metadata

"""
import codecs
import os
import xml.dom.minidom

ORIGINAL_PAPER_DIR = "/home/james/tmp/corpus/original_corpus"

OUTPUT_DIR = "/home/james/tmp/corpus/combined"

INPUT_DIR = "/home/james/tmp/corpus/ART_Corpus"

for root, dirs, files in os.walk(INPUT_DIR):
    
    for file in files:
        
        anno_path = os.path.join(root, file)

        #if a _ character is in the name, expect a name like b107078a_mode2.Denis.xml
        if( file.find("_") > -1):
            id = file.split("_")[0]
        else:
            id = os.path.splitext()[0]

        #try and find original
        orig_path = os.path.join(ORIGINAL_PAPER_DIR, id + ".xml")

        if not (os.path.exists(orig_path)):
            print "skipping " + file
            continue

        #load both original and annotated files into memory
        with open(orig_path, 'rb') as f:
            orig_doc = xml.dom.minidom.parse(f)

        with open(anno_path, 'rb') as f:
            anno_doc = xml.dom.minidom.parse(f)

        #get original author data and copy into anno tree
        anno_paperEl = anno_doc.getElementsByTagName("PAPER")[0]


        for tagName in ['METADATA', 'AUTHORLIST', 'CURRENT_AUTHORLIST']:
            try:
                el = orig_doc.getElementsByTagName(tagName)[0]
                anno_paperEl.appendChild(el)
            except:
                print "couldn't find %s element in %s" % (tagName, orig_doc)


        #write the new metadata to the output directory
        outPath = os.path.join(OUTPUT_DIR, id+".xml")

        with codecs.open(outPath, 'wb', encoding='utf-8') as f:
            anno_doc.writexml(f)
