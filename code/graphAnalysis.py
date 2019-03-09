import csv
import numpy as np
import json
from core import datasets,tasks,baseColumns, usersPerDataset, writeResults, getColumnType,mergeDuplicateLabels

#### NEW CLASSES ####

# Turns list of node IDs and list of edge dicts/JSON into node objects and edge objects
class Graph(object):
  def __init__(self,nodeData,edgeData):
    self.edges = self.prepEdges(edgeData)
    self.nodes = self.prepNodes(nodeData,self.edges)
    for n in self.nodes:
      node = self.nodes[n]
      node.children = node.getChildren(self.nodes)

  # turns json rows into edge objects
  def prepEdges(self,edgeData):
    edges = []
    for e in edgeData:
      edges.append(Edge(e["source"],e["target"],e["sourceOrder"],e["targetOrder"],e["interactionType"],e["interactionTypeHighlevel"],e["timestamp"]))
    return edges

  # turns node IDs and edge objects into node objects
  def prepNodes(self,nodeData,edges):
    nodes = {}
    for n in nodeData:
      nodes[n] = GraphNode(n,nodeData[n],edges)
    return nodes

  def getLeafNodes(self):
    leaves = []
    for nkey in self.nodes:
      node = self.nodes[nkey]
      if node.isLeaf():
        leaves.append(node)
    return leaves

  def getRootNodes(self):
    roots = []
    for nkey in self.nodes:
      node = self.nodes[nkey]
      if node.isRoot():
        roots.append(node)
    return roots

  def getNode(self,nid):
    if nid in self.nodes:
      return self.nodes[nid]
    else:
      return None

  def getNodeIds(self):
    return [nid for nid in self.nodes]

  # iterate over nodes by traversing all possible paths
  # with the given function (func), and the given options
  # object (opt) as a parameter. assumes that function does
  # its own bookkeeping and keeps track of visited nodes.
  def traverse(self,func,opt):
    roots = self.getRootNodes()
    for root in roots:
      root.traverse(func,opt)

class Tree(Graph):
  def __init__(self,nodeData,edgeData):
    super(Tree, self).__init__(nodeData,edgeData)
    self.filterTreeEdges()
    # fix the children
    for n in self.nodes:
      node = self.nodes[n]
      node.children = {}
    for n in self.nodes:
      node = self.nodes[n]
      node.children = node.getChildren(self.nodes)
    # fix the parents
    self.getParents()

    #print "max depth:",self.maxDepth(),", total nodes:",len(self.nodes.keys())
    #print self.maxDepthFromNode(self.nodes.keys()[-1]),self.nodes[self.nodes.keys()[-1]]

  def filterTreeEdges(self):
    for n in self.nodes:
      node = self.nodes[n]
      toKeep = []
      for edge in node.incomingEdges:
        if edge.isTreeEdge():
          toKeep.append(edge)
      node.incomingEdges = toKeep
      toKeep = []
      for edge in node.outgoingEdges:
        if edge.isTreeEdge():
          toKeep.append(edge)
      node.outgoingEdges = toKeep

  def getParents(self):
    for n in self.nodes:
      node = self.nodes[n]
      for c in node.children:
        child = node.children[c]
        child.parent = node

  def maxDepth(self):
    md = 0
    for nid in self.nodes:
      d = self.computeDepth(nid)
      md = d if d > md else md
    return md

  def minDepthFromNode(self,nid):
    node = self.nodes[nid]
    if node.isLeaf():
      return self.computeDepth(nid)
    toCheck = [node.children[c] for c in node.children]
    md = self.maxDepth()
    while len(toCheck) > 0:
      curr = toCheck.pop(0)
      if curr.isLeaf():
        d = self.computeDepth(curr.nid)
        #print "d:",d,", md:",md
        md = d if d < md else md
      else:
        toCheck.extend([curr.children[c] for c in curr.children])
    return md


  def maxDepthFromNode(self,nid):
    md = 0
    node = self.nodes[nid]
    toCheck = [node.children[c] for c in node.children]
    while len(toCheck) > 0:
      curr = toCheck.pop(0)
      if curr.isLeaf():
        d = self.computeDepth(curr.nid)
        md = d if d > md else md
      else:
        toCheck.extend([curr.children[c] for c in curr.children])
    return md

  def computeDepth(self,nid):
    node = self.getNode(nid)
    d = 0
    while node.parent is not None:
      d+=1
      node = node.parent
    return d

  def computeLeafWeight(self,nid):
    d = self.computeDepth(nid)
    md = self.minDepthFromNode(nid)
    return 1.0 * d / md if md > 0 else 0.0
    
  def distanceFromLeaf(self,nid):
    node = self.getNode(nid)
    for c in node.children:
      child

# node ID
# a list of edges (of class Edge) that may or may not involve this node
class GraphNode(object):
  def __init__(self,nid,label,allEdges):
    self.nid = nid
    self.label = label
    self.incomingEdges = self.getIncomingEdges(allEdges)
    self.outgoingEdges = self.getOutgoingEdges(allEdges)
    self.children = []
    self.parent = None

  def __repr__(self):
    return "GraphNode({},children={})".format(self.nid,self.children)

  # assumes outgoingEdges have been sorted out already
  def getChildren(self,allNodes):
    children = {}
    for o in self.outgoingEdges:
      if o.target != o.source:
        children[o.target] = allNodes[o.target]
    return children

  # filters the list of edges for only edges that have this node ID as a target
  def getIncomingEdges(self,allEdges):
    return self.getRelevantEdges(allEdges,fltr="incoming")

  # filters the list of edges for only edges that have this node ID as a source
  def getOutgoingEdges(self,allEdges):
    return self.getRelevantEdges(allEdges,fltr="outgoing")

  # returns whether this is a leaf node
  def isLeaf(self):
    return len(self.outgoingEdges) == 0

  # returns whether this is a root node, the graph may have more than one if not
  # a tree
  def isRoot(self):
    return len(self.incomingEdges) == 0

  # iterate over this node and its children with the given function (func),
  # with the given options object (opt) as a parameter. assumes that function
  # does its own bookkeeping and keeps track of visited nodes.
  def traverse(self,func,opt):
    func(self,opt)
    for c in self.outgoingEdges:
      traverse(func,opt)

  # fltr says if we should get any relevant edge (None), incoming edges
  # ("incoming"), or outgoing edges ("outgoing")
  def getRelevantEdges(self,allEdges,fltr=None):
    relevant = []
    for e in allEdges:
      if fltr is None and self.nid in [e.source,e.target]:
        relevant.append(e)
      elif fltr == "incoming" and self.nid == e.target:
        relevant.append(e)
      elif fltr == "outgoing" and self.nid == e.source:
        relevant.append(e)
    return relevant

  # count the number of self loops that occur
  def countSelfLoops(self):
    return len([1 for e in self.outgoingEdges if e.target == self.nid])

  def countIncomingEdges(self):
    return len(self.incomingEdges)

  def countOutgoingEdges(self):
    return len(self.outgoingEdges)

  # return the number of edges related to this node
  def countAllEdges(self):
    return len(self.incomingEdges) + len(self.outgoingEdges) - self.countSelfLoops()

class Edge(object):
  def __init__(self,source,target,sourceOrder,targetOrder,interactionType,interactionTypeHighlevel,timestamp):
    self.source = source
    self.sourceOrder = sourceOrder
    self.target = target
    self.targetOrder = targetOrder
    self.interactionType = interactionType
    self.interactionTypeHighlevel = interactionTypeHighlevel
    self.timestamp = timestamp

  def isSelfLoop(self):
    return self.source == self.target

  def isTreeEdge(self):
    return self.sourceOrder < self.targetOrder

  def __repr__(self):
    return "({},{})".format(self.source,self.target)

#### NEW FUNCTIONS ####

def computeTopkNodesPerSubject(dataset,task,allGraphs,allNodes,scoreFunc,k=-1):
  graphs = allGraphs[dataset][task]
  nodeIds = {}
  for n in allNodes[dataset][task]:
    nodeIds[n] = allNodes[dataset][task][n]
  scores = []
  for user in graphs:
    userScores = computeScores(nodeIds,{user:graphs[user]},scoreFunc,k=k)
    for score in userScores:
      score["user"] = user
      score["dataset"] = dataset
      score["task"] = task
    print userScores
    scores.extend(userScores)
  return scores

# given a node ID, and a set of graphs to compare, compute the overlap score
# for this node
def computeIncomingEdgesScore(nid,graphs):
  sumFrac = 0.0
  count = 0.0
  for g in graphs:
    node = graphs[g].getNode(nid)
    if node is not None:
      total = node.countAllEdges() * 1.0
      incoming = node.countIncomingEdges() * 1.0
      frac = incoming / total
      sumFrac += frac
      count += 1
  # average
  #return 0 if count == 0 else return sumFrac / count
  # sum
  return sumFrac

# given a node ID, and a set of graphs to compare, compute the overlap score
# for this node
def computeOverlapScore(nid,graphs):
  total = len(graphs)
  occurences = len([1 for g in graphs if graphs[g].getNode(nid) is not None])
  return 1.0 * occurences / total

def computeSelfLoopScore(nid,graphs):
  sumFrac = 0.0
  count = 0.0
  for g in graphs:
    node = graphs[g].getNode(nid)
    if node is not None:
      total = node.countAllEdges() * 1.0
      loopCount = node.countSelfLoops() * 1.0
      frac = loopCount / total
      sumFrac += frac
      count += 1
  # average
  #return 0 if count == 0 else return sumFrac / count
  # sum
  return sumFrac

def computeEqualWeightSelfLoopScore(nid,graphs):
  sm = 0.0
  total = 1.0 * len(graphs)
  for g in graphs:
    node = graphs[g].getNode(nid)
    if node is not None and node.countSelfLoops() > 0:
      sm += 1
  return 0.0 if total == 0 else sm / total

# given a list of node IDs, and a set of graphs to compare, computes the
# given score function for the list of nodes
def computeScores(nodeIds,graphs,scoreFunc,k=-1):
  scores = []
  for nid in nodeIds:
    scores.append({'nid':nid,'score':scoreFunc(nid,graphs),'label':nodeIds[nid]})
  return topkScores(scores,k=k)

def computeAllScores(dataset,task,allGraphs,allNodes,scoreFunc,k=-1):
  graphs = allGraphs[dataset][task]
  nodeIds = {}
  for n in allNodes[dataset][task]:
    nodeIds[n] = allNodes[dataset][task][n]
  scores = computeScores(nodeIds,graphs,scoreFunc,k=k)
  for score in scores:
    score["dataset"] = dataset
    score["task"] = task
  return scores

def compareTopkScoresWithLeaves(dataset,task,allTrees,scores):
  trees = allTrees[dataset][task]
  total = 0
  leavesFound = 0
  sumLeafWeights = 0
  results = []
  for s in scores:
    nid = s["nid"]
    for user in trees:
      tree = trees[user]
      node = tree.getNode(nid)
      if node is not None:
        total += 1
        sumLeafWeights += tree.computeLeafWeight(nid)
        if node.isLeaf():
          leavesFound += 1
        #results.append({"user":user,"score":json.dumps(s),"label":json.dumps(s["label"]),"leafWeight": tree.computeLeafWeight(nid),"isLeaf":node.isLeaf(),"dataset":dataset,"task":task})
        results.append({"user":user,"score":s["score"],"nid":nid,"label":json.dumps(s["label"]),"leafWeight": tree.computeLeafWeight(nid),"isLeaf":node.isLeaf(),"dataset":dataset,"task":task})
  #return {"scores":json.dumps(scores),"sumLeafWeights": sumLeafWeights,"leavesFound":leavesFound,"total":total,"frac":1.0*leavesFound/total,"dataset":dataset,"task":task,"averageLeafWeights":sumLeafWeights * 1.0 / total}
  return results

def sortScores(scores):
  return sorted(scores,key=(lambda r: r["score"]),reverse=True)

def topkScores(scores,k=3):
  if k < 0:
    return sortScores(scores)
  else:
    return sortScores(scores)[:k]

# creates a graph for a particular user/dataset/task tuple
def createTree(data,dataset,task,user):
  edgeData = getEdges(data,dataset,task,user,unique=True)
  nodeData = getNodes(data,dataset,task,user,unique=True)
  return Tree(nodeData,edgeData)

# creates a graph for a particular user/dataset/task tuple
def createGraph(data,dataset,task,user):
  edgeData = getEdges(data,dataset,task,user,unique=True)
  nodeData = getNodes(data,dataset,task,user,unique=True)
  return Graph(nodeData,edgeData)

# creates a new graph object for every user/dataset/task tuple in the data
def createGraphs(data):
  allGraphs = {}
  allTrees = {}
  allNodes = {}
  for dataset in usersPerDataset:
    allGraphs[dataset] = {}
    allTrees[dataset] = {}
    allNodes[dataset] = {}
    for task in tasks:
      allGraphs[dataset][task] = {}
      allTrees[dataset][task] = {}
      allNodes[dataset][task] = {}
      for user in usersPerDataset[dataset]:
        graph = createGraph(data,dataset,task,user)
        tree = createTree(data,dataset,task,user)
        allGraphs[dataset][task][user] = graph
        allTrees[dataset][task][user] = tree
        for nid in graph.getNodeIds():
          if nid not in allNodes[dataset][task]:
            allNodes[dataset][task][nid] = graph.getNode(nid).label
  return allGraphs,allTrees,allNodes

##### BEGIN OLD CODE #######

def isSelfLoop(edge):
  return edge['source'] == edge['target']

def isBranchRoot(nodeId,edges):
  outgoingEdges = getOutgoingEdges(nodeId,edges)
  return len([oe for oe in outgoingEdges if oe['target'] > nodeId]) > 1

def getBranchRoots(edges,nodes):
  roots = {}
  for nodeId in nodes.keys():
    if isBranchRoot(nodeId,edges):
      roots[nodeId] = True
  return sorted(roots.keys())

def getOutgoingEdges(nodeId,edges):
  return [e for e in edges if nodeId == e['source'] and not isSelfLoop(e)]

def getIncomingEdges(nodeId,edges):
  return [e for e in edges if nodeId == e['target'] and not isSelfLoop(e)]

def getSelfLoops(edges):
  return [e for e in edges if isSelfLoop(e)]

def isSubset(A,B):
  return A == B[:len(A)]

def getCycles(dataset,task,nodes,edges):
  cycles = []
  cycle = []
  for edge in edges:
    if isSelfLoop(edge): # ignore self loops
      continue
    if edge['source'] not in cycle:
      cycle.append(edge['source'])
    if edge['target'] not in cycle:
      cycle.append(edge['target'])
    if edge['target'] == cycle[0]: # backward edge, end of the loop
      cycle.append(edge['target']) # make sure the full cycle is captured
      promptscycle = len(nodes[edge['target']]) > 0 # better not be the empty state!
      if promptscycle:
        for state in nodes[edge['target']]:
          if state not in baseColumns[dataset][task]:
            promptscycle = False
            break
      cycles.append({'states':cycle,
        'twoStateCycle':len(cycle) == 3,'emptyStateCycle':len(nodes[edge['target']]) == 0,
        'oneColCycle':len(nodes[edge['target']]) == 1,'promptsCycle':promptscycle})
      cycle = []
  return cycles

# for histograms and aggregation
def calculatePerUserStats(data,edgeGroups,nodeGroups):
  # one row per user/dataset/task
  rowBase = {'dataset':None,'userid':None,'task':None, # done
    'totalSelfLoops':None,'totalCycles':None, # done
    'meanCycleLength':None,'maxCycleLength':None,'minCycleLength':None, # done
    'totalBranchRoots':None, 'totalInteractions':None, # done
    'meanPathLength':None,'maxPathLength':None,'minPathLength':None, # done
    'meanLengthOfAppearance':None}
  rows = []

  for dataset in usersPerDataset:
    for task in tasks:
      for user in usersPerDataset[dataset]:
        row = dict(rowBase)
        row['dataset'] = dataset
        row['task'] = task
        row['userid'] = user
        edges = edgeGroups[dataset][task][user]
        nodes = nodeGroups[dataset][task][user]
        # need
        row['totalStates'] = len(nodes)
        # need
        row['totalInteractions'] = len(edges) + 1
        # need
        row['totalSelfLoops'] = 1.0*len(getSelfLoops(edges))/row['totalInteractions']
        row['totalBranchRoots'] = 1.0*len(getBranchRoots(edges,nodes))/row['totalStates']
        cycles = getCycles(dataset,task,nodes,edges)
        row['totalCycles'] = len(cycles)
        row['meanCycleLength'] = 0 if row['totalCycles'] == 0 else np.mean([1.0*(len(c['states'])-1)/row['totalInteractions'] for c in cycles])
        row['minCycleLength'] = 0 if row['totalCycles'] == 0 else min([1.0*(len(c['states'])-1)/row['totalInteractions'] for c in cycles])
        row['maxCycleLength'] = 0 if row['totalCycles'] == 0 else max([1.0*(len(c['states'])-1)/row['totalInteractions'] for c in cycles])

        rows.append(row)
  return rows

# for histograms and aggregation
def calculatePerNodeStats(data,edgeGroups,nodeGroups):
  # one row per node/user/dataset/task
  rowBase = {'dataset':None,'userid':None,'task':None,'stateId':None,
    'totalIncomingEdges':None, 'totalOutgoingEdges':None,'totalSelfLoops':None,
    'totalInteractions':None, 'isBranchRoot':None,'totalBranches':None}
  rows = []

  for dataset in usersPerDataset:
    for task in tasks:
      for user in usersPerDataset[dataset]:
        edges = edgeGroups[dataset][task][user]
        nodes = nodeGroups[dataset][task][user]
        for nodeId in nodes:
          row = dict(rowBase)
          row['dataset'] = dataset
          row['userid'] = user
          row['task'] = task
          row['stateId'] = nodeId

          incomingEdges = getIncomingEdges(nodeId,edges)
          outgoingEdges = getOutgoingEdges(nodeId,edges)
          selfLoops = getSelfLoops([edge for edge in edges if edge['source'] == nodeId])
          row['totalEdges'] =  len(incomingEdges) +  len(outgoingEdges) + len(selfLoops) 
          row['totalOutgoingEdges'] = len(outgoingEdges)
          row['totalSelfLoops'] = len(selfLoops)
          row['totalIncomingEdges'] = len(incomingEdges)
          row['fractionOutgoingEdges'] = 1.0*len(outgoingEdges) / row['totalEdges']
          row['fractionSelfLoops'] = 1.0*len(selfLoops) / row['totalEdges']
          row['fracitonIncomingEdges'] = 1.0*len(incomingEdges) / row['totalEdges']

          row['totalInteractions'] = len(edges) + 1
          row['isBranchRoot'] = isBranchRoot(nodeId,edges)
          row['totalBranches'] = len([e for e in outgoingEdges if e['target'] > nodeId]) if row['isBranchRoot'] else 0
          row['fractionBranches'] = 1.0*len([e for e in outgoingEdges if e['target'] > nodeId]) / len(outgoingEdges) if row['isBranchRoot'] else 0
          rows.append(row)
  return rows
    
def calculatePerCycleStats(data,edgeGroups,nodeGroups):
  # user stats should be learned from calculatePerUserStats
  rowBase = {'states':None,'dataset':None,'userid':None,'task':None,
    'cycleLength':None, 'totalInteractions':None,
    'twoStateCycle':None,'emptyStateCycle':None,'oneColCycle':None,'promptsCycle':None}
  rows = []
  for dataset in usersPerDataset:
    for task in tasks:
      for user in usersPerDataset[dataset]:
        edges = edgeGroups[dataset][task][user]
        nodes = nodeGroups[dataset][task][user]
        cycles = getCycles(dataset,task,nodes,edges)
        branches = getBranchRoots(edges,nodes)
        for cycle in cycles:
          row = dict(rowBase)
          row['states'] = cycle['states']
          row['dataset'] = dataset
          row['userid'] = user
          row['task'] = task

          row['totalInteractions'] = len(edges) + 1
          row['cycleLength'] = 1.0*(len(cycle['states'])-1)/row['totalInteractions']
          row['cycleLengthNormalized'] = 1.0*(len(cycle['states'])-1)/row['totalInteractions']
          row['twoStateCycle'] = cycle['twoStateCycle']
          row['emptyStateCycle'] = cycle['emptyStateCycle']
          row['oneColCycle'] = cycle['oneColCycle']
          row['promptsCycle'] = cycle['promptsCycle']
          rows.append(row)
  return rows

def getAllEdgeGroups(data):
  edgeGroups = {}
  for dataset in usersPerDataset:
    edgeGroups[dataset] = {}
    for task in tasks:
      edgeGroups[dataset][task] = {}
      for user in usersPerDataset[dataset]:
        edgeGroups[dataset][task][user] = getEdges(data,dataset,task,user)
  return edgeGroups

def getAllNodeGroups(data):
  nodeGroups = {}
  for dataset in usersPerDataset:
    nodeGroups[dataset] = {}
    for task in tasks:
      nodeGroups[dataset][task] = {}
      for user in usersPerDataset[dataset]:
        nodeGroups[dataset][task][user] = getNodes(data,dataset,task,user)
  return nodeGroups

# get the sequence of edges for this task and user
def getEdges(data,dataset,task,user,unique=False):
  edges = []
  prevNode = None
  prevStateId = None
  for row in data:
    if row['dataset'] == dataset and row['task'] == task and row['userid'] == user:
      if unique:
        node = row['seriationId']
      else:
        node = row['stateId']
      if prevNode is not None:
        if unique:
          edge = {'source':prevNode,'target':row['seriationId'],'sourceOrder':prevStateId,'targetOrder':row['stateId'],'interactionType':row['interactionType'],
            'interactionTypeHighlevel':row['interactionTypeHighlevel'],'timestamp':row['timestamp']}
        else:
          edge = {'source':prevNode,'target':row['stateId'],'sourceOrder':prevStateId,'targetOrder':row['stateId'],'interactionType':row['interactionType'],
            'interactionTypeHighlevel':row['interactionTypeHighlevel'],'timestamp':row['timestamp']}
        edges.append(edge)
      prevNode = node
      prevStateId = row['stateId']
  return edges

# get a map from state IDs (i.e., nodes) to the node's states
def getNodes(data,dataset,task,user,unique=False):
  nodes = {}
  for row in data:
    if row['dataset'] == dataset and row['task'] == task and row['userid'] == user:
      if unique:
        nodes[row['seriationId']] = row['state']
      else:
        nodes[row['stateId']] = row['state']
  return nodes


#### NEW CODE ####

def getOverlapLeavesResults(data,k=3):
  allGraphs,allTrees,allNodes = createGraphs(data)
  results = []
  for dataset in datasets:
    for task in tasks:
      print "################### DATASET: {}, TASK: {} ############################".format(dataset,task)
      scores = computeAllScores(dataset,task,allGraphs,allNodes,computeOverlapScore,k+1)
      oldScores = scores
      scores = []
      for s in oldScores:
        if len(s["label"]) > 0:
          scores.append(s)
      scores = scores[:k]
      res = compareTopkScoresWithLeaves(dataset,task,allTrees,scores)
      results.extend(res)
  for res in results:
    res["scoringFunction"] = "overlap"
  return results

def getOverlapPromptsResults(data,prompt_states,k=3):
  allGraphs,allTrees,allNodes = createGraphs(data)
  overlapCount = 0
  total = 0
  for dataset in datasets:
    for task in tasks:
      print "################### DATASET: {}, TASK: {} ############################".format(dataset,task)
      scores = computeAllScores(dataset,task,allGraphs,allNodes,computeOverlapScore,k+1)
      oldScores = scores
      scores = []
      for s in oldScores:
        if len(s["label"]) > 0:
          scores.append(s)
      scores = scores[:k]
      overlapCount += compareStateWithPrompt(dataset,task,scores,prompt_states)
      total += 1
  return {'total':total,'overlapCount':overlapCount,'frac':1.0 * overlapCount / total}

def isSubset(A,B):
  for x in A:
    if x not in B:
      return False
  return True

def compareStateWithPrompt(dataset,task,scores,prompt_states):
  topkStates = [s["label"] for s in scores]
  relevant = prompt_states[dataset][task]
  for alternative in relevant:
    necessaryStates = [sorted(s) for s in relevant[alternative]]
    match = True
    for state in necessaryStates:
      found = False
      for candidate in topkStates:
        if isSubset(state,candidate):
          found = True
          break
      if not found:
        match = False
        break
    if match: # found match with task prompt states
      return 1
  return 0 # did not find match with task prompt states

#### END NEW CODE ####

if __name__ == "__main__":
  data = json.load(open('master_file.json'))

  edgeGroups = getAllEdgeGroups(data)
  nodeGroups = getAllNodeGroups(data)
  perUserStats = calculatePerUserStats(data,edgeGroups,nodeGroups)
  writeResults('graph_analysis_per_user.csv',perUserStats,delim='|')
  # includes branch root info too!
  perNodeStats = calculatePerNodeStats(data,edgeGroups,nodeGroups)
  writeResults('graph_analysis_per_node.csv',perNodeStats,delim='|')
  perCycleStats = calculatePerCycleStats(data,edgeGroups,nodeGroups)
  writeResults('graph_analysis_per_cycle.csv',perCycleStats,delim='|')

  '''
  for row in data:
    state=mergeDuplicateLabels(row["state"])
    row["state"] = state
  allGraphs,allTrees,allNodes = createGraphs(data)
  prompt_states = json.load(open('prompt_states.json'))

  results = getOverlapLeavesResults(data,k=3)
  writeResults('overlap_leaves.csv',results)
  json.dump(results,open('overlap_leaves.json','w'))

  #print "overlap with prompts:",getOverlapPromptsResults(data,prompt_states,k=3) 

  for dataset in datasets:
    for task in tasks:
      scores = computeAllScores(dataset,task,allGraphs,allNodes,computeSelfLoopScore,k=3)
      print dataset, task
      print scores
  #scores = computeAllScores("faa1","t1",allGraphs,allNodes,computeSelfLoopScore)
  #print scores
  #scores = computeAllScores("faa1","t1",allGraphs,allNodes,computeEqualWeightSelfLoopScore)
  #print scores
  #scores = computeAllScores("faa1","t1",allGraphs,allNodes,computeIncomingEdgesScore)
  #print scores
  #computeTopkNodesPerSubject("faa1","t1",allGraphs,allNodes,computeIncomingEdgesScore,k=3)
  '''
