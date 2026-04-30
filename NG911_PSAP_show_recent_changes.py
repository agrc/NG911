# -*- coding: utf-8 -*-
"""
Created on Fri Jan 9 09:06:42 2026
@author: eneemann
Script to show differences between two PSAP feature classes

"""

import arcpy
import os
import time
from datetime import datetime

# Start timer and print start time in UTC
start_time = time.time()
readable_start = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
print("The script start time is {}".format(readable_start))

######################
#  Set up variables  #
######################

arcpy.env.overwriteOutput = True
arcpy.env.qualifiedFieldNames = False

today = time.strftime("%Y%m%d")

before_layer = r"C:\Users\emneemann\Documents\NG911\polygon_datasets\working_directory\0 NG911_PSAP_Shapefile_20251219 - Weber\Final\UT_PSAPs_WGS84_20251224_change_1.shp"
after_layer = r"C:\Users\emneemann\Documents\NG911\polygon_datasets\working_directory\0 NG911_PSAP_Shapefile_20260401\UT_PSAPs_WGS84_20260401.shp"
in_features = [before_layer, after_layer]

out_dir = r'C:\Users\emneemann\Documents\NG911\polygon_datasets\working_directory'
out_union_name = f'PSAP_union_{today}'
out_union_path = rf'{out_dir}\{out_union_name}.shp'

#: Perform union
arcpy.analysis.Union(in_features, out_union_path, "ALL")

#: Export features with different DsplayName fields (these are the areas that changed)
out_changes_name = f'PSAP_changes_{today}'
out_changes_path = rf'{out_dir}\{out_changes_name}.shp'
where_clause = "DsplayName <> DsplayNa_1"
arcpy.conversion.ExportFeatures(out_union_path, out_changes_path, where_clause)


print("Script shutting down ...")
# Stop timer and print end time
readable_end = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
print("The script end time is {}".format(readable_end))
print("Time elapsed: {:.2f}s".format(time.time() - start_time))