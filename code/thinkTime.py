import datetime
import json
from core import writeResults
import numpy as np

time_format = "%Y-%m-%d %H:%M:%S.%f"
def getTime(ts):
  if ts is None:
    return None
  return datetime.datetime.strptime(ts,time_format)

def getTimeDiffs(data):
  diffRows = []
  nextRow = None
  nextNextRow = None
  totalInteractions = 0
  fivesec = 0
  tensec = 0
  for i,row in enumerate(data):
    d = row['dataset']
    t = row['task']
    u = row['userid']

    newRow = dict(row)
    newRow['currThinkTime'] = None
    newRow['currThinkTimeAdj'] = None
    newRow['totalQueries'] = len(row['queries'])
    newRow['stateSize'] = len(row['state'])
    # end of the current interaction
    end1 = newRow['timestamp-post'] if newRow['timestamp-post'] else newRow['timestamp']
    # stat of the next interaction
    start2 = None

    newRow['nextTotalQueries'] = None
    newRow['nextThinkTime'] = None
    newRow['nextStateSize'] = None
    newRow['nextThinkTimeAdj'] = None
    newRow['nextInteractionTypeHighlevel'] = nextRow['interactionTypeHighlevel'] if nextRow is not None and 'interactionTypeHighlevel' in nextRow else None
    newRow['nextInteractionType'] = nextRow['interactionType'] if nextRow is not None and 'interactionType' in nextRow else None
    if 'queryElapsedTime' not in newRow or not newRow['queryElapsedTime']:
      newRow['queryElapsedTime'] = 0.0
    tref = row['queryEndTime'] if 'queryEndTime' in row and row['queryEndTime'] else row['timestamp']
    newRow['renderTime'] = (getTime(row['finishRenderTime']) - getTime(tref)).total_seconds() if 'finishRenderTime' in row and row['finishRenderTime'] else 0.0
    if (i+1) < len(data) and d == data[i+1]['dataset'] and t == data[i+1]['task'] and u == data[i+1]['userid']:
      nextRow = data[i+1]
      start2 = nextRow['timestamp'] # beginning of the next interaction
      if 'queryElapsedTime' not in nextRow or not nextRow['queryElapsedTime']:
        nextRow['queryElapsedTime'] = 0.0
      tref = nextRow['queryEndTime'] if 'queryEndTime' in nextRow and nextRow['queryEndTime'] else nextRow['timestamp']
      nextRow['renderTime'] = (getTime(nextRow['finishRenderTime']) - getTime(tref)).total_seconds() if 'finishRenderTime' in nextRow and nextRow['finishRenderTime'] else 0.0

      # from start of curr to start of next
      #newRow['currThinkTime'] = (getTime(nextRow['timestamp']) - getTime(row['timestamp'])).total_seconds()  
      # from end of curr to end of next
      #newRow['currThinkTime'] = (getTime(nextRow['timestamp-post']) - getTime(row['timestamp-post'])).total_seconds()  

      # from end of curr to start of next
      newRow['currThinkTime'] = (getTime(start2) - getTime(end1)).total_seconds()  

      # take query time and render time into account
      newRow['currThinkTimeAdj'] = max(newRow['currThinkTime'] - newRow['queryElapsedTime'] - newRow['renderTime'],0)

      newRow['nextTotalQueries'] = len(nextRow['queries'])
      newRow['nextStateSize'] = len(nextRow['state'])
    if (i+2) < len(data) and d == data[i+2]['dataset'] and t == data[i+2]['task'] and u == data[i+2]['userid']:
      nextNextRow = data[i+2]
      #newRow['nextThinkTime'] = (getTime(nextNextRow['timestamp']) - getTime(nextRow['timestamp'])).total_seconds()  
      newRow['nextThinkTime'] = (getTime(nextNextRow['timestamp-post']) - getTime(nextRow['timestamp-post'])).total_seconds()  
      newRow['nextThinkTimeAdj'] = newRow['nextThinkTime'] - nextRow['queryElapsedTime'] - nextRow['renderTime']
    if i == 0 or d != data[i-1]['dataset'] or t != data[i-1]['task'] or u != data[i-1]['userid']:
      totalInteractions = 0
      fivesec = 0
      tensec = 0
    if newRow['currThinkTimeAdj'] and newRow['currThinkTimeAdj'] > 5:
      newRow['fivesec'] = fivesec
      fivesec = 0
    else:
      fivesec += 1
      newRow['fivesec'] = None
    if newRow['currThinkTimeAdj'] and newRow['currThinkTimeAdj'] > 10:
      newRow['tensec'] = tensec
      tensec = 0
    else:
      tensec += 1
      newRow['tensec'] = None
    newRow['interactionsBeforeQueries'] = totalInteractions
    if newRow['totalQueries'] > 0:
      totalInteractions = 0
    totalInteractions += 1

    #diffRows.append({'interactionTypeRaw':newRow['interactionTypeRaw'],'dataset':newRow['dataset'],'task':newRow['task'],'userid':newRow['userid'],'renderTime':newRow['renderTime'],'queryElapsedTime':newRow['queryElapsedTime'],'timestamp':newRow['timestamp']})
    #diffRows.append({'currThinkTime':newRow['currThinkTime'],'dataset':newRow['dataset'],'task':newRow['task'],'userid':newRow['userid'],'renderTime':newRow['renderTime'],'queryElapsedTime':newRow['queryElapsedTime']})
    diffRows.append(newRow)
  return diffRows

def computeStats(diffRows):
  blocks = {}
  res = []
  perTask = {}
  perDT = {}
  for r in diffRows:
    dataset = r['dataset']
    task = r['task']
    key = (dataset,task)
    if key not in blocks:
      blocks[key] = [r]
    else:
      blocks[key].append(r)
  for key in blocks:
    dataset = key[0]
    task = key[1]
    block = blocks[key]
    for r in block:
      if r['currThinkTime'] is not None:
        #res.append({'dataset':key[0],'task':key[1],'thinkTime':r['currThinkTime'],'interactionTypeHighlevel': r['interactionTypeHighlevel'] if 'interactionTypeHighlevel' in r else None,
        res.append({'userid':r['userid'],'rowid':r['seqId'],'dataset':key[0],'task':key[1],'thinkTime':r['currThinkTime'],'thinkTimeAdj':r['currThinkTimeAdj'],'interactionTypeHighlevel': r['interactionTypeHighlevel'] if 'interactionTypeHighlevel' in r else None,
          'interactionType': r['interactionType'] if 'interactionType' in r else None})
    #thinkTimes = [r['currThinkTime'] for r in block if r['currThinkTime'] is not None]
    thinkTimes = [r['currThinkTimeAdj'] for r in block if r['currThinkTimeAdj'] is not None]
    fracTwo = 1.0 * len([t for t in thinkTimes if t >= 2.0]) / len(thinkTimes)
    fracThree = 1.0 * len([t for t in thinkTimes if t >= 3.0]) / len(thinkTimes)
    fracFive = 1.0 * len([t for t in thinkTimes if t >= 5.0]) / len(thinkTimes)
    fracNine = 1.0 * len([t for t in thinkTimes if t >= 9.0]) / len(thinkTimes)
    fracTen = 1.0 * len([t for t in thinkTimes if t >= 10.0]) / len(thinkTimes)
    #print {'dataset':key[1],'task':key[1],'medianThinkTime':np.median(thinkTimes),'fractionThinkTimesThreeSecs':fracThree,'fractionThinkTimesTwoSecs':fracTwo,'fractionThinkTimesFiveSecs':fracFive,'fractionThinkTimesTenSecs':fracTen,'fractionThinkTimesNineSecs':fracNine,'meanThinkTime':np.mean(thinkTimes)}
    print {'dataset':key[0],'task':key[1],'mean':np.mean(thinkTimes),'count':len(thinkTimes)}
    dtk = tuple([dataset,task])
    if dtk not in perDT:
      perDT[dtk] = {'sum':sum(thinkTimes),'count':len(thinkTimes),'values':list(thinkTimes)}
    else:
      perDT[dtk]['sum'] += sum(thinkTimes)
      perDT[dtk]['count'] += len(thinkTimes)
      perDT[dtk]['values'].extend(thinkTimes)

    if task not in perTask:
      perTask[task] = {'sum':sum(thinkTimes),'count':len(thinkTimes),'values':list(thinkTimes)}
    else:
      perTask[task]['sum'] += sum(thinkTimes)
      perTask[task]['count'] += len(thinkTimes)
      perTask[task]['values'].extend(thinkTimes)
  print "task","mean","median","fractionFiveSecs","fractionTenSecs"
  for task in perTask:
    print task, perTask[task]['sum'] * 1.0 / perTask[task]['count'],np.median(perTask[task]['values']), 1.0 * len([t for t in perTask[task]['values'] if t >= 5.0]) / len(perTask[task]['values']), 1.0 * len([t for t in perTask[task]['values'] if t >= 10.0]) / len(perTask[task]['values'])
  print "dataset","task","mean","median","fractionFiveSecs","fractionTenSecs"
  for dtk in perDT:
    print dtk[0],dtk[1], perDT[dtk]['sum'] * 1.0 / perDT[dtk]['count'],np.median(perDT[dtk]['values']), 1.0 * len([t for t in perDT[dtk]['values'] if t >= 5.0]) / len(perDT[dtk]['values']), 1.0 * len([t for t in perDT[dtk]['values'] if t >= 10.0]) / len(perDT[dtk]['values'])

  #print res
  return res

if __name__ == "__main__":
  data = json.load(open("master_file.json"))
  results = getTimeDiffs(data)
  writeResults("think_time.csv",results)
  json.dump(results,open("think_time.json","w"))
  stats = computeStats(results)
  json.dump(stats,open("think_time_stats.json","w"))
  writeResults("think_time_stats.csv",stats)
  #print json.dumps(stats)
