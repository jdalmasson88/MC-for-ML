import os, glob, re, time, sys
import numpy as np
import subprocess
import ROOT

ROOT.gROOT.SetBatch()
ROOT.gSystem.Load("libEXOROOT")

running_jobs = 20 #Number of jobs running at once
exe = './gen_digi_test3D.sh' #Location of the talk to file

#Given a position (U or V postion)
#return the U or V channel that is closest 
def nearest_channel(pos, isV):
    # Which channel is closest?
    Channel = int(pos/ROOT.CHANNEL_WIDTH) + ROOT.NCHANNEL_PER_WIREPLANE/2;
    if(pos < 0): Channel-=1 #// round down, not towards zero.
    if(Channel < 0): Channel = 0
    if(Channel >= ROOT.NCHANNEL_PER_WIREPLANE): Channel = ROOT.NCHANNEL_PER_WIREPLANE-1;
    Channel = ROOT.NCHANNEL_PER_WIREPLANE - 1 - Channel
    if (isV): Channel += ROOT.NCHANNEL_PER_WIREPLANE
    return Channel


#----------------------------------------------------------------------
#Function to create a root file and fill with PCDs
#This will fill the EventBranch for the root file so that it can
#be passed into the signal generation part of MC.  This is used in place
#of GEANT4 for creating PCDs.

def createPCDFile(fname, num_events, fnum, ch_n):
    time_of_events = 1357754448
    rand = ROOT.TRandom3(0)

    #Open file and create tree/branch
    open_file = ROOT.TFile(fname, "recreate")
    tree = ROOT.TTree("tree", "tree")
    ed = ROOT.EXOEventData()
    tree.Branch("EventBranch", ed)
    radius = 150.0
    u_ch = ((ch_n-19)*9+4.5)
    root_sq = np.sqrt(0.75*(np.square(radius)-np.square(u_ch)))

    #Loop over number of events and add pcds
    for i in range(num_events):
        #print i
        ed.fRunNumber = fnum
        ed.fEventNumber = i
	v_rand = np.random.rand()*2*root_sq + 0.5*u_ch - root_sq

        #Uniform positon 
        # x/y --> [-160,+160]
        # z   --> [-180,+180]
        #y = rand.Rndm()*320 - 160
        #x = rand.Rndm()*320 - 160
        #z = rand.Rndm()*360 - 180
        z = rand.Rndm()*170 + 10
        x = v_rand - u_ch
        y = (u_ch + v_rand)/np.sqrt(3)  #produce the PCD with fixed u wire (ch_num) but varing the v-wire on a within $radius$ mm from the center of the TPC 

        #Energy [0,3.5MeV]
        energy = rand.Rndm()*3.0

        ed.fEventHeader.fTriggerSeconds = time_of_events
        mc_data = ed.fMonteCarloData
        pcd = mc_data.FindOrCreatePixelatedChargeDeposit(
                ROOT.EXOCoordinates(ROOT.EXOMiscUtil.kXYCoordinates, x, y, z, 0))
        pcd.fTotalEnergy = energy
        pcd.fTotalIonizationEnergy = energy

        tree.Fill()
        ed.Clear()

    tree.Write()
    open_file.Close()
    open_file.IsA().Destructor( open_file )
#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
#Function to pause and hold while waiting for submitted jobs to finish up
def Hold(proc):
    print "Holding", len(proc)
    while len(proc) > running_jobs:
        map(lambda x: x[0].poll(), proc)
        finishedProcs = filter(lambda x: x[0].returncode != None, proc)
        for p in finishedProcs:
            proc.remove(p)
            if p[0].returncode != 0: print "Run %s %s failed" % (p[1],p[2])
            else: print  "Run  %s  %s sucess" % (p[1],p[2])
        time.sleep(20) #Need this or loops to quickly
    print "Done Holding", len(proc)
    return proc
#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------

if __name__ == '__main__':
    #-----------------------------------------------------------------
    #----------------------WARNING------------------------------------
    #-----------------------------------------------------------------
    #--------These files are huge 785M per 10k events so be carful----
    #-----------------------------------------------------------------
    #-----------------------WARNING-----------------------------------
    #-----------------------------------------------------------------

    num_files = 1
    num_events = 10000 #Num of events
    ch_num = int(sys.argv[1])
    outdir = '/nfs/slac/g/exo-userdata/users/jdalmasson/ch%i/' %ch_num
    if not os.path.exists(outdir):
     os.makedirs(outdir)
    
    proc = [] 

    #Loop over each file, create PCD file, submit to EXOMC
    for fnum in np.arange(num_files):

        #Fill the tree with PCDs
        PCDfname =  outdir+("RN_1PCD_%i.root" % fnum)
        createPCDFile(PCDfname, num_events, fnum, ch_num)

        #Hold until system clears up
        proc = Hold(proc)

        #Submit and add to process list
        WFfname = outdir+("RN_1WF_%i.root" % fnum)
        PickleFile = outdir+("RN_1WF_%i.p" % fnum)
        EXOfname = "EXORNWFS%i" % fnum #Name of the .exo file
        proc.append((subprocess.Popen(['bsub','-q','long','-W', '6:00', '-R',
                                       'rhel60', '-K', exe, PCDfname, WFfname, 
                                       EXOfname, outdir, str(num_events), PickleFile, sys.argv[1]]), fnum, PCDfname))

    #Submission is done now loop over the processes still running and wait for each one to finish up
    print "Done submit now just wait"
    for p in proc:
        print "Waiting on", p[1], p[2]
        p[0].wait()
        if p[0].returncode != 0: print "Run %s %s failed" % (p[1], p[2])
        else: print  "Run %s %s sucess" % (p[1],p[2])
    print "Done."
