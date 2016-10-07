import ROOT
import numpy as np
import sys
import cPickle as pickle

ROOT.gSystem.Load("libEXOUtilities")
ROOT.gSystem.Load("libEXOCalibUtilities")

debug=True

infile = '/afs/slac.stanford.edu/u/xo/jdalma88/deep/MC_training/trees/RN_1WF_0.root'

print "Getting ROOT File"
testtree = ROOT.TChain("tree")
testtree.Add(infile)
print "Chained Data"

num_ents = testtree.GetEntries()
wf_list = []

c1 = ROOT.TCanvas("c1")
c1.Divide(3,1)

for i in range(num_ents):
    testtree.GetEntry(int(i))
    ed = testtree.EventBranch
    mcED =  ed.fMonteCarloData

    wf_data = ed.GetWaveformData()
    wf_data.Decompress()
    
    npcd = mcED.GetNumPixelatedChargeDeposits()
    print "----------------------------Event------------------------"

    EXOFound = []
    EXOFoundInd = []
    EXOEnergy=[]
    num_sigs = ed.GetNumUWireSignals()
    for sigi in range(num_sigs):
        usig = ed.GetUWireSignal(int(sigi))
        ch =  usig.fChannel
        if ch not in EXOFound: 
            EXOFound.append(ch)
            EXOEnergy.append(usig.fCorrectedEnergy)
        elif ch in EXOFound:
            for fchi,fch in enumerate(EXOFound):
                if ch==fch:
                    EXOEnergy[fchi]+=usig.fCorrectedEnergy
        
        if usig.fIsInduction: EXOFoundInd.append(ch)
        print "Sig ch = ", ch, "is ind = ", usig.fIsInduction, "energy=", usig.fCorrectedEnergy

    num_inds = ed.GetNumUWireInductionSignals()
    for indi in range(num_inds):
        indsig = ed.GetUWireInductionSignal(indi)
        ch = -1*(indsig.fChannel+500)
        EXOFound.append(ch)
        EXOEnergy.append(0.0)
        EXOFoundInd.append(ch)
        print "Ind ch = ", ch, " chiSquare = ", indsig.fChiSquare, "mag=", indsig.fMagnitude


    for pcdi in range(npcd):
        pcd = mcED.GetPixelatedChargeDeposit(int(pcdi))
        hit_ch = pcd.fDepositChannel
        hitT =  pcd.fWireHitTime
        energy = pcd.fTotalIonizationEnergy
        if hit_ch < 0:
             continue

        graph_list = []
        for j in [-1,0,+1]:
            ch = hit_ch+j 
            if ch > 37 and ch <76: continue
            if ch > 113 or ch < 0: continue
            wf = wf_data.GetWaveformWithChannel(ch)
            dwf = ROOT.EXODoubleWaveform(wf)
            
            fwf = ROOT.EXOWaveformFT()

            ROOT.EXOFastFourierTransformFFTW.GetFFT(dwf.GetLength()).PerformFFT(dwf, fwf)
            wfFFT = np.zeros(fwf.GetLength(),dtype=complex)
            wfFFT.real = np.array([fwf.At(i).real() for i in range(fwf.GetLength())])
            wfFFT.imag = np.array([fwf.At(i).imag() for i in range(fwf.GetLength())])

            wf_fft = wfFFT
           
            true_energy = energy
            found = False
            exoind = False
            if ch in EXOFound: 
                found = True
                if ch in EXOFoundInd:
                    exoind=True
            
            if j==0:
                wf_fft = np.append(wf_fft, 1)
                wf_fft = np.append(wf_fft, energy)
                print "true hit ch=",ch, "energy=", energy
            else:
                true_energy = 0.0
                wf_fft = np.append(wf_fft, 0)
                wf_fft = np.append(wf_fft, -energy)
                print "true ind ch=",ch, "mag=", energy
            #wf_fft = np.append(wf_fft, hitT)
            wf_list.append(wf_fft)

            exoenergy=0
            for echi, ech in enumerate(EXOFound):
                if ch==ech: 
                    exoenergy=EXOEnergy[echi]

            graph_list.append((ROOT.TGraph(wf.GimmeHist()), ch, true_energy*1e3,found,exoind,exoenergy))

        for gi, graphed in enumerate(graph_list):
            c1.cd(int(gi+1))
            print "Current ch",graphed[1],"offset=",gi-1
            graphed[0].SetTitle("#splitline{Ch = %i, TrueEnergy = %.2f}{EXOFound = %i, EXOInd = %i, EXOEnergy=%.2f}" % (graphed[1], graphed[2], graphed[3],graphed[4],graphed[5]))
            graphed[0].Draw('AL')
            c1.Update()
        
        c1.Update()
        raw_input("Enter")




        
