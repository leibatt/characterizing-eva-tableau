from core import writeResults
import json

stats = json.load(open('think_time_stats.json'))

means = {
  "faa1": {
    "t1": 17.2495642857,
    "t2": 15.4072255319,
    "t3": 14.6973209302,
    "t4": 18.665562982
  },
  "birdstrikes1": {
    "t1": 11.2963868852,
    "t2": 17.2184927536,
    "t3": 15.2921411765,
    "t4": 16.8479681275
  },
  "weather1": {
    "t1": 14.2444257813,
    "t2": 13.3043540146,
    "t3": 17.7557258687,
    "t4": 11.9923313725
  }
}

sortKeys = ["dataset","task","userid","rowid"]
currSeq = []
seqLengths = []
prev = None
for row in sorted(stats,key=lambda r: tuple([r[k] for k in sortKeys])):
  dataset = row["dataset"]
  task = row["task"]
  rowid = row["rowid"]
  userid = row["userid"]
  thinkTime = row["thinkTimeAdj"]
  curr = tuple([dataset,task,userid])
  if prev != curr:
    if len(currSeq) > 0:
      # record seq length
      seqLengths.append({"dataset":prev[0],
        #"task":prev[1],"userid":prev[2],"sequenceLength":len(currSeq),"sequence":json.loads(json.dumps(currSeq))})
        "task":prev[1],"userid":prev[2],"sequenceLength":len(currSeq)})
      # clear
      currSeq = []
  mean = means[dataset][task]
  if thinkTime < mean:
    currSeq.append(rowid)
  else:
    if len(currSeq) > 0:
      # record seq length
      seqLengths.append({"dataset":dataset,
        #"task":task,"userid":userid,"sequenceLength":len(currSeq),"sequence":json.loads(json.dumps(currSeq))})
        "task":task,"userid":userid,"sequenceLength":len(currSeq)})
      # clear
      currSeq = []
  prev = curr
    
json.dump(seqLengths,open("think_time_sequences.json","w"))
writeResults("think_time_sequences.csv",seqLengths)

