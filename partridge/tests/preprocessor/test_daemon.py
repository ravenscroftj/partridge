"""A set of tests for testing the behaviour of the preprocessor daemon

This module tests each of the constituent behaviours of the partridge
preprocessor daemon.

"""
import os
import logging
import unittest
import tempfile

from mock import patch, MagicMock, call

from partridge.preprocessor.daemon import PaperDaemon

class TestPaperDaemon(unittest.TestCase):


#-----------------------------------------------------------------------------

    @classmethod
    def setUpClass(self):
        self.watchdir = tempfile.mkdtemp()
        self.outdir   = tempfile.mkdtemp()

        self.daemon = PaperDaemon(self.watchdir, 
            self.outdir,
            logging.getLogger(__name__))

#-----------------------------------------------------------------------------
 
    @classmethod
    def tearDownClass(self):

        for d in [self.watchdir, self.outdir]:
            for root,dirs,files in os.walk(d):
                for file in files:
                    os.unlink(os.path.join(root, file))

            os.rmdir(d)


#-----------------------------------------------------------------------------

    def test_paper_exists(self):
        '''Make sure that the right paper exists db method is called '''

        with patch("partridge.preprocessor.daemon.PaperParser") as mock:

            self.daemon.paperExists("/path/to/file.xml")

            assert call().paperExists('/path/to/file.xml') in mock.mock_calls

#-----------------------------------------------------------------------------

    def test_split_xml(self):
        '''Ensure that the right split methods are called'''

        with patch("partridge.preprocessor.daemon.SentenceSplitter") as mock:
            
            infile  = "example.xml"
            outfile = os.path.join(self.outdir, "example_split.xml" )

            #inject some data into paper daemon
            self.daemon.name = "example"
            self.daemon.paper_files = []

            self.daemon.splitXML(infile)

            #make sure the SentenceSplitter.split() method was called
            assert call().split(infile,outfile) in mock.mock_calls

            #make sure the paper daemon has a paper files entry to be deleted
            assert self.daemon.paper_files.pop() == (outfile, 'delete')


#-----------------------------------------------------------------------------

    def test_convert_pdf(self):
        '''Ensure that the PDF conversion routine works'''

        with patch("partridge.preprocessor.daemon.PDFXConverter") as mock:
            
            infile = "example.pdf"
            outfile = os.path.join(self.outdir, "example.xml")

            #inject some data
            self.daemon.name = "example"
            self.daemon.paper_files = []

            self.daemon.convertPDF(infile)

            #make sure the pdf converter was called properly
            assert call().convert(infile,outfile) in mock.mock_calls

            #make sure the paper file entry is there
            assert self.daemon.paper_files.pop() == (outfile, 'keep')
            
#-----------------------------------------------------------------------------

    def test_annotate_xml(self):
        '''Ensure that the annotation routine works properly'''

        with patch("partridge.preprocessor.daemon.RemoteAnnotator") as mock:
            
            infile  = "example.xml"
            outfile = os.path.join(self.outdir, "example_final.xml")

            #inject some data
            self.daemon.name = "example"
            self.daemon.paper_files = []

            self.daemon.annotateXML( infile )

            #make sure call to annotate is set up properly
            assert call().annotate(infile,outfile) in mock.mock_calls
            #make sure file manager entry is set up properly
            assert self.daemon.paper_files.pop() == (outfile, 'keep')

#-----------------------------------------------------------------------------

    def test_store_paper(self):
        '''Ensure that paper data is stored properly'''

        with patch('partridge.preprocessor.daemon.PaperParser') as mock:
            
            infile = "example.xml"

            self.daemon.storePaperData( infile )

            assert call().storePaper(infile) in mock.mock_calls

#------------------------------------------------------------------------------

    def test_cleanup_files(self):
        '''Make sure that cleaning up paper files works as expected
        '''

        os_patcher = patch("partridge.preprocessor.daemon.os")
        db_patcher = patch("partridge.preprocessor.daemon.db")
        fi_patcher = patch("partridge.preprocessor.daemon.PaperFile")

        paper = MagicMock()
        
        files = [('file1.xml','delete'), 
                ('file2.xml','keep'),
                ('file3.xml', 'move')]

        with os_patcher as mock_os, db_patcher as mock_db, fi_patcher as mock_fi:


            mock_os.path.basename = MagicMock(wraps=os.path.basename)
            mock_os.path.join = MagicMock(wraps=os.path.join)

            self.daemon.paper_files = files
            self.daemon.cleanupFiles(paper)

            outpath = os.path.join(self.outdir, "file3.xml")
            assert call.rename('file3.xml', outpath) in mock_os.method_calls
            assert call.unlink('file1.xml')
            assert call(path=outpath) in mock_fi.mock_calls
            assert call(path="file2.xml") in mock_fi.mock_calls
