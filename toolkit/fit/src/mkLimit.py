#!/usr/bin/env python

import os,sys,re,json,datetime,subprocess
from glob import glob
from array import array
from optparse import OptionParser,OptionGroup
from string import Template
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
	mp.add_option('--workdir',help=colours[5]+'Case workdir.'+colours[0],default='case0',type='str')
	mp.add_option('--long',help=colours[5]+'Long filenames.'+colours[0],default=False,action='store_true')
	mp.add_option('-v','--verbosity',help=colours[5]+'Verbosity.'+colours[0],default=0,action='count')
	mp.add_option('-q','--quiet',help=colours[5]+'Quiet.'+colours[0],default=True,action='store_false')
#
	mg1 = OptionGroup(mp,'Combine setup')
	mg1.add_option('-t','--type',help=colours[5]+'Run Toys/MLFit/ProfileLikelihood/Asymptotic/ChannelCompatibility.'+colours[0],type='str',default='Asymptotic')
	mg1.add_option('-m','--mass',help=colours[5]+'Masspoint selection.'+colours[0],type='str',default=[125],action='callback',callback=optsplitint)
	mg1.add_option('-n','--label',help=colours[5]+'Labeling string.'+colours[0],type='str',default="vbfHbb")
	mg1.add_option('-r','--r',help=colours[5]+'Min and max r.'+colours[0],type='str',default=None,action='callback',callback=optsplitint)
	mg1.add_option('-p','--prefix',help=colours[5]+'Datacard prefix.'+colours[0],type='str',default='datacards')
	mg1.add_option('-V','--veto',help=colours[5]+'Veto label.'+colours[0],type='str',default='')
	mg1.add_option('-e','--extra',help=colours[5]+'Extra options.'+colours[0],type='str',default='')
	mp.add_option_group(mg1)
	
	mg2 = OptionGroup(mp,'Workspace settings')
	mg2.add_option('--bounds',help=colours[5]+'Template boundaries: 80,200 (min,max)'+colours[0],default=[80.,200.],type='str',action='callback',callback=optsplitfloat,dest='X')
	mg2.add_option('--binwidth',help=colours[5]+'Template bin width: 0.1,0.1 (NOM,VBF)'+colours[0],default=[0.1,0.1],type='str',action='callback',callback=optsplitfloat,dest='dX')
	mg2.add_option('--TF',help=colours[5]+'Transfer function label: POL1,POL2 (NOM,VBF)'+colours[0],default=['POL1','POL2'],type='str',action='callback',callback=optsplit)
	mg2.add_option('--BRN',help=colours[5]+'Bernstein order: 5,4 (NOM,VBF)'+colours[0],default=[5,4],type='str',action='callback',callback=optsplitint)
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

####################################################################################################
def task():
# Parse options
	mp = parser()
	opts,args = mp.parse_args()

# Style
	style()

# Create directories if needed
	makeDirs('%s'%opts.workdir)
	makeDirs('%s/combine'%opts.workdir)
	olddir = os.getcwd()
	os.chdir('%s/combine'%opts.workdir)

	if opts.long:
		opts.label = opts.label + "_B%d-%d_BRN%d-%d_TF%s-%s"%(opts.X[0],opts.X[1],opts.BRN[0],opts.BRN[1],opts.TF[0],opts.TF[1])

# Setup
	jsonfile = json.loads(filecontent("%s/vbfHbb_combine_2014.json"%basepath))

	for mass in opts.mass:
		tmp=jsonfile[opts.type]['opts']
		longtag = "B%d-%d_BRN%d-%d_TF%s-%s"%(opts.X[0],opts.X[1],opts.BRN[0],opts.BRN[1],opts.TF[0],opts.TF[1])
		datacard="../%s/datacard_m%d%s_%s.txt"%(opts.prefix,mass,"" if not opts.veto else "_CAT0-CAT6-CATveto%s"%(''.join(opts.veto.split(','))),longtag)#opts.workdir)
## Prepare command
		cmd='combine %s'%(tmp)
		cmd += ' -n .%s'%opts.label
		if "MaxLikelihood" in opts.type:
			cmd += '_mH%d'%mass
		elif "ProfileLikelihoodExp" in opts.type:
			cmd += '_ExpSig'
		elif "ProfileLikelihoodObs" in opts.type:
			cmd += '_ObsSig'
		cmd += ' -m %d'%mass
		cmd += ' %s'%datacard
## Add extra options to command
		if opts.extra: cmd += ' %s'%opts.extra
## Print command
	 	print cmd
## Run command
		p = subprocess.Popen(cmd.split(),shell=False,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
## Direct log output to file
		logname = "%s.%s.mH%s%s.log"%(opts.label,opts.type,mass,"" if not opts.veto else "_CAT0-CAT6-CATveto%s"%(''.join(opts.veto.split(','))))
		logname = logname.replace("Inj125.Injected","Inj125")
		log = open(logname,"w+")
		while p.poll() is None:
			l = p.stdout.readline()
			if opts.verbosity>0 and not opts.quiet: print l,
			log.write(l)
		for l in  p.stdout.read().split('\n'):
			if opts.verbosity>0 and not opts.quiet: print l
			log.write("%s\n"%l)
		if opts.verbosity>0 and not opts.quiet: print
		log.close()

## Print tail of logfile
		print "%sLast 10 lines of logfile:%s"%("\033[0;31m","\033[m")
		os.system("tail -n10 %s"%logname)

	os.chdir(olddir)

####################################################################################################
if __name__=='__main__':
	task()
