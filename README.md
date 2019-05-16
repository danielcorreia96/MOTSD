# TestSel_MOPSO
Code for the ESEC/FSE 2019 Tool Demo paper "A Multi-Objective Test Selection Tool using Test Suite Diagnosability"

## Dependencies + Assumptions
### General
- Python 3.7.2
- Minified OpenCover (fork) 
  - Code Comparison: https://github.com/OpenCover/opencover/compare/4.6.519...danielcorreia96:oc_2016_merged
  - Appveyor Artifact: https://ci.appveyor.com/project/danielcorreia96/opencover/builds/23686399
- Target source code is stored in SVN repository

### Python Libraries
- numpy: data manipulation and metrics calculations (https://github.com/numpy/numpy)
- jMetalPy: BMOPSO implementation (https://github.com/jMetal/jMetalPy)
- pyodbc: database integration (https://github.com/mkleehammer/pyodbc)
- PySvn: svn integration (https://github.com/dsoprea/PySvn)
- joblib: database results caching (https://github.com/joblib/joblib)
- faker: results anonymization for demonstration (https://github.com/joke2k/faker)

## Tool Usage Overview (3 main components)
### 1. Coverage Data Profiling (Offline/Ad-Hoc)
- Execute tests using OpenCover instrumentation and collect coverage data to build the required activity matrix.
- CLI: cov_profiler.py
- Input Dependencies:
   - Target source code and test suite is available in the system
   - A directory with lists of tests to be ran with coverage profiling
   - Configuration file: paths to minified OpenCover executable, NUnit test runner, input/output directories; OpenCover filters and cover_by_test to be used (following the docs at https://github.com/OpenCover/opencover/wiki/Usage); threshold value for methods visit counter.
   - A sample configuration file (with instructions) is provided at data/opencover/oc_config.json.sample
- Output: a set of xml reports at the chosen output directory
- Example Command: `python cov_profiler.py run data/opencover/oc_config.json`


### 2. Build Activity Matrix (Offline/Ad-Hoc)
- Process the obtained xml coverage reports into an activity matrix and some additional information to be used by the test selection pipeline
- CLI: parse_xml.py
- Input Dependencies:
  - Directory with xml coverage reports obtained in the previous component
  - Name/Id for the output json files
  - Name of the folder where the svn repository is stored in the local filesystem
- Output: 3 json files: an activity matrix, a map of row indices <-> test names and a map of column indices <-> method names
- Example Command: `python parse_xml data\reports\demo1\ demo1 trunk_demo1`


### 3. Test Selection Pipeline (Online)
- Run test selection pipeline for a given commit/revision id
- CLI: testsel_pipeline.py
- Input Dependencies:
  - JSON files from previous component -> only the path to activity matrix is passed as an argument, the other 2 are inferred
  - Database configuration file and SQL queries for metrics (samples provided in data/database)
  - Configuration file to setup branch path, dates range and ignored tests details 
  - CLI -o option: provide order of objectives to be used
  - Available metrics:
    - ddu: DDU
    - coverage: method coverage (raw sum)
    - norm_coverage: method coverage (normalized to 0/1)
    - n_tests: total number of tests selected
    - fails: total number of test failures from build history
    - exec_times: total "expected" execution time for the selected tests using build history info
  - CLI --masked option: anonymize output results by replacing the file/test names with fake ones
- Example command (interactive): `python testsel_pipeline.py single -o ddu -o fails data\jsons\actmatrix_demo1.json data\demo1.config`
- Example command (batch mode): `python testsel_pipeline.py demo -o ddu -o fails data\jsons\actmatrix_demo1.json data\demo1.config`
  

