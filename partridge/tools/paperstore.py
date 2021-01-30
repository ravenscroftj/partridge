import xml.dom.minidom

from partridge.config import config
from partridge.models import db
from partridge.models.doc import Paper, Sentence, Author


class PaperParser:
    """This class does the final step of paper preprocessing
    """

    def paperExists(self, filename):
        """Check the database to see if an identical paper is found"""
        with open(filename, 'rb') as f:
            self.doc = xml.dom.minidom.parse(f)

        # first test with DOI
        doi = self.extractDOI()

        results = Paper.query.filter(Paper.doi == doi)

        if((results.count() < 1) or (doi == None)):

            title = self.extractTitle()

            authors = self.extractAuthors()

            author_surnames = [x.surname for x in authors]

            results = Paper.query.join("authors").filter(
                Paper.title == title,
                Author.surname.in_(author_surnames))

        if results.count() > 0:
            return results.first()
        else:
            return None

    def parseFileObject(self, f):
        self.doc = xml.dom.minidom.parse(f)

    def parseString(self, s):
        self.doc = xml.dom.minidom.parseString(s)

    def parsePaper(self, filename):
        """Parse a paper but don't store it"""
        # parse the document
        with open(filename, 'rb') as f:
            self.parseFileObject(f)

    def storePaper(self, filename):
        """Store the paper information in the database"""
        self.parsePaper(filename)

        # extract metadata
        paper = Paper()
        paper.title = self.extractTitle()
        paper.abstract = self.extractAbstract()
        paper.doi = self.extractDOI()

        # add authors
        paper.authors.extend(self.extractAuthors())

        sentences = self.extractSentences()

        for text, coresc in sentences:
            sent = Sentence(text=text, coresc=coresc)
            db.session.add(sent)
            paper.sentences.append(sent)

        # store the updated database info
        db.session.add(paper)
        db.session.commit()

        return paper

    def extractDOI(self):
        """Extract a paper's DOI from the XML"""

        # first try extracting SciXML article ID style
        ids = self.doc.getElementsByTagName("article-id")
        for id in ids:
            if id.getAttribute("pub-id-type") == "doi":
                return self.extractText(id)

        # try TEI processing
        if len(self.doc.getElementsByTagName("teiHeader")) > 0:
            header = self.doc.getElementsByTagName("teiHeader")[0]
            idnos = header.getElementsByTagName("idno")

            for id in idnos:
                if id.getAttribute("type") == "DOI":
                    return self.extractText(id)


        # now try the ART format style
        mdlist = self.doc.getElementsByTagName("METADATA")

        if len(mdlist) > 0:
            for node in mdlist[0].childNodes:
                if ((node.nodeType == self.doc.ELEMENT_NODE) and
                        (node.localName == "DOI")):
                    return self.extractText(node)
                elif((node.nodeType == self.doc.TEXT_NODE) and
                     (node.wholeText.find("/") > -1)):

                    doi = node.wholeText

                    if(doi.endswith("article")):
                        return doi[:-7]
                    else:
                        return doi

        return None

    def extractSentences(self):
        """Extract sentences and relative coresc concept from xml"""

        for annoEl in self.doc.getElementsByTagName("CoreSc1"):

            # try and get the coreSC annotation
            s = annoEl.parentNode
            annoType = annoEl.getAttribute("type")

            yield (self.extractText(s), annoType)

    def extractRawSentences(self):
        """Extract sentence data without coresc information"""

        for s in self.doc.getElementsByTagName("s"):
            yield self.extractText(s)

    def extractAbstract(self):
        """Extract the paper abstract from xml"""

        # we are either looking for "abstract" element or "ABSTRACT" element
        if(len(self.doc.getElementsByTagName("abstract")) > 0):
            abEl = self.doc.getElementsByTagName("abstract")[0]
        else:
            abEl = self.doc.getElementsByTagName("ABSTRACT")[0]

        return self.extractText(abEl)

    def extractAuthors(self):
        """Extract author metadata from paper XML"""

        for contrib in self.doc.getElementsByTagName("contrib"):

            if contrib.getAttribute("contrib-type") == "author":

                # see if the document is using surname/given-names or name
                if(len(contrib.getElementsByTagName("surname")) > 0):
                    surnameEl = contrib.getElementsByTagName("surname")[0]
                    forenameEl = contrib.getElementsByTagName("given-names")[0]
                    surname = self.extractText(surnameEl)
                    forenames = self.extractText(forenameEl)
                elif(len(contrib.getElementsByTagName("name")) > 0):
                    # try and extract names from 'name' tag
                    nameEle = contrib.getElementsByTagName("name")[0]
                    names = self.extractText(nameEle).split(" ")
                    surname = names[-1]
                    forenames = " ".join(names[0:-1])
                else:
                    # could be acknowledgement that this is a collaboration
                    continue

                yield self.lookupAuthor(surname, forenames)

        # tei
        headerEls = self.doc.getElementsByTagName("teiHeader")

        if len(headerEls) > 0:
            
            for author in headerEls[0].getElementsByTagName("author"):

                # see if the document is using surname/given-names or name
                nameEls = author.getElementsByTagName("persName")
                if nameEls is not None:

                    nameEl = nameEls[0]

                    if len(nameEl.getElementsByTagName("surname")) > 0:
                        surnameEl = nameEl.getElementsByTagName("surname")[0]
                        forenames = nameEl.getElementsByTagName("forename")
                        surname = self.extractText(surnameEl)
                        forenames = " ".join([self.extractText(el) for el in forenames])

                        yield self.lookupAuthor(surname, forenames)

        authEls = self.doc.getElementsByTagName("CURRENT_AUTHOR")
        authEls.extend(self.doc.getElementsByTagName("AUTHOR"))

        # if there aren't any contrib elements, try CURRENT_AUTHOR els
        for authorEl in authEls:

            forenames = ""
            surname = ""

            if((authorEl.firstChild.nodeType == self.doc.ELEMENT_NODE)
                & ((authorEl.firstChild.localName == "CURRENT_NAME")
                   | (authorEl.firstChild.localName == "NAME"))):
                authorEl = authorEl.firstChild

            # get text node and surname
            for node in authorEl.childNodes:

                if((node.nodeType == self.doc.ELEMENT_NODE) &
                    ((node.localName == "CURRENT_SURNAME") |
                     (node.localName == "SURNAME"))):
                    surname = self.extractText(node)

                if(node.nodeType == self.doc.TEXT_NODE):

                    if (forenames == ""):
                        forenames = node.wholeText

                    if (len(node.wholeText) < len(forenames)):
                        forenames = node.wholeText

            yield self.lookupAuthor(surname, forenames)

    def extractTitle(self):
        """Extract paper title from XML"""
        titleEls = self.doc.getElementsByTagName("article-title")

        if len(titleEls) < 1:
            titleEls = self.doc.getElementsByTagName("TITLE")

        if len(titleEls) < 1:  # for TEI
            titleEls = self.doc.getElementsByTagName("title")

        return self.extractText(titleEls[0])

    def lookupAuthor(self, surname, forenames):
        """Given a surname and forename look up author or create new one
        """

        author = Author.query.filter_by(surname=surname,
                                        forenames=forenames).first()

        if not author:
            author = Author(surname=surname, forenames=forenames)
            db.session.add(author)

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

        return text.strip()


if __name__ == "__main__":

    import sys
    from optparse import OptionParser
    from partridge import create_app
    from flask import Config
    from partridge.config import config

    optparser = OptionParser()

    optparser.add_option("-c", "--configfile", dest="config",
                         default="", help="Override the path to the config file to load.")

    opts, args = optparser.parse_args(sys.argv)

    # config = Config({})
    # if(opts.config != ""):
    #     try:
    #         config.from_pyfile(opts.config)
    #     except IOError:
    #         print ("Could not find any configuration files. Exiting.")
    #         sys.exit(0)

    create_app(config)

    parser = PaperParser()

    if(len(args) < 2):
        print ("Provide the name of a paper to import")
        sys.exit(0)

    print (parser.paperExists(args[1]))
