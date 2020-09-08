# gost

Intercomparison workflow for Digital Earth Australia's Analyisis Ready Data.

The full workflow is built around using PBS on Australia's National Computational Infrastructure (NCI), with each task/component callable from the command line.
Simplified the work required for a user to undertake an intercomparison.
Used for:

* comparing and evaluating different versions of output data
* development testing prior to production release
* sensitivity analysis

Can also be adapated to a multitude of other datasets.

## Tasks

Query
-----

This task is to discover the datasets from both the reference and test locations. The test and reference datasets are then joined together in a 1-1 relationship based on a common ancestor.

Comparison
----------

This task is split into two independent sub-tasks:

* dataset measurement comparison (residual analysis of the imagery)
* dataset gqa comparison (residual analysis of the geometric quality)

Each of the above sub-tasks are run using MPI for mass scalability.

Collate
-------

This task is to collate and summarise the results computed by the comparison task, and like the comparison task, is split into two sub-tasks.

* spatial merging with the acquisition framing
* global summary statistics (summarise all results into singular statistics)

Results are merged with the spatial framing that the satellite acquisitions are comprised of; WRS2 for Landsat, and MGRS for Sentinel-2. This enables a user to spatially visualise the results in order to identify any spatial trends, patterns or highlighted regions worth further investigation.
The summary statistics simply provide the user with a quick overview for all measurements over the entire spatial area. Useful as the first go-to in identifying any extreme instances in the statistics, that can be further investigated.

Plotting and Reporting
----------------------

Provides the user with maps of the results of the comparison, as well as a basic LaTeX document containing plots of:

* minimum residual
* maximum residual
* 90th percentile of the residual
* 99th percentile of the residual
* percentage of pixels with a residual != 0
* skewness
* kurtosis

for each of the measurements within the NBAR, NBART and OA products.

LaTeX reports consisting of the above plots are also generated for each of the NBAR, NBART and OA products for ease of distribution.


## Examples of use

Available sub-commands
----------------------

```bash
ard-intercomparison --help
Usage: ard-intercomparison [OPTIONS] COMMAND [ARGS]...

  Entry point for the whole command module.

Options:
  --help  Show this message and exit.

Commands:
  collate           Collate the results of the product comparison.
  comparison        Test and Reference product intercomparison evaluation.
  pbs               Product intercomparison PBS workflow.
  plotting          Using the framing geometry, plot the results of the...
  query             Query the test and reference products to be used in the...
  query-filesystem  Query the test and reference products to be used in the...
```

The following is the help section for the pbs sub-command, which kicks off the entire workflow.

```bash
ard-intercomparison pbs --help
Usage: ard-intercomparison pbs [OPTIONS]

  Product intercomparison PBS workflow.

Options:
  --outdir DIRECTORY              The results output directory.  [required]
  --env PATH                      Environment script to source.
  --project TEXT                  Project code to allocate the compute costs.
                                  [required]

  -fsp, --filesystem-projects TEXT
                                  Required filesystem projects.
  --email TEXT                    Notification email address.
  --additional-filters JSON-DICT  Additional filters to use in the query.
                                  Specify as a JSON dictionary.

  --lat <FLOAT FLOAT>...          Latitudinal bounds.
  --lon <FLOAT FLOAT>...          Longitudinal bounds.
  --time [%Y-%m-%d]...            The time range to query.  [required]
  --db-env-reference TEXT         Database environment containing the
                                  reference data.  [required]

  --db-env-test TEXT              Database environment containing the test
                                  data.  [required]

  --product-name-reference TEXT   Product name for the reference data.
                                  [required]

  --product-name-test TEXT        Product name for the test data.  [required]
  --query-filesystem              If set, then instead of querying an ODC
                                  database, we query the filesystem instead.
                                  The commands product-name-test and
                                  --product-name-reference are used to specify
                                  the directory pathnames to the test and
                                  reference products. eg
                                  '/g/data/xu18/ga/ga_ls8c_ard_3'. The
                                  commands --db-env-test and --db-env-
                                  reference are used to specify the glob
                                  pattern to search, eg '*/*/2019/05/*/*.odc-
                                  metadata.yaml'.

  --help                          Show this message and exit.
```

Query via open data cube
------------------------

```bash
ard-intercomparison pbs --outdir $PWD/test --env $PWD/c3.env --time 2020-5-1 2020-5-2 --db-env-reference prod-db --db-env-test sample-db--product-name-reference ga_ls8c_ard_3 --product-name-test ga_ls8c_ard_3 --project u46
```

Query via filesystem
--------------------

If data hasn't been indexed into an Open Data Cube instance, datasets can still be discovered using the filesystem.
In this instance we need to use glob to discover the datasets. For example, "*/*/2019/05/*/*.odc-metadata.yaml", will look for data under the May 2019 directory structure which is organised (in this example) as *base/product_name/year/month/day/<data>*.
The *--time* options, do nothing in this instance, and are simply required to be populated.
Depending on how much data there is, the filesystem query could be slower to discover datasets.

```bash
ard-intercomparison pbs --outdir $PWD/test --env $PWD/c3.env --time 2020-5-1 2020-5-2 --db-env-reference "*/*/2019/05/*/*.odc-metadata.yaml" --db-env-test "*/*/2019/05/*/*.odc-metadata.yaml" --product-name-reference /g/data/xu18/ga/ga_ls8c_ard_3/ --product-name-test $PWD/pkgdir/ga_ls8c_ard_3/ --query-filesystem --project u46
```
