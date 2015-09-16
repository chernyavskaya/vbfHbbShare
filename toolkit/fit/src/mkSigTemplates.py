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
	mg2 = OptionGroup(mp,'Sig template setup')
	mg2.add_option('--bounds',help=colours[5]+'Template boundaries: 80,200 (min,max)'+colours[0],default=[80.,200.],type='str',action='callback',callback=optsplitfloat,dest='X')
	#mg2.add_option('--binsize',help=colours[5]+'Template NBINS (XMAX-XMIN)/dX: 1200,1200 (NOM,VBF)'+colours[0],default=[1200,1200],type='str',action='callback',callback=optsplitint,dest='NBINS')
	mg2.add_option('--binwidth',help=colours[5]+'Binwidth: 0.1,0.1 (NOM,VBF)'+colours[0],default=[0.1,0.1],type='str',action='callback',callback=optsplitfloat,dest='dX')
	mg2.add_option('--lumi',help=colours[5]+'Luminosity: 19784.,18281. (NOM,VBF)'+colours[0],default=[19784.,18281.],type='str',action='callback',callback=optsplitfloat,dest='LUMI')
	mg2.add_option('--mass',help=colours[5]+'Mass: 115,120,125,...'+colours[0],default=[115,120,125,130,135],type='str',action='callback',callback=optsplitint,dest='MASS')
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
def RooDraw(opts,can,x,h,hVBF,hGF,hTOT,yVBF,yGF,model,bkg,fsig,width,mass,m,s,iS,S,C,Cp,archive):
	can.cd(C+1)
	
	hGF.Rebin(25)
	hVBF.Rebin(25)
	hTOT.Rebin(25)
	hScale = RooDataHist("tmp","tmp",RooArgList(x),hTOT)

	frame = x.frame()
	hScale.plotOn(frame)
	model.plotOn(frame)#,RooFit.LineWidth(2))
	frame.GetXaxis().SetNdivisions(505)
	frame.GetXaxis().SetTitle("M_{bb} (GeV)")
	frame.GetYaxis().SetTitle("Events / (%.1f)"%hTOT.GetBinWidth(1))
	frame.GetYaxis().SetRangeUser(0.,hTOT.GetBinContent(hTOT.GetMaximumBin())*1.1);
	bkgplot = RooArgSet(bkg)
	model.plotOn(frame,RooFit.Components(bkgplot),RooFit.LineColor(kBlue),RooFit.LineWidth(2),RooFit.LineStyle(kDashed))
	frame.Draw()
	archive += [bkgplot]

	hGF.SetFillColor(kGreen-8)
	hVBF.SetFillColor(kRed-10)
	hS = THStack("hs","hs")
	hS.Add(hGF)
	hS.Add(hVBF)
	hS.Draw("same,hist")
	frame.Draw("same")
	gPad.RedrawAxis()
	archive += [hS]

	ftmp = model.asTF(RooArgList(x),RooArgList(fsig),RooArgSet(x))
	y0,x0       = ftmp.GetMaximum(),ftmp.GetMaximumX()
	x1,x2       = ftmp.GetX(y0/2.,opts.X[0],x0),ftmp.GetX(y0/2.,x0,opts.X[1])
	fwhm        = x2-x1
	width.setVal(fwhm)
	y1          = opts.dX[iS]*25*0.5*y0*(yVBF.getVal()+yGF.getVal())/ftmp.Integral(opts.X[0],opts.X[1])
	line        = TLine(x1,y1,x2,y1)
	line.SetLineColor(kMagenta+3)
	line.SetLineStyle(7)
	line.SetLineWidth(2)
	line.Draw("same")
	archive += [line]

	right,top   = gStyle.GetPadRightMargin(),gStyle.GetPadTopMargin()
	left,bottom = gStyle.GetPadLeftMargin(),gStyle.GetPadBottomMargin()
	
	leg = TLegend(0.65,0.35,1.-right-top*0.3333,0.45)
	leg.AddEntry(hVBF,"VBF","F")
	leg.AddEntry(hGF,"GF","F")
	leg.SetFillStyle(-1)
	leg.SetBorderSize(0)
	leg.SetTextFont(42)
	leg.SetTextSize(top*0.75)
	leg.SetY1(leg.GetY2()-top*leg.GetNRows()*0.87)
	leg.Draw()
	archive += [leg]

	pave = TPaveText(0.65,0.55,1.-right-top*0.3333,1.-top*1.666,"NDC")
	pave.SetTextAlign(11)
	pave.SetFillStyle(-1)
	pave.SetBorderSize(0)
	pave.SetTextFont(42)
	pave.SetTextSize(top*0.7)
	pave.SetTextColor(kBlue+1)
	pave.AddText("M_{H} = %d GeV"%mass)
	pave.AddText("%s selection"%S.label.replace('NOM','Set A').replace('PRK','Set B'))
	pave.AddText("CAT%d"%Cp)
	pave.AddText("m = %.1f #pm %.1f"%(m.getVal(),m.getError()))
	pave.AddText("#sigma = %.1f #pm %.1f"%(s.getVal(),s.getError()))
	pave.AddText("FWHM = %.2f"%fwhm)
	pave.Draw()
	gPad.Update()
	pave.SetY1NDC(pave.GetY2NDC()-top*0.9*pave.GetListOfLines().GetSize())
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
	fnames = json.loads(filecontent("%s/vbfHbb_samples_2014_sig.json"%basepath))
	finfo  = json.loads(filecontent("%s/vbfHbb_info_2013.json"%basepath))

# New histograms, graphs, containers
	w = RooWorkspace("w","workspace")
	MASS = opts.MASS
	LUMI = opts.LUMI
	NBINS = [int((opts.X[1]-opts.X[0])/x) for x in opts.dX] 
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
 ## Nuissance parameters
 		nVar = "CMS_vbfbb_scale_mbb_sel%s"%S.tag
		kJES[iS] = RooRealVar(nVar,nVar,1.0)
 		nVar = "CMS_vbfbb_res_mbb_sel%s"%S.tag
		kJER[iS] = RooRealVar(nVar,nVar,1.0)
		kJES[iS].setConstant(kTRUE)
		kJER[iS].setConstant(kTRUE)
#
#--- end of SEL loop
#

	can = TCanvas("c","c",900,750)

 ## File reading
	inf = {} 
	for f in [x['fname'] for x in fnames['files'].itervalues()]:
		mass = int(re.search('.*(1[0-9]{2}).*',f).group(1))
		styp = re.search('.*sel(NOM|VBF).*',f).group(1)
		ftyp = re.search('.*(VBF|GF)Pow.*',f).group(1)
		if not mass in inf: inf[mass] = {}
		if not styp in inf[mass]: inf[mass][styp] = {}
		inf[mass][styp][ftyp] = TFile.Open("flat/"+f,'read')
#	for k,v in inf.iteritems():
#		for k1,v1 in v.iteritems():
#			for k2,v2 in v1.iteritems():
#				print k,k1,k2,v2

# Mass loop
	for mass in MASS:
## Selection loop
		for iS,S in enumerate(SC.selections):
			fVBF = inf[mass][S.tag]['VBF']
			fGF  = inf[mass][S.tag]['GF']
			sVBF = float(fnames['files'][os.path.split(fVBF.GetName())[1]]['scale'])
			sGF  = float(fnames['files'][os.path.split(fGF.GetName())[1]]['scale'])
			tVBF = fVBF.Get("Hbb/events")
			tGF  = fGF.Get("Hbb/events")
 ### Container ## Containers
 			rh   = {}
 			rhs  = {}
 			hVBF = {}
			hGF  = {}
			hTOT = {}
			yVBF = {}
			yGF  = {}
 ### Canvas definition
			canM = TCanvas("sig_template_sel%s_mH%d"%(S.tag,mass),"cs%sm%d"%(S.tag,mass),900,750)
			canM.Divide(2,2)
		
### Category loop
			for C in range(S.ncat):
				Cp = C + sum([x for x in SC.ncats[0:iS]])
  #### Define cut
				cut = TCut("puWt[0]*trigWt%s%s*(mva%s>%.2f && mva%s<=%.2f)"%(S.tag,("" if S.tag=="VBF" else "[1]"),S.tag,S.boundaries[C],S.tag,S.boundaries[C+1]))
  #### Draw mass
  				N = "mH%d_sel%s_CAT%d"%(mass,S.tag,Cp)
  				hVBF[N] = TH1F("MbbShape_VBF_mH%d_sel%s_CAT%d"%(mass,S.tag,Cp),"MbbShape_VBF_mH%d_sel%s_CAT%d"%(mass,S.tag,Cp),NBINS[iS],opts.X[0],opts.X[1])
  				hGF[N]  = TH1F("MbbShape_GF_mH%d_sel%s_CAT%d"%(mass,S.tag,Cp),"MbbShape_GF_mH%d_sel%s_CAT%d"%(mass,S.tag,Cp),NBINS[iS],opts.X[0],opts.X[1])
				hVBF[N].Sumw2()
				hGF[N].Sumw2()
				can.cd()
				tVBF.Draw("mbbReg[%d]>>%s"%(iS+1,hVBF[N].GetName()),cut)
				tGF.Draw("mbbReg[%d]>>%s"%(iS+1,hGF[N].GetName()),cut)

####################################################################################################
#### Start of RooFit part 
  ## Yields
				x   = RooRealVar("mbbReg_CAT%d"%Cp,"mbbReg_CAT%d"%Cp,opts.X[0],opts.X[1])
  ## Fit components
				rh[N] = RooDataHist("roohist_fit_%s"%N,"roohist_fit_%s"%N,RooArgList(x),hVBF[N])
				hVBF[N].Scale(LUMI[iS]/sVBF)
				hGF[N].Scale(LUMI[iS]/sGF)
				hTOT[N] = hVBF[N].Clone("mass_Total_%s"%N)
				hTOT[N].Add(hGF[N])
				rhs[N] = RooDataHist("roohist_scaled_%s"%N,"roohist_scaled_%s"%N,RooArgList(x),hTOT[N])

				yVBF[N] = RooRealVar("yield_signalVBF_mass%d_CAT%d"%(mass,Cp),"yield_signalVBF_mass%d_CAT%d"%(mass,Cp),hVBF[N].Integral())
				yGF[N] = RooRealVar("yield_signalGF_mass%d_CAT%d"%(mass,Cp),"yield_signalGF_mass%d_CAT%d"%(mass,Cp),hGF[N].Integral())
				Nb = "m%d_CAT%d"%(mass,Cp)
				m             = RooRealVar("mean_%s"%Nb,"mean_%s"%Nb,mass,mass-5,mass+5)
				s             = RooRealVar("sigma_%s"%Nb,"sigma_%s"%Nb,12,3,30)
				width         = RooRealVar("fwhm_%s"%Nb,"fwhm_%s"%Nb,25,0,100)
				mShift        = RooFormulaVar("mean_shifted_%s"%Nb,"@0*@1",RooArgList(m,kJES[iS]))
				sShift        = RooFormulaVar("sigma_shifted_%s"%Nb,"@0*@1",RooArgList(s,kJER[iS]))
				a             = RooRealVar("alpha_%s"%Nb,"alpha_%s"%Nb,1,-10,10)
				n             = RooRealVar("exp_%s"%Nb,"exp_%s"%Nb,1,0,100)
				b0,b1,b2,b3   = [RooRealVar("b%d_%s"%(i,Nb),"b%d_%s"%(i,Nb),0.5,0.,1.) for i in range(4)]
  ### Bkg part: Bernstein     
				bkg           = RooBernstein("signal_bkg_%s"%Nb,"signal_bkg_%s"%Nb,x,RooArgList(b0,b1,b2))
  ### Sig part: Crystal Ball   
				fsig          = RooRealVar("fsig_%s"%Nb,"fsig_%s"%Nb,0.7,0.,1.)
				sig           = RooCBShape("signal_gauss_%s"%Nb,"signal_gauss_%s"%Nb,x,mShift,sShift,a,n)
  ### Combined model
				model         = RooAddPdf("signal_model_%s"%Nb,"signal_model_%s"%Nb,RooArgList(sig,bkg),RooArgList(fsig))
  ### Fit 
				res           = model.fitTo(rh[N],RooFit.SumW2Error(kFALSE))#"q"

  ### Draw 
	  			RooDraw(opts,canM,x,rhs[N],hVBF[N],hGF[N],hTOT[N],yVBF[N],yGF[N],model,bkg,fsig,width,mass,m,s,iS,S,C,Cp,archive)
				canM.cd(C+1)
				pCMS1.Draw()
				pCMS2.Draw()
				
  #### Set Constants
				for o in [b0,b1,b2,b3,m,s,a,n,fsig]: o.setConstant(kTRUE)
#### Import objects
				for o in [model,rh[N],width,yVBF[N],yGF[N]]:
					getattr(w,'import')(o,ROOT.RooCmdArg())
					if opts.verbosity>0 and not opts.quiet: o.Print()

#
#--- end of CAT loop
#

			makeDirs("%s/plot/sigTemplates/"%opts.workdir)
			canM.SaveAs("%s/plot/sigTemplates/%s.pdf"%(opts.workdir,canM.GetName()))
			canM.SaveAs("%s/plot/sigTemplates/%s.png"%(opts.workdir,canM.GetName()))
	
#
#--- end of SEL loop
#

	makeDirs("%s/root/"%opts.workdir)
	w.writeToFile("%s/root/sig_shapes_workspace%s.root"%(opts.workdir,"" if not opts.long else longtag))

####################################################################################################
if __name__=='__main__':
	main()
