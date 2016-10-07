import numpy as np
import cPickle as pickle
import matplotlib.pyplot as plt

filename="/nfs/slac/g/exo_data4/users/mjewell/Class/ML/MCWFs/RealNoisePCDs_Rec/RN_1WF_2.p"

pinput = open(filename, 'rb')
wfs = pickle.load(pinput)
pinput.close()

nextras = 7
wflen = len(wfs[0])-nextras

print len(wfs[0])
plt.ion()

print len(wfs)
raw_input()


Epcd = []
Erecon = []

#fft, is coll bool, energy pcd, found in Recon, recon energy, recon is ind, ch, gain


for i in np.arange(len(wfs)):
    
    wf = wfs[i][:wflen]
     
    print "Ending things"
    print wfs[i][0]
    for j in np.arange(nextras):
        print wfs[i][-(j+1)],
    print
    print


    if wfs[i][-(6)].real > 0:
        Epcd.append(wfs[i][-(6)].real)
        Erecon.append(wfs[i][-(4)].real)
    else:
        #Epcd.append(0.0)
        Epcd.append(wfs[i][-(6)].real)
        Erecon.append(wfs[i][-(4)].real)

    rE = wfs[i][-(4)].real
    pE = wfs[i][-(6)].real 
    #if wfs[i][-(4)].real < 0:
    #    if wfs[i][-(2)].real > 1000:
    if rE < 100:
        if pE > 1000:

            for ei in np.arange(nextras):
                print wfs[i][-(ei+1)].real,
            print

            plot = np.conj(wf)*wf
            plot =  plot.real
    
            wft = np.fft.irfft(wf)
    
            #wft = wft/np.max(np.abs(wft))
    
            plt.title("E = %f" % wfs[i][-3].real)
            plt.plot(wft)
            raw_input("Enter")
            plt.clf()
    if abs(rE-pE) > 300 and pE>0:
        wft = np.fft.irfft(wf)
        plt.plot(wft)
        plt.title("rE = %f vs pE = %f" % (rE, pE))
        plt.show()
        raw_input("Enter")
        plt.clf()
    
plt.xlabel("PCD Energy")
plt.ylabel("RECON")
plt.scatter(Epcd, Erecon)
raw_input()



