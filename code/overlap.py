import numpy as np
import json
import sklearn
import sklearn.neighbors
from core import getStates,getStatesForSubtask,usersPerDataset,tasks, writeResults


# states = dict, allStates == array
def computeHistogram(states,allStates):
  hist = [0] * len(allStates)
  for i,s in enumerate(allStates):
    if s in states:
      hist[i] = 1
  return np.array(hist)

def compareHistogramsHelper(histograms):
  results = {'distance':{},'similarity':{},'up':[]}
  #compute per dataset
  for i in range(len(histograms)):
    h1 = histograms[i]['histogram']
    for j in range(i+1,len(histograms)):
      h2 = histograms[j]['histogram']
      results['up'].append([histograms[i]['user'],histograms[j]['user']])
      distances = computeDistances(h1,h2)
      for d in distances:
        if d not in results['distance']:
          results['distance'][d] = []
        results['distance'][d].append(distances[d])
      similarities = computeSimilarity(h1,h2)
      for s in similarities:
        if s not in results['similarity']:
          results['similarity'][s] = []
        results['similarity'][s].append(similarities[s])
  return results

def compareHistograms(histograms,dataset,task):
  results = compareHistogramsHelper(histograms)
  rows = flatten(results,dataset,task)
  return rows

def flatten(results,dataset,task):
  rows = []
  distanceKeys = results['distance'].keys()
  similarityKeys = results['similarity'].keys()
  # for each comparison
  for i in range(len(results['distance'][distanceKeys[0]])):
    row = {'dataset':dataset,'user1':results['up'][i][0],'user2':results['up'][i][1],'task':task,'modifiedJaccard':results['similarity']['modifiedJaccard'][i]}
    rows.append(row)
  return rows

# compute modified Jaccard similarity index for pair of historgrams
def computeModifiedJaccardSimilarity(h1,h2):
  intersection = 0
  rest = 0
  for i,v1 in enumerate(h1):
    if v1 == 1 or h2[i] == 1:
      if v1 == h2[i]:
        intersection += 1
      else:
        rest += 1
  denom = min(sum(h1),sum(h2))
  return 1.0*intersection / denom

# compute Jaccard similarity index for pair of historgrams
def computeJaccardSimilarity2(h1,h2):
  intersection = 0
  rest = 0
  for i,v1 in enumerate(h1):
    if v1 == 1 or h2[i] == 1:
      if v1 == h2[i]:
        intersection += 1
      else:
        rest += 1
  return 1.0*intersection / (1.0*intersection + rest)

# compute all distance measures for the pair of historgrams
def computeDistances(h1,h2):
  return {
    'jaccard': sklearn.neighbors.DistanceMetric.get_metric('jaccard').pairwise([h1],[h2])[0][0],
    'dice': sklearn.neighbors.DistanceMetric.get_metric('dice').pairwise([h1],[h2])[0][0],
    'cosine': sklearn.metrics.pairwise.cosine_distances([h1],[h2])[0][0]
  }

# compute all similarity measures for the pair of historgrams
def computeSimilarity(h1,h2):
  return {
    'jaccard': sklearn.metrics.jaccard_similarity_score(h1,h2), # will also compare matching zeros
    'jaccard2': computeJaccardSimilarity2(h1,h2), # only considers nonzero dimensions
    'modifiedJaccard': computeModifiedJaccardSimilarity(h1,h2), # only considers nonzero dimensions
    'dice': computeDice(h1,h2), # only considers nonzero dimensions
    'cosine': sklearn.metrics.pairwise.cosine_similarity([h1],[h2])[0][0]
  }

# compute dice similarity index for pair of historgrams
def computeDice(h1,h2):
  intersection = 0
  rest = 0
  for i,v1 in enumerate(h1):
    if v1 == 1 or h2[i] == 1:
      if v1 == h2[i]:
        intersection += 1
      else:
        rest += 1
  return 2.0*intersection / (2.0*intersection + rest)
