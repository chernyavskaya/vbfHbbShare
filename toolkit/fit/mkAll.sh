#!/bin/sh

if [ "$(basename `pwd`)" == "fit" ]; then 
	basepath="."
else 
	basepath="fit"
fi

defaultopts="$basepath/../common/vbfHbb_defaultOpts_2013.json"
if [[ "`uname -a`" == *lxplus* ]]; then
	globalpath="~/eosaccess/cms/store/cmst3/group/vbfhbb/flat/"
elif [[ "`uname -a`" == *schrodinger* ]]; then
	globalpath="$basepath/../largefiles/"
fi

if [ ${#@} -gt 1 ]; then
	workdir=$2
else
	workdir=case0
fi

###   OPTIONS
###   
options="\n
   ./mkAll.sh RUNOPT WORKDIR\n\n
   RUNOPTS:\n\n
   0\tall\n
	\n
	0A\tall workspace preparation 1-5\n
   1\tmkTransferFunctions\n
   2\tmkBkgTemplates\n
   3\tmkSigTemplates\n
   4\tmkDataTemplates\n
   5\tmkDatacards\n
	\n
	1A\tall limit calculations 10-16 (not 17)\n
	10\tmkToys\n
	11\tmkAsymptotic limits\n
	12\tmkAsymptotic limits (injected)\n
	13\tmkMaxLikelihoodFit\n
	14\tmkProfileLikelihoodExp\n
	15\tmkProfileLikelihoodObs\n
	16\tmkNuisances\n
	17\tmkAsymptotic (CATvetoes) limits\n
	\n
	2A\tall plots (20-22)\n
	20\tplot asymptotic limit\n
	21\tplot mass spectra fits\n
	22\tplot nuisances\n
"
###
###

notext=""
## turning on/off legends
#if [ "$3" == "0" ]; then 
#	notext="--notext"
#else
#	notext=""
#fi

# OPTION OPTION OPTIONS ##########################
TF=POL1,POL2
#TF=AltPOL1,AltPOL2

##################################################


if [ "$1" == "-h" ] || [ "$1" == "--help" ]; then
	echo -e $options
fi

##################################################
#for i in `seq 0 1`; do
#	if [ "$notext" == "" ] && [ "$i" == "0" ]; then continue; fi
##################################################
if [ "$1" == "0" ] || [ "$1" == "0A" ] || [ "$1" == "1" ];then
	cmd="./src/mkTransferFunctions.py --workdir ${workdir} --long --TF ${TF}"
	echo ${cmd}
	eval ${cmd} | grep -v "Developed by Wouter" | grep -v "Copyright (C)" | grep -v "All rights reserved" | grep -v "^$"
fi
##################################################
if [ "$1" == "0" ] || [ "$1" == "0A" ] || [ "$1" == "2" ];then
	cmd="./src/mkBkgTemplates.py --workdir ${workdir} --long"
	echo ${cmd}
	eval ${cmd} | grep -v "Developed by Wouter" | grep -v "Copyright (C)" | grep -v "All rights reserved" | grep -v "^$" | grep -v "setting parameter"
fi
##################################################
if [ "$1" == "0" ] || [ "$1" == "0A" ] || [ "$1" == "3" ];then
	cmd="./src/mkSigTemplates.py --workdir ${workdir} --long"
	echo ${cmd}
	eval ${cmd} | grep -v "Developed by Wouter" | grep -v "Copyright (C)" | grep -v "All rights reserved" | grep -v "^$"
fi
##################################################
if [ "$1" == "0" ] || [ "$1" == "0A" ] || [ "$1" == "4" ];then
	cmd="./src/mkDataTemplates.py --workdir ${workdir} --long --TF ${TF}"
	echo ${cmd}
	eval ${cmd} | grep -v "Developed by Wouter" | grep -v "Copyright (C)" | grep -v "All rights reserved" | grep -v "^$"
fi
##################################################
if [ "$1" == "0" ] || [ "$1" == "0A" ] || [ "$1" == "5" ];then
	cmd="./src/mkDatacards.py --workdir ${workdir} --long --TF ${TF}"
	echo ${cmd}
	eval ${cmd} | grep -v "Developed by Wouter" | grep -v "Copyright (C)" | grep -v "All rights reserved" | grep -v "^$"
	for c in "1" "2" "3" "5" "6" "4,5,6" "0,1,2,3"; do
		cmd="./src/mkDatacards.py --workdir ${workdir} --long --TF ${TF} --CATveto $c"
		echo ${cmd}
		eval ${cmd} | grep -v "Developed by Wouter" | grep -v "Copyright (C)" | grep -v "All rights reserved" | grep -v "^$"
	done
fi
##################################################
##################################################
##################################################
if [ "$1" == "0" ] || [ "$1" == "1A" ] || [ "$1" == "10" ];then
	cmd="./src/mkLimit.py -t GenerateOnly -m 115,120,125,130,135 -n vbfHbb --long --workdir ${workdir}"
	echo ${cmd}
	eval ${cmd}
fi
##################################################
if [ "$1" == "0" ] || [ "$1" == "1A" ] || [ "$1" == "11" ];then
	cmd="./src/mkLimit.py -t Asymptotic -m 115,120,125,130,135 -n vbfHbb --long --workdir ${workdir}"
	echo ${cmd}
	eval ${cmd}
fi
##################################################
if [ "$1" == "0" ] || [ "$1" == "1A" ] || [ "$1" == "12" ];then
	for c in "1" "2" "3" "5" "6" "4,5,6" "0,1,2,3"; do
		cmd="./src/mkLimit.py -t Asymptotic -m 125 -n vbfHbb --long --workdir ${workdir} -V $c"
		echo ${cmd}
		eval ${cmd} 
	done
fi
##################################################
if [ "$1" == "0" ] || [ "$1" == "1A" ] || [ "$1" == "13" ];then
	cmd='./src/mkLimit.py -t Injected -m 115,120,125,130,135 -n vbfHbb.Injected -e "--toysFile higgsCombine.vbfHbb.GenerateOnly.mH125.123456.root" --long --workdir ${workdir}'
	echo ${cmd}
	eval ${cmd}
fi
##################################################
if [ "$1" == "0" ] || [ "$1" == "1A" ] || [ "$1" == "14" ];then
	cmd="./src/mkLimit.py -t MaxLikelihoodFit -m 115,120,125,130,135 -n vbfHbb --long --workdir ${workdir}"
	echo ${cmd}
	eval ${cmd}
	rm ${workdir}/combine/{CAT*,covariance*}.png
fi
##################################################
if [ "$1" == "0" ] || [ "$1" == "1A" ] || [ "$1" == "15" ];then
	cmd="./src/mkLimit.py -t ProfileLikelihoodExp -m 115,120,125,130,135 -n vbfHbb --long --workdir ${workdir}"
	echo ${cmd}
	eval ${cmd}
fi
##################################################
if [ "$1" == "0" ] || [ "$1" == "1A" ] || [ "$1" == "16" ];then
	cmd="./src/mkLimit.py -t ProfileLikelihoodObs -m 135 -n vbfHbb --long --workdir ${workdir}"
	echo ${cmd}
	eval ${cmd}
fi
##################################################
if [ "$1" == "0" ] || [ "$1" == "17" ];then
	for mass in 115 120 125 130 135; do 
		fname=`ls ${workdir}/combine/mlfit*${mass}.root`
		fname=${fname%.*}
		cmd="./src/mkNuisances.py -a -f text ${fname}.root -g ${fname//mlfit/pulls}.root > ${fname//mlfit/nuissances}.txt"
		echo ${cmd}
		eval ${cmd}
	done
fi
##################################################
##################################################
##################################################
if [ "$1" == "0" ] || [ "$1" == "2A" ] || [ "$1" == "20" ];then
	flist=`ls -m ${workdir}/combine/higgsCombine*{Asymptotic,Profile,MaxLik}*root | grep -v CATveto | tr -d '\n' | sed "s#,# #g"`
	cmd="./src/ptLimit.py -t vbfHbb --long --workdir ${workdir} ${flist}"
	echo ${cmd}
	eval ${cmd}
fi
##################################################
if [ "$1" == "0" ] || [ "$1" == "2A" ] || [ "$1" == "21" ];then
	for f in `ls ${workdir}/datacards/*.txt | grep -v CATveto`; do
		[ ! -f ${f%.*}.root ] && text2workspace.py $f -o ${f%.*}.root
	done
	olddir=`pwd`
	cd ${workdir}
	echo -e "\033[1;31mFilename hardcoded, be careful.\033[m"
	for mass in 115 120 125 130 135; do
		cmd="root -l ../src/ptBestFit.C'(2.5,0,\"$mass\",\"B80-200_BRN5-4_TFPOL1-POL2\")' -q"
		echo ${cmd}
		eval ${cmd}
	done
	cd ${olddir}
fi
##################################################
if [ "$1" == "0" ] || [ "$1" == "2A" ] || [ "$1" == "22" ];then
	olddir=`pwd`
	cd ${workdir}
	echo -e "\033[1;31mFilename hardcoded, be careful.\033[m"
	for mass in 115 120 125 130 135; do
		cmd="../src/ptNuisances.py .vbfHbb_B80-200_BRN5-4_TFPOL1-POL2 ${mass}"
		echo ${cmd}
		eval ${cmd}
	done
	cd ${olddir}
fi
##################################################
#notext=""
#done
