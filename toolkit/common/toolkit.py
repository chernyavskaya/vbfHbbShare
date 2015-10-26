#!/usr/bin/env python

import sys,os,json
basepath=os.path.split(os.path.abspath(__file__))[0]
sys.path.append(basepath)

tempargv = sys.argv[:]
sys.argv = []
import ROOT
from ROOT import *
sys.argv = tempargv

from copy import deepcopy as dc


# PRINTING #########################################################################################
def l1(text):
	print blue+'\n+ %s'%(text)+plain
def l2(text):
	print purple+'  ++ %s'%(text)+plain
def l3(text):
	print plain+'  ++++ %s'%(text)+plain
def l4(text):
	print orange+'    ++++ %s'%(text)+plain
def l5(text):
	print green+'      ++++ %s'%(text)+plain
def l6(text):
	print plain+'        ++ %s'%(text)+plain

# COLORS ########################################################################################## 
red 	= "\033[0;31m"
green	= "\033[0;32m"
yellow	= "\033[0;33m"
blue	= "\033[0;34m"
purple	= "\033[0;35m"
cyan	= "\033[0;36m"
Red		= "\033[1;31m"
Green	= "\033[1;32m"
Yellow	= "\033[1;33m"
Blue	= "\033[1;34m"
Purple	= "\033[1;35m"
Cyan	= "\033[1;36m"
grey    = "\033[38;5;243m"
orange  = "\033[38;5;208m" #202
Black   = "\033[1m"
plain	= "\033[m"


# ACCESS FILE CONTENT ##############################################################################
def filecontent(fname):
	f = file(fname,'r')
	content = f.read()
	f.close()
	return content


# RUN inside ROOT ##################################################################################
def inroot(cmd):
	gROOT.ProcessLineSync(cmd)


# SPLIT COMMA SEPARATED OPTION LIST ################################################################
def optsplitlist(option,opt,value,parser):
#	if ';' in value: setattr(parser.values, option.dest, [x.split(';') for x in value.split(',')])
#	else: setattr(parser.values, option.dest, [value.split(',')])
	setattr(parser.values, option.dest, [x.split(';') for x in value.split(',')])

def optsplit(option,opt,value,parser):
	setattr(parser.values, option.dest, value.split(','))

def optsplitfloat(option,opt,value,parser):
	setattr(parser.values, option.dest, [float(x) for x in value.split(',')])

def optsplitint(option,opt,value,parser):
	setattr(parser.values, option.dest, [int(x) for x in value.split(',')])

def optsplitdict(option,opt,value,parser):
	vd = {}
	for v in value.split(','):
		tmp = v.split("#")
		key = tmp[0]
		val = [tmp[1],tmp[2].split(';')]
		vd[key] = val
	setattr(parser.values,option.dest,vd)

def optsplitmore(option,opt,value,parser):
	vd = {}
	for v in value.split(','):
		tmp = v.split('_')
		key = tmp[0]
		lumi = tmp[1]
		wght = tmp[2].split(';')
		vd[(key,'lumi')] = lumi
		vd[(key,'wght')] = wght
		vd[(key,'old')] = [["%s"%lumi],["%s"%x for x in wght]]
	setattr(parser.values,option.dest,vd)

def setdefaults(option,opt,value,parser):
	jsondefaults = json.loads(filecontent(value))
	for ok,oval in jsondefaults.iteritems():
		if '.json' in oval: oval = os.path.join(basepath,oval)
		setattr(parser.values, ok, oval)
		l2("Set from opts file: %s --> %s"%(ok,oval))		
	globalpath=''
	try: 
		if any(['lxplus' in x for x in os.uname()]) and os.getlogin()=='salderwe' and parser.values.fileformat=='1': globalpath='/afs/cern.ch/work/s/salderwe/groups/Hbb/paper2012/'
		if any(['lxplus' in x for x in os.uname()]) and os.getlogin()=='salderwe' and parser.values.fileformat=='2': globalpath='/afs/cern.ch/user/s/salderwe/eosaccess/cms/store/cmst3/group/vbfhbb/flat/'#work/s/salderwe/groups/Hbb/autumn2013'
	except:
		pass	
	setattr(parser.values, 'globalpath', globalpath)
	if not globalpath=='': l2("Set default: %s --> %s"%('globalpath',globalpath))

def printopts(option,opt,value,parser):
	optname = str(option).split('/')[-1].strip('-')
	setattr(parser.values, optname, value)
	l2("Changed default: %s --> %s"%(optname,value))

# SAVING HELPER FUNCTIONS ##########################################################################
def makeDirsRoot(fout,ndir):
	gDirectory.cd('%s:/'%fout.GetName())
	for i in range(len(ndir.split('/'))+1):
		ipath = '/'.join(ndir.split('/')[0:i])
		if not gDirectory.GetDirectory('/%s'%ipath): gDirectory.mkdir('%s'%ipath)

def makeDirs(ndir):
	if not os.path.exists(ndir): os.makedirs(ndir)


# PLOTTING/LAYOUT HELPER FUNCTIONS #################################################################
def getSelLegend(left,bottom,right,top,rows=None,fillColor=0,fillStyle=0,textColor=1,textSize=0.020):
	selleg = TPaveText(left,bottom,right,top,"NDC")
	selleg.SetFillColor(fillColor)
	selleg.SetFillStyle(fillStyle)
	selleg.SetTextColor(textColor)
	selleg.SetTextSize(textSize)
	selleg.SetTextAlign(13)
	selleg.SetTextFont(82)
	selleg.SetBorderSize(0)
	return selleg

def getTLegend(left,bottom,right,top,columns=None,header=None,fillStyle=0,textColor=1,textSize=0.025):
	legend = TLegend(left,bottom,right,top)
	if not header==None: 
		legend.SetTextSize(textSize+0.005)
		legend.SetHeader(header)
	if not columns==None: legend.SetNColumns(int(columns))
	legend.SetFillStyle(fillStyle)
	legend.SetFillColor(kWhite)
	legend.SetTextColor(textColor)
	legend.SetTextSize(textSize)
	return legend

def getTLegendRight(left,bottom,right,top,columns=None,header=None,fillStyle=0,textColor=1,textSize=0.025):
	legend = TLegend(left,bottom,right,top)
	if not header==None: legend.SetHeader(header)
	if not columns==None: legend.SetNColumns(int(columns))
	legend.SetFillStyle(fillStyle)
	legend.SetFillColor(kWhite)
	legend.SetTextColor(textColor)
	legend.SetTextSize(textSize)
	legend.SetTextFont(42)
	return legend

def getTPave(left,bottom,right,top,rows=None,fillColor=0,fillStyle=0,textColor=1,textSize=0.025):
	text = TPaveText(left,bottom,right,top,"NDC")
	text.SetFillColor(fillColor)
	text.SetFillStyle(fillStyle)
	text.SetTextColor(textColor)
	text.SetTextSize(textSize)
	text.SetTextAlign(11)
	text.SetTextFont(42)
	text.SetBorderSize(0)
	return text

def getTLine(x1,y1,x2,y2,color=616,width=5,style=9):
	line = TLine(x1,y1,x2,y2)
	line.SetLineColor(color)
	line.SetLineWidth(width)
	line.SetLineStyle(style)
	return line

def setStyleTH1F(h,lineColor=1,lineStyle=1,fillColor=0,fillStyle=0,markerColor=1,markerStyle=0,lineWidth=3,markerSize=3):
	h.SetLineColor(lineColor)
	h.SetLineStyle(lineStyle)
	h.SetLineWidth(lineWidth)
	h.SetFillColor(fillColor)
	h.SetFillStyle(fillStyle)
	h.SetMarkerColor(markerColor)
	h.SetMarkerStyle(markerStyle)
	h.SetMarkerSize(markerSize)

def setStyleTHStack(stack,ratio=True):
	stack.Draw()
	stack.GetYaxis().SetLabelSize(stack.GetYaxis().GetLabelSize()*1.25)
	stack.GetYaxis().SetLabelOffset(stack.GetYaxis().GetLabelOffset()/3)
	stack.GetYaxis().SetTickLength(0.02)
	if ratio: stack.GetXaxis().SetLabelColor(0)

def setStyleTH2F(h):
	h.Draw()
	gPad.SetTopMargin(0.07)
	h.GetYaxis().SetLabelSize(h.GetYaxis().GetLabelSize()*1.5)
	h.GetYaxis().SetLabelOffset(h.GetYaxis().GetLabelOffset()*1.2)
	h.GetYaxis().SetTitleSize(h.GetYaxis().GetTitleSize()*1.5)
	h.GetYaxis().SetTitleOffset(h.GetYaxis().GetTitleOffset()*1.1)
	h.GetXaxis().SetLabelSize(h.GetXaxis().GetLabelSize()*1.5)
	h.GetXaxis().SetLabelOffset(h.GetXaxis().GetLabelOffset()*1.2)
	h.GetXaxis().SetTitleSize(h.GetXaxis().GetTitleSize()*1.5)
	h.GetXaxis().SetTitleOffset(h.GetXaxis().GetTitleOffset()*1.1)
	h.GetZaxis().SetLabelSize(h.GetZaxis().GetLabelSize()*1.5)
	h.GetYaxis().SetTickLength(0.02)

def getRangeTH1F(h,ymin,ymax):
	if h.GetMaximum() > ymax: ymax = h.GetMaximum()
	if h.GetMinimum() < ymin: ymin = h.GetMinimum()
	return ymin,ymax

def setRangeTH1F(h,ymin,ymax,log=True):
	if log:
		h.SetMinimum(float("1e%i"%log10(ymin+0.5)))
		h.SetMaximum(float("1e%i"%(log10(ymax)+1))) # +3
	else:
		h.SetMinimum(0)
		h.SetMaximum(round(ymax*1.3,2))

def getRatioPlotCanvas(canvas):
	c1 = TPad('c1','c1',0,0.27,1,1)
	c2 = TPad('c2','c2',0,0,1,0.332)
	c1.SetBottomMargin(0.039)
	c2.SetTopMargin(0.10)
	c2.SetBottomMargin(c2.GetBottomMargin()+0.25)
	c2.SetFillStyle(0)
	c1.Draw()
	c2.Draw()
	canvas.Update()
	return c1,c2

def setStyleTH1Fratio(h):
	# main
	h.SetTitle("")
	h.GetYaxis().SetTitle('Data / MC - 1')
	#h.GetYaxis().SetTitleSize(h.GetYaxis().GetTitleSize()*0.75)
	#h.GetYaxis().SetRangeUser(0.5,1.5)
	#h.GetYaxis().SetRangeUser(0.0,2.0)
	gPad.SetGridy(1)
	h.GetYaxis().SetRangeUser(-0.5,0.5)
	h.GetYaxis().SetNdivisions(205)
	h.GetXaxis().SetTickLength(0.08)
	h.GetYaxis().SetTickLength(0.015)
	# fonts & offsets
	h.SetTitleOffset(3.8,'X')
	h.GetYaxis().SetTitleSize(h.GetYaxis().GetTitleSize()*0.8)
	h.SetTitleOffset(h.GetYaxis().GetTitleOffset()/0.8,'Y')
	# filling
#	h.SetFillColor(kGray)
#	h.SetFillStyle(1)
	h.SetMarkerStyle(20)
	h.SetMarkerColor(kBlack)
	h.SetMarkerSize(0.7)

# CLOSE BRACKETS OF STRING #########################################################################
def closeBrackets(text):
	nLeft = text.count('(')
	nRight = text.count(')')
	if nLeft>nRight: text += ")"*(nLeft-nRight)
	if nRight>nLeft: text  = "("*(nRight-nLeft) + text	
	return text

# NAMING STRING CREATION ###########################################################################
def getNames(opts,sample,var,sel,trg,ref,extra=""):
	names = {}
# selection and trigger
	names['sel'] = 's'+'-'.join(sorted(sel))
	names['trg'] = 't'+'-'.join(trg)
	names['trg-data'] = 'd'+'-'.join(trg) if (opts.datatrigger==[] or trg==['None']) else 'd'+'-'.join(opts.datatrigger[opts.trigger.index(trg)])
	names['ref'] = 'r'+'-'.join(ref)
# variables
	names['var'] = var['var']
# samples
	jsoninfo = json.loads(filecontent(opts.jsoninfo))
#	names['sample'] = sample['pointer']
	names['tag']    = sample['tag'] if sample else "global"
	names['group']  = jsoninfo['groups'][names['tag']] if sample else "global"
# histograms
	binningstring = "-B%s-%s-%s"%(var['nbins_x'],var['xmin'],var['xmax'])
	names['hist']   = '_'.join(['h'+extra,names['var']+binningstring,names['group'],names['tag'],names['sel'],names['trg'],names['trg-data'],names['ref']])
	names['hist-title'] = names['hist']+";%s;%s"%(var['title_x'],var['title_y'])
	names['stack-sig'] = '_'.join(['ssig',names['var']+binningstring,names['sel'],names['trg'],names['trg-data'],names['ref']])
	names['stack-bkg'] = '_'.join(['sbkg',names['var']+binningstring,names['sel'],names['trg'],names['trg-data'],names['ref']])
	names['stack-dat'] = '_'.join(['sdat',names['var']+binningstring,names['sel'],names['trg'],names['trg-data'],names['ref']])
	names['stack-sig-title'] = names['stack-sig']+";%s;%s"%(var['title_x'],var['title_y'])
	names['stack-bkg-title'] = names['stack-bkg']+";%s;%s"%(var['title_x'],var['title_y'])
	names['stack-dat-title'] = names['stack-dat']+";%s;%s"%(var['title_x'],var['title_y'])
	names['stack'] = '_'.join(['hTurnon'+extra,names['var']+binningstring,names['group'],names['tag'],names['sel'],names['trg'],names['trg-data'],names['ref']])
	names['stack-title'] = names['stack']+";%s;%s"%(var['title_x'],var['title_y'])
	names['turnon']   = '_'.join(['t',names['var']+binningstring,names['group'],names['tag'],names['sel'],names['trg'],names['trg-data'],names['ref']])
	names['turnon-title'] = names['turnon']+";%s;%s"%(var['title_x'],'Trigger Efficiency (N-1 Cuts)') 
# paths
	names['path-hist'] = "%s/%s"%('_'.join([x for x in [names['group'],names['tag']] if not x==""]),'_'.join([x for x in [names['sel'],names['trg']] if not x==""]))
	names['path-turnon'] = "%s/%s"%('_'.join([x for x in [names['group'],names['tag']] if not x==""]),'_'.join([x for x in [names['sel'],names['trg']] if not x==""]))
	return names

# WEIGHT INFO ######################################################################################
def weightInfo(weights,KFWght=None):
	localweights = dc(weights)
	localweights[1] = [x.replace('#','.').replace(']','').replace('[','').replace('KFAC','KFAC%s'%("%.2f"%KFWght if KFWght else "def")) for x in weights[1] if not x=='']
	if weights==[[''],['']]: return 'None'
	else: return ('-'.join(sorted(localweights[1])))

# TRIGTRUTH ########################################################################################
def trigTruth(usebool):
	if usebool: return '1'
	else: return '49'

def trigData(opts,s,trg):
	#print "in: ",trg
	if s=="" and (not opts.datatrigger==[]):
		trg_orig = dc(trg)
		trg = opts.datatrigger[opts.trigger.index(trg)]
	elif (not s==None) and (not opts.datatrigger==[]) and any([x in s['tag'] for x in ['Data','DataV','JetMon']]):
		trg_orig = dc(trg)
		trg = opts.datatrigger[opts.trigger.index(trg)]
	else:
		trg_orig = dc(trg)
	#print "out: ",trg,trg_orig
	return trg, trg_orig
	
# CATsetup ########################################################################################
class CATsetupClass:
	def __init__(self,tcat,lcat,bcat):
		self.ncat       = len(bcat)-1
		self.tag        = tcat
		self.label      = lcat
		self.boundaries = bcat

class SELsetupClass:
	def __init__(self,nsel):
		self.nsel       = nsel
		self.selections = []
		self.seldict    = {}
			
	def addCAT(self,tcat,lcat,bcat):
		self.selections += [CATsetupClass(tcat,lcat,bcat)]
		self.seldict[tcat] = [self.selections[-1]]
	
	def reeval(self):
		self.ncats      = [x.ncat for x in self.selections]
		self.labels     = [x.label for x in self.selections]
		self.tags       = [x.tag for x in self.selections]
		self.mva        = ["mva%s"%x.tag for x in self.selections]

def SELsetup(option,opt=None,value=None,parser=None):
	if not parser: value = option
	l1 = value.split(',')
	nsel = len(l1)
	s = SELsetupClass(nsel)
	for l in l1:
		l2 = l.split(';')
		tcat = l2[0]
		lcat = l2[1]
		bcat = [float(x) for x in l2[2].split('#')]
		s.addCAT(tcat,lcat,bcat)
	s.reeval()
	if parser: setattr(parser.values, option.dest, s)
	else: return s
