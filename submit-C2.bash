#!/bin/bash
#PBS -P u46
#PBS -W umask=017
#PBS -q express
#PBS -l walltime=00:30:00,mem=960GB,ncpus=240,jobfs=2GB,other=pernodejobfs
#PBS -l wd
#PBS -l storage=scratch/da82+gdata/da82+scratch/v10+gdata/v10+scratch/xu18+gdata/xu18

module load wagl/gadi-test-5.4.0
module load openmpi

mpiexec -n 240 python comparison.py --reference-dir /g/data/rs0/scenes/nbar-scenes-tmp/ls8/2019/12/output --test-dir /g/data/rs0/scenes/nbar-scenes-tmp/ls8/2019/12/output --outdir /g/data/v10/testing_ground/jps547/gadi-test/C3/diff-results4