import os, sys, inspect
sys.path.insert(0, os.path.realpath(os.path.abspath(os.path.join(os.path.split(inspect.getfile( inspect.currentframe() ))[0],".."))))
from util import path_tools, configuration
import psycopg2
CONN_STRING = configuration.get_connection_string()

import psycopg2
import csv
import numpy as np
import pandas as pd
from util import path_tools, configuration
CONN_STRING = configuration.get_connection_string()


def get_clean_csv():
    years = ['2010', '2009', '2008', '2005']

    keep = [
            'earmark_id',
            'earmark_code',
            'agency_title',
            'bureau_title',
            'account_title',
            'program',
            'enacted_year',
            'short_description',
            'earmark_description',
            'earmark_type_name',
            'spendcom',
            'recipient'
            ]

    keepset = set(keep)

    ds = []
    for year in years:
        fname = configuration.get_path_to_omb_data() +year+'.csv'
        d = pd.read_csv(fname, low_memory=False)
        d.columns = [h.lower().replace(" ", "_") for h in d.columns]
        if year == '2005':
            d['earmark_id'] = range(d.shape[0])
            d['short_description'] = d['earmark_short_description']
        ds.append(d)

    d = pd.concat(ds)

    ear = pd.concat(ds)[keep]

    new_index = [
            'earmark_id',
            'earmark_code',
            'agency',
            'bureau',
            'account',
            'program',
            'enacted_year',
            'short_description',
            'full_description',
            'earmark_type',
            'spendcom',
            'recipient'
            ]

    ear.columns =  new_index
    ear = ear.groupby('earmark_id').apply(get_recipient)
    ear['full_description'] = ear.full_description.map(shorten_full_description)
    ear.apply(convert).to_csv(os.path.join(configuration.get_path_to_omb_data(), 'all.csv'), header=True, index=False)



# there is an entry per sponsor, just keep one of them
def get_recipient(df):
    most_complete_idx = df.index[0]
    most_complete_num = 0

    for index, row in df.iterrows():
        complete_num = row.count()
        if complete_num > most_complete_num:
            most_complete_idx = index
            most_complete_num = complete_num


    if row["recipient"] is np.NaN:
        print "recipient not found"

    return df.ix[most_complete_idx]


def shorten_full_description(str):
    try:
        return str[0:2045]
    except:
        return str


def convert(x):
    try:
       return x.astype(int)
    except:
        return x


def import_to_db():

    with open(os.path.join(configuration.get_path_to_omb_data(), 'all.csv', 'rb')) as f:
        reader = csv.reader(f)
        reader.next()
        rows = []
        for row in reader:
            rows.append(row)

        print len(rows)

    conn = psycopg2.connect(CONN_STRING)
    cmd = "insert into earmarks ("+", ".join(new_index)+") values ("+", ".join(["%s"]*len(new_index))+")"
    print cmd
    params = rows
    cur = conn.cursor()
    cur.execute ("delete from earmarks")
    cur.executemany(cmd, params)
    #conn.commit()
    conn.close()



if __name__ == '__main__':
    get_clean_csv()
    import_to_db()





