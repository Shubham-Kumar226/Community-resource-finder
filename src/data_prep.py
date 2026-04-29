import pandas as pd
import json

def load_and_clean():
    df1 = pd.read_csv('data/bengaluru_hospital.csv', encoding='utf-8')
    df2 = pd.read_csv('data/mumbai_hospital.csv', encoding='latin1') 

    print("Files loaded successfully!")

    df1_cleaned = df1[['Name', 'Address', 'Type']].rename(columns={
        'Name': 'name',
        'Address': 'location',
        'Type': 'category'
    })
    df1_cleaned['city'] = 'Bengaluru'

    df2_cleaned = df2[['Hospital Name', 'Address', 'Type of Hospital/Health facility']].rename(columns={
        'Hospital Name': 'name',
        'Address': 'location',
        'Type of Hospital/Health facility': 'category'
    })
    df2_cleaned['city'] = 'Mumbai'

    combined_df = pd.concat([df1_cleaned, df2_cleaned], ignore_index=True)
    combined_df['category'] = 'Hospital'

    combined_df['description'] = (
        combined_df['name'] + " is a " + 
        combined_df['category'].str.lower() + " resource located at " + 
        combined_df['location']
    )

    combined_df.to_json('data/resources.json', orient='records', indent=4)
    print(f"Success! Merged {len(combined_df)} hospitals into data/resources.json")

if __name__ == "__main__":
    load_and_clean()
