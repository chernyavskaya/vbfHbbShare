#!/usr/bin/env python

import sys
import os,re,json,datetime
basepath=os.path.split(os.path.abspath(__file__))[0]
sys.path.append(basepath)

from toolkit import *

class weightFactory:
	def __init__(self,samples,Lumi=None,KFWght=None):
		if not os.path.exists(samples)   : sys.exit('Input file doesn\'t exist : '+samples)
		self.samples   = json.loads(filecontent(samples))
		self.wOut      = '1.'
		self.Lumi      = Lumi if not Lumi==None else 19000.
		self.KFWght    = KFWght if not KFWght==None else 1.3

	def getFormula(self,weights,sample_tag):
		self.wOut='1.'
		for iWght in weights.split(','):
			if iWght == ''     : continue
			if iWght[0:2] == 'PU'   : self.addPUWght(sample_tag,iWght.split('#')[1])
			if iWght == 'XSEC' : self.addXSWght(sample_tag)
			if iWght == 'LUMI' : self.addLUWght(sample_tag)
			if iWght == 'KFAC' : self.addKFWght(sample_tag)
			if iWght == 'TRSF' : self.addTRWght(sample_tag)
			if iWght == 'TNOM' : self.addTNWght(sample_tag)
			if iWght == 'TVBF' : self.addTVWght(sample_tag)
			if iWght[0:3] == 'COR'   : self.add1DWght(sample_tag,iWght.split('#')[1:])
			if iWght[0:3] == 'MAP'   : self.add2DWght(sample_tag,iWght.split('#')[1:])
		return self.wOut

	def addPUWght(self,tag,element):
		for iFile in self.samples["files"]:
		   if self.samples["files"][iFile]["tag"] == tag and self.samples["files"][iFile]["xsec"] > 0 : self.wOut += '*puWt[%d]'%int(element)

	def addXSWght(self,tag):
		for iFile in self.samples["files"]:
		   if self.samples["files"][iFile]["tag"] == tag and self.samples["files"][iFile]["xsec"] > 0 : self.wOut += '*(1./'+self.samples["files"][iFile]["scale"]+')'

	def addLUWght(self,tag):
		for iFile in self.samples["files"]:
		   if self.samples["files"][iFile]["tag"] == tag and self.samples["files"][iFile]["xsec"] > 0 : self.wOut += '*%s'%(str(self.Lumi))

	def addKFWght(self,tag):
		for iFile in self.samples["files"]:
		   if self.samples["files"][iFile]["tag"] == tag and 'QCD' in self.samples["files"][iFile]["tag"] : self.wOut += '*%s'%(str(self.KFWght))

	def addTRWght(self,tag):
		for iFile in self.samples["files"]:
			if self.samples["files"][iFile]["tag"] == tag and self.samples["files"][iFile]["xsec"] > 0 : self.wOut += '*0.85'

	def addTNWght(self,tag):
		for iFile in self.samples["files"]:
			if self.samples["files"][iFile]["tag"] == tag and self.samples["files"][iFile]["xsec"] > 0 : self.wOut += '*trigWtNOM[1]'

	def addTVWght(self,tag):
		for iFile in self.samples["files"]:
			if self.samples["files"][iFile]["tag"] == tag and self.samples["files"][iFile]["xsec"] > 0 : self.wOut += '*trigWtVBF'

	def add1DWght(self,tag,variables):
		for iFile in self.samples["files"]:
		   if self.samples["files"][iFile]["tag"] == tag and self.samples["files"][iFile]["xsec"] > 0 :  self.wOut += '*oneDWght(%s)'%(variables[0])
	def add2DWght(self,tag,variables):
		for iFile in self.samples["files"]:
		   if self.samples["files"][iFile]["tag"] == tag and self.samples["files"][iFile]["xsec"] > 0 :  self.wOut += '*twoDWght(%s,%s)'%(variables[0],variables[1])

# Examples:
if __name__=='__main__':
  wf = weightFactory('vbfHbb_samples_XJ_2012Paper.json',18500)
  print 'Data   : ' , wf.getFormula('PU,XSEC,KFAC,LUMI','Data') 
  print 'QCD100 : ' , wf.getFormula('PU,XSEC,KFAC,LUMI','QCD100')
  print 'QCD100 : ' , wf.getFormula('PU,XSEC,KFAC,LUMI,MAP#ht#dEtaqq[3]','QCD100')
  print 'QCD250 : ' , wf.getFormula('PU,XSEC,KFAC,LUMI','QCD250')
  print 'QCD500 : ' , wf.getFormula('PU,XSEC,KFAC,LUMI','QCD500')
  print 'QCD1000: ' , wf.getFormula('PU,XSEC,KFAC,LUMI','QCD1000')
  print 'ZJets  : ' , wf.getFormula('PU,XSEC,KFAC,LUMI','ZJets')
  print 'TTJets : ' , wf.getFormula('PU,XSEC,KFAC,LUMI','TTJets')
