#!/usr/bin/env bash

#./gen_LB_diff.sh events file number

#Event not used so just make dummy
INFILE=${1}
OUTFILE=${2}
OUTNAME=${3}
OUTDIR=${4}
EVENT=${5}
PFILE=${6}
CHNUM=${7}
#ulimit -c 1024
finalRC=1
#set -e

NAME=${OUTNAME}
export SCRATCHDIR=/tmp/jdalma88/WFS_${NAME}
mkdir -p ${SCRATCHDIR}
cd ${SCRATCHDIR}

gotEXIT()
{
 rm -rf ${SCRATCHDIR}
 exit $finalRC
}
trap gotEXIT EXIT

source /nfs/slac/g/exo/mjewell/3D_Digitizer_Offline/EXOOUT/setup.sh
echo $EXOLIB/

cat > ${SCRATCHDIR}/${NAME}.exo << EOF
load $EXOLIB/plugins/EXOGeant4Module.*
use tinput digitizer realnoise rec uind wiregain toutput
/input/file ${INFILE}
/digitizer/setDatabaseTime 1348000000
/digitizer/driftVelocity 0.171
/digitizer/collectionDriftVelocity 0.210
/digitizer/setDigitizationTime 2048 microsecond
/digitizer/setTriggerTime 1024 microsecond
/digitizer/LXeEnergyRes 0.0
/digitizer/wireNoise 0.
/digitizer/APDNoise 0.
/digitizer/ElectronicsDBFlavor measured_times
/digitizer/setWeightPotentialFiles /nfs/slac/g/exo_data6/groups/3DFieldMaps/3Dmaxwell/3D_UWeight.root /nfs/slac/g/exo_data6/groups/3DFieldMaps/3Dmaxwell/3D_VWeight.root
/digitizer/setElectricFieldFile /nfs/slac/g/exo_data6/groups/3DFieldMaps/3Dmaxwell/3D_Efield.root
/digitizer/setNumberDigitizedVWireNeighbors 3
/digitizer/diffuseDuringDrift false
/digitizer/longDiffusionCoeff 0
/digitizer/transDiffusionCoeff 0
/digitizer/numdiffusePCDs 1
/digitizer/electronLifetime 4500
/realnoise/makeNoiseFile false
/realnoise/NoiseFile /nfs/slac/g/exo-userdata/users/mjjewell/NoiseLibrary_PhaseI_50k/NoiseLibrary_Phase1_2464_6370_50k.root
/realnoise/useNoiseFile true
/rec/LowerFitBoundWire 40
/rec/UpperFitBoundWire 140
/rec/ElectronicsDBFlavor measured_times
/rec/enable_stage multiple_sig_finder true
/rec/matched_filter_finder/APDSumThresholdFactor 5
/rec/matched_filter_finder/APDSmoothWindow 4
/rec/LowerFitBoundWireRestr 20
/rec/UpperFitBoundWireRestr 30
/rec/matched_filter_finder/DivideNoise false
/rec/matched_filter_finder/UserVWireThreshold -1.0
/rec/matched_filter_finder/VWireThresholdFactor 5.0
/rec/collection_drift_velocity_mm_per_ns 0.00210 
/rec/drift_velocity_mm_per_ns  0.00171
printmodulo 1000
maxevents ${EVENT}
/toutput/writeSignals true
/toutput/file ${OUTFILE}
show
begin
exit
EOF

ls -lh ${NAME}.exo

cp ${NAME}.exo ${OUTDIR}/

touch ${OUTDIR}/${NAME}.out
EXOAnalysis ${NAME}.exo > ${OUTDIR}/${NAME}.out

echo "run python"

python /nfs/slac/g/exo_data4/users/jdalmasson/MC_for_ML/DumpWFs.py ${OUTFILE} ${PFILE} ${CHNUM} > ${OUTDIR}/${NAME}_python.out

rm -rf ${SCRATCHDIR}


finalRC=0
