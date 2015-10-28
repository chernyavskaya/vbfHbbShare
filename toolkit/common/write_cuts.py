#!/usr/bin/env python

import sys,json,os
basepath=os.path.split(os.path.abspath(__file__))[0]
sys.path.append(basepath)

#import main
from toolkit import *
from copy import deepcopy as dc
from optparse import OptionParser,OptionGroup
from weightFactory import *
import datetime
today=datetime.date.today().strftime('%Y%m%d')

####################################################################################################
def get_trigger(trigs,sample,samplejson,trigequal="49",trigjoin=" || "):
	content = json.loads(filecontent(samplejson))
	samplename = [x for x,y in content['files'].iteritems() if y['tag']==sample][0]
	trg = group( trigjoin.join( ["triggerResult[%s]==%s"%(content['files'][samplename]['trigger'].split(',')[content['trigger'].index(x)],trigequal) for x in trigs] ))
	if "triggerResult[-]" in trg: sys.exit('  %sUnknown trigger in trigger string. Check! Exiting.\n  --> %s (from %s)%s'%(red,trg,','.join(trigs),plain))
	return trg

####################################################################################################
def group(text):
	gtext = "(%s)"%text
	return gtext

####################################################################################################
def combos(triggers):
	ccs = []
	for l in range(1,len(triggers.keys())+1):
		for combo in [list(x) for x in combinations(triggers.keys(),l)]:
			complement = list(set(triggers.keys()) - set(combo))
			ccs += [[combo,complement]]
	return ccs

####################################################################################################
def parser(mp=None):
	if mp==None: mp = OptionParser()
	mgc = OptionGroup(mp,"Cut options")	
	mgc.add_option('--use',help=red+"Specify for which sample this cut will be used (relevant for trigger)."+plain,dest='use',default='',type='str')
	mgc.add_option('--skip',help=blue+"Variable to leave out of selection (N-1 cuts)."+plain,dest='skip',type='str')

	mgt = OptionGroup(mp,"Trigger options")
	mgs = OptionGroup(mp,"Selection options")
	mgt.add_option('--trgjoin',help='Separator for joining triggers.',default=' || ',type='str',dest='trgjoin')
	mgt.add_option('--trgcmpjoin',help='Separator for joining complements.',default=' || ',type='str',dest='trgcmpjoin')
	mgt.add_option('--trgcmp',help="Put these triggers in the complement (comma separated).",dest='trgcmp',default='',type='str',action='callback',callback=optsplit)
	mgs.add_option('--seljoin',help='Separator for joining selections.',default=' && ',type='str',dest='seljoin')
	mgs.add_option('--selcmpjoin',help='Separator for joining complements.',default=' || ',type='str',dest='selcmpjoin')
	mgs.add_option('--selcmp',help="Put these selections in the complement (comma separated).",dest='selcmp',default='',type='str',action='callback',callback=optsplit)
	mgs.add_option('--stgroup',help='First group sel and trg, only then group complements.',action='store_true',default=False)
	
	mp.add_option_group(mgc)
	mp.add_option_group(mgt)
	mp.add_option_group(mgs)
	
	return mp





# MAIN #############################################################################################
def write_cuts(sel=[],trg=[],selcmp=[],trgcmp=[],**kwargs):
	# input
	cuts = json.loads(filecontent(kwargs["jsoncuts"]))
	selections = cuts['sel']
	triggers = cuts['trg']
	selnew = dc(list(set(sel)-set(['None'])))
	trgnew = dc(list(set(trg)-set(['None'])))
	selold = sel
	trgold = trg
	sel = selnew
	trg = trgnew
	# defaults
	seljoin        = (' && '  if not 'seljoin'         in kwargs else kwargs['seljoin'])
	trgjoin        = (' || '  if not 'trgjoin'         in kwargs else kwargs['trgjoin'])
	selcmpjoin     = (' && '  if not 'selcmpjoin'      in kwargs else kwargs['selcmpjoin'])
	trgcmpjoin     = (' && '  if not 'trgcmpjoin'      in kwargs else kwargs['trgcmpjoin'])
	stgroup        = (False   if not 'stgroup'         in kwargs else kwargs['stgroup']) # first group sel and trg, then group complements	
	reftrig        = ([]      if not 'reftrig'         in kwargs else kwargs['reftrig'])
	varskip        = (''      if not 'varskip'         in kwargs else kwargs['varskip'])
	weight         = ([[''],['']] if not 'weight'      in kwargs else kwargs['weight'])
	KFWght         = (None    if not 'KFWght'          in kwargs else kwargs['KFWght'])
	trigequal      = ('49'    if not 'trigequal'       in kwargs else kwargs['trigequal'])
	sample         = (None    if not 'sample'          in kwargs else kwargs['sample'])
	extra          = ([]      if not 'extra'           in kwargs else kwargs['extra'])
	if not (seljoin[0]==' ' and seljoin[-1]==' '): seljoin = ' '+seljoin+' '
	if not (trgjoin[0]==' ' and trgjoin[-1]==' '): trgjoin = ' '+trgjoin+' '

	# trivialize run conditions in selection if not data sample
	if (not any([x in kwargs['sample'] for x in ['Data','JetMon']])) or (not 'sample' in kwargs):
		for y in cuts['sel'].keys():
			if 'run' in y: cuts['sel'][y] = {'runNo':['==','1']}
	
	# catch selection VETOs
	est = ""
	for k in sorted(sel):
		if not ('selection' in cuts['sel'][k].keys() or 'trigger' in cuts['sel'][k].keys()): continue
		else:
			if 'selection' in cuts['sel'][k].keys():
				subsel = [y[1] for x,y in cuts['sel'][k].iteritems() if x=='selection']
				es, eslabels = write_cuts(subsel,['None'],[],[],sample=sample,jsonsamp=kwargs['jsonsamp'],jsoncuts=kwargs['jsoncuts'],weight=[[''],['']],KFWght=KFWght,trigequal=kwargs['trigequal'])
				es = '('+es[1:]
				est += es + ' && '
			if 'trigger' in cuts['sel'][k].keys():
				subtrg = [y[1] for x,y in cuts['sel'][k].iteritems() if x=='trigger']
				et, etlabels = write_cuts(['None'],subtrg,[],[],sample=sample,jsonsamp=kwargs['jsonsamp'],jsoncuts=kwargs['jsoncuts'],weight=[[''],['']],KFWght=KFWght,trigequal=kwargs['trigequal'])
				et = '('+et[1:]
				est += et + ' && '
	if not est=='': est = group("!"+group(est.rstrip(' && ')))

	# edit weights if needed
	wfString = ''
	if not weight == [[''],['']]:
		parsedWeight = dc(weight)
		if (trg==[]) and (len(weight)>1) and (('MAP' in [x[:3] for x in weight[1]]) or ('FUN' in [x[:3] for x in weight[1]]) or ('COR' in [x[:3] for x in weight[1]])): parsedWeight[1] = [x for x in weight[1] if not (x[:3]=='MAP' or x[:3]=='FUN' or x[:3]=='COR')] 
		wf = weightFactory(kwargs['jsonsamp'],weight[0][0],KFWght) 
		wfString = wf.getFormula(','.join(parsedWeight[1]),kwargs['sample']) if len(weight)>1 else wf.getFormula('',kwargs['sample'])

	# construct
	if not (selold==[] and trgold==[]):
		if not stgroup:
			# selection
			#out# print [[k for (k,v) in selections[si].iteritems()] for si in sel]
			s      = group( seljoin.join( [ group( ' && '.join([ ' && '.join([k+v[2*ind]+v[2*ind+1] for ind in range(len(v)/2)]) for k,v in sorted(selections[si].iteritems(), key=lambda(x,y):x) if not ((k in varskip) or (k.replace("mqq[2]","mjjTrig") in varskip) or (k.replace("dEtaqq[2]","dEtaTrig") in varskip) or (k.replace("mjjTrig","mqq[2]") in varskip) or (k.replace("dEtaTrig","dEtaqq[2]") in varskip) or (k=='selection' or k=='trigger')) ]) ) for si in sorted(sel)] + extra ) ).replace(' && ()','').replace('() &&','')
			scmp   = group( selcmpjoin.join( [ group("! "+group( ' && '.join([ ' && '.join([k+v[2*ind]+v[2*ind+1] for ind in range(len(v)/2)]) for k,v in sorted(selections.iteritems(), key=lambda(x,y):x) if not ((k in varskip)  or (k.replace("mqq[2]","mjjTrig") in varskip) or (k.replace("dEtaqq[2]","dEtaTrig") in varskip) or (k.replace("mjjTrig","mqq[2]") in varskip) or (k.replace("dEtaTrig","dEtaqq[2]") in varskip)) ]) )) for si in selcmp ] ) )
			if s=='()' : s='(1.)'
			# trigger
			t      = group( trgjoin.join( [ get_trigger(triggers[x],kwargs['sample'],kwargs['jsonsamp'],trigequal) for x in trg ] ) )
			tcmp   = group( trgcmpjoin.join( [ group("! "+get_trigger(triggers[x],kwargs['sample'],kwargs['jsonsamp'],trigequal)) for x in trgcmp ] ) )
			if t=='()' : t='(1.)'
	
			# selection labels
			slabels      = group( seljoin.join( [ 's'+x for x in (sel if not sel==[] else selold) ] + ['s'+x for x in extra] ) )
			scmplabels   = group( selcmpjoin.join( [ group('! s'+x) for x in selcmp ] ) )
			# trigger labels
			tlabels      = group( trgjoin.join( [ 't'+x for x in (trg if not trg==[] else trgold) ] ) )
			tcmplabels   = group( trgcmpjoin.join( [ group('! t'+x) for x in trgcmp ] ) )
	
			# combo
			st = group(' && '.join([x for x in [s,scmp,t,tcmp] if not (x=="()" or x=='(1.)')]))
			stlabels = group(' && '.join([x for x in [slabels,scmplabels,tlabels,tcmplabels] if not x=="()"]))
			if st=='()': st='(1.)'
	
		else:
			st        = group( seljoin.join( [ group( ' && '.join([ ' && '.join([k+v[2*ind]+v[2*ind+1] for ind in range(len(v)/2)]) for k,v in sorted(selections.iteritems(), key=lambda(x,y):x) if not ((k in varskip) or k=='selection' or k=='trigger' or (k.replace("mqq[2]","mjjTrig") in varskip) or (k.replace("dEtaqq[2]","dEtaTrig") in varskip) or (k.replace("mjjTrig","mqq[2]") in varskip) or (k.replace("dEtaTrig","dEtaqq[2]") in varskip) ) ]+[get_trigger(triggers,kwargs['sample'],kwargs['jsonsamp'],trigequal)]) ) for si in (sel if not sel==[] else selold) ] ) )
			stlabels  = group( seljoin.join( [ group('s'+x+' && t'+x) for x in (sel if not sel==[] else selold) ] ) )
	
		# reftrig
		if len(reftrig)>0:
			rt       = group( ' && '.join( [ get_trigger(triggers[x],kwargs['sample'],kwargs['jsonsamp'],trigequal) for x in reftrig ] ) )
			rtlabels = group( ' && '.join( [ 'r'+x for x in reftrig ] ) )
			if rt=='(())' : rt='(1.)'
			st       = group( st + ' && ' + rt ) 
			stlabels = group( stlabels + ' && ' + rtlabels ) 

		# extra selection (from veto)
		if not est == '':
			st = group( st + ' && ' + est )


	# when only None for sel/trg
	else:
		st=group("1.")
		stlabels=group("1.")
	
	if not weight == [[''],['']]:
		st = group("%s * %s"%(st,group(wfString)))
		stlabels = group("%s * %s"%(stlabels,group('weight factors')))
	
	if st.replace('(','').replace(')','').replace(' ','') == "":
		st=group("1.")
		stlabels=group("1.")

	return st,stlabels





####################################################################################################
if __name__=='__main__':
	mp = parser(main.parser())
	opts,args = mp.parse_args()

	for sel in opts.selection:
		for trg in opts.trigger:
			for ref in opts.reftrig:
				st, stlabels = write_cuts(sel,trg,opts.selcmp,opts.trgcmp,reftrig=ref,jsoncuts=opts.jsoncuts,sample=opts.use,jsonsamp=opts.jsonsamp,seljoin=opts.seljoin,trgjoin=opts.trgjoin,varskip=opts.skip,selcmpjoin=opts.selcmpjoin,trgcmpjoin=opts.trgcmpjoin,stgroup=opts.stgroup,weight=opts.weight,trigequal=trigTruth(opts.usebool))
	print st
	print
	print stlabels
	print
