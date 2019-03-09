import csv
import json

stats = {}
topStates = {}
selfLoopStates = {}
prevState = None
totalInteractions = {}

for row in json.load(open('master_file.json')):
  dataset = row['dataset']
  task = row['task'].upper()
  userid = row['userid']
  state = row['seriationId'] 
  cols = tuple(row['state'])
  tup = tuple([dataset,task])
  tup2 = tuple([dataset,task,state])
  tup3 = tuple([dataset,task,userid,cols])
  tup4 = tuple([dataset,task,userid])
  if tup4 not in totalInteractions:
    totalInteractions[tup4] = 0
  totalInteractions[tup4] += 1

  if prevState == tup3 and len(cols) > 0: # self loop
    if tup not in selfLoopStates:
      selfLoopStates[tup4] = {}
    if cols not in selfLoopStates[tup4]:
      selfLoopStates[tup4][cols] = 0
    selfLoopStates[tup4][cols] += 1
  if tup not in stats:
    stats[tup] = {'dataset':dataset,'task':task,'totalInteractions':0}
  stats[tup]['totalInteractions'] += 1
  if tup not in topStates:
    topStates[tup] = {}
  if len(cols) > 0:
    if cols not in topStates[tup]:
      topStates[tup][cols] = []
    if userid not in topStates[tup][cols]:
      topStates[tup][cols].append(userid)

  interactionRaw = row['interactionTypeRaw']
  prevState = tup3

def getTopK2(topStates,k):
  tops = {}
  for tup in topStates:
    dataset = tup[0]
    task = tup[1]
    topk = []
    for state in topStates[tup]:
      insert = -1
      if len(topk) < k:
        insert = 0
      for i,e in enumerate(topk):
        if e[1] < topStates[tup][state]:
          insert = i
          break
        elif e[1] == topStates[tup][state]:
          insert = i
          break
      if insert >= 0:
        topk.insert(insert,[state,topStates[tup][state]])
      if len(topk) > k:
        topk = topk[:k]
    tops[tup] = topk
  return tops
    
selfLoopsNormalized = {}
for tup4 in selfLoopStates:
  for cols in selfLoopStates[tup4]:
    selfLoopStates[tup4][cols] /= 1.0 * totalInteractions[tup4]
    if tup4[:2] not in selfLoopsNormalized:
      selfLoopsNormalized[tup4[:2]] = {}
    if cols not in selfLoopsNormalized[tup4[:2]]:
      selfLoopsNormalized[tup4[:2]][cols] = []
    selfLoopsNormalized[tup4[:2]][cols].append(selfLoopStates[tup4][cols])
for tup in selfLoopsNormalized:
  for cols in selfLoopsNormalized[tup]:
    print selfLoopsNormalized[tup][cols]
    selfLoopsNormalized[tup][cols] = sum(selfLoopsNormalized[tup][cols])
    
topK = getTopK2(selfLoopsNormalized,3)
for tup in topK:
  for t in topK[tup]:
    print tup[0],tup[1],'['+','.join(list(t[0]))+']',t[1]

