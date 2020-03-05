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

python merge.py --pathname /g/data/v10/testing_ground/jps547/gadi-test/S2/diff-results/s2-c1-raijin-gadi-comparison.h5 --out-pathname /g/data/v10/testing_ground/jps547/gadi-test/S2/diff-results/merge-general-results-s2-c1.geojsonl --framing MGRS --dataset-name GENERAL-RESULTS
python merge.py --pathname /g/data/v10/testing_ground/jps547/gadi-test/S2/diff-results/s2-c1-raijin-gadi-comparison.h5 --out-pathname /g/data/v10/testing_ground/jps547/gadi-test/S2/diff-results/merge-fmask-results-s2-c1.geojsonl --framing MGRS --dataset-name FMASK-RESULTS
python merge.py --pathname /g/data/v10/testing_ground/jps547/gadi-test/S2/diff-results/s2-c1-raijin-gadi-comparison.h5 --out-pathname /g/data/v10/testing_ground/jps547/gadi-test/S2/diff-results/merge-contiguity-results-s2-c1.geojsonl --framing MGRS --dataset-name CONTIGUITY-RESULTS
python merge.py --pathname /g/data/v10/testing_ground/jps547/gadi-test/S2/diff-results/s2-c1-raijin-gadi-comparison.h5 --out-pathname /g/data/v10/testing_ground/jps547/gadi-test/S2/diff-results/merge-shadow-results-s2-c1.geojsonl --framing MGRS --dataset-name SHADOW-RESULTS

python aggregate.py --pathname1 /g/data/v10/testing_ground/jps547/gadi-test/S2/diff-results/merge-wagl-results-s2-c1.geojsonl --pathname2 /g/data/v10/testing_ground/jps547/gadi-test/S2/diff-results/merge-fmask-results-s2-c1.geojsonl --pathname3 /g/data/v10/testing_ground/jps547/gadi-test/S2/diff-results/merge-contiguity-results-s2-c1.geojsonl --pathname4 /g/data/v10/testing_ground/jps547/gadi-test/S2/diff-results/merge-shadow-results-s2-c1.geojsonl --outdir /g/data/v10/testing_ground/jps547/gadi-test/S2/diff-results
