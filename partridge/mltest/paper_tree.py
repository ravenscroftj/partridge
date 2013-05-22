""" Like paper forest but trains single Dtree so we can see decisions

"""

import os
import Orange
import orngTree

from partridge.mltest.paper_forest import FEATURES, TYPE_DIRS,\
build_papers_table, printResults, buildConfusion, printConfusion, printMeasures

def buildTotalConfusions(confusions, keys):
    
    confusion = {y : { x:0 for x in keys } for y in keys}


    for c in confusions:
        for c1,c2 in [(c1,c2) for c1 in keys for c2 in keys]:
            confusion[c1][c2] += c[c1][c2]

    return confusion
            
        

def main():
    """Main script"""

    paper_table = build_papers_table()
    tree = orngTree.TreeLearner(minSubset=5,sameMajorityPruning=True)

    learners = [tree]

    FOLDS = 10

    results = Orange.evaluation.testing.cross_validation(learners, paper_table,
    folds=FOLDS,storeClassifiers=1)

    confusions = []

    print "Learner  CA     Brier  AUC"
    for i in range(len(learners)):
        print "%-8s %5.3f  %5.3f  %5.3f" % (learners[i].name, \
        Orange.evaluation.scoring.CA(results)[i], 
        Orange.evaluation.scoring.Brier_score(results)[i],
        Orange.evaluation.scoring.AUC(results)[i])
    
        for k in range(0,FOLDS):
            indices = [paper_table[x] for x in range(0,len(paper_table)) 
                if results.results[x].iteration_number == k]
            
            confusions.append(buildConfusion(indices,
            results.classifiers[k][i], TYPE_DIRS.keys()))

        confusion = buildTotalConfusions(confusions, TYPE_DIRS.keys())

        printConfusion(confusion, TYPE_DIRS.keys())
        printMeasures(confusion)
        

        orngTree.printTxt(results.classifiers[k][i], leafFields=['major', 'contingency'])

if __name__ == "__main__":
    main()
