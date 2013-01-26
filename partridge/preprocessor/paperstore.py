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
        titleEl = self.doc.getElementsByTagName("article-title")[0]

        paper = Paper()
        paper.title = self.extractText(titleEl)

        #add authors
        for contrib in self.doc.getElementsByTagName("contrib"):

            if contrib.getAttribute("contrib-type") == "author":
                surnameEl = contrib.getElementsByTagName("surname")[0]
                forenameEl = contrib.getElementsByTagName("given-names")[0]
                surname = self.extractText(surnameEl)
                forenames = self.extractText(forenameEl)

                author = self.lookupAuthor(surname, forenames)
                paper.authors.append(author)

        print paper.title
        db.session.add(paper)
        db.session.commit()

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
    from partridge import create_app

    create_app({'SQLALCHEMY_DATABASE_URI' : "mysql://root:icecream@localhost/partridge"}
    )

    parser = PaperParser()

    if(len(sys.argv) < 2):
        print "Provide the name of a paper to test reading"
        sys.exit(0)

    parser.storePaper(sys.argv[1])
