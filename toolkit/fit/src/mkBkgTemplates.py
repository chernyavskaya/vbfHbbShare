#!/usr/bin/env python

import os,sys,re,json,datetime
from glob import glob
from array import array
from optparse import OptionParser,OptionGroup
import warnings
warnings.filterwarnings( action='ignore', category=RuntimeWarning, message='.*class stack<RooAbsArg\*,deque<RooAbsArg\*> >' )

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
	mp.add_option('-v','--verbosity',help=colours[5]+'Verbosity.'+colours[0],default=0,action='count')
	mp.add_option('-q','--quiet',help=colours[5]+'Quiet.'+colours[0],default=True,action='store_false')
#
	mg1 = OptionGroup(mp,'Selection setup')
	mg1.add_option('--SELCATs',help=colours[5]+'Selection/Category setup: "NOM;NOM;-0.6#0.0#0.7#0.84#1.0,VBF;PRK;-0.1#0.4#0.8#1.0,...".'+colours[0],default='NOM;NOM;-0.6#0.0#0.7#0.84#1.0,VBF;PRK;-0.1#0.4#0.8#1.0',type='str',action='callback',callback=SELsetup,dest='SC')
	mp.add_option_group(mg1)
#
	mg2 = OptionGroup(mp,'Bkg template setup')
	mg2.add_option('--bounds',help=colours[5]+'Template boundaries: 80,200 (min,max)'+colours[0],default=[80.,200.],type='str',action='callback',callback=optsplitfloat,dest='X')
	mg2.add_option('--binsize',help=colours[5]+'Template NBINS: 20,20 (NOM,VBF)'+colours[0],default=[20,20],type='str',action='callback',callback=optsplitint,dest='NBINS')
	mg2.add_option('--lumi',help=colours[5]+'Luminosity: 19784.,18281. (NOM,VBF)'+colours[0],default=[19784.,18281.],type='str',action='callback',callback=optsplitfloat,dest='LUMI')
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
	RooMsgService.instance().setSilentMode(kTRUE)
	for i in range(2): RooMsgService.instance().setStreamStatus(i,kFALSE)

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
def RooDraw(can,x,h,model,S,C,Cp,text,archive):
	can.cd(C+1)
	frame = x.frame()
	h.plotOn(frame)
	model.plotOn(frame,RooFit.LineWidth(2))
	frame.GetXaxis().SetTitle("M_{bb} (GeV)")
	frame.Draw()
	right,top = gStyle.GetPadRightMargin(),gStyle.GetPadTopMargin()
	pave = TPaveText(0.72,0.75,1.-right-top*0.3333,1.-top*1.666,"NDC")
	pave.SetTextAlign(11)
	pave.SetFillStyle(-1)
	pave.SetBorderSize(0)
	pave.SetTextFont(62)
	pave.SetTextSize(top*0.80)
	pave.AddText("%s selection"%(S.label.replace('NOM','Set A') if 'NOM' in S.label else S.label.replace('PRK','Set B')))
	pave.AddText("CAT%d"%Cp)
	pave.AddText(text)
	pave.Draw()
	gPad.Update()
	pave.SetY1NDC(pave.GetY2NDC()-top*0.92*pave.GetListOfLines().GetSize())
	pave.Draw()
	archive += [pave]

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
	longtag = "_B%d-%d"%(opts.X[0],opts.X[1])

# Setup
	SC = opts.SC if not type(opts.SC)==str else SELsetup(opts.SC)
	fnames = json.loads(filecontent("%s/vbfHbb_samples_2014_bkg.json"%basepath))
	finfo  = json.loads(filecontent("%s/vbfHbb_info_2013.json"%basepath))

# New histograms, graphs, containers
	w = RooWorkspace("w","workspace")
	CN0 = TCanvas("c1","c1",900,750)
	kJES = [None]*(SC.nsel)
	kJER = [None]*(SC.nsel)
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
 ## Container ## Containers
 		hMbb = {}
 		hMbbYield = {}
 		rh_Z = {}
 		rh_T = {}
 ## File reading
		inf = [None]*(len(fnames['files'])/2)
		fi = 0
		for f in fnames['files'].itervalues():
			if 'sel%s'%S.tag in f['fname']: 
				inf[fi] = TFile.Open("flat/"+f['fname'],'read')
				fi += 1
 ## Canvas definition
		canZ = TCanvas("canZ_sel%s"%S.tag,"canZ_sel%s"%S.label,900,600)
		canT = TCanvas("canT_sel%s"%S.tag,"canT_sel%s"%S.label,900,600)
		canZ.Divide(2,2)
		canT.Divide(2,2)
		can = TCanvas("c","c",900,600)
 ## Nuissance parameters
 		nVar = "CMS_vbfbb_scale_mbb_sel%s"%S.tag
		kJES[iS] = RooRealVar(nVar,nVar,1.0)
 		nVar = "CMS_vbfbb_res_mbb_sel%s"%S.tag
		kJER[iS] = RooRealVar(nVar,nVar,1.0)
		kJES[iS].setConstant(kTRUE)
		kJER[iS].setConstant(kTRUE)
		
## Category loop
		for C in range(S.ncat):
			Cp = C + sum([x for x in SC.ncats[0:iS]])
			if C>2: NBINS=12
			else: NBINS=opts.NBINS[iS]
### File loop
			for fi,F in enumerate(inf):
				ni = F.GetName()
				niShort = os.path.split(F.GetName())[1]
				if 'ZJets' in ni: group = 'ZJets'
				elif 'WJets' in ni: group = 'WJets'
				else: group = finfo['groups'][fnames['files'][niShort]['tag']]
				N  = "MbbShape_sel%s_CAT%d_%d_%s"%(S.label,Cp,fi,group)
				NYield  = "MbbYield_sel%s_CAT%d_%d_%s"%(S.label,Cp,fi,group)
  #### Load tree
				T = F.Get("Hbb/events")
  #### Define cut
				cut = TCut("puWt[0]*trigWt%s%s*(mva%s>%.2f && mva%s<=%.2f)"%(S.tag,("" if S.tag=="VBF" else "[1]"),S.tag,S.boundaries[C],S.tag,S.boundaries[C+1]))
  #### Draw mass
  				hMbb[N] = TH1F(N,N,NBINS,opts.X[0],opts.X[1])
				h = hMbb[N]
				h.Sumw2()
				can.cd()
				T.Draw("mbbReg[%d]>>%s"%(iS+1,h.GetName()),cut)
				hMbbYield[NYield] = h.Clone(NYield)
				hY = hMbbYield[NYield]
				xsec,npass = float(fnames['files'][niShort]['xsec']),float(fnames['files'][niShort]['npassed'])
				hY.Scale(opts.LUMI[iS]*xsec/npass)

#
#--- end of FILE loop
#
  ### Group histograms
			hW,hZ,hST,hTT,hT = None,None,None,None,None
			for hi,h in enumerate(hMbb.itervalues()):
				nh = h.GetName()
				if not "CAT%d"%Cp in nh: continue
				if 'ZJets' in nh: hZ = h.Clone("Z")
				elif 'WJets' in nh: hW = h.Clone("W")
				elif 'TTJets' in nh: hTT = h.Clone("TT")
				elif 'singleT' in nh: 
					if not hST: hST = h.Clone("ST")
					else: hST.Add(h)
			hT = hTT.Clone("Top")
			hT.Add(hST)
 ### Group yields
			hWY,hZY,hSTY,hTTY,hTY = None,None,None,None,None
			for hi,hY in enumerate(hMbbYield.itervalues()):
				nh = hY.GetName()
				if not "CAT%d"%Cp in nh: continue
				if 'ZJets' in nh: hZY = hY.Clone("ZYield")
				elif 'WJets' in nh: hWY = hY.Clone("WYield")
				elif 'TTJets' in nh: hTTY = hY.Clone("TTYield")
				elif 'singleT' in nh: 
					if not hSTY: hSTY = hY.Clone("STYield")
					else: hSTY.Add(hY)
			hTY = hTTY.Clone("TopYield")
			hTY.Add(hSTY)
			hZY.Add(hWY)
			for o in hW,hZ,hST,hTT,hT,hWY,hZY,hSTY,hTTY,hTY: archive += [o]

####################################################################################################
#### Start of RooFit part 
  ## Yields
			x   = RooRealVar("mbbReg_CAT%d"%Cp,"mbbReg_CAT%d"%Cp,opts.X[0],opts.X[1])
			YZ  = RooRealVar("yield_ZJets_CAT%d"%Cp,"yield_ZJets_CAT%d"%Cp,hZY.Integral())
			YW  = RooRealVar("yield_WJets_CAT%d"%Cp,"yield_WJets_CAT%d"%Cp,hWY.Integral())
			YTT = RooRealVar("yield_TTJets_CAT%d"%Cp,"yield_TTJets_CAT%d"%Cp,hTTY.Integral())
			YST = RooRealVar("yield_singleT_CAT%d"%Cp,"yield_singleT_CAT%d"%Cp,hSTY.Integral())
			YT  = RooRealVar("yield_Top_CAT%d"%Cp,"yield_Top_CAT%d"%Cp,hTY.Integral())
  ## Z Fit
			rh_Z["CAT%d"%Cp] = RooDataHist("roohist_Z_CAT%d"%Cp,"roothist_Z_CAT%d"%Cp,RooArgList(x),hZ)
			mZ              = RooRealVar("Z_mean_CAT%d"%Cp,"Z_mean_CAT%d"%Cp,95,80,110)
			sZ              = RooRealVar("Z_sigma_CAT%d"%Cp,"Z_sigma_CAT%d"%Cp,12,9,20)
			mZShift         = RooFormulaVar("Z_mean_shifted_CAT%d"%Cp,"@0*@1",RooArgList(mZ,kJES[iS]))
			sZShift         = RooFormulaVar("Z_sigma_shifted_CAT%d"%Cp,"@0*@1",RooArgList(sZ,kJER[iS]))
			aZ              = RooRealVar("Z_a_CAT%d"%Cp,"Z_a_CAT%d"%Cp,-1,-10,10)
			nZ              = RooRealVar("Z_n_CAT%d"%Cp,"Z_n_CAT%d"%Cp,1,0,10)
			Zb0,Zb1,Zb2     = [RooRealVar("Z_b%d_CAT%d"%(i,Cp),"Z_b%d_CAT%d"%(i,Cp),0.5,0,1) for i in range(3)]
  ### Bkg part: Bernstein
  			Zbkg            = RooBernstein("Z_bkg_CAT%d"%Cp,"Z_bkg_CAT%d"%Cp,x,RooArgList(Zb0,Zb1,Zb2))
  ### Sig part: Crystal Ball
  			Zcore           = RooCBShape("Zcore_CAT%d"%Cp,"Zcore_CAT%d"%Cp,x,mZShift,sZShift,aZ,nZ)
			fZsig           = RooRealVar("fZsig_CAT%d"%Cp,"fZsig_CAT%d"%Cp,0.7,0,1)
  ### Combined model
  			modelZ          = RooAddPdf("Z_model_CAT%d"%Cp,"Z_model_CAT%d"%Cp,RooArgList(Zcore,Zbkg),RooArgList(fZsig))
  ### Fit Z
  			resZ            = modelZ.fitTo(rh_Z["CAT%d"%Cp],RooFit.Save())
			resZ.Print()
  ### Draw Z
  			RooDraw(canZ,x,rh_Z["CAT%d"%Cp],modelZ,S,C,Cp,"Z template",archive)
			canZ.cd(C+1)
			pCMS1.Draw()
			pCMS2.Draw()

  ## T Fit
  			rh_T["CAT%d"%Cp] = RooDataHist("roohist_Top_CAT%d"%Cp,"roohist_Top_CAT%d"%Cp,RooArgList(x),hTY if C<3 else hSTY)
			mT              = RooRealVar("Top_mean_CAT%d"%Cp,"Top_mean_CAT%d"%Cp,130,0,200)
			sT              = RooRealVar("Top_sigma_CAT%d"%Cp,"Top_sigma_CAT%d"%Cp,50,0,200)
			mTShift         = RooFormulaVar("Top_mean_shifted_CAT%d"%Cp,"@0*@1",RooArgList(mT,kJES[iS]))
			sTShift         = RooFormulaVar("Top_sigma_shifted_CAT%d"%Cp,"@0*@1",RooArgList(sT,kJER[iS]))
  ### Full model: Gaussian
			modelT          = RooGaussian("Top_model_CAT%d"%Cp,"Top_model_CAT%d"%Cp,x,mTShift,sTShift)
  ### Fit T
			resT            = modelT.fitTo(rh_T["CAT%d"%Cp],RooFit.Save(),RooFit.SumW2Error(kTRUE))#,"q")
  ### Draw T
  			RooDraw(canT,x,rh_T["CAT%d"%Cp],modelT,S,C,Cp,"Top template",archive)
			canT.cd(C+1)
			pCMS1.Draw()
			pCMS2.Draw()

#### Set Constants
			for o in [mZ,sZ,aZ,nZ,Zb0,Zb1,Zb2,fZsig,mT,sT]: 
				o.setConstant(kTRUE)
#### Import objects
			for o in [modelZ,modelT,YZ,YT,YTT,YST]:
				getattr(w,'import')(o,ROOT.RooCmdArg())
				if opts.verbosity>0 and not opts.quiet: o.Print()

#
#--- end of CAT loop
#

		makeDirs("%s/plot/bkgTemplates/"%opts.workdir)
		canZ.SaveAs("%s/plot/bkgTemplates/%s.pdf"%(opts.workdir,canZ.GetName()))
		canZ.SaveAs("%s/plot/bkgTemplates/%s.png"%(opts.workdir,canZ.GetName()))
		canT.SaveAs("%s/plot/bkgTemplates/%s.pdf"%(opts.workdir,canT.GetName()))
		canT.SaveAs("%s/plot/bkgTemplates/%s.png"%(opts.workdir,canT.GetName()))
	
		canZ.Close()
		canT.Close()
		can.Close()
#
#--- end of SEL loop
#

	makeDirs("%s/root/"%opts.workdir)
	w.writeToFile("%s/root/bkg_shapes_workspace%s.root"%(opts.workdir,"" if not opts.long else longtag))

####################################################################################################
if __name__=='__main__':
	main()
