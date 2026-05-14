import sqlite3
import pandas as pd
import os
import re
import glob


# Function to extract date from filename
def extract_date(filename):
    match = re.search(r'Chile_PriceVector_(\d{4}-\d{2}-\d{2})\.xlsx', filename)
    if match:
        return match.group(1)
    return None

# Function to clean numeric values: replace comma with dot, remove %
def clean_numeric(value):
    if isinstance(value, str):
        value = value.replace(',', '.').replace('%', '')
    try:
        return float(value)
    except ValueError:
        return value

# Use the script's directory as base so paths work regardless of where Python is invoked from
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)

# Database setup
db_dir = os.path.join(BASE_DIR, 'db')
os.makedirs(db_dir, exist_ok=True)
db_path = os.path.join(db_dir, 'fixed_income.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create table if not exists
cursor.execute('''
CREATE TABLE IF NOT EXISTS fixed_income (
    date TEXT,
    ticker TEXT,
    family TEXT,
    group_col TEXT,
    quote REAL,
    yield_val REAL,
    duration REAL,
    convexity REAL,
    UNIQUE(date, ticker)
)
''')

# Find all XLSX files
pattern = os.path.join(BASE_DIR, 'data', 'Chile_PriceVector_*.xlsx')
files = glob.glob(pattern)

for file in files:
    date = extract_date(file)
    if not date:
        continue

    df = pd.read_excel(file)
    # Assume columns are: Ticker, Family, Group, Quote, Yield, Duration, Convexity
    for _, row in df.iterrows():
        ticker = row['Ticker']
        family = row['Family']
        group = row['Group']
        quote = clean_numeric(row['Quote'])
        yield_val = clean_numeric(row['Yield'])
        duration = clean_numeric(row['Duration'])
        convexity = clean_numeric(row['Convexity'])

        cursor.execute('''
        INSERT OR IGNORE INTO fixed_income (date, ticker, family, group_col, quote, yield_val, duration, convexity)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (date, ticker, family, group, quote, yield_val, duration, convexity))

conn.commit()
conn.close()

print("Database created and populated successfully.")
