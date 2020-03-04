#!/bin/bash
#PBS -P v10
#PBS -W umask=017
#PBS -q express
#PBS -l walltime=01:00:00,mem=960GB,ncpus=240,jobfs=2GB,other=pernodejobfs
#PBS -l wd
#PBS -l storage=scratch/da82+gdata/da82+scratch/v10+gdata/v10+scratch/xu18+gdata/xu18+scratch/if87+gdata/if87

module use /g/data/v10/private/modules/modulefiles
module use /g/data/v10/public/modules/modulefiles

module load wagl/5.4.1
module load openmpi

mpiexec -n 240 python workflow.py --reference-dir /g/data/if87/datacube/002/ --test-dir /g/data/v10/testing_ground/jps547/gadi-test/S2/S2_MSI_ARD --pattern 'ARD-METADATA.yaml' --out-pathname /g/data/v10/testing_ground/jps547/gadi-test/S2/diff-results/s2-c1-raijin-gadi-comparison.h5 --log-pathname status-s2-c1.log
