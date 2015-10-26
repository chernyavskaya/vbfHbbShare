#!/usr/bin/env python

from optparse import OptionParser
import datetime,sys,os,re,json
basepath=os.path.split(os.path.abspath(__file__))[0]
sys.path.append(basepath)

tempargv = sys.argv[:]
sys.argv = []
import ROOT
from ROOT import *
sys.argv = tempargv 

from toolkit import * 

today = datetime.date.today().strftime('%Y%m%d')

class info:
	def __init__(self,oname):
		self.oname = oname
		self.content = {}
		self.content['variables'] = {}
		self.content['fields'] = ['var','root','bare','title','title_x','title_y','nbins_x','xmin','xmax','nbins_y','ymin','ymax']
		self.read_info()

	def print_info(self):
		l1("Printing content for %s"%self.oname)
		l2("variables:")
		if not len(self.content['variables'])==0: 
			for field in self.content['fields']: print "%s%14s | %s"%(cyan,field,plain),
			print
			print '-'*(18*len(self.content['fields']))
		for k,v in sorted(self.content['variables'].iteritems()):
			for field in self.content['fields']:
				print "%14s | "%(v[field] if len(v[field])<14 else v[field][0:10]+"..."),
			print

	def read_info(self):
		l1("Reading %s"%self.oname)
		if os.path.exists(self.oname):
			self.content = json.loads(filecontent(self.oname))
		else: l2("%s will be a new file."%self.oname)
	
	def clean_info(self):
		l1("Cleaning content for %s"%self.oname)
		for k in sorted(self.content['variables'].keys()):
			keep = False if raw_input("Keep %s? [(y)/n] "%k)=='n' else True
			if not keep: del self.content['variables'][k]
		self.print_info()
		self.write_info()

	def update_info_y(self):
		l1("Updating content for %s"%self.oname)
		for k,v in sorted(self.content['variables'].iteritems()):
			# update title_y
			title_y_new = 'N / %.2f'%((float(v['xmax'])-float(v['xmin']))/float(v['nbins_x']))
			v['title_y'] = title_y_new

	def update_info(self,var):
		l1("Updating content for %s"%self.oname)
		for k,v in sorted(self.content['variables'].iteritems()):
			if (not var=='') and (not k==var): continue
			update = True if str(raw_input("Update %s? [y/(n)] "%k))=="y" else False
			if not update: continue
			else: 
				l2("Updating %s:"%k)
				for field in self.content['fields'][1:]:
					if field=='title_y':
						field_new = 'N / %.2f'%((float(self.content['variables'][k]['xmax'])-float(self.content['variables'][k]['xmin']))/float(self.content['variables'][k]['nbins_x']))
					elif field=='bare':
						field_new = ','.join(re.findall('[A-Za-z0-9]{2,}',v['root']))
						print "bare: ",field_new
					else:
						field_new = str(raw_input("    %s? [%s] "%(field,self.content['variables'][k][field])))
					if not field_new=="": self.content['variables'][k][field] = field_new
				# update title_y
				title_y_new = 'N / %.2f'%((float(v['xmax'])-float(v['xmin']))/float(v['nbins_x']))
				v['title_y'] = title_y_new

	def add_info(self,passed_content):
		fields = []
		if type(passed_content)==str: 
			fields.append(passed_content)
			if not fields[0] in self.content['variables']:
				l2("Adding %s:"%passed_content)
				for field in self.content['fields'][1:]: 
					if field=='bare': 
						field_new = ','.join(re.findall('[A-Za-z0-9]{2,}',fields[1]))
						print "      %s: %s"%(field,field_new)
					elif field=='title_y':
						field_new = 'N / bin' 
						print "      %s: %s"%(field,field_new)
					else:
						field_new = str(raw_input("      %s? "%(field)))
					fields.append(field_new if not field_new=="" else "-")
				# update title_y
				title_y_new = 'N / %.2f'%((float(fields[self.content['fields'].index('xmax')])-float(fields[self.content['fields'].index('xmin')]))/float(fields[self.content['fields'].index('nbins_x')]))
				fields[self.content['fields'].index('title_y')] = title_y_new
		elif type(passed_content)==list: 
			fields=passed_content
			if not fields[0] in self.content['variables']: l2("Adding %s:"%fields[0])
		else: l2(yellow+"Unknown passed content. Skipping."+plain)
		#
		if not fields[0] in self.content['variables']:
			self.content['variables'][fields[0]] = {}
			for ifield,field in enumerate(self.content['fields']):
				self.content['variables'][fields[0]][field] = fields[ifield]
		elif fields[0] in self.content['variables']: l2("%s%s already in dict. Skipping.%s"%(yellow,fields[0],plain))

	def write_info(self):
		l1("Writing content for %s"%self.oname)
		f = file(self.oname,'w+')	# overwrite
		f.write(json.dumps(self.content))
		f.close()



def parser():
	mp = OptionParser()
	mp.add_option('-o','--output',help='Output file name (including prefix).',dest='output',type='str',default='%s/vbfHbb_variables_%s.json'%(basepath,today))
	mp.add_option('-a','--add',help='Add content to the file.',action='store_true',default=False)
	mp.add_option('-r','--readonly',help='Print content of output file.',action='store_true',default=False)
	mp.add_option('-c','--clean',help='Clean json file (remove existing variables).',dest='clean',action='store_true',default=False)
	mp.add_option('-u','--update',help='Update json file (edit existing variables).',dest='update',type='str',default='')
	mp.add_option('-y','--updatey',help='Update json file (edit existing variables)(auto y-axis label update).',dest='updatey',action='store_true',default=False)
	return mp



if __name__=='__main__':
	mp = parser()
	opts,args = mp.parse_args()

	if sum([(1 if x else 0) for x in [opts.add, opts.readonly, opts.clean, opts.update]]) > 1:
		print "%sConflicting opts. Never combine add, readonly, clean and update. Use one at a time. Exiting.%s"%(Red,plain)
		sys.exit()

	myinfo = info(opts.output)
	myinfo.print_info()

	if opts.clean and not (opts.readonly or opts.update or opts.add or opts.updatey):
		myinfo.clean_info()
	
	if opts.update and not (opts.readonly or opts.clean or opts.add or opts.updatey):
		myinfo.update_info(opts.update)
		myinfo.print_info()
		myinfo.write_info()

	if opts.updatey and not (opts.readonly or opts.clean or opts.add or opts.update):
		myinfo.update_info_y()
		myinfo.print_info()
		myinfo.write_info()

	if opts.add and not (opts.clean or opts.update or opts.readonly or opts.updatey):
		var = str(raw_input("var? [varname] "))
		while not var == "":
			myinfo.add_info(var)
			var = str(raw_input("var? [varname] ")) 
		myinfo.print_info()
		myinfo.write_info()
