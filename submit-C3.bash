#!/bin/bash
#PBS -P v10
#PBS -W umask=017
#PBS -q express
#PBS -l walltime=00:15:00,mem=960GB,ncpus=240,jobfs=2GB,other=pernodejobfs
#PBS -l wd
#PBS -l storage=scratch/da82+gdata/da82+scratch/v10+gdata/v10+scratch/xu18+gdata/xu18

module use /g/data/v10/private/modules/modulefiles
module use /g/data/v10/public/modules/modulefiles

module load wagl/5.4.1
module load openmpi

mpiexec -n 240 python workflow.py --reference-dir /g/data/xu18/ga --test-dir /g/data/v10/testing_ground/jps547/gadi-test/C3/pkgdir/ga_ls8c_ard_3 --out-pathname /g/data/v10/testing_ground/jps547/gadi-test/C3/diff-results8/c3-raijin-gadi-comparison.h5 --pattern '*.odc-metadata.yaml' --log-pathname status-c3.log
