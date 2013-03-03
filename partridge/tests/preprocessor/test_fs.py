"""
Test the partridge filesystem
"""
import os
import tempfile
import time
import logging

from Queue import Empty

from unittest import TestCase

from nose.tools import raises

from partridge.preprocessor.fs import FilesystemWatcher, PaperProcesser

#---------------------------------------------------------------------------
class MockPaperProcessor:
    
    def process_IN_CLOSE_WRITE(self, evt):
        pass


#---------------------------------------------------------------------------

class FileSystemWatchTester(TestCase):

    @classmethod
    def setUpClass(self):
        self.watchpath = tempfile.mkdtemp()
        self.fsw = FilesystemWatcher(logging.getLogger("test"))
        self.fsw.watch_directory(self.watchpath)
        self.fsw.start()



    @classmethod
    def tearDownClass(self):
        self.fsw.stop()

        for root,dirs,files in os.walk(self.watchpath):
            for file in files:
                os.unlink(os.path.join(root, file))

        os.rmdir(self.watchpath)
        

    def test_add_valid_paper(self): 
        """Test the filesystem watcher adds pdf and xml"""

        tests = ['test.xml', 'test.pdf']

        for n in [ os.path.join(self.watchpath, x) for x in tests]:
            with file(n, 'wb') as f:
                f.write("hello!")

            assert self.fsw.paper_queue.get() == n

    @raises(Empty)
    def test_add_invalid_paper(self):
        """Add a load of invalid papers and make sure they don't queue"""
        
        filename = os.path.join(self.watchpath, "test.blob")

        with file(filename,'wb') as f:
            f.write("blah blah")

        self.fsw.paper_queue.get(block=False)


    def test_queue_files(self):
        """Test that queuing up files works """

        files = []

        #add some files to the directory
        for n in range(0,20):
            path = os.path.join(self.watchpath, "test_%d.xml" % n)

            with file(path, 'wb') as f:
                f.write("testdata")

            files.append(path)

        #now make sure that all the files are queued 
        for f in files:
            assert self.fsw.paper_queue.get() == f

   
