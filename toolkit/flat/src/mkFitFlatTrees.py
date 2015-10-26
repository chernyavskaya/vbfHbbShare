#!/usr/bin/env python

import sys,os,json,re
basepath=os.path.split(os.path.abspath(__file__))[0]
sys.path.append(basepath+'/../../common/')

tempargv = sys.argv[:]
sys.argv = []
import ROOT
from ROOT import *
sys.argv = tempargv

from toolkit import *
from write_cuts import *

# OPTION PARSER ####################################################################################
def parser(mp=None):
	if mp==None: mp = OptionParser()

	mgf = OptionGroup(mp,cyan+"mkFlatTree settings"+plain)
	mgf.add_option('--tag',help='Tag set with this.',default=[],type='str',action='callback',callback=optsplit)

	mgj = OptionGroup(mp,cyan+"json settings"+plain)
	mgj.add_option('-D','--jsondefaults',help="Set jsons accoring to default file.",dest='jsondefaults',default="%s/vbfHbb_defaults.json"%(basepath),type='str',action='callback',callback=setdefaults)
	mgj.add_option('-S','--jsonsamp',help="File name for json with sample info.",dest='jsonsamp',default="%s/vbfHbb_samples.json"%(basepath),type='str')
	mgj.add_option('-V','--jsonvars',help="File name for json with variable info.",dest='jsonvars',default="%s/vbfHbb_variables.json"%(basepath),type='str')
	mgj.add_option('-C','--jsoncuts',help="File name for json with cut info.",dest='jsoncuts',default="%s/vbfHbb_cuts.json"%(basepath),type='str')
	mgj.add_option('-I','--jsoninfo',help="File name for json with general info.",dest='jsoninfo',default="%s/vbfHbb_info.json"%(basepath),type='str')
	mgj.add_option('-G','--globalpath',help="Global prefix for samples.",dest='globalpath',type='str',action='callback',callback=printopts)
	mgj.add_option('-F','--fileformat',help="File format for samples (1: 2012, 2: 2013).",dest='fileformat',default=1,type='int')
	mgj.add_option('--source',help="Filepath for original flatTrees.",dest='source',default="",type='str')
	mgj.add_option('--destination',help="Filepath for new flatTrees.",dest='destination',default="",type='str')
	mgj.add_option('--flatprefix',help="Prefix to flatTree names.",dest='flatprefix',default="",type='str')
	mgj.add_option('--flatsuffix',help="Suffix to flatTree names.",dest='flatsuffix',default="",type='str')

	mgd = OptionGroup(mp,cyan+"detail settings"+plain)
	mgd.add_option('-b','--batch',help="Set batch mode for ROOT = FALSE.",action='store_false',default=True)
	mgd.add_option('-d','--debug',help="Write extra printout statements.",action='store_true',default=False)
	mgd.add_option('--usebool',help="Use original trees, not the char ones.",action='store_true',default=False)

	mgst = OptionGroup(mp,cyan+"Run for subselection determined by variable, sample and/or selection/trigger"+plain)
	mgst.add_option('-v','--variable',help=purple+"Run only for these variables (comma separated)."+plain,dest='variable',default='',type='str',action='callback',callback=optsplit)
	mgst.add_option('--novariable',help=purple+"Don't run for these variables (comma separated)."+plain,dest='novariable',default='',type='str',action='callback',callback=optsplit)
	mgst.add_option('-s','--sample',help=purple+"Run only for these samples (comma separated)."+plain,dest='sample',default='',type='str',action='callback',callback=optsplit)
	mgst.add_option('--nosample',help=purple+"Don't run for these samples (comma separated)."+plain,dest='nosample',default='',type='str',action='callback',callback=optsplit)
	mgst.add_option('-t','--trigger',help=purple+"Run only for these triggers (comma and colon separated)."+plain,dest='trigger',default=[['None']],type='str',action='callback',callback=optsplitlist)
	mgst.add_option('--datatrigger',help=purple+"Run only for these triggers (comma and colon separated) (override for data sample(s))."+plain,dest='datatrigger',default=[],type='str',action='callback',callback=optsplitlist)
	mgst.add_option('-p','--selection',help=purple+"Run only for these selections (comma and colon separated)."+plain,dest='selection',default=[['None']],type='str',action='callback',callback=optsplitlist)
	mgst.add_option('-r','--reftrig',help=purple+"Add reference trigger to selection."+plain,dest='reftrig',default=[['None']],type='str',action='callback',callback=optsplitlist)
	mgst.add_option('-w','--weight',help=purple+"Put this weight (\"lumi,weight1;weight2;...,manualKFWght,mapfile;mapname\")"+plain,dest='weight',default=[[''],['']],type='str',action='callback',callback=optsplitlist)
	
	mp.add_option_group(mgj)
	mp.add_option_group(mgf)
	mp.add_option_group(mgd)
	mp.add_option_group(mgst)
	return mp


# mkFitFlatTree ####################################################################################
def mkFitFlatTree(opts,s,sel,trg):
	# info
	jsoninfo = json.loads(filecontent(opts.jsoninfo))
	jsonsamp = json.loads(filecontent(opts.jsonsamp))
	ismc = True if not 'Data' in s['tag'] else False

	# prepare
	tag = 'VBF' if 'VBF' in trg else 'NOM'
	nfin = s['fname']
	nfout = nfin.replace('flatTree','Fit').replace('.root','_sel%s.root'%tag) 
	if not os.path.exists(opts.destination): makeDirs(opts.destination)
	fin = TFile.Open(opts.globalpath+nfin,"read")
	fout = TFile.Open(opts.destination+nfout,"recreate")
	l2("Working for %s"%s['tag'])
	l3("File in : %s"%nfin)
	l3("File out: %s"%nfout)

	# process
	fin.cd()
	tin = fin.Get("Hbb/events")
	hpass = fin.Get("Hbb/TriggerPass")

	tin.SetBranchStatus("*",0)
	for b in ["mvaNOM","mvaVBF","selNOM","selVBF","dPhibb","mbbReg","mbb","nLeptons","triggerResult"]:
		tin.SetBranchStatus(b,1)
	if ismc:
		for b in ["puWt","trigWtNOM","trigWtVBF"]:
			tin.SetBranchStatus(b,1)
		 
	# cuts
	cut,cutlabel = write_cuts(sel,trg,reftrig=["None"],sample=s['tag'],jsonsamp=opts.jsonsamp,jsoncuts=opts.jsoncuts,weight=opts.weight,trigequal=trigTruth(opts.usebool))
	if opts.debug: l3("Cut %s: \n\t\t\t%s%s%s: \n\t\t\t%s"%(s['tag'],blue,cutlabel,plain,cut))
#	cut = ""
#	if tag=="NOM":
#		cut ="selNOM && (triggerResult[5] || triggerResult[7]) && nLeptons==0"
#	elif tag=="VBF":
#		cut = "selVBF && triggerResult[9] && (!(selNOM && (triggerResult[0] || triggerResult[1]))) && nLeptons==0"
#	else: sys.exit(Red+"Tag type unclear: NOM/VBF. Exiting."+plain)
#	if opts.debug: l3("Cut %s: %s%s%s"%(s['tag'],blue,cut,plain))

	# process
	fout.cd()
	if hpass: hpass.Write("TriggerPass")
	makeDirsRoot(fout,"Hbb")
	gDirectory.cd("%s:/%s"%(fout.GetName(),"Hbb"))
	tout = tin.CopyTree(cut)
	l3("Events: %d"%tout.GetEntries())
	tout.Write()

	# cleaning
	fout.Close()
	fin.Close()

def mkFitFlatTrees():
	# init option parsing
	mp = parser()
	opts,args = mp.parse_args()
	
	# info
	l1('Loading:')
	l2('Globalpath: %s'%opts.globalpath)
 	l1('Loading samples:')
	jsoninfo = json.loads(filecontent(opts.jsoninfo))
	jsonsamp = json.loads(filecontent(opts.jsonsamp))
	allsamples = jsonsamp['files']
	selsamples = []
	for s in sorted(allsamples.itervalues(),key=lambda x: (x['tag'] if not 'QCD' in x['tag'] else x['tag'][0:3],float(x['tag'][3:]) if 'QCD' in x['tag'] else 1)):
		# require regex in opts.sample
		if not opts.sample==[] and not any([(x in s['tag']) for x in opts.sample]): continue
	   # veto regex in opts.nosample
		if not opts.nosample==[] and any([(x in s['tag']) for x in opts.nosample]): continue
		# extra vetoes
		if 'VBF1' in s['fname'] and (not any(['VBF' in trg for trg in opts.trigger])): continue
		if ('BJetPlus' in s['fname'] or 'MultiJet' in s['fname']) and any(['VBF' in trg for trg in opts.trigger]): continue
		selsamples += [s]
		l2('%s: %s'%(s['tag'],s['fname']))
 	l1('Creating FitFlatTrees:')
	
	# consistensy check
	if not len(opts.trigger)==len(opts.selection): sys.exit(Red+"\n!!! Sel and trg options need to have the same length. Exiting.\n"+plain)
	
	# process	
	for i in range(len(opts.selection)):
		sel = opts.selection[i]
		trg = opts.trigger[i]
		for s in selsamples: mkFitFlatTree(opts,s,sel,trg)
		### END LOOP over samples
	### END LOOP over tags

####################################################################################################
if __name__=='__main__':
	mkFitFlatTrees()
	
