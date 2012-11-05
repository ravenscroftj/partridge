'''
Some utilities for curl that are reused in the pdf libraries
'''

import pycurl
from progressbar import ProgressBar

class CURLUploader:

    def perform(self, c, size=None):
        '''Do the upload with a progress bar and store result in self.result
           '''
        
            
        c.setopt(c.PROGRESSFUNCTION, self.__progress)
        self.result = "" #output from conversion
        c.setopt(c.NOPROGRESS, 0)
        c.setopt(pycurl.WRITEFUNCTION, self.__recv)
        #if size is provided, set up progress bar now, else let CURL guess later
        if(size != None):
            self.progress = ProgressBar(size)
            self.progress.start()
        else:
            self.progress = None 
        c.perform()
        self.progress.finish()
   
        

    #--------------------------------------------------------------------------  
    
    def __progress(self, download_t, download_d, upload_t, upload_d):
        '''Curl callback method used to display progress to user
        '''
        
        if( self.progress == None):

            if(upload_t < 1):
                return

            self.progress = ProgressBar(upload_t)
            self.progress.start()
        else:
            self.progress.update(upload_d)

    #--------------------------------------------------------------------------

    def __recv(self, buf):
        '''Method used to store data received from curl operations
        '''
        self.result += buf
        return len(buf)

    #--------------------------------------------------------------------------
