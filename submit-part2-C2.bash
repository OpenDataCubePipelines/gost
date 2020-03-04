#!/bin/bash
#PBS -P u46
#PBS -W umask=017
#PBS -q express
#PBS -l walltime=00:05:00,mem=4GB,ncpus=1
#PBS -l wd
#PBS -l storage=scratch/da82+gdata/da82+scratch/v10+gdata/v10+scratch/xu18+gdata/xu18

module use /g/data/v10/private/modules/modulefiles
module use /g/data/v10/public/modules/modulefiles
module load wagl/5.4.1

python merge.py --pathname /g/data/v10/testing_ground/jps547/gadi-test/C2/diff-results-test/c2-raijin-gadi-nbar-comparison.h5 --out-pathname1 /g/data/v10/testing_ground/jps547/gadi-test/C2/diff-results-test/merge-wagl-results-c2.geojsonl --out-pathname2 /g/data/v10/testing_ground/jps547/gadi-test/C2/diff-results-test/merge-fmask-results-c2.geojsonl --framing WRS2
python aggregate.py --pathname1 /g/data/v10/testing_ground/jps547/gadi-test/C2/diff-results-test/merge-wagl-results-c2.geojsonl --pathname2 /g/data/v10/testing_ground/jps547/gadi-test/C2/diff-results-test/merge-fmask-results-c2.geojsonl --outdir /g/data/v10/testing_ground/jps547/gadi-test/C2/diff-results-test/
