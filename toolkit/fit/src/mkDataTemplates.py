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
	mg2 = OptionGroup(mp,'Data template setup')
	mg2.add_option('--bounds',help=colours[5]+'Template boundaries: 80,200 (min,max)'+colours[0],default=[80.,200.],type='str',action='callback',callback=optsplitfloat,dest='X')
	mg2.add_option('--binwidth',help=colours[5]+'Template bin width: 0.1,0.1 (NOM,VBF)'+colours[0],default=[0.1,0.1],type='str',action='callback',callback=optsplitfloat,dest='dX')
	mg2.add_option('--lumi',help=colours[5]+'Luminosity: 19784.,18281. (NOM,VBF)'+colours[0],default=[19784.,18281.],type='str',action='callback',callback=optsplitfloat,dest='LUMI')
	mg2.add_option('--TF',help=colours[5]+'Transfer function label: POL1,POL2 (NOM,VBF)'+colours[0],default=['POL1','POL2'],type='str',action='callback',callback=optsplit)
	mg2.add_option('--BRN',help=colours[5]+'Bernstein order: 5,4 (NOM,VBF)'+colours[0],default=[5,4],type='str',action='callback',callback=optsplitint)
	mg2.add_option('--MASS',help=colours[5]+'Signal masspoint: 125'+colours[0],default=125,type='int')
	mg2.add_option('--forfit',help=colours[5]+'Freeze/free parameters for fit or not (for toys)'+colours[0],default=True,action='store_false')
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
def RooDraw(opts,can,C,x,rh,model,qPDF,zPDF,tPDF,archive):
	can.cd(C+1)
	gPad.SetBottomMargin(0.4)
	frametop = x.frame()
	framebot = x.frame()
# part 1
	rh.plotOn(frametop)
	model.plotOn(frametop,RooFit.LineWidth(2))
	rhres = frametop.residHist()
	p1 = RooArgSet(qPDF)
	p2 = RooArgSet(zPDF)
	p3 = RooArgSet(tPDF)
	model.plotOn(frametop,RooFit.Components(p1),RooFit.LineWidth(2),RooFit.LineColor(kBlack),RooFit.LineStyle(kDashed))
	model.plotOn(frametop,RooFit.Components(p2),RooFit.LineWidth(2),RooFit.LineColor(kBlue))
	model.plotOn(frametop,RooFit.Components(p3),RooFit.LineWidth(2),RooFit.LineColor(kGreen+1))
	frametop.GetXaxis().SetTitleSize(0)
	frametop.GetXaxis().SetLabelSize(0)
	frametop.Draw()
	gPad.Update()
# part 2
	pad = TPad("pad","pad",0.,0.,1.,1.)
	pad.SetTopMargin(0.6)
	pad.SetFillStyle(-1)
	pad.SetBorderSize(0)
	pad.Draw()
	pad.cd(0)
	framebot.addPlotable(rhres,"p")
	framebot.Draw()
	archive += [pad]
	archive += [rhres]

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
	longtag1 = "_B%d-%d"%(opts.X[0],opts.X[1])
	longtag2 = "_B%d-%d_TF%s-%s"%(opts.X[0],opts.X[1],opts.TF[0],opts.TF[1])
	longtag3 = "_B%d-%d_BRN%d-%d_TF%s-%s"%(opts.X[0],opts.X[1],opts.BRN[0],opts.BRN[1],opts.TF[0],opts.TF[1])
	
# Setup
	SC = opts.SC if not type(opts.SC)==str else SELsetup(opts.SC)
	fTF = json.loads(filecontent("%s/vbfHbb_transfer_2014.json"%basepath))
	LUMI = opts.LUMI
	NBINS = [int((opts.X[1]-opts.X[0])/x) for x in opts.dX] 
	MASS = opts.MASS

# Files
	fBKG = TFile.Open("%s/root/bkg_shapes_workspace%s.root"%(opts.workdir,"" if not opts.long else longtag1),"read")
	fSIG = TFile.Open("%s/root/sig_shapes_workspace%s.root"%(opts.workdir,"" if not opts.long else longtag1),"read")
	fTRF = TFile.Open("%s/root/TransferFunctions%s.root"%(opts.workdir,"" if not opts.long else longtag2),"read")
	wBKG = fBKG.Get("w")
	wSIG = fSIG.Get("w")
	w    = RooWorkspace("w","workspace")

# New histograms, graphs, containers
	archive = []
	C0  = TCanvas("c1","c1",900,750)
	rh  = {}
	rhb = {}
	h   = {}
	hb  = {}
	Y   = {}

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
	c0 = TCanvas("can","can",900,750)

# Selection loop
	for iS,S in enumerate(SC.selections):
## Load tree
		fin = TFile.Open("flat/Fit_data_sel%s.root"%S.tag,"read")
		T = fin.Get("Hbb/events")
## Containers
		brn          = {}
		brn_params   = {}
		qcd_pdf      = {}
		qcd_pdf_aux  = {}
		qcd_pdf_aux2 = {}
		model        = {}
		nQCD         = {}
		transfer     = {}
		zPDF,tPDF,qPDF,sPDF = {},{},{},{}
		yZ,yT,yQ     = {},{},{}
		can = TCanvas("canD_sel%s"%S.tag,"canD_sel%s"%S.tag,900,750)
		can.Divide(2,2)
## Category loop
		for C in range(S.ncat):
			Cp = C + sum([x for x in SC.ncats[0:iS]])
####################################################################################################
#### Start of RooFit part 
  ## BRN parameters
			for ib in range(opts.BRN[iS]+1):
				if C>0: continue
				nb = "b%d_sel%s_CAT%d"%(ib,S.tag,Cp)
				brn[nb] = RooRealVar(nb,nb,0.5,0,100.)
				nbp = "sel%s_CAT%d"%(S.tag,Cp)
				if not nbp in brn_params: brn_params[nbp] = RooArgList()
				brn_params[nbp].add(brn[nb])
  ## x
  			x = RooRealVar("mbbReg_CAT%d"%Cp,"mbbReg_CAT%d"%Cp,opts.X[0],opts.X[1])
			trans_p = {}
  ## Transfer functions			
			if not C==0:
				ftf = fTRF.Get("fRat_sel%s_CAT%d"%(S.label,Cp))
				npar = ftf.GetNpar()
  ### TF Parameters
				ntf = "trans_%s_CAT%d"%(opts.TF[iS],Cp)
				for ip in range(npar):
					if not ntf in trans_p: trans_p[ntf] = []
					trans_p[ntf] += [RooRealVar(ntf+"_p%d"%ip,ntf+"_p%d"%ip,ftf.GetParameter(ip),-0.1,0.1)]
					if 'Fix' in opts.TF[iS]:
						trans_p[ntf][-1].setError(fTF[opts.TF[iS]]['scale'][Cp]*ftf.GetParError(ip))
					else:
						trans_p[ntf][-1].setError(ftf.GetParError(ip))
					trans_p[ntf][-1].setConstant(kTRUE)
  ### TF Functions
				rl = RooArgList(x)
				for ti,t in enumerate(trans_p[ntf]): 
					if ti==0 and fTF[opts.TF[iS]]['f'][-3:]=="+ 1": continue
					rl.add(t)
				ntf = "transfer_%s_CAT%d"%(opts.TF[iS],Cp)
  				transfer[ntf] = RooGenericPdf(ntf,fTF[opts.TF[iS]]['f'],rl)

  ### QCD part
	  ### Containers
			N = "sel%s_CAT%d"%(S.tag,Cp)
			h[N]   = TH1F("hMbb_%s"%N,"hMbb_%s"%N,NBINS[iS],opts.X[0],opts.X[1])
			hb[N]  = TH1F("hMbb_blind_%s"%N,"hMbb_blind_%s"%N,NBINS[iS],opts.X[0],opts.X[1])
	  ### Define cut
			cut    = TCut("mva%s>%.2f && mva%s<=%.2f"%(S.tag,S.boundaries[C],S.tag,S.boundaries[C+1]))
			cutB   = TCut("mva%s>%.2f && mva%s<=%.2f && mbbReg[%d]>100 && mbbReg[%d]<150"%(S.tag,S.boundaries[C],S.tag,S.boundaries[C+1],iS+1,iS+1))
	  ### Draw
	  		c0.cd()
			T.Draw("mbbReg[%d]>>%s"%(iS+1,h[N].GetName()),cut)
			T.Draw("mbbReg[%d]>>%s"%(iS+1,hb[N].GetName()),cutB)
	  ### Yields
			Y[N]   = RooRealVar("yield_data_CAT%d"%Cp,"yield_data_CAT%d"%Cp,h[N].Integral())
	  ### Histograms
			rh[N]  = RooDataHist("data_hist_CAT%d"%Cp,"data_hist_CAT%d"%Cp,RooArgList(x),h[N])
			rhb[N] = RooDataHist("data_hist_blind_CAT%d"%Cp,"data_hist_blind_CAT%d"%Cp,RooArgList(x),hb[N])

  ### Model
	  ### Bernstein 0 or 4
			if C==0:
				for ib in range(opts.BRN[iS]+1):
					nb = "b%d_sel%s_CAT%d"%(ib,S.tag,Cp)
					brn[nb].setConstant(kFALSE)
				qcd_pdf_aux[N] = RooBernstein("qcd_model_%s_CAT%d"%(''.join(opts.TF),Cp),"qcd_model_%s_CAT%d"%(''.join(opts.TF),Cp),x,brn_params[N])
				qcd_pdf[N]     = qcd_pdf_aux[N]#RooAbsPdf(qcd_pdf_aux[N])
	  ### Bernstein * TFs other CATs
			else:
				for ib in range(opts.BRN[iS]+1):
					nb = "b%d_sel%s_CAT%d"%(ib,S.tag,sum(SC.ncats[0:iS]))
					brn[nb].setConstant(kTRUE)
				qcd_pdf_aux[N]  = RooBernstein("qcd_model_aux_%s_CAT%d"%(''.join(opts.TF),Cp),"qcd_model_aux_%s_CAT%d"%(''.join(opts.TF),Cp),x,brn_params["sel%s_CAT%d"%(S.tag,sum(SC.ncats[0:iS]))])
				qcd_pdf_aux2[N] = RooProdPdf("qcd_model_%s_CAT%d"%(''.join(opts.TF),Cp),"qcd_model_%s_CAT%d"%(''.join(opts.TF),Cp),RooArgList(transfer["transfer_%s_CAT%d"%(opts.TF[iS],Cp)],qcd_pdf_aux[N]))
				qcd_pdf[N]      = qcd_pdf_aux2[N] #RooAbsPdf(qcd_pdf_aux2[N])
				if opts.verbosity>0 and not opts.quiet: qcd_pdf[N].Print()

	  ### PDFs
	  		zPDF[N] = wBKG.pdf("Z_model_CAT%d"%Cp)
			tPDF[N] = wBKG.pdf("Top_model_CAT%d"%Cp)
			sPDF[N] = wSIG.pdf("signal_model_mH%d_sel%s_CAT%d"%(MASS,S.tag,Cp))

	  ### Yields
	  		yZ[N]    = wBKG.var("yield_ZJets_CAT%d"%Cp)
	  		yT[N]    = wBKG.var("yield_Top_CAT%d"%Cp)
			yQ[N]    = RooRealVar("yield_QCD_CAT%d"%Cp,"yield_QCD_CAT%d"%Cp,1000,0,1e+10)
			yZ[N].setConstant(kTRUE)
			yT[N].setConstant(kTRUE)
#			ySVBF = wSIG.var("yield_signalVBF_mass%d_CAT%d"%(MASS,Cp))
#			ySGF  = wSIG.var("yield_signalGF_mass%d_CAT%d"%(MASS,Cp))
#			yS    = RooRealVar("yield_signal_mass%d_CAT%d"%(MASS,Cp),"yield_signal_mass%d_CAT%d"%(MASS,Cp),ySVBF.getValV()+ySGF.getValV(),0.,400.)

  ### Combined model
	  		model[N] = RooAddPdf("bkg_model_%s_CAT%d"%(opts.TF[iS],Cp),"bkg_model_%s_CAT%d"%(opts.TF[iS],Cp),RooArgList(zPDF[N],tPDF[N],qcd_pdf[N]),RooArgList(yZ[N],yT[N],yQ[N]))
			
  ### Fit
	  		res   = model[N].fitTo(rh[N],RooFit.Save())
			if opts.verbosity>0 and not opts.quiet: res.Print()

  ### Draw
  			#RooDraw(opts,can,C,x,rh[N],model[N],qcd_pdf[N],zPDF[N],tPDF[N],archive)
			#can.cd(C+1)
			#pCMS1.Draw()
			#pCMS2.Draw()

  ### Reset constant settings
			for ib in range(opts.BRN[iS]+1):
				if C==0:
					nb = "b%d_sel%s_CAT%d"%(ib,S.tag,Cp)
					brn[nb].setConstant(kFALSE if opts.forfit else kTRUE)  ## false for final fit, true if fixed
			if not C==0:
				ntf = "trans_%s_CAT%d"%(opts.TF[iS],Cp)
				for t in trans_p[ntf]: t.setConstant(kFALSE if opts.forfit else (kFALSE if not 'Fix' in opts.TF[iS] else kTRUE)) ## false for final fit, true if fixed
			
  ### Saving
			for o in [rh[N],rhb[N],model[N],Y[N]]:
				getattr(w,'import')(o,RooFit.RenameConflictNodes("(1)"))
				if opts.verbosity>0 and not opts.quiet: o.Print()
###
###--- end of CAT loop
###
		if opts.verbosity>0 and not opts.quiet: w.Print()

#		makeDirs("%s/plot/dataTemplates/"%opts.workdir)
#		can.SaveAs("%s/plot/dataTemplates/%s.pdf"%(opts.workdir,can.GetName()))
#		can.SaveAs("%s/plot/dataTemplates/%s.png"%(opts.workdir,can.GetName()))
	
#
#--- end of SEL loop
#

	makeDirs("%s/root/"%opts.workdir)
	w.writeToFile("%s/root/data_shapes_workspace%s.root"%(opts.workdir,"" if not opts.long else longtag3))
	print "Done."

####################################################################################################
if __name__=='__main__':
	main()
