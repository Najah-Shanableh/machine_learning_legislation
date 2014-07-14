import os, sys, inspect
sys.path.insert(0, os.path.realpath(os.path.abspath(os.path.join(os.path.split(inspect.getfile( inspect.currentframe() ))[0],".."))))

import re
from pprint import pprint
import argparse
import csv
import math
import psycopg2
import psycopg2.extras
import random
import time
import codecs 
from util import wiki_tools

CONN_STRING = "dbname=harrislight user=harrislight password=harrislight host=dssgsummer2014postgres.c5faqozfo86k.us-west-2.rds.amazonaws.com"


def get_positive_eamples(year, outfile):
	entities =get_earmark_entities(year)
	f = codecs.open(outfile,'w', 'utf8')
	for entity in entities:
		pages = wiki_tools.get_wiki_page_title_google_cse(entity['entity_inferred_name'])
		if len(pages)>1:
		    f.write( "%d\t%s\n"%(entity["matched_entity_id"], pages[0]))
	f.close()




def get_negative_examples(year, outfile):
    pass

def get_earmark_entities(year):
    """
    get entities for doc_id
    """
    conn = psycopg2.connect(CONN_STRING)
    columns = ["matched_entity_id", "entity_inferred_name"]
    cmd = "select "+", ".join(columns)+" from entities, earmark_documents, earmarks where \
     matched_entity_id = entities.id and earmarks.earmark_id = earmark_documents.earmark_id and enacted_year = %s"
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute(cmd, (year,))
    records = cur.fetchall()
    conn.close()
    return records



def get_negative_examples_from_db( congress = 111, count=10000 ):
    """
    generates negative examples, randomly, for a given year
    """
    conn = psycopg2.connect(CONN_STRING)
    try:
        cmd = """
        select mid, entity_inferred_name, random() as r
        from
        (select e.entity_inferred_name, max(e.id) as mid
        from entities as e 
        join documents on e.document_id = documents.id 
        join congress_meta_document as cmd on documents.congress_meta_document = cmd.id 
        left join earmark_documents as ed on ed.matched_entity_id = e.id 
        where e.source = 'table' 
            and cmd.congress = %s 
            and ed.matched_entity_id is null group by e.entity_inferred_name) 
        order by r limit %s
        """
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(cmd, (congress, count))
        records = cur.fetchall()
        conn.close()
        return records
    except Exception as ex:
        logging.exception("failed to get negative examples")
    finally:
        conn.close()




if __name__=="__main__":
    parser = argparse.ArgumentParser(description='get positive examples')
    parser.add_argument('--year', type = int, required=True, help='year for pulling data')
    parser.add_argument('--outfile',  required=True, help='the file to which to write results')
    args = parser.parse_args()
    get_positive_eamples(args.year, args.outfile)
