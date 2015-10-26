#!/usr/bin/env python

import sys,os,re,json,datetime
basepath=os.path.split(os.path.abspath(__file__))[0]
sys.path.append(basepath)

from optparse import OptionParser
from toolkit import *

today = datetime.date.today().strftime('%Y%m%d')






####################################################################################################
def parser():
	mp = OptionParser()
	mp.add_option('-i','--input',help='Name of json file containing cross section, tagging and colour info.',dest='input',type='str',default='%s/vbfHbb_cuts_%s'%(basepath,today))
	mp.add_option('-r','--readonly',help='Just print out content.',action='store_true',default=True)
	mp.add_option('-u','--update',help='Update content.',action='store_true',default=False)
	return mp 
	




#####1###############################################################################################
class info:
	def __init__(self,iname):
		self.fname = iname
		self.content = json.loads(filecontent(self.fname))#,encoding='utf-8')
		self.crosssections = self.content['crosssections']
		self.tags = self.content['tags']
	##########	
	def _print(self):
		l1("Printing content for %s"%self.fname)
		l2("cross sections and tags:")
		print "%s%25s | %25s | %15s | %60s%s"%(cyan,"name","group","cross section","possible tags",plain)
		print "%s"%cyan+"-"*134+"%s"%plain
		for sample in sorted(self.crosssections.keys()):
			print "%25s | %25s | %15s | %60s"%(sample,self.content['groups'][sample], self.crosssections[sample],', '.join([str(x) for x in self.tags[sample]]))
	##########	
	def _update(self):
		l1("Updating content for %s"%self.fname)
		if not raw_input("  ++ cross sections? [Y(es)/s(kip)] ")=="s":
			for sample in sorted(self.crosssections.keys()): 
				new_value = raw_input('%s: cross section? [%s] '%(sample,self.crosssections[sample]))
				if not new_value == "": self.crosssections[sample]=float(new_value)
		if not raw_input("  ++ tags? [Y(es)/s(kip)] ")=="s":
			for tag in sorted(self.tags.keys()): 
				new_value = raw_input('%s: tags? [%s] '%(tag,','.join([str(x) for x in self.tags[tag]])))
				if not new_value == "": self.tags[tag]=new_value.split(',')
		f = file(self.fname,'w+')
		f.write(json.dumps(self.content))
		f.close()
			




####################################################################################################
if __name__=='__main__':
	mp = parser()
	opts,args = mp.parse_args()

	myinfo = info(opts.input)
	if opts.readonly and not opts.update:
		myinfo._print()
	if opts.update:
		myinfo._update()
		myinfo._print()
