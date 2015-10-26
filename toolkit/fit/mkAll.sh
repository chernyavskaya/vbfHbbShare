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

###   OPTIONS
###   
options="\n
   ./mkAll.sh RUNOPT WORKDIR\n\n
   RUNOPTS:\n\n
   0\tall\n
	\n
	0A\tall workspace preparation 1-5 (not 6)\n
   1\tmkTransferFunctions\n
   2\tmkBkgTemplates\n
   3\tmkSigTemplates\n
   4\tmkDataTemplates\n
   5\tmkDatacards\n
	6\tmkDatacards (CATvetoes)\n
	\n
	1A\tall limit calculations 10-16 (not 17)\n
	10\tmkToys\n
	11\tmkAsymptotic limits\n
	12\tmkAsymptotic limits (vetoes)\n
	13\tmkAsymptotic limits (injected)\n
	14\tmkMaxLikelihoodFit\n
	15\tmkProfileLikelihoodExp\n
	16\tmkProfileLikelihoodObs\n
	17\tmkNuisances\n
	18\tmkMultiDimFit\n
	\n
	2A\tall plots (20-22)\n
	20\tplot asymptotic limit\n
	21\tplot mass spectra fits\n
	22\tplot nuisances\n
"
###
###

### PARSE
if [[ $# > 1 ]]; then ACTION="$1"; shift; fi
if [[ $# < 2 ]] && [[ ! ( $1 == "-h" || $1 == "--help" ) ]]; then echo -e $options; fi
while [[ $# > 0 ]]; do
key="$1"
case $key in
	-h|--help) echo -e $options;;
	-m|--mass) MASS="$2"; shift;;	
	-w|--workdir) WORKDIR="$2"; shift;;
	-t|--transfer) TRANSFER="$2"; shift;;
    *) echo -e "!! unknown option setup !!";;
esac
shift 
done

### DEFAULTS
if [ ! $WORKDIR ]; then WORKDIR="case0"; fi
if [ ! $MASS ]; then MASS="115,120,125,130,135"; fi
if [ ! $TRANSFER ]; then TRANSFER="POL1,POL2"; fi
if [ ! $ACTION ]; then ACTION=""; fi

##################################################
if [ "${ACTION}" == "0" ] || [ "${ACTION}" == "0A" ] || [ "${ACTION}" == "1" ];then
	cmd="./src/mkTransferFunctions.py --workdir ${WORKDIR} --long --TF ${TRANSFER}"
	echo ${cmd}
	eval ${cmd} | grep -v "Developed by Wouter" | grep -v "Copyright (C)" | grep -v "All rights reserved" | grep -v "^$"
fi
##################################################
if [ "${ACTION}" == "0" ] || [ "${ACTION}" == "0A" ] || [ "${ACTION}" == "2" ];then
	cmd="./src/mkBkgTemplates.py --workdir ${WORKDIR} --long"
	echo ${cmd}
	eval ${cmd} | grep -v "Developed by Wouter" | grep -v "Copyright (C)" | grep -v "All rights reserved" | grep -v "^$" | grep -v "setting parameter"
fi
##################################################
if [ "${ACTION}" == "0" ] || [ "${ACTION}" == "0A" ] || [ "${ACTION}" == "3" ];then
	cmd="./src/mkSigTemplates.py --workdir ${WORKDIR} --long"
	echo ${cmd}
	eval ${cmd} | grep -v "Developed by Wouter" | grep -v "Copyright (C)" | grep -v "All rights reserved" | grep -v "^$"
fi
##################################################
if [ "${ACTION}" == "0" ] || [ "${ACTION}" == "0A" ] || [ "${ACTION}" == "4" ];then
	cmd="./src/mkDataTemplates.py --workdir ${WORKDIR} --long --TF ${TRANSFER}"
	echo ${cmd}
	eval ${cmd} | grep -v "Developed by Wouter" | grep -v "Copyright (C)" | grep -v "All rights reserved" | grep -v "^$"
fi
##################################################
if [ "${ACTION}" == "0" ] || [ "${ACTION}" == "0A" ] || [ "${ACTION}" == "5" ];then
	cmd="./src/mkDatacards.py --workdir ${WORKDIR} --long --TF ${TRANSFER}"
	echo ${cmd}
	eval ${cmd} | grep -v "Developed by Wouter" | grep -v "Copyright (C)" | grep -v "All rights reserved" | grep -v "^$"
fi
##################################################
if [ "${ACTION}" == "0" ] || [ "${ACTION}" == "6" ];then
	for c in "1" "2" "3" "5" "6" "4,5,6" "0,1,2,3"; do
		cmd="./src/mkDatacards.py --workdir ${WORKDIR} --long --TF ${TRANSFER} --CATveto $c"
		echo ${cmd}
		eval ${cmd} | grep -v "Developed by Wouter" | grep -v "Copyright (C)" | grep -v "All rights reserved" | grep -v "^$"
	done
fi
##################################################
##################################################
##################################################
if [ "${ACTION}" == "0" ] || [ "${ACTION}" == "1A" ] || [ "${ACTION}" == "10" ];then
	cmd="./src/mkLimit.py -t GenerateOnly -m 125 -n vbfHbb --long --workdir ${WORKDIR}"
	echo ${cmd}
	eval ${cmd}
fi
##################################################
if [ "${ACTION}" == "0" ] || [ "${ACTION}" == "1A" ] || [ "${ACTION}" == "11" ];then
	cmd="./src/mkLimit.py -t Asymptotic -m ${MASS} -n vbfHbb --long --workdir ${WORKDIR}"
	echo ${cmd}
	eval ${cmd}
fi
##################################################
if [ "${ACTION}" == "0" ] || [ "${ACTION}" == "1A" ] || [ "${ACTION}" == "12" ];then
	for c in "1" "2" "3" "5" "6" "4,5,6" "0,1,2,3"; do
		cmd="./src/mkLimit.py -t Asymptotic -m 125 -n vbfHbb --long --workdir ${WORKDIR} -V $c"
		echo ${cmd}
		eval ${cmd} 
	done
fi
##################################################
if [ "${ACTION}" == "0" ] || [ "${ACTION}" == "1A" ] || [ "${ACTION}" == "13" ];then
	finj=`ls -m ${WORKDIR}/combine/higgsCombine*GenerateOnly*125*root | xargs basename`
	cmd="./src/mkLimit.py -t Injected -m ${MASS} -n vbfHbb.Injected -e '--toysFile ${finj}' --long --workdir ${WORKDIR}"
	echo ${cmd}
	eval ${cmd}
fi
##################################################
if [ "${ACTION}" == "0" ] || [ "${ACTION}" == "1A" ] || [ "${ACTION}" == "14" ];then
	cmd="./src/mkLimit.py -t MaxLikelihoodFit -m ${MASS} -n vbfHbb --long --workdir ${WORKDIR}"
	echo ${cmd}
	eval ${cmd}
	rm ${WORKDIR}/combine/{CAT*,covariance*}.png
fi
##################################################
if [ "${ACTION}" == "0" ] || [ "${ACTION}" == "1A" ] || [ "${ACTION}" == "15" ];then
	cmd="./src/mkLimit.py -t ProfileLikelihoodExp -m ${MASS} -n vbfHbb --long --workdir ${WORKDIR}"
	echo ${cmd}
	eval ${cmd}
fi
##################################################
if [ "${ACTION}" == "0" ] || [ "${ACTION}" == "1A" ] || [ "${ACTION}" == "16" ];then
	cmd="./src/mkLimit.py -t ProfileLikelihoodObs -m ${MASS} -n vbfHbb --long --workdir ${WORKDIR}"
	echo ${cmd}
	eval ${cmd}
fi
##################################################
if [ "${ACTION}" == "0" ] || [ "${ACTION}" == "17" ];then
	for mass in ${MASS}; do 
		fname=`ls ${WORKDIR}/combine/mlfit*${mass}.root`
		fname=${fname%.*}
		cmd="./src/mkNuisances.py -a -f text ${fname}.root -g ${fname//mlfit/pulls}.root > ${fname//mlfit/nuissances}.txt"
		echo ${cmd}
		eval ${cmd}
	done
fi
##################################################
if [ "${ACTION}" == "0" ] || [ "${ACTION}" == "18" ];then
	cmd="./src/mkLimit.py -t MultiDimFit -m ${MASS} -n vbfHbb --long --workdir ${WORKDIR}"
	echo ${cmd}
	eval ${cmd}
fi
##################################################
##################################################
##################################################
if [ "${ACTION}" == "0" ] || [ "${ACTION}" == "2A" ] || [ "${ACTION}" == "20" ];then
	flist=`ls -m ${WORKDIR}/combine/higgsCombine*{Asymptotic,Profile,MaxLik}*root | grep -v CATveto | tr -d '\n' | sed "s#,# #g"`
	cmd="./src/ptLimit.py -t vbfHbb --long --workdir ${WORKDIR} ${flist}"
	echo ${cmd}
	eval ${cmd}
fi
##################################################
if [ "${ACTION}" == "0" ] || [ "${ACTION}" == "2A" ] || [ "${ACTION}" == "21" ];then
	for f in `ls ${WORKDIR}/datacards/*.txt | grep -v CATveto`; do
		[ ! -f ${f%.*}.root ] && text2workspace.py $f -o ${f%.*}.root
	done
	olddir=`pwd`
	cd ${WORKDIR}
	echo -e "\033[1;31mFilename hardcoded, be careful.\033[m"
	for mass in ${MASS}; do
		cmd="root -l ../src/ptBestFit.C'(2.5,0,\"$mass\",\"B80-200_BRN5-4_TFPOL1-POL2\")' -q"
		echo ${cmd}
		eval ${cmd}
	done
	cd ${olddir}
fi
##################################################
if [ "${ACTION}" == "0" ] || [ "${ACTION}" == "2A" ] || [ "${ACTION}" == "22" ];then
	olddir=`pwd`
	cd ${WORKDIR}
	echo -e "\033[1;31mFilename hardcoded, be careful.\033[m"
	for mass in ${MASS}; do
		cmd="../src/ptNuisances.py .vbfHbb_B80-200_BRN5-4_TFPOL1-POL2 ${mass}"
		echo ${cmd}
		eval ${cmd}
	done
	cd ${olddir}
fi
##################################################
