#!/bin/sh

basepath="."

defaultopts="$basepath/../common/vbfHbb_defaultOpts_2013.json"
if [[ "`uname -a`" == *lxplus* ]]; then
	globalpath="~/eosaccess/cms/store/cmst3/group/vbfhbb/flat/"
	globalpathtrigger="~/eosaccess/cms/store/cmst3/group/vbfhbb/flat/trigger"
fi

variablesslim="$basepath/../../common/vbfHbb_variables_2013_bareslim.json"
globalpathskimslim="$basepath/fitforflat"
samples="VBF,GluGlu,Data,T,WJets,ZJets,QCD"
#samples="Data"

preselNOM="sNOM;nLeptons"
preselVBF="sVBF;nLeptons;sNOMveto"

NOweight="1."

##################################################
# NOM FitFlatTrees
python $basepath/src/mkFitFlatTrees.py -d -D "$defaultopts" -G "$globalpath" --destination "${globalpathskimslim}/" -t "NOM" --datatrigger "NOM" -p "$preselNOM" -s "$samples" -w "$NOweight" --usebool 
	
# VBF FitFlatTrees
python $basepath/src/mkFitFlatTrees.py -d -D "$defaultopts" -G "$globalpath" --destination "${globalpathskimslim}/" -t "VBF" --datatrigger "VBF" -p "$preselVBF" -s "$samples" -w "$NOweight" --usebool

if [ ! -d ${globalpathskimslim}/dataSeparate ]; then mkdir ${globalpathskimslim}/dataSeparate; fi
if [ ! -f ${globalpathskimslim}/Fit_MultiJetA_selNOM.root ]; then mv ${globalpathskimslim}/dataSeparate/Fit_{MultiJet,BJetPlusX,VBF1Parked}*.root ${globalpathskimslim}/; fi

if [ -f "${globalpathskimslim}/Fit_data_selNOM.root" ]; then mv ${globalpathskimslim}/Fit_data_selNOM.root ${globalpathskimslim}/dataSeparate/Fit_data_selNOM.root.backup; fi
hadd ${globalpathskimslim}/Fit_data_selNOM.root ${globalpathskimslim}/Fit_{MultiJet,BJetPlusX}*_selNOM.root
mv ${globalpathskimslim}/Fit_{MultiJet,BJetPlusX}*_selNOM.root ${globalpathskimslim}/dataSeparate/

if [ -f "${globalpathskimslim}/Fit_data_selVBF.root" ]; then mv ${globalpathskimslim}/Fit_data_selVBF.root ${globalpathskimslim}/dataSeparate/Fit_data_selVBF.root.backup; fi
hadd ${globalpathskimslim}/Fit_data_selVBF.root ${globalpathskimslim}/Fit_VBF1Parked*_selVBF.root
mv ${globalpathskimslim}/Fit_VBF1Parked*_selVBF.root ${globalpathskimslim}/dataSeparate/

