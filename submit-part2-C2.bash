#!/bin/bash
#PBS -P u46
#PBS -W umask=017
#PBS -q express
#PBS -l walltime=00:05:00,mem=4GB,ncpus=1
#PBS -l wd
#PBS -l storage=scratch/da82+gdata/da82+scratch/v10+gdata/v10+scratch/xu18+gdata/xu18

module load wagl/gadi-test-5.4.0

python merge.py --indir /g/data/v10/testing_ground/jps547/gadi-test/C3/diff-results4 --outdir /g/data/v10/testing_ground/jps547/gadi-test/C3/diff-results4
python aggregate.py --indir /g/data/v10/testing_ground/jps547/gadi-test/C3/diff-results4 --outdir /g/data/v10/testing_ground/jps547/gadi-test/C3/diff-results4