#!/usr/bin/env python

import os,re,sys
import ROOT
from ROOT import *
from optparse import OptionParser

####################################################################################################
def PAVE(x1,y1,x2,y2,text,color):
	p = TPaveText(x1,y1,x2,y2)
	p.SetTextAlign(31)
	p.SetBorderSize(0)
	p.SetFillStyle(-1)
	p.SetTextFont(82)
	p.SetTextSize(0.018)
	p.SetTextColor(color)
	l = p.AddText(text)
	l.SetTextAngle(90.)
	return p

####################################################################################################
####################################################################################################
####################################################################################################
def PLOTNUISS(tag,mass):
	if not os.path.exists('plot'): os.makedirs('plot')
	if not os.path.exists('plot/limits'): os.makedirs('plot/limits')
	
# Files
	f = TFile.Open("combine/pulls%s_mH%s.root"%(tag,mass),"read")
	hbin = f.Get("h_pull_b")
	hbsin = f.Get("h_pull_s")
	hbsigin = f.Get("h_unc_b")
	hbssigin = f.Get("h_unc_s")
	
# ROOT settings
	gROOT.ProcessLineSync('gErrorIgnoreLevel = kWarning;')
	gROOT.ProcessLineSync('.x ../../common/styleCMSTDR.C')
	gROOT.SetBatch(1)
	gStyle.SetPadTopMargin(0.06)
	gStyle.SetPadRightMargin(0.02)
	gStyle.SetPadLeftMargin(0.085)
	gStyle.SetPadBottomMargin(0.30)
	
# Containers
	paves = []
	pavessig = []

####################
# Load data
	n = hbin.GetNbinsX()
	c = TCanvas("c","c",1600,800)
	hb = TH1F("hb",";;pull",n+2,0,n+2)
	hbs = TH1F("hbs",";;pull",n+2,0,n+2)
	hbsig = TH1F("hbsig",";;#sigma_{post}/#sigma_{pre} - 1",n+2,0,n+2)
	hbssig = TH1F("hbssig",";;#sigma_{post}/#sigma_{pre} - 1",n+2,0,n+2)
## Load per bin
	for ibin in range(2,n+2): 
#	for il,l in enumerate(lines):
		hb.SetBinContent(ibin,hbin.GetBinContent(ibin-1))
		hbs.SetBinContent(ibin,hbsin.GetBinContent(ibin-1))
		hbsig.SetBinContent(ibin,hbsigin.GetBinContent(ibin-1))
		hbssig.SetBinContent(ibin,hbssigin.GetBinContent(ibin-1))
		hbs.GetXaxis().SetBinLabel(ibin,"%s"%hbin.GetXaxis().GetBinLabel(ibin-1))
		hbssig.GetXaxis().SetBinLabel(ibin,hbsin.GetXaxis().GetBinLabel(ibin-1))
		paves += [PAVE(hbs.GetBinLowEdge(ibin),0.51,hbs.GetBinLowEdge(ibin)+hbs.GetBinWidth(ibin),0.73,"%.3f"%hb.GetBinContent(ibin),kBlack)]
		paves += [PAVE(hbs.GetBinLowEdge(ibin),0.73,hbs.GetBinLowEdge(ibin)+hbs.GetBinWidth(ibin),0.95,"%.3f"%hbs.GetBinContent(ibin),kRed)]
		pavessig += [PAVE(hbssig.GetBinLowEdge(ibin),-0.25,hbssig.GetBinLowEdge(ibin)+hbssig.GetBinWidth(ibin),-0.15,"%.3f"%(hbsig.GetBinContent(ibin)),kBlack)]
		pavessig += [PAVE(hbssig.GetBinLowEdge(ibin),-0.15,hbssig.GetBinLowEdge(ibin)+hbssig.GetBinWidth(ibin),-0.05,"%.3f"%(hbssig.GetBinContent(ibin)),kRed)]
	for ibin in [1,n+2]:
		hbs.GetXaxis().SetBinLabel(ibin,"")
		hbssig.GetXaxis().SetBinLabel(ibin,"")
	
####################
# pulls
####################
## Format histograms
	hb.SetLineColor(kBlack)
	hb.SetLineWidth(1)
	hbs.SetLineColor(kRed)
	hbs.SetLineWidth(1)
	hbs.SetFillColor(kRed-10)
	hbs.SetFillStyle(1001)
	hbs.GetXaxis().LabelsOption("v")
	hbs.GetXaxis().SetLabelSize(0.027)
	hbs.GetXaxis().SetTickLength(0.02)
	hbs.GetYaxis().SetRangeUser(-0.8,0.8)
	hbs.GetYaxis().SetTitleOffset(0.7)
	hbs.GetYaxis().SetNdivisions(509)
	gPad.SetTicks(1,1)
	
## Add legend
	leg = TLegend(0.8,0.7,0.9,0.85)
	leg.SetHeader("m_{H} = %s GeV"%mass)
	leg.AddEntry(hb,"b","L")
	leg.AddEntry(hbs,"b+s","F")
	leg.SetFillStyle(-1)
	leg.SetBorderSize(0)
	leg.SetTextFont(62)
	leg.SetTextSize(0.035)
	leg.SetY1(leg.GetY2()-leg.GetNRows()*0.038)

## Draw elements
	hbs.Draw("hist")
	hb.Draw("histsame")
	lin = TLine(hbs.GetBinLowEdge(1),0.,hbs.GetBinLowEdge(hbs.GetNbinsX()),0.0)
	lin.SetLineStyle(7)
	lin.Draw("same")
	leg.Draw()
	
## Add text
	paveCMS = TPaveText(gStyle.GetPadLeftMargin()+0.02,0.7,gStyle.GetPadLeftMargin()+0.15,1.-gStyle.GetPadTopMargin()-0.03,"NDC")
	paveCMS.SetTextFont(62)
	paveCMS.SetTextSize(gStyle.GetPadTopMargin()*3./4.)
	paveCMS.SetBorderSize(0)
	paveCMS.SetFillStyle(-1)
	paveCMS.SetTextAlign(12)
	paveCMS.AddText("CMS")
	#l = paveCMS.AddText("Preliminary")
	#l.SetTextFont(52)
	paveCMS.Draw()
	gPad.Update()
	paveCMS.SetY1NDC(paveCMS.GetY2NDC()-paveCMS.GetListOfLines().GetSize()*gStyle.GetPadTopMargin())
	
	paveLumi = TPaveText(0.5,1.-gStyle.GetPadTopMargin(),0.99,1.00,"NDC")
	paveLumi.SetTextFont(42)
	paveLumi.SetTextSize(gStyle.GetPadTopMargin()*3./4.)
	paveLumi.SetBorderSize(0)
	paveLumi.SetFillStyle(-1)
	paveLumi.SetTextAlign(32)
	paveLumi.AddText("19.8 fb^{-1} (8TeV)")#//+ 18.2 
	paveLumi.Draw()
	
## Save plots
	c.SaveAs("plot/limits/nuissances%s_mH%s_1.pdf"%(tag,mass))
	c.SaveAs("plot/limits/nuissances%s_mH%s_1.png"%(tag,mass))

## Version with text
	hbs.GetYaxis().SetRangeUser(-1.0,1.0)
	gPad.Update()
	paveCMS.SetY1NDC(gStyle.GetPadBottomMargin()+0.02)
	paveCMS.SetY2NDC(gStyle.GetPadBottomMargin()+0.02+paveCMS.GetListOfLines().GetSize()*gStyle.GetPadTopMargin())
	leg.SetY2NDC(0.55)
	leg.SetY1NDC(0.55-leg.GetNRows()*0.038)
	leg.Draw()
	for p in paves: p.Draw()
	c.SaveAs("plot/limits/nuissances%s_mH%s_2.pdf"%(tag,mass))
	c.SaveAs("plot/limits/nuissances%s_mH%s_2.png"%(tag,mass))

########################################
# ratios
########################################
## Format histograms
	hbsig.SetLineColor(kBlack)
	hbsig.SetLineWidth(1)
	hbssig.SetLineColor(kRed)
	hbssig.SetLineWidth(1)
	hbssig.SetFillColor(kRed-10)
	hbssig.SetFillStyle(1001)
	hbssig.GetXaxis().LabelsOption("v")
	hbssig.GetXaxis().SetLabelSize(0.027)
	hbssig.GetXaxis().SetTickLength(0.02)
	hbssig.GetYaxis().SetRangeUser(-0.2,0.2)
	hbssig.GetYaxis().SetTitleOffset(0.7)
	hbssig.GetYaxis().SetNdivisions(505)
	gPad.SetTicks(1,1)
	
## Add legend
	leg = TLegend(0.8,0.7,0.9,0.85)
	leg.SetHeader("m_{H} = %s GeV"%mass)
	leg.AddEntry(hb,"b","L")
	leg.AddEntry(hbs,"b+s","F")
	leg.SetFillStyle(-1)
	leg.SetBorderSize(0)
	leg.SetTextFont(62)
	leg.SetTextSize(0.035)
	leg.SetY1(leg.GetY2()-leg.GetNRows()*0.038)
	
## Draw elements
	hbssig.Draw("hist")
	hbsig.Draw("histsame")
	lin = TLine(hbssig.GetBinLowEdge(1),0.,hbssig.GetBinLowEdge(hbssig.GetNbinsX()),0.0)
	lin.SetLineStyle(7)
	lin.Draw("same")
	leg.Draw()
	
## Add text
	paveCMS = TPaveText(gStyle.GetPadLeftMargin()+0.02,0.7,gStyle.GetPadLeftMargin()+0.15,1.-gStyle.GetPadTopMargin()-0.03,"NDC")
	paveCMS.SetTextFont(62)
	paveCMS.SetTextSize(gStyle.GetPadTopMargin()*3./4.)
	paveCMS.SetBorderSize(0)
	paveCMS.SetFillStyle(-1)
	paveCMS.SetTextAlign(12)
	paveCMS.AddText("CMS")
	#l = paveCMS.AddText("Preliminary")
	#l.SetTextFont(52)
	paveCMS.Draw()
	gPad.Update()
	paveCMS.SetY1NDC(paveCMS.GetY2NDC()-paveCMS.GetListOfLines().GetSize()*gStyle.GetPadTopMargin())
	
	paveLumi = TPaveText(0.5,1.-gStyle.GetPadTopMargin(),0.99,1.00,"NDC")
	paveLumi.SetTextFont(42)
	paveLumi.SetTextSize(gStyle.GetPadTopMargin()*3./4.)
	paveLumi.SetBorderSize(0)
	paveLumi.SetFillStyle(-1)
	paveLumi.SetTextAlign(32)
	paveLumi.AddText("19.8 fb^{-1} (8TeV)")#//+ 18.2 
	paveLumi.Draw()

## Save plots
	c.SaveAs("plot/limits/nuissances%s_mH%s_3.pdf"%(tag,mass))
	c.SaveAs("plot/limits/nuissances%s_mH%s_3.png"%(tag,mass))

## Version with text
	hbssig.GetYaxis().SetRangeUser(-0.3,0.3)
	gPad.Update()
	for p in pavessig: p.Draw()
	c.SaveAs("plot/limits/nuissances%s_mH%s_4.pdf"%(tag,mass))
	c.SaveAs("plot/limits/nuissances%s_mH%s_4.png"%(tag,mass))
	
####################################################################################################
## Close files
	c.Close()
	f.Close()

####################################################################################################
####################################################################################################
####################################################################################################
if __name__=='__main__':
	mp = OptionParser()
	opts,args = mp.parse_args()

	PLOTNUISS(args[0],args[1])


