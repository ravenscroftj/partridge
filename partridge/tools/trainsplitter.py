from xml.dom import minidom
from nltk.tokenize import punkt
import os
import cPickle


papers_dir = "/home/james/phase2_forTudor"

def get_xml_text( parentElement ):
    '''Get all text in child elements of parentElement
    '''

    output = ""

    for el in parentElement.childNodes:
        
        if el.nodeType == el.ELEMENT_NODE:
            output += " " + get_xml_text( el )

        elif el.nodeType == el.TEXT_NODE:
            output += el.wholeText

    return output


if __name__ == "__main__":

    t = punkt.PunktTrainer()

    for root,dirs,files in os.walk(papers_dir):
        
        for fname in files:
            
            name,ext = os.path.splitext(fname)

            if(ext == ".xml"):
                
                print "Training with data from %s " % fname
                with open(os.path.join(root,fname), 'r') as f:
                    doc = minidom.parse(f)
                
                sentences = ""
                i = 0
                for el in doc.getElementsByTagName("s"):
                    sentences += " " + get_xml_text( el)
                    i += 1

                print "Found %d sentences in %s" %(i,fname)
                t.train(sentences)

    #finalize the trainer
    print "Finalizing training..."
    t.finalize_training()

    p = punkt.PunktSentenceTokenizer(train_text=t.get_params())

    print "Writing new tokenizer object to file..."
    #write the training data to a pickle file
    with open("splitter.dat",'wb') as f:
        cPickle.dump(p,f)



