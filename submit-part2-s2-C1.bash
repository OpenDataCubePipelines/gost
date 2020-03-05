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

python merge.py --pathname /g/data/v10/testing_ground/jps547/gadi-test/S2/dif-results4/s2-c1-raijin-gadi-comparison.h5 --out-pathname /g/data/v10/testing_ground/jps547/gadi-test/S2/dif-results4/merge-general-results-s2-c1.geojsonl --framing MGRS --dataset-name GENERAL-RESULTS
python merge.py --pathname /g/data/v10/testing_ground/jps547/gadi-test/S2/dif-results4/s2-c1-raijin-gadi-comparison.h5 --out-pathname /g/data/v10/testing_ground/jps547/gadi-test/S2/dif-results4/merge-fmask-results-s2-c1.geojsonl --framing MGRS --dataset-name FMASK-RESULTS
python merge.py --pathname /g/data/v10/testing_ground/jps547/gadi-test/S2/dif-results4/s2-c1-raijin-gadi-comparison.h5 --out-pathname /g/data/v10/testing_ground/jps547/gadi-test/S2/dif-results4/merge-contiguity-results-s2-c1.geojsonl --framing MGRS --dataset-name CONTIGUITY-RESULTS
python merge.py --pathname /g/data/v10/testing_ground/jps547/gadi-test/S2/dif-results4/s2-c1-raijin-gadi-comparison.h5 --out-pathname /g/data/v10/testing_ground/jps547/gadi-test/S2/dif-results4/merge-shadow-results-s2-c1.geojsonl --framing MGRS --dataset-name SHADOW-RESULTS

python summarise.py --pathname /g/data/v10/testing_ground/jps547/gadi-test/S2/dif-results4/merge-general-results-s2-c1.geojsonl --out-pathname /g/data/v10/testing_ground/jps547/gadi-test/S2/dif-results4/summary-general-results-s2-c1.csv
python summarise.py --pathname /g/data/v10/testing_ground/jps547/gadi-test/S2/dif-results4/merge-fmask-results-s2-c1.geojsonl --out-pathname /g/data/v10/testing_ground/jps547/gadi-test/S2/dif-results4/summary-fmask-results-s2-c1.csv --categorical
python summarise.py --pathname /g/data/v10/testing_ground/jps547/gadi-test/S2/dif-results4/merge-contiguity-results-s2-c1.geojsonl --out-pathname /g/data/v10/testing_ground/jps547/gadi-test/S2/dif-results4/summary-contiguity-results-s2-c1.csv --categorical
python summarise.py --pathname /g/data/v10/testing_ground/jps547/gadi-test/S2/dif-results4/merge-shadow-results-s2-c1.geojsonl --out-pathname /g/data/v10/testing_ground/jps547/gadi-test/S2/dif-results4/summary-shadow-results-s2-c1.csv --categorical
