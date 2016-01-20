#include <ctype.h>
#include <iomanip>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <cstdlib>
#include "TFile.h"
#include "TH1.h"
#include "TH1F.h"
#include "TH2.h"
#include "TTree.h"
#include "TChain.h"
#include <vector>
#include <iostream>
#include <fstream>
#include <cstdio>
#include <TROOT.h>
#include <TString.h>
#include <TStyle.h>
#include <TSystem.h>
#include <TCanvas.h>
#include <TMarker.h>
#include <THStack.h>
#include <TLegend.h>
#include <TLatex.h>
#include <TCut.h>
#include <TGraph.h>
#include <TGraphErrors.h>
#include <TLorentzVector.h>
#include <TMath.h>
#include <TF1.h>
#include "/afs/cern.ch/work/n/nchernya/Hbb/preselection_double_csv.C"
#include "/afs/cern.ch/work/n/nchernya/Hbb/preselection_single.C"
#include "/afs/cern.ch/work/n/nchernya/Hbb/preselection_single_blike.C"

Double_t erf( Double_t *x, Double_t *par){
  return par[0]/2.*(1.+TMath::Erf((x[0]-par[1])/par[2]));
}
Double_t erf2( Double_t *x, Double_t *par){
  return par[0]/2.*(1.+TMath::Erf((x[0]-par[1])/par[2]))+ (1.-par[0]);
}

#define SWAP2(A, B) { TLorentzVector t = A; A = B; B = t; }
void SortByEta(std::vector<TLorentzVector> &jets){
  int i, j;
	int n=jets.size();
  for (i = n - 1; i >= 0; i--){
    for (j = 0; j < i; j++){
      if (jets[j].Eta() < jets[j + 1].Eta() ){
        SWAP2( jets[j], jets[j + 1] );
		}
    }
	}
}

typedef std::map<double, int> JetList;
const int njets = 300;

typedef struct {
   Float_t eta[njets];
   Float_t pt[njets];
   Float_t phi[njets];
	Float_t mass[njets];
	Float_t btag[njets];
	Int_t id[njets];
	Int_t puId[njets];
	Float_t pt_regVBF[njets];	
	Float_t blike_VBF[njets];
} Jets;

using namespace std;


///////    0 18 0/1 0/1/2

int main(int argc, char* argv[]){

int files=atoi(argv[1]);
int files_max=atoi(argv[2]);
int set_type=atoi(argv[3]);

TString dataset_type[2] = {"","_single"};
TString dataset_type_output[2] = {"",""};
TString file_postfix[2] = {"_v14","_v14"};

const int nfiles  = 20;

TString file_names[nfiles] = {"QCD_HT100to200", "QCD_HT200to300", "QCD_HT300to500","QCD_HT500to700", "QCD_HT700to1000", "QCD_HT1000to1500", "QCD_HT1500to2000", "QCD_HT2000toInf", "VBFHToBB_M-125_13TeV_powheg", "GF", "BTagCSV_golden","TTbar","DYtoQQ","ST_tW","ttHtobb","ttHtoNbb", "DYtoLL"};
TString file_names_output[nfiles] = {"QCD_HT100to200", "QCD_HT200to300", "QCD_HT300to500","QCD_HT500to700", "QCD_HT700to1000", "QCD_HT1000to1500", "QCD_HT1500to2000", "QCD_HT2000toInf", "VBFPowheg125", "GFPowheg125", "BTagCSV_golden","TTbar","DYtoQQ","ST_tW","ttHtobb","ttHtoNbb", "DYtoLL"};
Double_t xsec[nfiles] = { 2.75E07, 1.74E06,  3.67E05, 2.94E04, 6.52E03,1.064E03,   121.5,  2.54E01,  2.16 , 25.17 ,1.,816.,1461., 71.7,0.2934,  0.2151,  6025.2  };
//Float_t BG[nfiles] = {1.,1.,1.,1.,1.,1.,1.,1,1.,1.,0.,1.,1.,1.,1.,1.,1.}; //it is actually all MC not only BG
Float_t BG[nfiles] =   {0.,0.,0, 0, 0, 0, 0, 0,0 ,0 ,0.,0.,0.,0.,0.,0.,0.}; //it is actually all MC not only BG
Float_t data[nfiles]={0.,0.,0.,0.,0.,0.,0.,0,0.,0.,1.,0.,0.,0.,0.,0.,0.};
     
TString type[nfiles]; 		
for (int i=0;i<nfiles;i++){
	type[i] = file_names[i];
}


do {
	
	Float_t puweight;
	Float_t genweight;
	Float_t HLT_QuadPFJet_DoubleBTag_CSV_VBF_Mqq200;
	Float_t HLT_QuadPFJet_SingleBTag_CSV_VBF_Mqq460;
	TFile *file_initial;
	TChain *tree_initial;


/////////////////qgd//////////////
	dataset_type[0] = "_double";
	dataset_type[1] = "_single";
	dataset_type_output[0] = "Double";
	dataset_type_output[1] = "Single";
	TString path ;
	path= "dcap://t3se01.psi.ch:22125//pnfs/psi.ch/cms/trivcat///store/user/nchernya/Hbb/v14/main_tmva/new5jet_float_final/";
	TString ending = "";
	path.Append(ending);
	file_initial = TFile::Open(path+"/main_mva_v14_"+file_names[files]+dataset_type[set_type]+".root");
////////////////////////////

	cout<<files<<endl;
	
	tree_initial = (TChain*)file_initial->Get("tree");
	Int_t events_generated;
	TH1F *countPos;
	TH1F *countNeg;
	TH1F*	count; 
	TH1F*	countWeighted; 
	TH1F*	hTriggerPass = new TH1F("TriggerPass","",1,0.,1.);
	hTriggerPass->GetXaxis()->SetTitle("total events (Npos - Nneg)"); 
	if ((data[files]!=1)){
		count = (TH1F*)file_initial->Get("Count");
		countPos = (TH1F*)file_initial->Get("CountPosWeight");
 		countNeg = (TH1F*)file_initial->Get("CountNegWeight");
		countWeighted =(TH1F*)file_initial->Get("CountWeighted");
 		events_generated = countPos->GetEntries()-countNeg->GetEntries();
	} else events_generated = 1;
    Jets Jet;
    Float_t v_type;
    Float_t wrong_type=0.;
    Int_t nJets;
	Float_t JSON;	
	Float_t mva;


    tree_initial->SetBranchAddress("Vtype",&v_type);
    tree_initial->SetBranchAddress("nJet",&nJets);
    tree_initial->SetBranchAddress("Jet_pt",Jet.pt);
    tree_initial->SetBranchAddress("Jet_eta",Jet.eta);
    tree_initial->SetBranchAddress("Jet_phi",Jet.phi);
	tree_initial->SetBranchAddress("Jet_mass",Jet.mass);
	tree_initial->SetBranchAddress("Jet_btagCSV",Jet.btag);
	tree_initial->SetBranchAddress("Jet_blike_VBF",Jet.blike_VBF);
	tree_initial->SetBranchAddress("Jet_id",Jet.id);	
	tree_initial->SetBranchAddress("Jet_puId",Jet.puId);
	
	tree_initial->SetBranchAddress("genWeight",&genweight);
	tree_initial->SetBranchAddress("puWeight",&puweight);
 	tree_initial->SetBranchAddress("HLT_BIT_HLT_QuadPFJet_DoubleBTagCSV_VBF_Mqq200_v",&HLT_QuadPFJet_DoubleBTag_CSV_VBF_Mqq200);
 	tree_initial->SetBranchAddress("HLT_BIT_HLT_QuadPFJet_SingleBTagCSV_VBF_Mqq460_v",&HLT_QuadPFJet_SingleBTag_CSV_VBF_Mqq460);
	tree_initial->SetBranchAddress("Jet_pt_regVBF",Jet.pt_regVBF);
	tree_initial->SetBranchAddress("json",&JSON);
	tree_initial->SetBranchAddress("BDT_VBF",&mva);
    


	if (data[files]==1){
		genweight = 1.;
		puweight=1.;
	}


	TFile *output_file = new TFile("root/Fit_"+ file_names_output[files]+"_sel"+dataset_type_output[set_type]+".root","recreate");
	TDirectory *tree_dir = output_file->mkdir("Hbb");
   tree_dir->cd(); 
	TTree *output_tree = new TTree("events","events");
	Float_t  Mbb, Mbb_reg, Mbb_reg_fsr, bbDeltaPhi,sel,trigWt;
	Int_t trig; 
	output_tree->Branch("mbb",&Mbb,"mbb/F");
	output_tree->Branch("mbbReg",&Mbb_reg,"mbbReg/F");
	output_tree->Branch("mbbRegFSR",&Mbb_reg_fsr,"mbbRegFSR/F");
	output_tree->Branch("dPhibb",&bbDeltaPhi,"dPhibb/F");
	output_tree->Branch("puWt",&puweight,"puWt/F");
	output_tree->Branch("genWt",&genweight,"genWt/F");
	output_tree->Branch("mva"+dataset_type_output[set_type],&mva,"mva/F");
	output_tree->Branch("sel"+dataset_type_output[set_type],&sel,"sel/F");
	output_tree->Branch("trigWt"+dataset_type_output[set_type],&trigWt,"trigWt/F");
	output_tree->Branch("triggerResult",&trig,"trig/I");
	
 	

	int nentries = tree_initial->GetEntries() ;

    for (int entry=0; entry<nentries;++entry){
        tree_initial->GetEntry(entry);

		if (JSON!=1) {
			continue;
		}

		puweight*=TMath::Abs(genweight)/genweight;

		if (!((v_type==-1)||(v_type==4))) continue;
	
		int btag_max1_number = -1;
		int btag_max2_number = -1;
		int pt_max1_number = -1;
		int pt_max2_number = -1;
		TLorentzVector Bjet1;
		TLorentzVector Bjet2;
		TLorentzVector Qjet1;
		TLorentzVector Qjet2;
		TLorentzVector qq;
		

///////// preselection(Int_t nJets, Float_t Jet_pt[300], Float_t Jet_eta[300], Float_t Jet_phi[300], Float_t Jet_mass[300], Float_t Jet_btagCSV[300], Int_t id[300], Int_t& btag_max1_number, Int_t& btag_max2_number, Int_t& pt_max1_number, Int_t& pt_max2_number, Float_t trigger, TLorentzVector& Bjet1,TLorentzVector& Bjet2, TLorentzVector& Qjet1, TLorentzVector& Qjet2,TLorentzVector& qq, Float_t scale=1.)
		if (set_type==0) {
		/////////////////////////////////////////
				if (preselection_single_blike(nJets, Jet.pt,Jet.eta, Jet.phi, Jet.mass, Jet.blike_VBF, Jet.id, btag_max1_number, btag_max2_number, pt_max1_number, pt_max2_number, HLT_QuadPFJet_SingleBTag_CSV_VBF_Mqq460, Bjet1, Bjet2, Qjet1, Qjet2, qq) == 0) continue; 	
				if (preselection_double(nJets, Jet.pt,Jet.eta, Jet.phi, Jet.mass, Jet.btag, Jet.id, btag_max1_number, btag_max2_number, pt_max1_number, pt_max2_number,HLT_QuadPFJet_DoubleBTag_CSV_VBF_Mqq200 , Bjet1, Bjet2, Qjet1, Qjet2, qq)!=0) continue;
		/////////////////////////////////////////
		}
		else if (set_type==1){
			////////////////////////////////////////	
			if (preselection_single_blike(nJets, Jet.pt,Jet.eta, Jet.phi, Jet.mass, Jet.blike_VBF, Jet.id, btag_max1_number, btag_max2_number, pt_max1_number, pt_max2_number,HLT_QuadPFJet_SingleBTag_CSV_VBF_Mqq460 , Bjet1, Bjet2, Qjet1, Qjet2, qq)!=0) continue;
			////////////////////////////////////////	
		}
	
		sel = 1;
		trig = 1;

	 	bbDeltaPhi = TMath::Abs(Bjet1.DeltaPhi(Bjet2));


		TLorentzVector bb;
		bb = Bjet1+Bjet2;
		Mbb = bb.M();

		Float_t alpha_bjet1_reg = 1; 
		Float_t alpha_bjet2_reg = 1 ;
		if (Jet.pt_regVBF[btag_max1_number]>0) alpha_bjet1_reg = Jet.pt_regVBF[btag_max1_number]/Jet.pt[btag_max1_number];
  		if (Jet.pt_regVBF[btag_max2_number]>0) alpha_bjet2_reg = Jet.pt_regVBF[btag_max2_number]/Jet.pt[btag_max2_number];
		Mbb_reg = (alpha_bjet1_reg*Bjet1 + alpha_bjet2_reg*Bjet2).M(); 
		int fsr_bjet=0;

		TLorentzVector FSRjet;
		for (int i=0;i<nJets;i++){
			if ((i!=btag_max1_number)&&(i!=btag_max2_number)&&(i!=pt_max1_number)&&(i!=pt_max2_number)){
				FSRjet.SetPtEtaPhiM(Jet.pt[i],Jet.eta[i],Jet.phi[i],Jet.mass[i]);
				if ((FSRjet.DeltaR(Bjet1)<0.8) || (FSRjet.DeltaR(Bjet2)<0.8)) {
					fsr_bjet++;
					break;
				} 
			}
		}

		if (fsr_bjet>0) Mbb_reg_fsr=(alpha_bjet1_reg*Bjet1 + alpha_bjet2_reg*Bjet2 + FSRjet).M();
		else  Mbb_reg_fsr=(alpha_bjet1_reg*Bjet1 + alpha_bjet2_reg*Bjet2).M();

		trigWt=1.;

		TF1 *func_r = new TF1("erffunc",erf,0.,1000.,3);
		func_r->FixParameter(0,1.);
		if ((set_type==0)&&(data[files]!=1)) {
			func_r->FixParameter(1,8.76821e+01 );
			func_r->FixParameter(2,2.90000e+01 );
			trigWt*=func_r->Eval(Jet.pt[0]);
		}
		if ((set_type==0)&&(data[files]!=1)) {
			func_r->FixParameter(1,7.33919e+01);
			func_r->FixParameter(2,1.39033e+01);
			trigWt*=func_r->Eval(Jet.pt[1]);
		}
		if ((set_type==0)&&(data[files]!=1)) {
			func_r->FixParameter(1,4.11547e+01);	
			func_r->FixParameter(2,3.09873e+01);	
			trigWt*=func_r->Eval(Jet.pt[2]);
		}
		if ((set_type==0)&&(data[files]!=1)) {
			func_r->FixParameter(1,1.89223e+01 );	
			func_r->FixParameter(2,1.22918e+01 );	
			trigWt*=func_r->Eval(Jet.pt[3]);
		}
		
		if ((set_type==0)&&(data[files]!=1)){ 
			func_r->FixParameter(1,1.03187e+00  );	
			func_r->FixParameter(2,3.85456e+00 );	
			trigWt*=func_r->Eval(-1.*TMath::Log(1.-Jet.btag[btag_max1_number]));
		}

		if ((set_type==1)&&(data[files]!=1)){
			func_r->FixParameter(1,9.65220e+01);
			func_r->FixParameter(2,1.75952e+01);
			trigWt*=func_r->Eval(Jet.pt[0]);
		}
		if ((set_type==1)&&(data[files]!=1)){
			func_r->FixParameter(1,8.37198e+01);
			func_r->FixParameter(2,2.65591e+01);
			trigWt*=func_r->Eval(Jet.pt[1]);
		}
		TF1 *func_r_2 = new TF1("erffunc2",erf2,0.,1000.,3);
		if ((set_type==1)&&(data[files]!=1)){
			func_r_2->FixParameter(0,4.45514e-01);
			func_r_2->FixParameter(1,2.12454e+00);
			func_r_2->FixParameter(2,6.29383e-01);
			trigWt*=func_r_2->Eval(-1.*TMath::Log(1.-Jet.btag[btag_max1_number]));
		}

		output_tree->Fill();
	}
		

	output_file->cd();
	if ((data[files]!=1)){
		count->Write();
		countPos->Write();
		countNeg->Write();
		countWeighted->Write();
	}
	hTriggerPass->Fill(0.,events_generated);
	hTriggerPass->Write();
	tree_dir->cd();
	output_tree->AutoSave();
	output_file->Close();

files++;
} while (files<files_max); 

return 0;
}
