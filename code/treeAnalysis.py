import csv
import numpy as np
import json
from core import datasets,tasks,columnInfo, baseColumns, usersPerDataset, writeResults, getColumnType
from graphAnalysis import getAllEdgeGroups,getAllNodeGroups

class Node:
  def __init__(self,nid):
    self.nid = nid
    self.parent = None
    self.children = []

  def computeLeaves(self):
    if len(self.children) == 0: # this is a leaf
      return 1
    return sum([child.computeLeaves() for child in self.children])

  def computeDepth(self):
    d = 0
    currNode = self
    while(currNode.parent):
      d += 1
      currNode = currNode.parent
    return d

  def getOutgoingEdges(self):
    return len(self.children)

def computeTreeStats(edges):
  tree = computeTree(edges)
  if tree is None:
    return 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
  total = countNodes(tree)
  leaves = tree.computeLeaves()
  sumd = computeSumDepth(tree)
  maxd = computeMaxDepth(tree)
  sumbf = computeSumBranchingFactor(tree)
  maxbf = computeMaxBranchingFactor(tree)
  #print total,sumbf,maxbf,[e['target'] for e in edges]
  return total,1.0*sumd/total,1.0*sumbf/total,leaves,1.0*sumd/(total*total),1.0*sumbf/(total*total),1.0*leaves/total,1.0*maxd,1.0*maxbf,1.0*maxd/total,1.0*maxbf/total

def countNodes(tree):
  cnt = 1
  for child in tree.children:
    cnt += countNodes(child)
  return cnt

def computeSumBranchingFactor(tree):
  sumbf = tree.getOutgoingEdges()
  for child in tree.children:
    sumbf += computeSumBranchingFactor(child)
  return sumbf

def computeMaxBranchingFactor(tree):
  if len(tree.children) > 0:
    return max(tree.getOutgoingEdges(),max([computeMaxBranchingFactor(child) for child in tree.children]))
  return tree.getOutgoingEdges()

def computeMaxDepth(tree):
  if len(tree.children) > 0:
    return max([computeMaxDepth(child) for child in tree.children])
  return tree.computeDepth()
    
def computeSumDepth(tree):
  sumd = tree.computeDepth()
  for child in tree.children:
    sumd += computeSumDepth(child)
  return sumd

def computeTree(edges):
  tnodes = {}
  for edge in getTreeEdges(edges):
    source = edge['source']
    target = edge['target']
    if source not in tnodes:
      tnodes[source] = Node(source)
    if source == target:
      continue
    if target not in tnodes:
      tnodes[target] = Node(target)
    tnodes[target].parent = tnodes[source]
    node = tnodes[source]
    if target not in [n.nid for n in node.children]:
      node.children.append(tnodes[target])
  return tnodes[min(tnodes.keys())] if len(tnodes) > 0 else None

def getTreeEdges(edges):
  tedges = {}
  for edge in edges:
    if edge['target'] >= edge['source']:
      tedges[json.dumps({'source':edge['source'],'target':edge['target']})] = True
  return [json.loads(e) for e in tedges]

# for histograms and aggregation
def calculatePerUserStats(data,edgeGroups,nodeGroups):
  # one row per user/dataset/task
  rowBase = {'dataset':None,'userid':None,'task':None,'totalNodes':None,
    'meanDepth':None,'maxBranchingFactor':None,'meanBranchingFactor':None,'meanAspectRatio':None,'maxDepth':None}
  rows = []

  for dataset in usersPerDataset:
    for task in tasks:
      for user in usersPerDataset[dataset]:
        row = dict(rowBase)
        row['dataset'] = dataset
        row['task'] = task
        row['userid'] = user
        edges = edgeGroups[dataset][task][user]
        total,meand,meanbf,leaves,meandn,meanbfn,leavesn,maxd,maxbf,maxdn,maxbfn = computeTreeStats(edges)
        row['totalNodes'] = total
        row['totalInteractions'] = len(edges)+1
        row['meanDepthNotNormalized'] = meand
        row['meanBranchingFactorNotNormalized'] = meanbf
        row['leavesNotNormalized'] = leaves
        row['leaves'] = leavesn
        row['meanDepth'] = meandn
        row['meanBranchingFactor'] = meanbfn
        row['maxBranchingFactor'] = maxbfn
        row['maxBranchingFactorNotNormalized'] = maxbf
        row['meanAspectRatio'] = meanbf / meand if meand > 0 else 0
        row['maxDepth'] = maxdn
        row['maxDepthNotNormalized'] = maxd
        rows.append(row)
  return rows

if __name__ == "__main__":
  data = json.load(open('master_file.json'))
  edgeGroups = getAllEdgeGroups(data)
  nodeGroups = getAllNodeGroups(data)
  perUser = calculatePerUserStats(data,edgeGroups,nodeGroups)
  writeResults('graph_analysis_per_tree.csv',perUser,delim='|')
  json.dump([{'dataset':row['dataset'],'task':row['task'],'userid':row['userid'],'branching':row['meanBranchingFactorNotNormalized'],'depth':row['meanDepthNotNormalized'],'aspectRatio':row['meanAspectRatio']} for row in perUser],open('graph_analysis_per_tree.json','w'))
