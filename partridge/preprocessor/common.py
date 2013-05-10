"""
Code common across server and client for preprocessor
"""

class PreprocessingException(Exception):

    #exc_type, exc_obj, exc_tb = sys.exc_info()
    paper = ""
    files = []
    traceback = None
    pdf = False
