import xml.dom.minidom

from partridge.models import db
from partridge.models.doc import Paper, Sentence, Author 

class PaperParser:
    """This class does the final step of paper preprocessing
    """

    def storePaper(self, filename):
        
        #parse the document
        with open(filename,'rb') as f:
            self.doc = xml.dom.minidom.parse(f)

        #extract metadata
        self.paper = Paper()
        self.extractTitle()

        #add authors
        for contrib in self.doc.getElementsByTagName("contrib"):

            if contrib.getAttribute("contrib-type") == "author":
                
                #see if the document is using surname/given-names or name
                if(len(contrib.getElementsByTagName("surname")) > 0):
                    surnameEl = contrib.getElementsByTagName("surname")[0]
                    forenameEl = contrib.getElementsByTagName("given-names")[0]
                    surname = self.extractText(surnameEl)
                    forenames = self.extractText(forenameEl)
                else:
                    #try and extract names from 'name' tag
                    nameEle = contrib.getElementsByTagName("name")[0]
                    names = self.extractText(nameEle).split(" ")
                    surname = names[-1]
                    forenames = " ".join(names[0:-1])


                author = self.lookupAuthor(surname, forenames)
                self.paper.authors.append(author)

        db.session.add(self.paper)
        db.session.commit()

        return self.paper

    def extractTitle(self):
         """Extract paper title from XML"""
         titleEls = self.doc.getElementsByTagName("article-title")

         if len(titleEls) < 1:
            titleEls = self.doc.getElementsByTagName("TITLE")


         self.paper.title = self.extractText(titleEls[0])

    def lookupAuthor(self, surname, forenames):
        """Given a surname and forename look up author or create new one
        """

        author = Author.query.filter_by(surname=surname, 
                                        forenames=forenames).first()

        if not author:
            author = Author(surname=surname, forenames=forenames)     
            db.session.add(author)
            db.session.commit()

        return author

        

    def extractText(self, node):
        """Recurse into DOM element and extract text info
        """

        text = ""
        
        for child in node.childNodes:

            if child.nodeType == self.doc.ELEMENT_NODE:
                text += self.extractText(child)
            elif child.nodeType == self.doc.TEXT_NODE:
                text += child.wholeText

        return text

if __name__ == "__main__":

    import sys
    from optparse import OptionParser
    from partridge import create_app
    from flask import Config

    optparser = OptionParser()
    
    optparser.add_option("-c", "--configfile", dest="config",
        default="", help="Override the path to the config file to load.")

    opts,args = optparser.parse_args(sys.argv)

    if(opts.config != ""):
        try:
            config.from_pyfile(opts.config)
        except IOError:
                print "Could not find any configuration files. Exiting."
                sys.exit(0)

    create_app(config)

    parser = PaperParser()

    if(len(sys.argv) < 2):
        print "Provide the name of a paper to import"
        sys.exit(0)

    parser.storePaper(sys.argv[1])