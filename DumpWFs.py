import ROOT
import numpy as np
import sys
import cPickle as pickle

#ROOT.gROOT.SetBatch()
c1=ROOT.TCanvas("c1")
ROOT.gSystem.Load("libEXOUtilities")
ROOT.gSystem.Load("libEXOCalibUtilities")

debug=False

def GetSignalInfo(ed):
    EXOFound = [] #Array of all found signals (coll+ind)
    EXOFoundInd = [] #Array of all collection signals
    EXOEnergy=[]     #Array of energy fCorrectedEnergy

    num_sigs = ed.GetNumUWireSignals()
    num_inds = ed.GetNumUWireInductionSignals()

    #Get all found Usignals and save hit channel 
    for sigi in range(num_sigs):
        usig = ed.GetUWireSignal(int(sigi))
        
        #print usig.fCorrectedEnergy
        ch =  usig.fChannel
        if ch not in EXOFound: 
            EXOFound.append(ch)
            EXOEnergy.append(0.0)

        if ch not in EXOFoundInd:
            if usig.fIsInduction: EXOFoundInd.append(ch)

    #For each Found Channel add up total signal energy
    for i,ch in enumerate(EXOFound):
        for sigi in range(num_sigs):
            usig = ed.GetUWireSignal(int(sigi))
            if usig.fChannel==ch:
                EXOEnergy[i]+=usig.fCorrectedEnergy
    
    #Get all found Induction signals
    for indi in range(num_inds):
        indsig = ed.GetUWireInductionSignal(indi)
        ch = -1*(indsig.fChannel+500) #Ind channels offset weirdly
        if (ch not in EXOFoundInd) and (ch not in EXOFound):
        #if (ch not in EXOFoundInd):
            EXOFoundInd.append(ch)
            EXOFound.append(ch)
            EXOEnergy.append(0.0)
    #print EXOEnergy, EXOFound, EXOFoundInd
    return EXOFound, EXOFoundInd, EXOEnergy

def GetWFs(ed, mcED):
    #Get the WFs
    wf_data = ed.GetWaveformData()
    wf_data.Decompress()
    
    npcd = mcED.GetNumPixelatedChargeDeposits()
    wf_list = []
    RealFound = []
    RealInd  = []

    #Loop over PCDs in this event
    for pcdi in range(npcd):
        pcd = mcED.GetPixelatedChargeDeposit(int(pcdi))

        hit_ch = pcd.fDepositChannel #Channel deposited on
        hitT =  pcd.fWireHitTime #Wire hit time (useful if multiple PCDs)
        energy = pcd.fTotalIonizationEnergy #Energy of PCD 
        
        #Skip if there was no hit channel (can occasionally happen)
        if hit_ch < 0:
            continue

        #Get hit channel and 2 neighboring channels (largest induction signals)
        #This part assumes we only have 1 PCD.  If more than this needs to be
        #redone to not assume induction on neighboring channels.
        for j in [-1,0,+1]:
            ch = hit_ch+j

            #Make sure it is a U-wire channel
            if ch > 37 and ch <76: continue
            if ch > 113 or ch < 0: continue

            #Extract the WF
            wf = wf_data.GetWaveformWithChannel(ch)
            dwf = ROOT.EXODoubleWaveform(wf)
            
            #Plot if in debug mode
            if debug:
                wfg = ROOT.TGraph(wf.GimmeHist())
                wfg.Draw('AL')
                c1.Update()
                raw_input("Enter")

            #Get the FFT (maybe we want to go back to time space??)
            fwf = ROOT.EXOWaveformFT()
            ROOT.EXOFastFourierTransformFFTW.GetFFT(dwf.GetLength()).PerformFFT(dwf, fwf)
            wfFFT = np.zeros(fwf.GetLength(),dtype=complex)
            wfFFT.real = np.array([fwf.At(i).real() for i in range(fwf.GetLength())])
            wfFFT.imag = np.array([fwf.At(i).imag() for i in range(fwf.GetLength())])

            #Append the energy and isInduction onto 
            wf_fft = wfFFT
            if j==0:
                #This is the center channel (collection)
                RealFound.append(ch)
                wf_fft = np.append(wf_fft, 1)
                wf_fft = np.append(wf_fft, energy*1e3)
            else:
                #This is a neighboring channel (induction)
                RealInd.append(ch)
                RealFound.append(ch)
                wf_fft = np.append(wf_fft, 0)
                wf_fft = np.append(wf_fft, -energy*1e3)
            
            wf_list.append(wf_fft)
    
    return wf_list, RealFound, RealInd

def CompareChs(RealFound, RealInd, EXOFound, EXOFoundInd):
    missed = 0
    for ech in EXOFound:
        if (ech not in RealFound):
            #Channel was found by EXO but not a PCD hit
            print "--------------------Missed a channel------------------------"
            missed+=1
    for ech in EXOFoundInd:
        if (ech not in RealInd):
            #Channel was found as induction but not actual induction 
            print "--------------------Missed induct------------------------"
            missed+=1
    return missed

def CheckWF(ed, mcED, rE, pE, ch, EXOEnergy, EXOFound, EXOFoundInd):
    #Just for debugging

    #if pE > 1000.0 and rE < 100.0:
    if pE < 10.0 and rE > 1000.0:
        wf_data = ed.GetWaveformData()
        wf_data.Decompress()
        wf = wf_data.GetWaveformWithChannel(ch)
        dwf = ROOT.EXODoubleWaveform(wf)
        wfg = ROOT.TGraph(dwf.GimmeHist())
        wfg.Draw('AL')
        c1.Update()
        print "Recon = ", rE, "true = ", pE
        pcd = mcED.GetPixelatedChargeDeposit(int(0))
        print "PCD Ch = ", pcd.fDepositChannel, "plot ch=", ch
        print EXOEnergy
        print EXOFound
        print EXOFoundInd
        print "Event number=", ed.fEventNumber
        for sigi in range(ed.GetNumUWireSignals()):
            usig = ed.GetUWireSignal(int(sigi))
            print "Check ch=", usig.fChannel, "E=",usig.fCorrectedEnergy, " isInd = ",usig.fIsInduction, "Raw Energy = ", usig.fRawEnergy
        for indi in range(ed.GetNumUWireInductionSignals()):
            indsig = ed.GetUWireInductionSignal(indi)
            print "Border Induction", -1*(indsig.fChannel+500), "mag=", indsig.fMagnitude

        raw_input("Enter")

    return

def getgain(chin):
     gain, ch = np.loadtxt("/nfs/slac/g/exo/mjewell/EXOML/MCWFGeneration/wiregains.txt",unpack=True)
     return gain[chin]

if __name__ == '__main__':
    #Run as "python DumpWFs.py  input_ROOT_File  output_pickle_file"
    #Example: python DumpWFs.py  /nfs/slac/g/exo_data4/users/mjewell/Class/ML/MCWFs/RealNoisePCDs_Rec/RN_1WF_2.root  /nfs/slac/g/exo_data4/users/mjewell/Class/ML/MCWFs/RealNoisePCDs_Rec/RN_1WF_2.p
    infile = sys.argv[1]
    pfile =  sys.argv[2]
    ch_num = int(sys.argv[3])

    print "ROOT file is ", infile
    print "Pfile is ",  pfile
    print "Getting ROOT File"
    testtree = ROOT.TChain("tree")
    testtree.Add(infile)
    print "Chained Data"
    num_ents = testtree.GetEntries()

    wf_list = []
    misses=0
    for i in range(num_ents):                            #############################num_ents
        testtree.GetEntry(int(i))
        ed = testtree.EventBranch
        mcED =  ed.fMonteCarloData

        #Get the MC WFs
        curr_wfs, RealFound, RealInd = GetWFs(ed, mcED)

        #Get the info From EXO-200 Recon
        EXOFound, EXOFoundInd, EXOEnergy = GetSignalInfo(ed)

        #Compare found channels make sure they agree
        misses+=CompareChs(RealFound, RealInd, EXOFound, EXOFoundInd)

        for wf, chf in zip(curr_wfs, RealFound):
            reconEnergy = 0.0
            reconIsInd = -1
            reconIsFound = 0

            #If found by EXO-200 save the current recon energy
            if chf in EXOFound:
                if chf not in [ch_num-1,ch_num,ch_num+1]: 
                    print "Skip", chf
                    continue
                reconIsFound = 1
                #Get Recon Energy
                for ei, che in enumerate(EXOFound):
                    if chf==che: reconEnergy = EXOEnergy[ei]
                
                #Was it called collection or induction
                if chf in EXOFoundInd: reconIsInd=1
                else: reconIsInd=0
            
            wf = np.append(wf, reconIsFound)
            wf = np.append(wf, reconEnergy)
            wf = np.append(wf, reconIsInd)
            wf = np.append(wf, chf)
            wf = np.append(wf, getgain(chf))
            wf_list.append(wf)
            print len(wf)
            #Structure
            #fft, is coll bool, energy pcd, found in Recon, recon energy, recon is ind, ch, gain
            #recon is ind = -1 for not found
            #Just for Debug
            #CheckWF(ed, mcED, reconEnergy, wf[-4], chf, EXOEnergy, EXOFound, EXOFoundInd)

    print "Total Missed Signals----->", misses

    dfile = open(pfile, 'wb')
    pickle.dump(wf_list, dfile)
    dfile.close()
