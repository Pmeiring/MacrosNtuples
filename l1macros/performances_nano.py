from datetime import datetime
import ROOT
import os
import sys
import argparse



#In case you want to load an helper for C++ functions
ROOT.gInterpreter.Declare('#include "../helpers/Helper.h"')
ROOT.gInterpreter.Declare('#include "../helpers/Helper_HadW.h"')
ROOT.gInterpreter.Declare('#include "../helpers/Helper_InvariantMass.h"')
#Importing stuff from other python files
sys.path.insert(0, '../helpers')

import helper_nano as h
import helper_nano_hadw as h_hadw


def main():
    ###Arguments 
    parser = argparse.ArgumentParser(
        description='''L1 performance studies (turnons, scale/resolution/...)
        Based on ntuples produced from MINIAOD with a code adapted from:
        https://github.com/lathomas/JetMETStudies/blob/master/JMEAnalyzer/python/JMEanalysis.py''',
        usage='use "%(prog)s --help" for more information',
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--max_events", dest="max_events", help="Maximum number of events to analyze. Default=-1 i.e. run on all events.", type=int, default=-1)
    parser.add_argument("-i", "--input", dest="inputFile", help="Input file", type=str, default='')
    parser.add_argument("-o", "--output", dest="outputFile", help="Output file", type=str, default='')
    parser.add_argument("-g", "--golden", dest="golden", help="Golden JSON file to use", type = str, default = '')
    parser.add_argument("-c", "--channel", dest="channel", help=
                        '''Set channel and analysis:
                        -PhotonJet: For L1 jet studies with events trigger with a SinglePhoton trigger
                        -DiJet: For L1 jet studies with events triggered with a SingleJet trigger
                        -MuonJet: For L1 jet studies with events trigger with a SingleMuon trigger
                        -ZToMuMu: For L1 muon studies with Z->mumu
                        -ZToEE: For L1 EG studies with Z->ee
                        -ZToTauTau: For L1 Tau studies with Z->tau(mu)tau(h)
                        ''', 
                        type=str, default='PhotonJet')
    parser.add_argument("--config", dest="config", help="Yaml configuration file to read. Default: full config for that channel.", type=str, default='')
    parser.add_argument("--reemul", help="Run on reemulated quantities", action='store_true')
    #parser.add_argument("--plot_nvtx", dest="plot_nvtx", help="Whether to save additional plots in bins of nvtx. Boolean, default = False", type=bool, default=False)
    #parser.add_argument("--nvtx_bins", dest="nvtx_bins", help="Edges of the nvtx bins to use if plotNvtx is set to True. Default=[10, 20, 30, 40, 50, 60]", nargs='+', type=int, default=[10, 20, 30, 40, 50, 60])
    args = parser.parse_args() 

    ###Define the RDataFrame from the input tree
    inputFile = args.inputFile
    if inputFile == '':
        if args.channel == 'PhotonJet':
            inputFile = '/pnfs/iihe/cms/store/user/lathomas/EGamma1/2023Dv1_L1TNanowithPrefiringInfo/231129_154543/0000/out_234.root'
        elif args.channel == 'MuonJet':
            inputFile = '/pnfs/iihe/cms/store/user/lathomas/Muon1/2023Dv1_L1TNanowithPrefiringInfo/231129_162737/0000/out_196.root'
        elif args.channel == 'ZToMuMu':
            inputFile = '/pnfs/iihe/cms/store/user/lathomas/Muon1/2023Dv1_L1TNanowithPrefiringInfo/231129_162737/0000/out_196.root'
        elif args.channel == 'ZToEE':
            inputFile = '/pnfs/iihe/cms/store/user/lathomas/EGamma1/2023Dv1_L1TNanowithPrefiringInfo/231129_154543/0000/out_234.root'
        elif args.channel == 'DiJet':
            inputFile = '/pnfs/iihe/cms/store/user/lathomas/JetMET1/2023Dv1_L1TNanowithPrefiringInfo/231129_162802/0000/out_98.root'
        
    ### Set default config file
    config_file = args.config
    if config_file == '':
        if args.channel == 'PhotonJet':
            config_file = '../config_cards/full_PhotonJet.yaml'
        elif args.channel == 'MuonJet':
            config_file = '../config_cards/full_MuonJet.yaml'
        elif args.channel == 'ZToMuMu':
            config_file = '../config_cards/full_ZToMuMu.yaml'
        elif args.channel == 'ZToEE':
            config_file = '../config_cards/full_ZToEE.yaml'
        elif args.channel == 'DiJet':
            config_file = '../config_cards/full_DiJet.yaml'
        elif args.channel == 'ZToTauTau':
            config_file = '../config_cards/full_ZToTauTau.yaml'
        elif args.channel == 'TTbar1Mu4Jets2BJets':
            config_file = '../config_cards/full_MuonJet.yaml'
        elif args.channel == 'TTbar1Mu4Jets2BJets_L1Only':
            config_file = '../config_cards/full_MuonJet.yaml'

    # Read config and set config_dict in helper
    with open(config_file) as s:
        h.set_config(s)

    fltr = h.make_filter(args.golden)

    ### Create filters and suffix, if needed, to later run on bins of nvtx

    filter_list = ["true"]
    suffix_list = [""]

    # bins of nvtx
    #if args.plot_nvtx == True:
    if h.config['PU_plots']['make_histos']:
        filter_list += ["PV_npvs>={}&&PV_npvs<{}".format(low, high) for (low, high) \
                in zip(h.config['PU_plots']['nvtx_bins'][:-1],h.config['PU_plots']['nvtx_bins'][1:])]
        suffix_list += ["_nvtx{}to{}".format(low, high) for (low, high) \
                in zip(h.config['PU_plots']['nvtx_bins'][:-1],h.config['PU_plots']['nvtx_bins'][1:])]

    ###

    df = ROOT.RDataFrame('Events', inputFile)
    if fltr != '':
        df = df.Filter(fltr)
    nEvents = df.Count().GetValue()

    if not 'L1_FinalOR_BXmin1' in df.GetColumnNames():
        df = df.Define('L1_FinalOR_BXmin1','return false;')
    if not 'L1_FinalOR_BXmin2' in df.GetColumnNames():
        df = df.Define('L1_FinalOR_BXmin2','return false;')


    if not 'L1_UnprefireableEvent_TriggerRules' in df.GetColumnNames():
        df = df.Define('L1_UnprefireableEvent_TriggerRules','L1_UnprefireableEvent')
    if not 'L1_UnprefireableEvent_FirstBxInTrain' in df.GetColumnNames():
        df = df.Define('L1_UnprefireableEvent_FirstBxInTrain','return false;')
    
    if not 'Jet_btagPNetB' in df.GetColumnNames():
        df = df.Define('Jet_btagPNetB','Jet_btagDeepFlavB')

    if not 'HLT_Photon45EB_TightID_TightIso' in df.GetColumnNames():
        df = df.Define('HLT_Photon45EB_TightID_TightIso','return false;')

    if args.reemul:
        df=df.Redefine('L1Mu_pt','L1EmulMu_pt')
        df=df.Redefine('L1Mu_eta','L1EmulMu_eta')
        df=df.Redefine('L1Mu_phi','L1EmulMu_phi')
        df=df.Redefine('L1Mu_bx','L1EmulMu_bx')
        df=df.Redefine('L1Mu_hwCharge','L1EmulMu_hwCharge')
        df=df.Redefine('L1Mu_hwQual','L1EmulMu_hwQual')
        df=df.Redefine('L1Mu_etaAtVtx','L1EmulMu_etaAtVtx')
        df=df.Redefine('L1Mu_phiAtVtx','L1EmulMu_phiAtVtx')
        
        df=df.Redefine('L1EG_pt','L1EmulEG_pt')
        df=df.Redefine('L1EG_eta','L1EmulEG_eta')
        df=df.Redefine('L1EG_phi','L1EmulEG_phi')
        df=df.Redefine('L1EG_bx','L1EmulEG_bx')
        df=df.Redefine('L1EG_hwIso','L1EmulEG_hwIso')
        
        
        df=df.Redefine('L1Tau_pt','L1EmulTau_pt')
        df=df.Redefine('L1Tau_eta','L1EmulTau_eta')
        df=df.Redefine('L1Tau_phi','L1EmulTau_phi')
        df=df.Redefine('L1Tau_bx','L1EmulTau_bx')
        df=df.Redefine('L1Tau_hwIso','L1EmulTau_hwIso')
        
        df=df.Redefine('L1Jet_pt','L1EmulJet_pt')
        df=df.Redefine('L1Jet_eta','L1EmulJet_eta')
        df=df.Redefine('L1Jet_phi','L1EmulJet_phi')
        df=df.Redefine('L1Jet_bx','L1EmulJet_bx')
        df=df.Redefine('L1Jet_hwIso','L1EmulJet_hwIso')
        df=df.Redefine('L1Jet_rawEt','L1EmulJet_rawEt')
        df=df.Redefine('L1Jet_puEt','L1EmulJet_puEt')

        df=df.Redefine('L1EtSum_pt','L1EmulEtSum_pt')
        df=df.Redefine('L1EtSum_phi','L1EmulEtSum_phi')
        df=df.Redefine('L1EtSum_bx','L1EmulEtSum_bx')
        df=df.Redefine('L1EtSum_etSumType','L1EmulEtSum_etSumType')

    df = df.Define('Jet_passJetIdTight', '((abs(Jet_eta)<=2.6)&&(Jet_neHEF < 0.99)&&(Jet_neEmEF<0.9)&&(Jet_chMultiplicity+Jet_neMultiplicity>1)&&(Jet_chHEF>0.01)&&(Jet_chMultiplicity>0)) || ((abs(Jet_eta)>2.6&&abs(Jet_eta)<=2.7)&&(Jet_neHEF<0.90)&&(Jet_neEmEF < 0.99)) || ((abs(Jet_eta)>2.7&&abs(Jet_eta)<=3.0)&&(Jet_neHEF < 0.99)) || ((abs(Jet_eta)>3.0)&&(Jet_neMultiplicity>=2)&&(Jet_neEmEF<0.4))')
    df = df.Define('Jet_passJetIdTightLepVeto', '((abs(Jet_eta)<=2.7)&&Jet_passJetIdTight&&(Jet_muEF<0.8)&&(Jet_chEmEF<0.8)) || ((abs(Jet_eta)>2.7)&&Jet_passJetIdTight)')





    print('There are {} events'.format(nEvents))
    print('File is: ',inputFile )
    

    #Max events to run on 
    max_events = min(nEvents, args.max_events) if args.max_events >=0 else nEvents
    df = df.Range(0, max_events)
    #Next line to monitor event loop progress
    df = df.Filter('if(tdfentry_ %100000 == 0) {cout << "Event is  " << tdfentry_ << endl;} return true;')

    #Apply MET filters
    df = df.Filter('Flag_HBHENoiseFilter&&Flag_HBHENoiseIsoFilter&&Flag_goodVertices&&Flag_EcalDeadCellTriggerPrimitiveFilter&&Flag_BadPFMuonFilter&&Flag_BadPFMuonDzFilter')
    if args.channel != 'ZToMuMu':
        df = df.Filter('run<379315||run >379354') #prefire veto test, hcal phase scan, ecal timing scan
    df = df.Filter('run<379344||run>379411') #Pixels off, at least for some of these runs
    #df = df.Filter('run>=380647') #First run with updated HF resp corrs
    #df = df.Filter('run>=379800&&run<380647') #New offline JECs
    #df = df.Filter('run>=379800')
    #    if args.channel == 'ZToMuMu' or args.channel == 'DiJet':
    #        df = df.Filter('run>379600')
    # binning for run number
    h.set_runnb_bins(df)

    #Define ETMHF
    df = h.L1ETMHF(df)
    if args.outputFile == '':
        args.outputFile = 'output_'+args.channel+'.root'
    out = ROOT.TFile(args.outputFile, "recreate")
    ####The sequence of filters/column definition starts here
    
    if args.channel not in ['PhotonJet','MuonJet','ZToMuMu','ZToEE', 'DiJet', 'ZToTauTau', 'TTbar1Mu4Jets2BJets', 'TTbar1Mu4Jets2BJets_L1Only']:
        print("Channel {} does not exist".format(args.channel))
        return 

    # add nvtx histo
    nvtx_histo = df.Histo1D(ROOT.RDF.TH1DModel("h_nvtx" , "Number of reco vertices;N_{vtx};Events"  ,    100, 0., 100.), "PV_npvs")
        
    if args.channel == 'PhotonJet':
        df = h.SinglePhotonSelection(df) 
        
        df = h.CleanJets(df)
        
        # make copies of df for each bin of nvtx (+1 copy of the original)
        df_list = [df.Filter(nvtx_cut) for nvtx_cut in filter_list]

        all_histos_jets = {}
        all_histos_balance = {}
        all_histos_hf = {}

        # run for each bin of nvtx:
        for i, df_element in enumerate(df_list):
            df_element, histos_jets = h.AnalyzeCleanJets(df_element, 200, 100, suffix = suffix_list[i])
            df_element = h.lepton_iselectron(df_element)
            if h.config['PtBalance']:
                df_element = h.PtBalanceSelection(df_element)
                df_element, histos_balance = h.AnalyzePtBalance(df_element, suffix = suffix_list[i])
            #df_report = df_element.Report()
            if h.config['HF_noise']:
                df_element, histos_hf = h.HFNoiseStudy(df_element, suffix = suffix_list[i])

            for key, val in histos_jets.items():
                all_histos_jets[key] = val

            if h.config['PtBalance']:
                for key, val in histos_balance.items():
                    all_histos_balance[key] = val

            if h.config['HF_noise']:
                for key, val in histos_hf.items():
                    all_histos_hf[key] = val

            #df_report.Print()

        for i in all_histos_jets:
            all_histos_jets[i].GetValue().Write()
            
        if h.config['PtBalance']:
            for i in all_histos_balance:
                all_histos_balance[i].GetValue().Write()
            
        if h.config['HF_noise']:
            for i in all_histos_hf:
                all_histos_hf[i].GetValue().Write()

#        df, histos_jets = AnalyzeCleanJets(df, 200, 100) 
#        
#        df = PtBalanceSelection(df)
#        
#        df, histos_balance = AnalyzePtBalance(df)
#        
#        df_report = df.Report()
#        
#        df, histos_hf = HFNoiseStudy(df)
#
#        #Selection is over. Now do some plotting
#
#        for i in histos_jets:
#            histos_jets[i].GetValue().Write()
#
#        for i in histos_balance:
#            histos_balance[i].GetValue().Write()
#            
#        for i in histos_hf:
#            histos_hf[i].GetValue().Write()
#        df_report.Print()
        
        
    if args.channel == 'MuonJet':
        df = h.MuonJet_MuonSelection(df) 
        # df = h.ZMuMu_MuSelection(df, 60, 10000)

        df = h.CleanJets(df)
        
        # make copies of df for each bin of nvtx (+1 copy of the original)
        df_list = [df.Filter(nvtx_cut) for nvtx_cut in filter_list]

        all_histos_jets = {}
        all_histos_sum = {}
        all_histos_hf = {}

        for i, df_element in enumerate(df_list):
            df_element, histos_jets = h.AnalyzeCleanJets(df_element, 100, 50, suffix = suffix_list[i]) 
            df_element = h.lepton_ismuon(df_element)
            if h.config['MET_plots']:
                df_element, histos_sum = h.EtSum(df_element, suffix = suffix_list[i])
            if h.config['HF_noise']:
                df_element, histos_hf = h.HFNoiseStudy(df_element, suffix = suffix_list[i])

            for key, val in histos_jets.items():
                all_histos_jets[key] = val

            if h.config['MET_plots']:
                for key, val in histos_sum.items():
                    all_histos_sum[key] = val

            if h.config['HF_noise']:
                for key, val in histos_hf.items():
                    all_histos_hf[key] = val

        for i in all_histos_jets:
            all_histos_jets[i].GetValue().Write()
            
        if h.config['MET_plots']:
            for i in all_histos_sum:
                all_histos_sum[i].GetValue().Write()

        if h.config['HF_noise']:
            for i in all_histos_hf:
                all_histos_hf[i].GetValue().Write()
            
#        df, histos_jets = AnalyzeCleanJets(df, 100, 50) 
#        
#        df, histos_sum = EtSum(df)
#        
#        df_report = df.Report()
#        
#        df, histos_hf = HFNoiseStudy(df)
#
#        #Selection is over. Now do some plotting
#        
#        for i in histos_jets:
#            histos_jets[i].GetValue().Write()
#            
#        for i in histos_sum:
#            histos_sum[i].GetValue().Write()
#            
#        for i in histos_hf:
#            histos_hf[i].GetValue().Write()
#                
#        df_report.Print()

    if args.channel == 'ZToEE':
        
        df = h.lepton_iselectron(df)
        df_photon50 = h.ZEE_EleSelection_forHLTPhoton50(df, 80, 100)
        df_photon50, histos_photon50 = h.ZEE_Plots_forHLTPhoton50(df_photon50) 

        df_fwd = h.ZEE_Forward_EleSelection(df, 70, 120)
        df_prefvsmll = h.ZEE_EleSelection(df, 60, 10000)
        df = h.ZEE_EleSelection(df, 80, 100)


        # make copies of df for each bin of nvtx (+1 copy of the original)
        df_list = [df.Filter(nvtx_cut) for nvtx_cut in filter_list]
        all_histos = {}

        for i, df_element in enumerate(df_list):
            df_element, histos = h.ZEE_Plots(df_element, suffix = suffix_list[i])
            
            for key, val in histos.items():
                all_histos[key] = val

        df_fwd, fwd_histos = h.ZEE_Forward_Plots(df_fwd)
        
        
        df_prefvsmll, histos_pref = h.PrefiringVsMll(df_prefvsmll)
        

        for i in all_histos:
            all_histos[i].GetValue().Write()
        for i in fwd_histos:
            fwd_histos[i].GetValue().Write()
        for i in histos_pref:
            histos_pref[i].GetValue().Write()
        for i in histos_photon50:
            histos_photon50[i].GetValue().Write()


    if args.channel == 'ZToMuMu':
        df_prefvsmll = h.ZMuMu_MuSelection(df, 70, 10000)
        df = h.ZMuMu_MuSelection(df, 80, 100)

        # make copies of df for each bin of nvtx (+1 copy of the original)
        df_list = [df.Filter(nvtx_cut) for nvtx_cut in filter_list]
        all_histos = {}

        for i, df_element in enumerate(df_list):
            df_element, histos = h.ZMuMu_Plots(df_element, suffix = suffix_list[i])

            for key, val in histos.items():
                all_histos[key] = val
           

        df_prefvsmll, histos_pref = h.PrefiringVsMll(df_prefvsmll)
        for i in all_histos:
            all_histos[i].GetValue().Write()
        for i in histos_pref:
            histos_pref[i].GetValue().Write()

    if args.channel == 'DiJet':
        df = h.DiJetSelection(df) 
        #df = h.DiJet_Plots(df)
        df = h.CleanJets(df)
        all_histos_jets = {}

        df, histos_jets = h.AnalyzeCleanJets(df, 500, 180 )
        
        df, histos_mjj = h.PrefiringVsMjj(df)
        
        for i in histos_jets:
            histos_jets[i].GetValue().Write()

        for i in histos_mjj:
            histos_mjj[i].GetValue().Write()
            
    if args.channel == 'ZToTauTau':
        df = h.ZTauTauSelection(df)
        
        # make copies of df for each bin of nvtx (+1 copy of the original)
        df_list = [df.Filter(nvtx_cut) for nvtx_cut in filter_list]
        all_histos = {}

        for i, df_element in enumerate(df_list):
            df_element, histos = h.ZTauTau_Plots(df_element, suffix = suffix_list[i])

            for key, val in histos.items():
                all_histos[key] = val
        
        for i in all_histos:
            all_histos[i].GetValue().Write()


    if args.channel == 'TTbar1Mu4Jets2BJets':
        df = h_hadw.TTbar1Mu2BJets4Jets(df)
        df_report = df.Report()
        df, histos = h_hadw.AnalyzeJetsTTbar1Mu4Jets2BJets(df)
        for i in histos:
            histos[i].GetValue().Write()
        df_report.Print()

    if args.channel == 'TTbar1Mu4Jets2BJets_L1Only':
        df = h_hadw.TTbar1Mu2BJets4Jets_l1only(df)
        df_report = df.Report()
        df, histos = h_hadw.AnalyzeJetsTTbar1Mu4Jets2BJets_l1only(df)
        for i in histos:
            histos[i].GetValue().Write()
        df_report.Print()


    nvtx_histo.GetValue().Write()

    # njet35_histo.GetValue().Write()
    # njet110_histo.GetValue().Write()

if __name__ == '__main__':
    main()
