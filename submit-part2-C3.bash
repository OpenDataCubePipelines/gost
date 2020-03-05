#!/bin/bash
#PBS -P v10
#PBS -W umask=017
#PBS -q express
#PBS -l walltime=00:05:00,mem=4GB,ncpus=1
#PBS -l wd
#PBS -l storage=scratch/da82+gdata/da82+scratch/v10+gdata/v10+scratch/xu18+gdata/xu18

module use /g/data/v10/private/modules/modulefiles
module use /g/data/v10/public/modules/modulefiles
module load wagl/5.4.1

python merge.py --pathname /g/data/v10/testing_ground/jps547/gadi-test/C3/diff-results8/c3-raijin-gadi-comparison.h5 --out-pathname /g/data/v10/testing_ground/jps547/gadi-test/C3/diff-results8/merge-general-results-c3.geojsonl --framing WRS2 --dataset-name GENERAL_RESULTS
python merge.py --pathname /g/data/v10/testing_ground/jps547/gadi-test/C3/diff-results8/c3-raijin-gadi-comparison.h5 --out-pathname /g/data/v10/testing_ground/jps547/gadi-test/C3/diff-results8/merge-fmask-results-c3.geojsonl --framing WRS2 --dataset-name FMASK_RESULTS
python merge.py --pathname /g/data/v10/testing_ground/jps547/gadi-test/C3/diff-results8/c3-raijin-gadi-comparison.h5 --out-pathname /g/data/v10/testing_ground/jps547/gadi-test/C3/diff-results8/merge-contiguity-results-c3.geojsonl --framing WRS2 --dataset-name CONTIGUITY-RESULTS
python merge.py --pathname /g/data/v10/testing_ground/jps547/gadi-test/C3/diff-results8/c3-raijin-gadi-comparison.h5 --out-pathname /g/data/v10/testing_ground/jps547/gadi-test/C3/diff-results8/merge-shadow-results-c3.geojsonl --framing WRS2  --dataset-name SHADOW-RESULTS


python aggregate.py --pathname1 /g/data/v10/testing_ground/jps547/gadi-test/C3/diff-results8/merge-wagl-results-c3.geojsonl --pathname2 /g/data/v10/testing_ground/jps547/gadi-test/C3/diff-results8/merge-fmask-results-c3.geojsonl --pathname3 /g/data/v10/testing_ground/jps547/gadi-test/C3/diff-results8/merge-contiguity-results-c3.geojsonl --pathname4 /g/data/v10/testing_ground/jps547/gadi-test/C3/diff-results8/merge-shadow-results-c3.geojsonl --outdir /g/data/v10/testing_ground/jps547/gadi-test/C3/diff-results8
