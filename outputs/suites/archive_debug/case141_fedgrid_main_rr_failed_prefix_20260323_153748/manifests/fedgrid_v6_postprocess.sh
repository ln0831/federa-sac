#!/usr/bin/env bash
set -euo pipefail

'D:\Anaconda\envs\tianshou_env\python.exe' 'C:\Users\ASUS\Desktop\fuxian\fedgrid_runtime_bundle_v1\runtime_bundle\summarize_fedgrid_suite_v6.py' --suite_root 'C:\Users\ASUS\Desktop\fuxian\fedgrid_runtime_bundle_v1\runtime_bundle\outputs\suites\case141_fedgrid_main_rr'
'D:\Anaconda\envs\tianshou_env\python.exe' 'C:\Users\ASUS\Desktop\fuxian\fedgrid_runtime_bundle_v1\runtime_bundle\export_fedgrid_tables_v6.py' --suite_root 'C:\Users\ASUS\Desktop\fuxian\fedgrid_runtime_bundle_v1\runtime_bundle\outputs\suites\case141_fedgrid_main_rr'
'D:\Anaconda\envs\tianshou_env\python.exe' 'C:\Users\ASUS\Desktop\fuxian\fedgrid_runtime_bundle_v1\runtime_bundle\make_fedgrid_figures_v6.py' --suite_root 'C:\Users\ASUS\Desktop\fuxian\fedgrid_runtime_bundle_v1\runtime_bundle\outputs\suites\case141_fedgrid_main_rr'
'D:\Anaconda\envs\tianshou_env\python.exe' 'C:\Users\ASUS\Desktop\fuxian\fedgrid_runtime_bundle_v1\runtime_bundle\make_fedgrid_report_v6.py' --suite_root 'C:\Users\ASUS\Desktop\fuxian\fedgrid_runtime_bundle_v1\runtime_bundle\outputs\suites\case141_fedgrid_main_rr'
