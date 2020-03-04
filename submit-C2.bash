#!/bin/bash
#PBS -P u46
#PBS -W umask=017
#PBS -q express
#PBS -l walltime=00:15:00,mem=960GB,ncpus=240,jobfs=2GB,other=pernodejobfs
#PBS -l wd
#PBS -l storage=scratch/da82+gdata/da82+scratch/v10+gdata/v10+scratch/xu18+gdata/xu18

module use /g/data/v10/private/modules/modulefiles
module use /g/data/v10/public/modules/modulefiles

module load wagl/5.4.1
module load openmpi

mpiexec -n 240 python workflow.py --reference-dir /g/data/rs0/scenes/nbar-scenes-tmp/ls8/2019/12/output --test-dir /g/data/rs0/scenes/nbar-scenes-tmp/ls8/2019/12/output/nbar --out-pathname /g/data/v10/testing_ground/jps547/gadi-test/C2/diff-results-test/c2-raijin-gadi-nbar-comparison.h5 --pattern 'ga-metadata.yaml' --log-pathname status-c2.log
