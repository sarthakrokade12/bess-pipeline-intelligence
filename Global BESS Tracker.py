import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ==========================================
# 1. FILE PATH CONFIGURATION
# ==========================================
# Using relative paths so the script runs on any machine
caiso_file = 'CAISO_Data.xlsx' 
aemo_file = 'Australia_Data.xlsx'

# ==========================================
# 2. CAISO DATA PIPELINE
# ==========================================
print("Processing CAISO Data...")

# Load Data
caiso_cluster_15 = pd.read_excel(caiso_file, sheet_name='Cluster 15 ')
caiso_withdrawn = pd.read_excel(caiso_file, sheet_name='Withdrawn')

# Clean headers and assign status
caiso_cluster_15.rename(columns=lambda x: str(x).strip(), inplace=True)
caiso_withdrawn.rename(columns=lambda x: str(x).strip(), inplace=True)
caiso_cluster_15['Standard_Status'] = 'Proposed' 
caiso_withdrawn['Standard_Status'] = 'Withdrawn'

# Combine and filter for BESS
caiso_raw = pd.concat([caiso_cluster_15, caiso_withdrawn], ignore_index=True)
caiso_bess_mask = (caiso_raw['Generation/Fuel 1'] == 'Storage/Battery') | \
                  (caiso_raw['Generation/Fuel 2'] == 'Storage/Battery') | \
                  (caiso_raw['Generation/Fuel 3'] == 'Storage/Battery')
caiso_bess = caiso_raw[caiso_bess_mask].copy()

# Capacity Calculation
def get_bess_capacity(row):
    if row['Generation/Fuel 1'] == 'Storage/Battery': return row['NET MW 1']
    elif row['Generation/Fuel 2'] == 'Storage/Battery': return row['NET MW 2']
    elif row['Generation/Fuel 3'] == 'Storage/Battery': return row['NET MW 3']
    return 0.0

caiso_bess['BESS_Capacity_MW'] = pd.to_numeric(caiso_bess.apply(get_bess_capacity, axis=1), errors='coerce').fillna(0)

# Technology Classification
def determine_tech(row):
    fuels = [str(row['Generation/Fuel 1']), str(row['Generation/Fuel 2']), str(row['Generation/Fuel 3'])]
    fuels = [f for f in fuels if f not in ['nan', 'N/A', 'None']]
    if len(fuels) > 1:
        return 'Hybrid (Solar+BESS)' if 'Photovoltaic/Solar' in fuels else 'Hybrid (Other+BESS)'
    return 'Standalone BESS'

caiso_bess['Primary_Technology'] = caiso_bess.apply(determine_tech, axis=1)

# Geographic Cleaning
caiso_bess['County/Region'] = caiso_bess['PROJECT COUNTY'].astype(str) \
    .str.replace(r'(?i)\bcounty\b', '', regex=True) \
    .str.strip() \
    .str.title()

# Date Handling
caiso_bess['Temp_Date'] = pd.to_datetime(caiso_bess['Requested COD'], errors='coerce')
def get_caiso_year(row):
    if pd.notnull(row['Temp_Date']):
        return str(int(row['Temp_Date'].year))
    elif row['Standard_Status'] == 'Operational':
        return 'Operational'
    return 'TBD'
caiso_bess['COD_Year'] = caiso_bess.apply(get_caiso_year, axis=1)

# Cycle Time Math
math_cod = pd.to_datetime(caiso_bess['Requested COD'], errors='coerce')
math_queue = pd.to_datetime(caiso_bess['Queue Date'], errors='coerce')
caiso_bess['Dev_Cycle_Years'] = ((math_cod - math_queue).dt.days / 365).round(1)

# Standardize CAISO Schema
caiso_std = pd.DataFrame({
    'Project_ID': 'CAISO-' + caiso_bess['Project Number'].astype(str),
    'Country': 'United States',
    'Market_Operator': 'CAISO',
    'County_or_Region': caiso_bess['County/Region'],  
    'Project_Name': caiso_bess['Project Name'],
    'Developer': 'Undisclosed (CAISO Policy)',
    'Primary_Technology': caiso_bess['Primary_Technology'],
    'BESS_Capacity_MW': caiso_bess['BESS_Capacity_MW'],
    'BESS_Capacity_MWh': caiso_bess['BESS_Capacity_MW'] * 4.0,  
    'Duration_Hours': 4.0,                                      
    'Estimated_COD': caiso_bess['Temp_Date'].dt.strftime('%Y-%m-%d'),
    'COD_Year': caiso_bess['COD_Year'], 
    'Project_Status': caiso_bess['Standard_Status'],
    'Dev_Cycle_Years': caiso_bess['Dev_Cycle_Years']
})


# ==========================================
# 3. AEMO DATA PIPELINE
# ==========================================
print("Processing AEMO Data...")

# Load Data
aemo_gen_info = pd.read_excel(aemo_file, sheet_name="Generator Information", skiprows=3)

# Filter for BESS
aemo_bess = aemo_gen_info[aemo_gen_info['Technology Type'] == 'Battery Storage'].copy()

# Status Mapping
status_mapping = {
    'Publicly Announced': 'Early Stage',
    'Anticipated': 'Proposed',
    'Committed': 'Approved/Committed',
    'Committed*': 'Approved/Committed',
    'In Commissioning': 'In Construction',
    'In Service': 'Operational',
    'Announced Withdrawal': 'Withdrawn',
    'Withdrawn': 'Withdrawn'
}

aemo_bess['County/Region'] = aemo_bess['Region'].astype(str).str.strip().str.upper()
aemo_bess['Standard_Status'] = aemo_bess['Commitment Status'].map(status_mapping)

# Date Handling
aemo_bess['Temp_Date'] = pd.to_datetime(aemo_bess['Full Commercial Use Date'], errors='coerce')
def get_aemo_year(row):
    if pd.notnull(row['Temp_Date']):
        return str(int(row['Temp_Date'].year))
    elif row['Standard_Status'] == 'Operational':
        return 'Operational'
    return 'TBD'
aemo_bess['COD_Year'] = aemo_bess.apply(get_aemo_year, axis=1)

# MWh and Duration Math
aemo_bess['MWh_Clean'] = pd.to_numeric(aemo_bess['Agg Nameplate Storage Capacity (MWh)'], errors='coerce')
aemo_bess['MW_Clean'] = pd.to_numeric(aemo_bess['Agg Nameplate Capacity (MW AC)'], errors='coerce').fillna(0)
aemo_bess['Duration_Clean'] = (aemo_bess['MWh_Clean'] / aemo_bess['MW_Clean']).round(2)

# Standardize AEMO Schema
aemo_std = pd.DataFrame({
    'Project_ID': 'AEMO-' + aemo_bess['Gen Info Unit ID'].astype(str),
    'Country': 'Australia',
    'Market_Operator': 'AEMO',
    'County_or_Region': aemo_bess['County/Region'],  
    'Project_Name': aemo_bess['Site Name'],
    'Developer': aemo_bess['Site Owner'].fillna('Unknown'),
    'Primary_Technology': 'Standalone BESS',
    'BESS_Capacity_MW': aemo_bess['MW_Clean'],
    'BESS_Capacity_MWh': aemo_bess['MWh_Clean'],
    'Duration_Hours': aemo_bess['Duration_Clean'],
    'Estimated_COD': aemo_bess['Temp_Date'].dt.strftime('%Y-%m-%d'),
    'COD_Year': aemo_bess['COD_Year'],
    'Project_Status': aemo_bess['Standard_Status']
})


# ==========================================
# 4. EXPORT PIPELINE
# ==========================================
caiso_std.to_csv("CAISO_Cleaned_Staging.csv", index=False)
aemo_std.to_csv("AEMO_Cleaned_Staging.csv", index=False)

print("Success! CAISO_Cleaned_Staging.csv and AEMO_Cleaned_Staging.csv have been generated.")