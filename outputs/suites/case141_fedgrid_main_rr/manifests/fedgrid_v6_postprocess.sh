#!/usr/bin/env bash
set -euo pipefail

'C:\Users\ASUS\AppData\Local\Programs\Python\Python313\python.exe' 'C:\Users\ASUS\Desktop\runtime_bundle\summarize_fedgrid_suite_v6.py' --suite_root 'C:\Users\ASUS\Desktop\runtime_bundle\outputs\suites\case141_fedgrid_main_rr'
'C:\Users\ASUS\AppData\Local\Programs\Python\Python313\python.exe' 'C:\Users\ASUS\Desktop\runtime_bundle\export_fedgrid_tables_v6.py' --suite_root 'C:\Users\ASUS\Desktop\runtime_bundle\outputs\suites\case141_fedgrid_main_rr'
'C:\Users\ASUS\AppData\Local\Programs\Python\Python313\python.exe' 'C:\Users\ASUS\Desktop\runtime_bundle\make_fedgrid_figures_v6.py' --suite_root 'C:\Users\ASUS\Desktop\runtime_bundle\outputs\suites\case141_fedgrid_main_rr'
'C:\Users\ASUS\AppData\Local\Programs\Python\Python313\python.exe' 'C:\Users\ASUS\Desktop\runtime_bundle\make_fedgrid_report_v6.py' --suite_root 'C:\Users\ASUS\Desktop\runtime_bundle\outputs\suites\case141_fedgrid_main_rr'
