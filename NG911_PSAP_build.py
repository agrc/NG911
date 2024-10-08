# -*- coding: utf-8 -*-
"""
Created on Mon Dec 28 14:48:42 2020
@author: eneemann
Script to build NG911 PSAP boundaries from SGID data

"""

import arcpy
import os
import time
from datetime import datetime
import pandas as pd

# Start timer and print start time in UTC
start_time = time.time()
readable_start = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
print("The script start time is {}".format(readable_start))

######################
#  Set up variables  #
######################

# Set up databases (SGID must be changed based on user's path)
SGID = r"C:\Users\gbunce\AppData\Roaming\ESRI\ArcGISPro\Favorites\internal@SGID@internal.agrc.utah.gov.sde"
ng911_db = r"C:\Users\gbunce\Documents\projects\NG911\polygon_datasets\NG911_PSAPs\NG911_data_updates.gdb"
## ng911_db = r"C:\NG911\NG911_data_updates.gdb" (erik's path)

arcpy.env.workspace = ng911_db
arcpy.env.overwriteOutput = True
arcpy.env.qualifiedFieldNames = False

today = time.strftime("%Y%m%d")

SGID_counties = os.path.join(SGID, 'SGID.BOUNDARIES.Counties')
counties = os.path.join(ng911_db, f'SGID_counties_{today}')
SGID_munis = os.path.join(SGID, 'SGID.BOUNDARIES.Municipalities')
munis = os.path.join(ng911_db, f'SGID_munis_{today}')
unique = os.path.join(ng911_db, 'NG911_PSAP_unique_UTM')
psap_schema = os.path.join(ng911_db, 'NG911_PSAP_Schema')
psap_working = os.path.join(ng911_db, f'NG911_PSAP_bound_working_{today}')

# List of PSAPs with known "nested holes" that need to be fixed - use DsplayName
nested_list = ['Salt Lake Valley Emergency Communications Center', 'Central Utah 911']

# Read in CSV of PSAP info into pandas dataframe, use df to build dictionaries
print("Reading in CSV to get PSAP info ...")
## textfile_dir = r'C:\Users\eneemann\Desktop\Python Code\NG911' (erik's path)
textfile_dir = r"C:\Users\gbunce\Documents\projects\NG911\polygon_datasets\NG911_PSAPs"
## work_dir =r'C:\NG911'
work_dir = r"C:\Users\gbunce\Documents\projects\NG911\polygon_datasets\working_directory"

csv = os.path.join(textfile_dir, 'PSAP_info.csv')
psap_info = pd.read_csv(csv)

# Create dictionary for single county PSAPs
single_county = psap_info[psap_info['Type'] == 'single county']
single_county.drop(['Key', 'Type', 'Munis'], axis=1, inplace=True)
single_county_dict = single_county.set_index('PSAP').to_dict()['Counties']

# Create dictionary for multi county PSAPs
multi_county = psap_info[psap_info['Type'] == 'multi county']
multi_county.drop(['Key', 'Type', 'Munis'], axis=1, inplace=True)
multi_county_dict = multi_county.set_index('PSAP').to_dict()['Counties']

# Create dictionary for single muni PSAPs
single_muni = psap_info[psap_info['Type'] == 'single muni']
single_muni.drop(['Key', 'Type', 'Counties'], axis=1, inplace=True)
single_muni_dict = single_muni.set_index('PSAP').to_dict()['Munis']

# Create dictionary for multi muni PSAPs
multi_muni = psap_info[psap_info['Type'] == 'multi muni']
multi_muni.drop(['Key', 'Type', 'Counties'], axis=1, inplace=True)
multi_muni_dict = multi_muni.set_index('PSAP').to_dict()['Munis']

# Create dictionary for mixed PSAPs (county & muni boundaries)
mixed = psap_info[psap_info['Type'] == 'mixed']
mixed.drop(['Key', 'Type'], axis=1, inplace=True)
mixed_county_dict = mixed.set_index('PSAP').to_dict()['Counties']
mixed_muni_dict = mixed.set_index('PSAP').to_dict()['Munis']

# Create dictionary for unique PSAPs (county & muni boundaries)
unique = psap_info[psap_info['Type'] == 'unique']
unique.drop(['Key', 'Type'], axis=1, inplace=True)
unique_county_df = unique.dropna(subset=['Counties'])
unique_muni_df = unique.dropna(subset=['Munis'])
unique_county_dict = unique_county_df.set_index('PSAP').to_dict()['Counties']
unique_muni_dict = unique_muni_df.set_index('PSAP').to_dict()['Munis']

# Read in CSV of NGUIDs for PSAPs
print("Reading in CSV to get NGUIDs ...")
# textfile_dir = r'C:\Users\eneemann\Desktop\Neemann\NG911\NG911_project'
psap_csv = os.path.join(textfile_dir, 'psap_nguid.csv')
psap_df = pd.read_csv(psap_csv)

# Create dictionary for PSAP NGUIDs
nguid_dict = psap_df.set_index('DsplayName').to_dict()['ES_NGUID']
uri_dict = psap_df.set_index('DsplayName').to_dict()['URI']
county_dict = psap_df.set_index('DsplayName').to_dict()['County']

# Set up variables for static table and feature class
sgid_data_table = os.path.join(ng911_db, 'SGID_PSAP_data_to_join_20210616')
unique = os.path.join(ng911_db, 'NG911_PSAP_unique_UTM') # Hill AFB and NN

# Set up more variables for intermediate and final feature classes
single_county_temp = os.path.join(ng911_db, 'NG911_psap_bound_sc_temp')
multi_county_temp = os.path.join(ng911_db, 'NG911_psap_bound_mc_temp')
all_county_temp = os.path.join(ng911_db, 'NG911_psap_bound_allc_temp')
mc_diss = os.path.join(ng911_db, 'NG911_psap_bound_mc_diss')
mixed_temp = os.path.join(ng911_db, 'NG911_psap_bound_mixed_temp')
mixed_diss = os.path.join(ng911_db, 'NG911_psap_bound_mixed_diss')
all_mixed_temp = os.path.join(ng911_db, 'NG911_psap_bound_allmixed_temp')
single_muni_temp = os.path.join(ng911_db, 'NG911_psap_bound_sm_temp')
multi_muni_temp = os.path.join(ng911_db, 'NG911_psap_bound_mm_temp')
mm_diss = os.path.join(ng911_db, 'NG911_psap_bound_mm_diss')
county_single_muni_temp = os.path.join(ng911_db, 'NG911_psap_bound_allc_sm_temp')
all_county_muni_temp = os.path.join(ng911_db, 'NG911_psap_bound_allcm_temp')
fixed_edges = os.path.join(ng911_db, 'NG911_PSAP_fixed_edges')
poly_fixes = os.path.join(ng911_db, 'NG911_PSAP_poly_fixes')
unique_muni_temp = os.path.join(ng911_db, 'NG911_PSAP_um_temp')
unique_muni_erased = os.path.join(ng911_db, 'NG911_PSAP_um_erased')
unique_county_temp = os.path.join(ng911_db, 'NG911_PSAP_uc_temp')
unique_county_erased = os.path.join(ng911_db, 'NG911_PSAP_uc_erased')
unique_county_muni_temp = os.path.join(ng911_db, 'NG911_psap_bound_uniquecm_temp')
unique_diss = os.path.join(ng911_db, 'NG911_PSAP_unique_diss') # Hill AFB and NN
all_unique_temp = os.path.join(ng911_db, 'NG911_PSAP_allu_temp') # add in others before cutting in
nested_temp = os.path.join(ng911_db, 'NG911_PSAP_nested_temp') # features with nested holes
nested_fixes = os.path.join(ng911_db, 'NG911_PSAP_nested_fixes') # nested holes are fixed
all_fixed_temp = os.path.join(ng911_db, 'NG911_PSAP_allfixed_temp') # combined fixed features
sgid_final = os.path.join(ng911_db, 'NG911_psap_bound_final_sgid_' + today) # create version for SGID
sgid_final_no_uris = os.path.join(ng911_db, 'NG911_psap_final_sgid_NoURIs_' + today) # create version for SGID without public URIs
psap_wgs84 = os.path.join(ng911_db, 'NG911_psap_bound_final_WGS84_' + today) # create version for NG911

fc_list = [counties, munis, single_county_temp, multi_county_temp, all_county_temp,
           mc_diss, mixed_temp, mixed_diss, all_mixed_temp, single_muni_temp, multi_muni_temp,
           mm_diss, county_single_muni_temp, all_county_muni_temp, unique_muni_temp,
           unique_muni_erased, unique_county_temp, unique_county_muni_temp, unique_diss, all_unique_temp,
           nested_temp, nested_fixes, all_fixed_temp]

for fc in fc_list:
    if arcpy.Exists(fc):
        print(f'Deleting {fc} ...')
        arcpy.management.Delete(fc)
        
# Copy SGID counties and munis to local fc
arcpy.management.CopyFeatures(SGID_counties, counties)
arcpy.management.CopyFeatures(SGID_munis, munis)

# Upper case the names of the munis
# Populate fields with correct information
update_count = 0
fields = ['NAME']
with arcpy.da.UpdateCursor(munis, fields) as update_cursor:
    for row in update_cursor:
        row[0] = row[0].upper()
        update_count += 1
        update_cursor.updateRow(row)
print(f"Total count of upper case muni name updates is: {update_count}")

###############
#  Functions  #
###############

def add_single_county():
    # Build single county PSAP boundaries from county boundaries
    print("Building single county PSAPs from county boundaries ...")
    arcpy.management.CopyFeatures(psap_schema, single_county_temp)
    if arcpy.Exists("county_lyr"):
        arcpy.management.Delete("county_lyr")
    arcpy.management.MakeFeatureLayer(counties, "county_lyr")
    
    # Field Map county name into psap schema fields
    fms = arcpy.FieldMappings()
    
    # NAME to DsplayName
    fm_name = arcpy.FieldMap()
    fm_name.addInputField("county_lyr", "NAME")
    output = fm_name.outputField
    output.name = "DsplayName"
    fm_name.outputField = output
    fms.addFieldMap(fm_name)
    
    # Complete the append with field mapping and query
    sc_list = list(single_county_dict.values())
    print(sc_list)
    sc_query = f"NAME IN ({sc_list})".replace('[', '').replace(']', '')
    print(sc_query)
    
    arcpy.management.Append("county_lyr", single_county_temp, "NO_TEST", field_mapping=fms, expression=sc_query)
    
    # Populate fields with correct information
    update_count = 0
    fields = ['DsplayName']
    with arcpy.da.UpdateCursor(single_county_temp, fields) as update_cursor:
        print("Looping through rows in FC ...")
        for row in update_cursor:
            for k,v in single_county_dict.items():
                if v == row[0]:
                    row[0] = k
            update_count += 1
            update_cursor.updateRow(row)
    print(f"Total count of single county updates is: {update_count}")


def add_multi_county():
    # Build multi county PSAP boundaries from county boundaries
    print("Building multi county PSAPs from county boundaries ...")
    arcpy.management.CopyFeatures(psap_schema, multi_county_temp)
    if arcpy.Exists("county_lyr"):
        arcpy.management.Delete("county_lyr")
    arcpy.management.MakeFeatureLayer(counties, "county_lyr")
       
    # Field Map county name into psap schema fields
    fms = arcpy.FieldMappings()
    
    # NAME to DsplayName
    fm_name = arcpy.FieldMap()
    fm_name.addInputField("county_lyr", "NAME")
    output = fm_name.outputField
    output.name = "DsplayName"
    fm_name.outputField = output
    fms.addFieldMap(fm_name)
    
    # Build query to select multi county 
    mc_list = [ item.split(',') for item in list(multi_county_dict.values())]
    mc_list = [y.strip() for x in mc_list for y in x]
    print(mc_list)
    mc_query = f"NAME IN ({mc_list})".replace('[', '').replace(']', '')
    print(mc_query)
    
    # Complete the append with field mapping and query to get all counties in group
    arcpy.management.Append("county_lyr", multi_county_temp, "NO_TEST", field_mapping=fms, expression=mc_query)
    
    # Loop through and populate fields with appropriate information and rename to multi county psaps
    update_count = 0
    fields = ['DsplayName']
    with arcpy.da.UpdateCursor(multi_county_temp, fields) as update_cursor:
        print("Looping through rows in FC ...")
        for row in update_cursor:
            for k,v in multi_county_dict.items():
                # print(f'key: {k}     value: {v}')
                if row[0] in v:
                    # print(f'Found {row[0]} in {v} ...')
                    row[0] = k
            update_count += 1
            update_cursor.updateRow(row)
    print(f"Total count of multi county updates is: {update_count}")
        
    print("Dissolving multi county PSAPs ...")
    arcpy.management.Dissolve(multi_county_temp, mc_diss, "DsplayName")
    
    # Append multi county psaps into single county psaps fc
    arcpy.management.CopyFeatures(single_county_temp, all_county_temp)
    print("Appending multi county PSAPs with single county PSAPs ...")
    arcpy.management.Append(mc_diss, all_county_temp, "NO_TEST")
    

def add_mixed_psaps():
    # Build mixed PSAP boundaries from county and muni boundaries
    print("Building mixed PSAPs from county and muni boundaries ...")
    arcpy.management.CopyFeatures(psap_schema, mixed_temp)
    if arcpy.Exists("county_lyr"):
        arcpy.management.Delete("county_lyr")
    if arcpy.Exists("muni_lyr"):
        arcpy.management.Delete("muni_lyr")
    arcpy.management.MakeFeatureLayer(counties, "county_lyr")
    arcpy.management.MakeFeatureLayer(munis, "muni_lyr")
    
    # Assemble counties
    # Field Map county name into psap schema fields
    fms = arcpy.FieldMappings()
    
    # NAME to DsplayName
    fm_name = arcpy.FieldMap()
    fm_name.addInputField("county_lyr", "NAME")
    output = fm_name.outputField
    output.name = "DsplayName"
    fm_name.outputField = output
    fms.addFieldMap(fm_name)
    
    # Build query to select multi county 
    mixc_list = [ item.split(',') for item in list(mixed_county_dict.values())]
    mixc_list = [y.strip() for x in mixc_list for y in x]
    print(mixc_list)
    mixc_query = f"NAME IN ({mixc_list})".replace('[', '').replace(']', '')
    print(mixc_query)
    
    # Complete the append with field mapping and query to get all counties in group
    arcpy.management.Append("county_lyr", mixed_temp, "NO_TEST", field_mapping=fms, expression=mixc_query)
    
    # Assemble munis and append
    # Field Map muni name into psap schema fields
    fms = arcpy.FieldMappings()
    
    # NAME to DsplayName
    fm_name = arcpy.FieldMap()
    fm_name.addInputField("muni_lyr", "NAME")
    output = fm_name.outputField
    output.name = "DsplayName"
    fm_name.outputField = output
    fms.addFieldMap(fm_name)
    
    # Build query to select multi muni 
    mixm_list = [ item.split(',') for item in list(mixed_muni_dict.values())]
    mixm_list = [y.strip() for x in mixm_list for y in x]
    print(mixm_list)
    mixm_query = f"NAME IN ({mixm_list})".replace('[', '').replace(']', '')
    print(mixm_query)
    
    # Complete the append with field mapping and query to get all counties in group
    arcpy.management.Append("muni_lyr", mixed_temp, "NO_TEST", field_mapping=fms, expression=mixm_query)
     
    # Loop through and populate fields with appropriate information and rename to mixed psaps
    update_count = 0
    fields = ['DsplayName']
    with arcpy.da.UpdateCursor(mixed_temp, fields) as update_cursor:
        print("Looping through rows in FC ...")
        for row in update_cursor:
            for k,v in mixed_county_dict.items():
                # print(f'key: {k}     value: {v}')
                if row[0] in v:
                    # print(f'Found {row[0]} in {v} ...')
                    row[0] = k
            for k,v in mixed_muni_dict.items():
                # print(f'key: {k}     value: {v}')
                if row[0] in v:
                    # print(f'Found {row[0]} in {v} ...')
                    row[0] = k
            update_count += 1
            update_cursor.updateRow(row)
    print(f"Total count of mixed PSAP updates is: {update_count}")
        
    print("Dissolving mixed PSAPs ...")
    arcpy.management.Dissolve(mixed_temp, mixed_diss, "DsplayName")
    
    # Drop in mixed psaps via erase/append
    print("Adding mixed PSAPs into working psaps layer ...")
    # Erase
    arcpy.analysis.Erase(all_county_temp, mixed_diss, all_mixed_temp)
    # Append
    arcpy.management.Append(mixed_diss, all_mixed_temp, "NO_TEST")    


def add_single_muni():
    # Build single muni PSAP boundaries from muni boundaries
    print("Building single muni PSAPs from muni boundaries ...")
    arcpy.management.CopyFeatures(psap_schema, single_muni_temp)
    if arcpy.Exists("muni_lyr"):
        arcpy.management.Delete("muni_lyr")
    arcpy.management.MakeFeatureLayer(munis, "muni_lyr")
    
    # Field Map muni name into psap schema fields
    fms = arcpy.FieldMappings()
    
    # NAME to DsplayName
    fm_name = arcpy.FieldMap()
    fm_name.addInputField("muni_lyr", "NAME")
    output = fm_name.outputField
    output.name = "DsplayName"
    fm_name.outputField = output
    fms.addFieldMap(fm_name)
    
    # Complete the append with field mapping and query
    sm_list = list(single_muni_dict.values())
    print(sm_list)
    sm_query = f"NAME IN ({sm_list})".replace('[', '').replace(']', '')
    print(sm_query)
    
    arcpy.management.Append("muni_lyr", single_muni_temp, "NO_TEST", field_mapping=fms, expression=sm_query)
    
    # Populate fields with correct information
    update_count = 0
    fields = ['DsplayName']
    with arcpy.da.UpdateCursor(single_muni_temp, fields) as update_cursor:
        print("Looping through rows in FC ...")
        for row in update_cursor:
            for k,v in single_muni_dict.items():
                if v == row[0]:
                    row[0] = k
            update_count += 1
            update_cursor.updateRow(row)
    print(f"Total count of single muni updates is: {update_count}")
    
    # Drop in single muni psaps via erase/append
    print("Adding single muni PSAPs into working psaps layer ...")
    # Erase
    arcpy.analysis.Erase(all_mixed_temp, single_muni_temp, county_single_muni_temp)
    # Append
    arcpy.management.Append(single_muni_temp, county_single_muni_temp, "NO_TEST")


def add_multi_muni():
    # Build multi muni PSAP boundaries from muni boundaries
    print("Building multi muni PSAPs from muni boundaries ...")
    arcpy.management.CopyFeatures(psap_schema, multi_muni_temp)
    if arcpy.Exists("muni_lyr"):
        arcpy.management.Delete("muni_lyr")
    arcpy.management.MakeFeatureLayer(munis, "muni_lyr")
       
    # Field Map muni name into psap schema fields
    fms = arcpy.FieldMappings()
    
    # NAME to DsplayName
    fm_name = arcpy.FieldMap()
    fm_name.addInputField("muni_lyr", "NAME")
    output = fm_name.outputField
    output.name = "DsplayName"
    fm_name.outputField = output
    fms.addFieldMap(fm_name)
    
    # Build query to select multi muni 
    mm_list = [ item.split(',') for item in list(multi_muni_dict.values())]
    mm_list = [y.strip() for x in mm_list for y in x]
    print(mm_list)
    mm_query = f"NAME IN ({mm_list})".replace('[', '').replace(']', '')
    print(mm_query)
    
    # Complete the append with field mapping and query to get all munis in group
    arcpy.management.Append("muni_lyr", multi_muni_temp, "NO_TEST", field_mapping=fms, expression=mm_query)
    
    # Loop through and populate fields with appropriate information and rename to multi muni psaps
    update_count = 0
    fields = ['DsplayName']
    with arcpy.da.UpdateCursor(multi_muni_temp, fields) as update_cursor:
        print("Looping through rows in FC ...")
        for row in update_cursor:
            for k,v in multi_muni_dict.items():
                # print(f'key: {k}     value: {v}')
                if row[0] in v:
                    # print(f'Found {row[0]} in {v} ...')
                    row[0] = k
            update_count += 1
            update_cursor.updateRow(row)
    print(f"Total count of multi muni updates is: {update_count}")
        
    print("Dissolving multi muni PSAPs ...")
    arcpy.management.Dissolve(multi_muni_temp, mm_diss, "DsplayName")
    
    # Drop in multi muni psaps via erase/append
    print("Adding multi muni PSAPs into working psaps layer ...")
    # Erase
    arcpy.analysis.Erase(county_single_muni_temp, mm_diss, all_county_muni_temp)
    # Append
    arcpy.management.Append(mm_diss, all_county_muni_temp, "NO_TEST")
    
    
def add_unique_psaps():
    # Assemble VECC, Metro EC based on mixed boundaries and append static boundaries (Hill AFB -- Navajo Nation not longer used)
    print("Building unique PSAPs from county, muni, and fixed boundaries ...")
    arcpy.management.CopyFeatures(psap_schema, unique_muni_temp)
    arcpy.management.CopyFeatures(psap_schema, unique_county_temp)
    if arcpy.Exists("county_lyr"):
        arcpy.management.Delete("county_lyr")
    if arcpy.Exists("muni_lyr"):
        arcpy.management.Delete("muni_lyr")
    arcpy.management.MakeFeatureLayer(counties, "county_lyr")
    arcpy.management.MakeFeatureLayer(munis, "muni_lyr")
    
    # Assemble munis
    # Field Map muni name into psap schema fields
    fms = arcpy.FieldMappings()
    
    # NAME to DsplayName
    fm_name = arcpy.FieldMap()
    fm_name.addInputField("muni_lyr", "NAME")
    output = fm_name.outputField
    output.name = "DsplayName"
    fm_name.outputField = output
    fms.addFieldMap(fm_name)
    
    # Build query to select unique muni 
    unim_list = [ item.split(',') for item in list(unique_muni_dict.values())]
    unim_list = [y.strip() for x in unim_list for y in x]
    print(unim_list)
    unim_query = f"NAME IN ({unim_list})".replace('[', '').replace(']', '')
    print(unim_query)
    
    # Complete the append with field mapping and query to get all munis in group
    arcpy.management.Append("muni_lyr", unique_muni_temp, "NO_TEST", field_mapping=fms, expression=unim_query)
    
    # Buffer fixed edge layer
    print("Buffering fixed edges and erasing muni layer ...")
    arcpy.analysis.Buffer(fixed_edges, 'in_memory\\edge_buffer', '100 Meters')
    
    # Erase current muni layer with buffer
    arcpy.analysis.Erase(unique_muni_temp, 'in_memory\\edge_buffer', unique_muni_erased)
    
    # Append polygon fixes into erased muni layer
    # polygon fixes with NULL names are ignored from the solution
    no_nulls = "DsplayName IS NOT NULL AND Type = 'muni'"
    print("Appending polygon fixes to erased muni layer ...")
    arcpy.management.Append(poly_fixes, unique_muni_erased, "NO_TEST", expression=no_nulls)
      
    # Assemble counties and cut in poly-fixed muni layer
    # Field Map county name into psap schema fields
    fms = arcpy.FieldMappings()
    
    # NAME to DsplayName
    fm_name = arcpy.FieldMap()
    fm_name.addInputField("county_lyr", "NAME")
    output = fm_name.outputField
    output.name = "DsplayName"
    fm_name.outputField = output
    fms.addFieldMap(fm_name)
    
    # Build query to select unique county 
    unic_list = [ item.split(',') for item in list(unique_county_dict.values())]
    unic_list = [y.strip() for x in unic_list for y in x]
    print(unic_list)
    unic_query = f"NAME IN ({unic_list})".replace('[', '').replace(']', '')
    print(unic_query)
    
    # Complete the append with field mapping and query to create county layer
    arcpy.management.Append("county_lyr", unique_county_temp, "NO_TEST", field_mapping=fms, expression=unic_query)
    
    # Append polygon fixes into the county layer
    # polygon fixes with NULL names are ignored from the solution
    no_nulls = "DsplayName IS NOT NULL AND Type = 'county'"
    print("Appending polygon fixes to erased county layer ...")
    arcpy.management.Append(poly_fixes, unique_muni_erased, "NO_TEST", expression=no_nulls)
    

    # Erase county layer with poly-fixed muni layer
    arcpy.analysis.Erase(unique_county_temp, unique_muni_erased, unique_county_muni_temp)
    
    # Append poly-fixed muni layer into county layer with holes
    print("Appending poly-fixed muni layer to erased county layer ...")
    arcpy.management.Append(unique_muni_erased, unique_county_muni_temp, "NO_TEST")
    
    # Loop through and populate fields with appropriate information and rename polygons
    update_count = 0
    fields = ['DsplayName']
    with arcpy.da.UpdateCursor(unique_county_muni_temp, fields) as update_cursor:
        print("Looping through rows in FC ...")
        for row in update_cursor:
            for k,v in unique_county_dict.items():
                # print(f'key: {k}     value: {v}')
                if row[0] in v:
                    # print(f'Found {row[0]} in {v} ...')
                    row[0] = k
            for k,v in unique_muni_dict.items():
                # print(f'key: {k}     value: {v}')
                if row[0] in v:
                    # print(f'Found {row[0]} in {v} ...')
                    row[0] = k
            update_count += 1
            update_cursor.updateRow(row)
    print(f"Total count of unique PSAP updates is: {update_count}")
    
    # Now append the unique/static PSAPS (Hill AFB, NN) into the working layer
    print("Appending unique/static PSAPs ...")
    arcpy.management.Append(unique, unique_county_muni_temp, "NO_TEST")   
    
    print("Dissolving unique PSAPs ...")
    arcpy.management.Dissolve(unique_county_muni_temp, unique_diss, "DsplayName")
    
    # Drop in unique psaps via erase/append
    print("Adding unique PSAPs into working psaps layer ...")
    # Erase
    arcpy.analysis.Erase(all_county_muni_temp, unique_diss, all_unique_temp)
    # Append
    arcpy.management.Append(unique_diss, all_unique_temp, "NO_TEST") 
     
    
def calc_fields(): 
    # Loop through and populate fields with appropriate information
    update_count = 0
        #          0           1           2           3          4            5           6             7          8           9
    fields = ['DsplayName', 'Source', 'DateUpdate', 'State', 'ServiceNum', 'ES_NGUID', 'OBJECTID', 'ServiceURI', 'County', 'DiscrpAgID']
    with arcpy.da.UpdateCursor(all_unique_temp, fields) as update_cursor:
        print("Looping through rows in FC ...")
        for row in update_cursor:
            row[1] = 'UGRC'
            row[2] = datetime.now()
            row[3] = 'UT'
            if 'Colorado' in row[0]: row[3] = 'AZ'
            row[4] = '911'
#            row[5] = f'PSAP{row[6]}@gis.utah.gov'
            row[5] = nguid_dict[f'{row[0]}']
            row[7] = uri_dict[f'{row[0]}']
            row[8] = county_dict[f'{row[0]}']
            row[9] = 'gis.utah.gov/data/911'
            update_count += 1
            update_cursor.updateRow(row)
    print(f"Total count of attribute updates is: {update_count}")
    

def build_sgid():
    if arcpy.Exists(sgid_final):
        arcpy.management.Delete(sgid_final)
    
    joined_data = arcpy.management.JoinField(all_unique_temp, "DsplayName", sgid_data_table, "DsplayName")
    # Remove extra field from join
    arcpy.management.DeleteField(all_unique_temp, "DsplayName_1")
    
    # Copy sgid data table to all_unique_temp feature class
    # This is a copy of the PSAP Boundaries feature class with all fields for SGID
    arcpy.management.CopyFeatures(joined_data, sgid_final)
    
    # Make another version without URIs populated
    arcpy.management.CopyFeatures(sgid_final, sgid_final_no_uris)
        
    # Delete the URI field - can still truncate/load into SGID
    arcpy.management.DeleteField(sgid_final_no_uris, "ServiceURI")


def remove_nested_holes():
    # Converted features with nested holes to singlepart polygons
    print("Fixing PSAPs with nested holes ...")
    if arcpy.Exists("nested_lyr"):
        arcpy.management.Delete("nested_lyr")
    nested_query = f"DsplayName IN ({nested_list})".replace('[', '').replace(']', '')
    arcpy.management.MakeFeatureLayer(all_unique_temp, "nested_lyr", nested_query)
    arcpy.management.CopyFeatures("nested_lyr", nested_temp)
    
    # Explode nested features into singlepart features
    arcpy.management.MultipartToSinglepart(nested_temp, nested_fixes)
    
    # Drop nested fixes back in via erase/append
    print("Adding nested PSAPs back into working psaps layer ...")
    # Erase
    arcpy.analysis.Erase(all_unique_temp, nested_fixes, all_fixed_temp)
    # Append
    arcpy.management.Append(nested_fixes, all_fixed_temp, "NO_TEST") 


def renumber(val, record, base):
    Start = 1  
    Interval = 1 
    if (record == 0):  
        record = Start  
    else:  
        record += Interval
     
    output = val.replace(base, base + str(record).zfill(3))
    
    return output
    
    
def recalc_nguids():
    # Loop through to recalculate NGUIDS on exploded features
    nguid_count = 0
    rec = 0
    nested_query = f"DsplayName IN ({nested_list})".replace('[', '').replace(']', '')
    #              0             1          2
    fields = ['DsplayName', 'ES_NGUID', 'OBJECTID']
    with arcpy.da.UpdateCursor(all_fixed_temp, fields, nested_query) as update_cursor:
        print("Recalculating NGUIDS on exploded features ...")
        for row in update_cursor:
            base_guid = row[1].split('@', 1)[0]
            updated = renumber(row[1], rec, base_guid)
            row[1] = updated   
            rec += 1
            nguid_count += 1
            update_cursor.updateRow(row)
    print(f"Total count of NGUID updates is: {nguid_count}")


def project_to_WGS84():
    # Project final data to WGS84
    print("Projecting final psap boundaries into WGS84 ...")
    sr = arcpy.SpatialReference("WGS 1984")
    arcpy.management.Project(all_fixed_temp, psap_wgs84, sr, "WGS_1984_(ITRF00)_To_NAD_1983")


def export_to_shapefile():
    shape_folder = "0 NG911_PSAP_Shapefile_" + today
    out_shape_dir = os.path.join(work_dir, shape_folder)
    if os.path.isdir(out_shape_dir) == False:
        os.mkdir(out_shape_dir)

    shape_name = "UT_PSAPs_WGS84_" + today
    arcpy.conversion.FeatureClassToFeatureClass(psap_wgs84, out_shape_dir, shape_name)



##########################
#  Call Functions Below  #
##########################

function_time = time.time()    

add_single_county()
add_multi_county()
add_mixed_psaps()
add_single_muni()
add_multi_muni()
add_unique_psaps()
calc_fields()
build_sgid()
remove_nested_holes()
recalc_nguids()
project_to_WGS84()
export_to_shapefile()

print("Time elapsed in functions: {:.2f}s".format(time.time() - function_time))

print("Script shutting down ...")
# Stop timer and print end time in UTC
readable_end = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
print("The script end time is {}".format(readable_end))
print("Time elapsed: {:.2f}s".format(time.time() - start_time))