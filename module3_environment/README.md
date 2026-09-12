1. Project Structure

module3_environment
│
├── configs/
│   └── config.yaml
│
├── data_cache/
│   ├── era5/
│   └── glorys/
│
├── outputs/
│   └── source_estimates/
│
├── src/
│   ├── __init__.py
│   ├── fetch_era5.py
│   ├── fetch_glorys.py
│   ├── interpolation.py
│   ├── backward_advection.py
│   ├── uncertainty.py
│   ├── source_estimation_pipeline.py
│   └── utils.py
│
└── tests/ ( not included rn, waiting for trained data!!)
    ├── test_fetch_era5.py
    ├── test_fetch_glorys.py
    ├── test_interpolation.py
    ├── test_backward_advection.py
    └── test_pipeline.py

2. INSTALL: install numpy xarray netCDF4 pyproj pyyaml cdsapi copernicusmarine

3. TO RUN : run from the project root directory using
   -m src.source_estimation

   4. `source_estimate.json` is generated at the end of run
