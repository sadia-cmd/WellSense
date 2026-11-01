Petrobras 3W Dataset - working dataset for KBS (CT-359) CCP project
===================================================================

Source
------
Official dataset: Petrobras 3W Dataset, version 2.0.0
https://github.com/petrobras/3W
Paper: Vargas et al., "3W Dataset 2.0.0: a realistic and public dataset with rare
undesirable real events in oil wells" (2025), https://arxiv.org/abs/2507.01048
License: CC BY 4.0

Files
-----
3W_real_small.csv       Working dataset (65,846 rows x 34 columns)
3W_data_dictionary.csv  Meaning and unit of every column

How this file was made from the official data
---------------------------------------------
1. Only REAL instances were used (files named WELL-*.parquet).
   Simulated and hand-drawn instances were excluded.
2. The official Parquet files were converted to CSV.
3. One raw reading per minute was kept (the original is one reading per second).
4. Up to 15 instances per event type were selected, spread across different wells.
5. Each fault instance was trimmed to 5 hours before the fault starts and
   15 hours after. Normal instances keep their first 10 hours.

No cleaning was done. Missing values, frozen sensors and outliers are left
exactly as Petrobras published them. Cleaning is part of the project's ETL.

Event types (event_type column)
-------------------------------
0 Normal operation
1 Abrupt increase of BSW (water fraction)
2 Spurious closure of DHSV (downhole safety valve)
3 Severe slugging
4 Flow instability
5 Rapid productivity loss
6 Quick restriction in PCK (production choke)
7 Scaling in PCK
8 Hydrate in production line
9 Hydrate in service line

Labels (class column)
---------------------
0 = normal, N = event N established, 100+N = event N developing (transient),
empty = unlabelled.
