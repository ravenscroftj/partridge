from xml.dom import minidom


d = minidom.parse(open("mode2.xml","rb"))

doctext = ""

for e in d.getElementsByTagName("s"):

    for child in e.childNodes:
        
        if(child.nodeType == d.ELEMENT_NODE):
            if(child.localName == "annotationART"):
                
                for textPart in child.childNodes:
                    
                    if( textPart.nodeType == d.TEXT_NODE):
                        doctext += textPart.wholeText
print doctext
