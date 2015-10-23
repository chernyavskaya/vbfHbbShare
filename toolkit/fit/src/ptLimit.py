#!/usr/bin/env python
import ROOT
from ROOT import *
from optparse import OptionParser
from copy import deepcopy as dc
import os,sys,re,operator
import numpy
from array import *

####################################################################################################
basepath=os.path.split(os.path.abspath(__file__))[0]+"/../../"
sys.path.append(basepath+"common/")

tempargv = sys.argv[:]
sys.argv = []
import ROOT
from ROOT import *
sys.argv = tempargv

from toolkit import *

colours = ["\033[m"] + ["\033[%d;%dm"%(x,y) for (x,y) in [(0,z) for z in range(31,37)]+[(1,z) for z in range(31,37)]]

####################################################################################################
def treeAccess(tree):
	tree.SetBranchStatus('*',0)

	_lm = numpy.array(1,'d')
	_mh = numpy.array(1,'d')

	tree.SetBranchStatus('limit',1)
	tree.SetBranchStatus('mh'   ,1)
	tree.SetBranchAddress('limit',_lm)
	tree.SetBranchAddress('mh',   _mh)

	return _lm, _mh

####################################################################################################
def localParser():
	lp = OptionParser()
	lp.add_option('--workdir',help='Case workdir.',default='case0',type='str')
	lp.add_option('--long',help='Long filenames.',default=False,action='store_true')
	lp.add_option('-b','--blind',help='Without observed.',default=False,action='store_true')
	lp.add_option('-t','--tag',help='Name tag.',default="")
	return lp

####################################################################################################
####################################################################################################
####################################################################################################
def main(opts,limnames):
	cwd = os.getcwd()
	makeDirs('%s/plot/limits'%(opts.workdir))
	path = os.path.split(limnames[0])[0]
	os.chdir(path)

# Set ROOT style
	gROOT.ProcessLine(".x /afs/cern.ch/work/s/salderwe/private/2014/vbfHbb/kostas/../common/styleCMSTDR.C")
	gROOT.ProcessLine('gROOT->ForceStyle();')
	gStyle.SetPadLeftMargin(0.12)
	gStyle.SetPadRightMargin(0.04)
	gStyle.SetPadTopMargin(0.06)
	gStyle.SetStripDecimals(0)
	gStyle.SetTitleOffset(0.8,"Y")
	gROOT.SetBatch(1)

####################
# Load input files
	limfiles = []
	limits = []
	masses = []
	print "Limit files:"
	for limname in [os.path.split(x)[1] for x in limnames]:
		if limname == '': sys.exit('No useable root file given. Exiting.')
		if not os.path.exists(limname): sys.exit('Specified root file doesn\'t exist. Exiting.')
		if os.path.getsize(limname)<1000: 
			print "\t - %s --> TOO SMALL, SKIPPED!"%limname
			continue
		MH = re.search(".*mH([0-9]{3}).*",limname).group(1)
		try:
			limfiles.append(TFile.Open(limname))
			limfile = limfiles[-1]
			print "\t - %s"%limname
			limits.append(limfile.Get('limit'))
			limit = limits[-1]
			masses.append(float(MH))
			m = masses[-1]
		except:
			pass
	
	masses = sorted(list(set(masses)))
	
####################
# Prepare containers
	bare = [0.]*len(masses)
	lists = {'aMass':dc(bare),'ExpLimit95D':dc(bare),'ExpLimit68D':dc(bare),'ExpLimitMed':dc(bare),'ExpLimit68U':dc(bare),'ExpLimit95U':dc(bare),'ObsLimit':dc(bare),'InjLimit':dc(bare),'aMassErr':dc(bare),'Exp68U':dc(bare),'Exp68D':dc(bare),'Exp95U':dc(bare),'Exp95D':dc(bare),'ExpSig':dc(bare),'ObsSig':dc(bare),'Mu':dc(bare),'Mu68D':dc(bare),'Mu68U':dc(bare)}
	positions = {0:'ExpLimit95D',1:'ExpLimit68D',2:'ExpLimitMed',3:'ExpLimit68U',4:'ExpLimit95U'}
	
# Loop over files and fill containers
	for ilimit, limit in enumerate(limits):
		print limfiles[ilimit]
		nentries = limit.GetEntries()
		limit.Print()
		lm, mh = treeAccess(limit)
		if 'Asymptotic' in limnames[ilimit]:
			for ientry in range(nentries):
				limit.GetEntry(ientry)
				mi = masses.index(mh)
				if ientry<5 and not 'Inj' in limnames[ilimit]:   lists[positions[ientry]][mi] = dc(lm)
				elif ientry >= 5 and 'Inj' in limnames[ilimit]:  lists['InjLimit'][mi] = dc(lm)
				elif ientry >= 5:                                lists['ObsLimit'][mi] = dc(lm)
				elif ientry<5: continue
				else: print "unknown case!", ientry, lm, mh
			if len(lists['ExpLimit68U'])>0:
				for k in ['Exp68U','Exp95U']:
					map(operator.sub, lists[k], lists['ExpLimitMed'])
				for k in ['Exp68D','Exp95D']:
					map(operator.sub, lists['ExpLimitMed'], lists[k])
			if not 'Inj' in limnames[ilimit]: 
				lists['aMass'][mi] = dc(mh)
				lists['aMassErr'][mi] = 0.
				print lists['aMass']
			if not any(['Inj' in x for x in limnames]):
				lists['InjLimit'][mi] = 0.
		elif 'Profile' in limnames[ilimit]:
			for ientry in range(nentries):
				limit.GetEntry(ientry)
				mi = masses.index(mh)
				if ientry == 0 and 'ExpSig' in limnames[ilimit]:    lists['ExpSig'][mi] = dc(lm)
				elif ientry == 0 and 'ObsSig' in limnames[ilimit]:  lists['ObsSig'][mi] = dc(lm)
				else: print "unknown case!", ientry, lm, mh
		elif 'Max' in limnames[ilimit]:
			for ientry in range(nentries):
				limit.GetEntry(ientry)
				mi = masses.index(mh)
				if ientry == 0:     lists['Mu'][mi] = dc(lm)
				elif ientry == 1:   lists['Mu68D'][mi] = dc(lm) - lists['Mu'][mi]
				elif ientry == 2:   lists['Mu68U'][mi] = dc(lm) - lists['Mu'][mi]
				else: print "unknown case!", ientry, lm, mh
		print lists
		print

	print
	arrays = dict([(k,array('d',v)) for (k,v) in lists.iteritems()])

####################
# Prepare plot
	c = TCanvas('c','c',900,750)
	c.cd()
	nMass = len(arrays['aMass'])
	limitplotband95 = TGraphAsymmErrors(nMass, arrays['aMass'], arrays['ExpLimitMed'],arrays['aMassErr'],arrays['aMassErr'],arrays['Exp95D'],arrays['Exp95U']) 
	limitplotband68 = TGraphAsymmErrors(nMass, arrays['aMass'], arrays['ExpLimitMed'],arrays['aMassErr'],arrays['aMassErr'],arrays['Exp68D'],arrays['Exp68U']) 
	limitplotexp    = TGraph           (nMass, arrays['aMass'], arrays['ExpLimitMed']) 
	limitplotobs    = TGraph           (nMass, arrays['aMass'], arrays['ObsLimit'])
	limitplotinj    = TGraph           (nMass, arrays['aMass'], arrays['InjLimit'])

####################
# Print output to screen
	print limitplotband95.Print()
	print limitplotband68.Print()
	print limitplotexp.Print()
	print limitplotobs.Print()
	print limitplotinj.Print()

# Print table resembling analysis note to screen
	print "#"*200
	print 
	print
	print "%6s | %8s | %8s | %8s | %8s | %8s | %20s |"%("mH","ExpLim","ObsLim","InjLim","ExpSig","ObsSig","Mu")
	print "-"*86
	for i,m in enumerate(range(115,140,5)):
		print "%6d |"%m,
		print "%8.2f |"%arrays['ExpLimitMed'][i],
		try: print "%8.2f |"%arrays['ObsLimit'][i],
		except: print "%8s |"%" ",
		try: print "%8.2f |"%arrays['InjLimit'][i],
		except: print "%8s |"%" ",
		try: print "%8.2f |"%arrays['ExpSig'][i],
		except: print "%8s |"%" ",
		try: print "%8.2f |"%arrays['ObsSig'][i],
		except: print "%8s |"%" ",
		try: 
			print "%8.2f"%arrays['Mu'][i],
			print "%+5.2f"%arrays['Mu68U'][i],
			print "%+5.2f |"%arrays['Mu68D'][i]
		except: print "%20s |"%" "
	print 
	print
	print "#"*200
	
####################
# Make plot
	maxplot = int(max(arrays['ExpLimit95U'])*1.2)
	if maxplot<10: maxplot=10

## Expected bands
	limitplotexp.GetYaxis().SetRangeUser(0.0,maxplot)
	limitplotband95.SetFillColor(kYellow)#90)
	limitplotband95.SetLineColor(kYellow)#90)
	limitplotband68.SetFillColor(kGreen)#211)
	limitplotband68.SetLineColor(kGreen)#211)

## Expected curve
	gPad.SetTicks(1)
	limitplotexp.GetXaxis().SetTickLength(0.03)
	limitplotexp.GetYaxis().SetTickLength(0.03)
	limitplotexp.GetYaxis().SetNdivisions(310)
	limitplotexp.SetLineStyle(1)
	limitplotexp.SetLineWidth(2)
	limitplotexp.SetLineColor(kBlack)#kBlue
	limitplotexp.GetXaxis().SetTitle("Higgs Boson Mass (GeV)")
	limitplotexp.GetYaxis().SetTitle("95% Asymptotic CL Limit on #sigma/#sigma_{SM}")
	limitplotexp.GetXaxis().SetLimits(114,136)

## Injected curve
	gStyle.SetLineStyleString(11,"24 24")
	limitplotinj.SetLineStyle(11)
	limitplotinj.SetLineWidth(2)
	limitplotinj.SetLineColor(kBlue)

## Observed curve
	limitplotobs.SetLineStyle(1)
	limitplotobs.SetLineWidth(2)
	limitplotobs.SetLineColor(kBlack)
	limitplotobs.SetMarkerStyle(20)
	limitplotobs.SetMarkerColor(kBlack)
	limitplotobs.SetMarkerSize(1.7)

## Line at 1.0
	line = TF1("line","1.0",114,136)
	line.SetLineColor(kGray+2)
	line.SetLineStyle(3)#2
	line.SetLineWidth(1)

## CMS text
	pave = TPaveText(0.16,0.7,0.25,0.91,"NDC")
	pave.SetTextFont(62)
	pave.SetTextSize(gStyle.GetPadTopMargin()*3./4.)
	pave.SetBorderSize(0)
	pave.SetFillStyle(-1)
	pave.SetTextAlign(12)
	pave.AddText("CMS")
	pave.Draw()
	gPad.Update()
	pave.SetY1NDC(pave.GetY2NDC()-len(pave.GetListOfLines())*gStyle.GetPadTopMargin())

## Lumi text
	pave2 = TPaveText(0.5,0.94,0.98,1.00,"NDC")
	pave2.SetTextFont(42)
	pave2.SetTextSize(0.04)
	pave2.SetBorderSize(0)
	pave2.SetFillStyle(-1)
	pave2.SetTextAlign(32)
	pave2.AddText("19.8 fb^{-1} (8 TeV)")#+ 18.2 

## Category text
	tag=""
	if 'CATveto' in limnames[ilimit]:
		if '0123' in limnames[ilimit]:
			tag="PRK"
		elif '456' in limnames[ilimit]:
			tag="NOM"
		else: 
			tag = re.search('.*CATveto([0-9]*)\..*',limnames[ilimit]).group(1)

	pave3 = TPaveText(0.72,0.7,0.92,0.90,"NDC")
	pave3.SetTextFont(62)
	pave3.SetTextSize(0.045)
	pave3.SetBorderSize(0)
	pave3.SetFillStyle(-1)
	pave3.SetTextAlign(32)
	if tag=="": pass 
	elif len(tag)<3: pave3.AddText("veto CAT%s"%tag)
	else: pave3.AddText(tag)
	pave3.Draw()
	gPad.Update()
	pave3.SetY1NDC(pave3.GetY2NDC()-len(pave3.GetListOfLines())*0.055)

## Legend
	leg = TLegend(0.38,0.92-0.04*4,0.62,0.90)
	leg.SetTextFont(42)
	leg.SetTextSize(0.042)
	leg.SetBorderSize(0)
	leg.SetFillStyle(-1)

	leg.AddEntry(limitplotobs,"Observed^{ }","LP")
	leg.AddEntry(limitplotexp,"Expected^{ }","L")
	if any(['Inj' in x for x in limnames]): leg.AddEntry(limitplotinj,"Exp. for SM m_{H} = 125 GeV","L")
	leg.AddEntry(limitplotband68,"Expected (68%)^{ }","F")
	leg.AddEntry(limitplotband95,"Expected (95%)^{ }","F")
	leg.SetY1(leg.GetY2()-(leg.GetNRows())*0.052)

## Draw all elements
	limitplotexp.Draw("axisl")
	limitplotband95.Draw("same3")
	limitplotband68.Draw("same3")
	limitplotexp.Draw("samel")
	if not opts.blind: limitplotobs.Draw("samelp")
	if any(['Inj' in x for x in limnames]): limitplotinj.Draw("samel")
	line.Draw("same")
	leg.Draw("same")
	pave.Draw("same")
	pave2.Draw("same")
	if 'CATveto' in limnames[ilimit]: pave3.Draw("same")

	os.chdir(cwd)

####################
# Save plots
	print os.getcwd()
	c.SaveAs('%s/plot/limits/limit%s.png'%(opts.workdir,opts.tag))
	c.SaveAs('%s/plot/limits/limit%s.pdf'%(opts.workdir,opts.tag))
	c.Close()

# Close files
	for limfile in limfiles:
		if limfile: limfile.Close()


####################################################################################################
####################################################################################################
####################################################################################################
if __name__=='__main__':
	lp = localParser()
	opts,args = lp.parse_args()

	main(opts,args)
