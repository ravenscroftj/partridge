'''
Created on 26 Mar 2012

@author: grabmuel
'''
import os
from os.path import join, split


sourceDirs = [
              '/nfs/research2/textmining/sapienta/Project/Development/Sapient2/corpora/TierA',
              '/nfs/research2/textmining/sapienta/Project/Development/Sapient2/corpora/TierB'
              ]
targetRoot = '/nfs/research2/textmining/grabmuel/coresc_corpus'

for sourceDir in sourceDirs:
    targetDir = join(targetRoot, split(sourceDir)[1])
    try:
        os.makedirs(targetDir)
    except OSError:
        pass # directory already exists
    
    files = [f for f in os.listdir(sourceDir) if f.endswith('.xml') and not f.startswith('.')]
    for f in files:
        targetFile = open(join(targetDir, f), 'w')
        for line in open(join(sourceDir, f)):
            if line == '<?xml version="1.0"?>\n':
                targetFile.write('<?xml version="1.0" encoding="ISO-8859-1"?>\n')
            else:
                targetFile.write(line) 
        targetFile.close()