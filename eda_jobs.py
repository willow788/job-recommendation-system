import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

with open("data/scraped_jobs.json", "r", encoding="utf-8") as f:
    scraped_jobs = json.load(f)

df = pd.DataFrame(scraped_jobs)

#basic info
print("shape of the dataframe:", df.shape)

#data types
datatypes = df.dtypes
print("data types of the columns:\n", datatypes)

print(f"missing values in each column: \n{df.isnull().sum()}")

print(f"missing values percentage in each column: \n{(df.isnull().sum() / len(df)) * 100}")

#duplicate jobs 
print(f"number of duplicate jobs: {df.duplicated().sum()}")

#duplicate job descriptions
print("dublicatee job descriptions:")
print(df['description'].duplicated().sum())

#job description
print("\nTOP 15 JOB TITLES:")
print(df['title'].value_counts().head(15))
print("\nTOP 15 JOB LOCATIONS:")
print(df['location'].value_counts().head(15))

print("\nTOP 15 JOB COMPANIES:")
print(df['company'].value_counts().head(15))

#handling the missing values
missing_values = df.isnull().sum()
#filling the missing values with 'Unknown'
for col in df.columns:
    if missing_values[col] > 0:
        df[col].fillna('Unknown', inplace=True)

#now we will print all the missing val again
print(f"total no of missing values in each column after filling: \n{df.isnull().sum()}")

#remove duplicates
df.drop_duplicates(inplace=True)

#remove duplicate job descriptions
df.drop_duplicates(subset='description', inplace=True)

#standardize company names and their locations
#company names
df['company'] = df['company'].str.strip().str.title()

df['location'] = df['location'].str.strip().str.title()

df['description'] = df['description'].str.strip()

df['location'] = df['location'].str.replace(r'\s+', ' ', regex=True)





