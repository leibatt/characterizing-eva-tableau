import csv
import json
from overlap import computeModifiedJaccardSimilarity
from core import usersPerDataset,tasks,writeResults

MERGE_TEMPF = True # treat the temp and temp_f states as equivalent states
MERGE_LATLNG = True # treat lat, lng, latitude (generated), and longitude (generated) as equivalent pairings

def computeHistograms(data):
  rows = []
  dataset = None
  task = None
  userid = None
  states = {}
  allStates = {}
  origStates = {}
  origAllStates = {}
  visStates = {}
  visAllStates = {}
  aStates = {}
  aAllStates = {}
  for row in data:
    dataset = row['dataset']
    task = row['task']
    user = row['userid']
    if tuple([dataset,task]) not in allStates:
      allStates[tuple([dataset,task])] = {}
      origAllStates[tuple([dataset,task])] = {}
      visAllStates[tuple([dataset,task])] = {}
      aAllStates[tuple([dataset,task])] = {}
    if tuple([dataset,task,user]) not in states:
      states[tuple([dataset,task,user])] = {}
      origStates[tuple([dataset,task,user])] = {}
      visStates[tuple([dataset,task,user])] = {}
      aStates[tuple([dataset,task,user])] = {}

    if MERGE_TEMPF:
      state = row['state']
      for i,s in enumerate(state):
        if s == 'tmax_f':
          state[i] = 'tmax'
        elif s == 'tmin_f':
          state[i] = 'tmin'

    if MERGE_LATLNG:
      state = row['state']
      for i,s in enumerate(state):
        if s == 'latitude (generated)':
          state[i] = 'lat'
        elif s == 'longitude (generated)':
          state[i] = 'lng'
      
    sObj = json.dumps({'state':row['state'],'dataManipulation':row['dataManipulation']})
    oObj = json.dumps(row['state'])
    encodings = row['encodings']
    markTypes = []
    for e in encodings:
      if 'markType' in e:
        markTypes.append(e['markType'])
    vObj = json.dumps({'state':row['state'],'markTypes':markTypes})

    aObj = json.dumps({'state':row['state'],'dataManipulation':row['dataManipulation'],'markTypes':markTypes})
    if sObj not in states[tuple([dataset,task,user])]:
      states[tuple([dataset,task,user])][sObj] = 1.0
    else:
      states[tuple([dataset,task,user])][sObj] += 1.0

    if sObj not in allStates[tuple([dataset,task])]:
      allStates[tuple([dataset,task])][sObj] = 1.0
    else:
      allStates[tuple([dataset,task])][sObj] += 1.0

    if oObj not in origStates[tuple([dataset,task,user])]:
      origStates[tuple([dataset,task,user])][oObj] = 1.0
    else:
      origStates[tuple([dataset,task,user])][oObj] += 1.0

    if oObj not in origAllStates[tuple([dataset,task])]:
      origAllStates[tuple([dataset,task])][oObj] = 1.0
    else:
      origAllStates[tuple([dataset,task])][oObj] += 1.0

    if vObj not in visStates[tuple([dataset,task,user])]:
      visStates[tuple([dataset,task,user])][vObj] = 1.0
    else:
      visStates[tuple([dataset,task,user])][vObj] += 1.0

    if vObj not in visAllStates[tuple([dataset,task])]:
      visAllStates[tuple([dataset,task])][vObj] = 1.0
    else:
      visAllStates[tuple([dataset,task])][vObj] += 1.0

    if aObj not in aStates[tuple([dataset,task,user])]:
      aStates[tuple([dataset,task,user])][aObj] = 1.0
    else:
      aStates[tuple([dataset,task,user])][aObj] += 1.0

    if json.dumps(row['state']) not in aAllStates[tuple([dataset,task])]:
      aAllStates[tuple([dataset,task])][aObj] = 1.0
    else:
      aAllStates[tuple([dataset,task])][aObj] += 1.0

  allHistograms = []
  for dataset in usersPerDataset:
    for task in tasks:
      histograms = []
      origHistograms = []
      statesIndex = sorted(allStates[tuple([dataset,task])].keys())
      origStatesIndex = sorted(origAllStates[tuple([dataset,task])].keys())
      visStatesIndex = sorted(visAllStates[tuple([dataset,task])].keys())
      aStatesIndex = sorted(aAllStates[tuple([dataset,task])].keys())
      for user in usersPerDataset[dataset]:
        h = [0] * len(statesIndex)
        fh = [0.0] * len(statesIndex)
        fht = 0.0
        oh = [0] * len(origStatesIndex)
        foh = [0.0] * len(origStatesIndex)
        foht = 0.0
        vh = [0] * len(visStatesIndex)
        fvh = [0.0] * len(visStatesIndex)
        fvht = 0.0
        ah = [0] * len(aStatesIndex)
        fah = [0.0] * len(aStatesIndex)
        faht = 0.0

        for s in states[tuple([dataset,task,user])]:
          h[statesIndex.index(s)] = 1
          fh[statesIndex.index(s)] += states[tuple([dataset,task,user])][s]
          fht += states[tuple([dataset,task,user])][s]
        for s in origStates[tuple([dataset,task,user])]:
          oh[origStatesIndex.index(s)] = 1
          foh[origStatesIndex.index(s)] += origStates[tuple([dataset,task,user])][s]
          foht += origStates[tuple([dataset,task,user])][s]
        for s in visStates[tuple([dataset,task,user])]:
          vh[visStatesIndex.index(s)] = 1
          fvh[visStatesIndex.index(s)] += visStates[tuple([dataset,task,user])][s]
          fvht += visStates[tuple([dataset,task,user])][s]
        for s in aStates[tuple([dataset,task,user])]:
          ah[aStatesIndex.index(s)] = 1
          fah[aStatesIndex.index(s)] += aStates[tuple([dataset,task,user])][s]
          faht += aStates[tuple([dataset,task,user])][s]

        for i in range(len(fh)):
          fh[i] /= fht
        for i in range(len(foh)):
          foh[i] /= foht
        
        #print {'dataset':dataset,'task':task,'user':user,'origHistogram':oh,'frequencyOrigHistogram':foh}
        allHistograms.append({'statesIndex':statesIndex,'origStatesIndex':origStatesIndex,'histogram':h,'origHistogram':oh,'dataset':dataset,'task':task,'user':user,
          'frequencyHistogram':fh,'frequencyOrigHistogram':foh,
          'visHistogram':vh,'visFrequencyHistogram':fvh,'aHistogram':ah,'aFrequencyHistogram':fah})
          
  return allHistograms


if __name__ == "__main__":
  data = json.load(open("master_file.json"))
  histograms = computeHistograms(data)
  with open('histograms.json','w') as f:
    json.dump(histograms,f)
