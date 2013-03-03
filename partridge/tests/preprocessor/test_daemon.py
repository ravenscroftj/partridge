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

    @classmethod
    def setUpClass(self):
        self.watchdir = tempfile.mkdtemp()
        self.outdir   = tempfile.mkdtemp()

        self.daemon = PaperDaemon(self.watchdir, 
            self.outdir,
            logging.getLogger(__name__))

    @classmethod
    def tearDownClass(self):

        for d in [self.watchdir, self.outdir]:
            for root,dirs,files in os.walk(d):
                for file in files:
                    os.unlink(os.path.join(root, file))

            os.rmdir(d)

    def test_paper_exists(self):
        '''Make sure that the right method is called '''

        with patch("partridge.preprocessor.daemon.PaperParser") as mock:

            self.daemon.paperExists("/path/to/file.xml")

            assert call().paperExists('/path/to/file.xml') in mock.mock_calls

    def test_split_xml(self):
        '''Ensure that '''
