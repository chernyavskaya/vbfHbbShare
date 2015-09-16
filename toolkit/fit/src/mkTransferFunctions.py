#!/usr/bin/env python

import os,sys,re,json,datetime
from glob import glob
from array import array
from math import *
from optparse import OptionParser,OptionGroup
import warnings
warnings.filterwarnings( action='ignore', category=RuntimeWarning, message='.*class stack<RooAbsArg\*,deque<RooAbsArg\*> >' )

basepath=os.path.split(os.path.abspath(__file__))[0]+"/../../"
sys.path.append(basepath+'common/')

tempargv = sys.argv[:]
sys.argv = []
import ROOT
from ROOT import *
sys.argv = tempargv

from toolkit import *

colours = ["\033[m"] + ["\033[%d;%dm"%(x,y) for (x,y) in [(0,z) for z in range(31,37)]+[(1,z) for z in range(31,37)]]

####################################################################################################
def parser(mp=None):
	if not mp: mp = OptionParser()
#	mp.add_option('','',help=colours[5]+''+colours[0],default='',type='',dest='')
#
#	mg1 = OptionGroup(mp,'GroupTitle')
#	mg1.add_option('','',help=colours[5]+''+colours[0],default='',type='',dest='')
#	mp.add_option_group(mg1)
#
	mp.add_option('--workdir',help=colours[5]+'Case workdir.'+colours[0],default='case0',type='str')
	mp.add_option('--long',help=colours[5]+'Long filenames.'+colours[0],default=False,action='store_true')
#
	mg1 = OptionGroup(mp,'Selection setup')
	mg1.add_option('--SELCATs',help=colours[5]+'Selection/Category setup: "NOM;NOM;-0.6#0.0#0.7#0.84#1.0,VBF;PRK;-0.1#0.4#0.8#1.0,...".'+colours[0],default='NOM;NOM;-0.6#0.0#0.7#0.84#1.0,VBF;PRK;-0.1#0.4#0.8#1.0',type='str',action='callback',callback=SELsetup,dest='SC')
	mp.add_option_group(mg1)
#
	mg2 = OptionGroup(mp,'Transfer function setup')
	mg2.add_option('--TF',help=colours[5]+'Transfer function label: POL1,POL2 (NOM,VBF)'+colours[0],default=['POL1','POL2'],type='str',action='callback',callback=optsplit)
	mg2.add_option('--bounds',help=colours[5]+'Transfer function boundaries: 80,200 (min,max)'+colours[0],default=[80.,200.],type='str',action='callback',callback=optsplitfloat,dest='X')
	mg2.add_option('--binsize',help=colours[5]+'Transfer function bin size: 10,5 (NOM,VBF)'+colours[0],default=[10,5],type='str',action='callback',callback=optsplitint,dest='BINS')
	mp.add_option_group(mg2)
#
	return mp

####################################################################################################
def style():
	gROOT.SetBatch(1)
	gROOT.ProcessLineSync(".x %s/styleCMSTDR.C"%basepath)
	gROOT.ForceStyle()
	gStyle.SetPadTopMargin(0.06)
	gStyle.SetPadRightMargin(0.04)
	gROOT.ProcessLineSync("gErrorIgnoreLevel = kWarning;")

def hStyle(h,i,sumw2=True):
	if sumw2: h.Sumw2()
	h.SetMarkerStyle([20,20,23,21][i])
	h.SetMarkerSize(1.2)
	h.SetMarkerColor([kBlack,kBlue,kRed,kGreen+2][i])
	h.SetLineColor([kBlack,kBlue,kRed,kGreen+2][i])

def gpStyle(g,i):
	g.SetFillColor([kBlack,kBlue,kRed,kGreen+2][i])
	g.SetFillStyle(3004)

def gaStyle(g,i):
	g.SetFillColor(kGray)
	g.SetFillStyle(1001)

####################################################################################################
def write(obj):
	if (obj): obj.Write(obj.GetName(),TH1.kOverwrite)

def getUnc(cov,f,h,appBool,scale):
	n = cov.GetNrows()
	vx, vy, vex, vey = [None]*200,[None]*200,[None]*200,[None]*200
	dx = (h.GetBinLowEdge(h.GetNbinsX()+1)-h.GetBinLowEdge(1))/200.
	for i in range(200):
		vx[i] = h.GetBinLowEdge(i)+(i+1)*dx
		vy[i] = f.Eval(vx[i])
		vex[i] = 0
		s = 0
		if appBool:
			for j in range(n): 
				s += scale*scale*pow(vx[i],j)*pow(vx[i],j)*cov(j,j)
		else:
			for j in range(n):
				for k in range(n):
					s += pow(vx[i],j)*pow(vx[i],k)*cov(j,k)
		vey[i] = sqrt(s)
	g = TGraphErrors(200,array('f',vx),array('f',vy),array('f',vex),array('f',vey))
	return g

def scale(tf,cat):
	s = { "POL1":[1.0,0.5,0.62,0.67,1.0,1.2,1.7],
		  "POL2":[1.0,0.04,0.05,0.07,1.0,0.085,0.1],
		  "POL3":[1.0,0.01,0.01,0.01,1.0,0.015,0.022]
		}
	return s[tf][cat]



####################################################################################################
def main():
# Parse options
	mp = parser()
	opts,args = mp.parse_args()

# Style
	style()

# Create directories if needed
	makeDirs('%s'%opts.workdir)
	makeDirs('%s/plot'%opts.workdir)
	makeDirs('%s/root'%opts.workdir)
	longtag = "_B%d-%d_TF%s-%s"%(opts.X[0],opts.X[1],opts.TF[0],opts.TF[1])
	
# New files
	fout = TFile.Open("%s/root/TransferFunctions%s.root"%(opts.workdir,"" if not opts.long else longtag),"recreate")

# Setup
	SC = opts.SC if not type(opts.SC)==str else SELsetup(opts.SC)
	TF = opts.TF
	TFinfo = json.loads(filecontent("%s/vbfHbb_transfer_2014.json"%basepath))

# New histograms, graphs, containers
	CN1 = TCanvas("c2","c2",900,900)
	CN0 = TCanvas("c1","c1",900,750)
	hDat = {}
	hRat = {}
	fRat = {}
	gUnc = {}
	fitters = {}
	covs  = {}
	archive = []

## CMS info
	left,right,top,bottom = gStyle.GetPadLeftMargin(),gStyle.GetPadRightMargin(),gStyle.GetPadTopMargin(),gStyle.GetPadBottomMargin()
	pCMS1 = TPaveText(left,1.-top,0.4,1.,"NDC")
	pCMS1.SetTextFont(62)
	pCMS1.SetTextSize(top*0.75)
	pCMS1.SetTextAlign(12)
	pCMS1.SetFillStyle(-1)
	pCMS1.SetBorderSize(0)
	pCMS1.AddText("CMS")
	pCMS2 = TPaveText(0.5,1.-top,1.-right*0.5,1.,"NDC")
	pCMS2.SetTextFont(42)
	pCMS2.SetTextSize(top*0.75)
	pCMS2.SetTextAlign(32)
	pCMS2.SetFillStyle(-1)
	pCMS2.SetBorderSize(0)
	pCMS2.AddText("L = 19.8 fb^{-1} (8 TeV)")

# Selection loop
	for iS,S in enumerate(SC.selections):
## Baseline
		line = TF1("line","1.",opts.X[0],opts.X[1])
		line.SetLineColor(kBlack)
		line.SetLineWidth(1)
		line.SetLineStyle(2)
		line.SetMinimum(0.8)
		line.SetMaximum(1.2)
		line.GetXaxis().SetTitle("M_{bb} (GeV)")
		line.GetYaxis().SetTitle("Signal / Control")
		line.GetYaxis().SetTitleOffset(1.35)
## Load trees
		fin = TFile.Open("flat/Fit_data_sel%s.root"%S.tag,"read")
		T = fin.Get("Hbb/events")
## Make canvas
		CN = TCanvas("c_sel%s"%S.tag,"c_sel%s"%S.tag,900*(S.ncat-1),900)
		CN.Divide(S.ncat-1,1)
## Set legend
		L0 = TLegend(0.6,0.6,1.-gStyle.GetPadRightMargin()-gStyle.GetPadTopMargin()*0.3333,1.-gStyle.GetPadTopMargin()*1.3333)
		L0.SetHeader("%s selection"%S.label.replace('NOM','Set A').replace('PRK','Set B'))
		L0.SetFillColor(-1)
		L0.SetBorderSize(0)
		L0.SetTextFont(42)
		L0.SetTextSize(gStyle.GetPadTopMargin()*0.80)

## Category loop
		for C in range(S.ncat):
			Cp = C + sum([x for x in SC.ncats[0:iS]])
			N  = "sel%s_CAT%d"%(S.label,Cp)#.replace('NOM','Set A').replace('PRK','Set B')
### Get histogram
			hDat["hDat_"+N] = TH1F("hDat_"+N,"hDAT_"+N,int(opts.X[1]-opts.X[0])/opts.BINS[iS],opts.X[0],opts.X[1])
			h = hDat["hDat_"+N]
			hStyle(h,C)
### Fill
			CN1.cd()
			cut = "%s>%.2f && %s<=%.2f"%(SC.mva[iS],S.boundaries[C],SC.mva[iS],S.boundaries[C+1])
			T.Draw("mbbReg[%d]>>hDat_%s"%(iS+1,N),cut)
### Blind
			for iBin in range(1,h.GetNbinsX()+1):
				if h.GetBinLowEdge(iBin) >= 100 and h.GetBinLowEdge(iBin) < 150:
					h.SetBinContent(iBin,0)
					h.SetBinError(iBin,0)
### Normalize
			h.Scale(1./h.Integral())
### Get ratio histogram
			hRat["hRat_"+N] = h.Clone("hRat_"+N)
			r = hRat["hRat_"+N]
			hStyle(r,C,False)
			r.Divide(hDat["hDat_sel%s_CAT%s"%(S.label,sum([x for x in SC.ncats[0:iS]]))])#.replace('NOM','Set A').replace('PRK','Set B')
			r.SetMarkerSize(1.8)
			r.SetDirectory(0)
### Get fit function			
			fRat["fRat_"+N] = TF1("fRat_"+N,TFinfo[TF[iS]]['tf1'],opts.X[0],opts.X[1])
			f = fRat["fRat_"+N]
			f.SetLineColor([kBlack,kBlue,kRed,kGreen+2][C])

#### CAT 0 or 4 (control CATs)
			if not C==0:
##### Fit and store
				r.Fit(f,"RBQ")
				fitters["fitter_"+N] = TVirtualFitter.GetFitter()
				ff = fitters["fitter_"+N]
				covs["cov_"+N] = TMatrixDSym(ff.GetNumberTotalParameters(),ff.GetCovarianceMatrix())
				cov = covs["cov_"+N]
##### Uncertainty bands
  ### statistical (correlated) +
  ### approximate overcovering (uncorrelated)
  				gUnc["gUnc_"+N] = getUnc(cov,f,h,False,0.)
				gUnc["gUncApp_"+N] = getUnc(cov,f,h,True,TFinfo[TF[iS]]['scale'][Cp])
				g = gUnc["gUnc_"+N]
				ga = gUnc["gUncApp_"+N]
				gpStyle(g,C)
				gaStyle(ga,C)
#### Other CATs
			if C==0:
  ## Mbb plot
				CN0.cd()
				h.SetFillColor(kGray)
				h.GetXaxis().SetTitle("M_{bb} (GeV)")
				h.GetYaxis().SetTitle("PDF")
				h.GetYaxis().SetNdivisions(505)
				h.SetMaximum(0.3 if iS==0 else 0.2)
				h.Draw("hist")
				L0.AddEntry(h,"CAT%d"%Cp,"F")
  ## Mbb plot
			else:
				CN0.cd()
				h.Draw("same,PE")
				L0.AddEntry(h,"CAT%d"%Cp,"P")
  ## Ratio plot
  				CN.cd(C)
				line.Draw()
				ga.Draw("sameE3")
				line.Draw("same")
				g.Draw("sameE3")
				r.Draw("same")
				L1 = TLegend(gStyle.GetPadLeftMargin()+gStyle.GetPadTopMargin()*0.3333,gStyle.GetPadBottomMargin()+gStyle.GetPadTopMargin()*0.3333,0.6,0.4)
				L1.SetHeader("%s selection CAT%d/CAT%d"%(S.label.replace('NOM','Set A').replace('PRK','Set B'),Cp,sum(SC.ncats[0:iS])))
				L1.SetFillColor(-1)
				L1.SetBorderSize(0)
				L1.SetTextFont(42)
				L1.SetTextSize(gStyle.GetPadTopMargin()*0.7)
				L1.AddEntry(r,"data","P")
				L1.AddEntry(f,"fit","L")
				L1.AddEntry(ga,"uncert.","F")
				L1.AddEntry(g,"uncert. (stat)","F")
				L1.SetY2(L1.GetY1()+L1.GetNRows()*gStyle.GetPadTopMargin()*0.8)
				L1.Draw()
				archive += [L1]
				pCMS1.Draw()
				pCMS2.Draw()
				gPad.RedrawAxis()

### Save histograms and graphs
			fout.cd()
			if C==0: 
				for o in [h,r,f]: write(o)
			else:    
				for o in [h,r,f,g,ga,cov]: write(o)

#
#--- end of CAT loop
#

## Draw plots
		CN0.cd()
		pCMS1.Draw()
		pCMS2.Draw()
		L0.SetY1(L0.GetY2()-L0.GetNRows()*gStyle.GetPadTopMargin()*0.95)
		L0.Draw()
		n = "%s/plot/TransferFunctions"%opts.workdir
		makeDirs(n)
		CN0.SaveAs(n+"/MbbShape_sel%s.pdf"%S.tag)
		CN0.SaveAs(n+"/MbbShape_sel%s.png"%S.tag)
		CN.SaveAs(n+"/transfer_sel%s.pdf"%S.tag)
		CN.SaveAs(n+"/transfer_sel%s.png"%S.tag)

#
#--- end of SEL loop
#

	print "Done."
	fout.Close()

if __name__=='__main__':
	main()
