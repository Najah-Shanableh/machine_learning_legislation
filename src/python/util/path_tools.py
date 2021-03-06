import os, sys
import json
import traceback
import codecs

import configuration


class BillPathUtils:

    def __init__(self, path="", rootDir=configuration.get_path_to_bills()):
        self.path = path
        self.rootDir = rootDir
        self.CONN_STRING = configuration.get_connection_string()
        if not self.rootDir.endswith('/'):
            self.rootDir += '/'


    def congress(self):
        return int(self.path[len(self.rootDir):len(self.rootDir)+3])

    def chamber(self):
        subpath = self.path[len(self.rootDir):]
        if subpath[10] =="s":
            return "senate"
        else:
            return "house"

    def bill_number(self):
        subpath = self.path[len(self.rootDir):]
        parts= subpath.split('/')
        return parts[3]

    def version(self):
         subpath = self.path[len(self.rootDir):]
         parts= subpath.split('/')
         return parts[5]

    def bill_date(self):
        date = json.load(open(os.path.join(self.path, 'data.json')))
        return date['issued_on']

    def get_bill_path(self, congress, number, version):
        """
        returns the path to a bill using the information provided
        congress: integer for congress number, example: 111
        number: bill number, example hr2244 or s154. Note it's a string
        version: string version, example ih, rs
        """
        chars = "".join([ch for ch in number if ch.isalpha()])
        return "%s%d/bills/%s/%s/text-versions/%s/document.txt" %(self.rootDir, congress, chars,number,version )

    def get_all_versions(self, path_to_bill):
        """
        returns the name of the available versions for a current bill
        path_to_bill: absolute path to a bill. Assumes no versions in the path
        example: /mnt/data/sunlight/bills/111/bills/s/s100/
        """
        path = os.path.join(path_to_bill, 'text-versions')
        if os.path.exists(path):
            return os.listdir(path )
        else:
            return []
    def get_db_document_id(self):
        """
        returns the database document id for the current object that represents a path
        """
        import psycopg2
        conn = psycopg2.connect(self.CONN_STRING)
        try:
            cmd = "select documents.id from documents, congress_meta_document \
            where congress_meta_document.id = documents.congress_meta_document \
            and congress = %s and version = %s and senate = %s and bill= true \
            and number = %s"
            cur = conn.cursor()
            cur.execute(cmd, (self.congress(), self.version(), self.chamber()=='senate', self.bill_number() )  )
            return cur.fetchone()[0]
        except Exception as ex:
            print ex
            raise ex
        finally:
            conn.close()

    def get_path_from_doc_id(self, doc_id):
        """
        given document id of a row in the documents table, returns the path to the file
        """
        import psycopg2
        conn = psycopg2.connect(self.CONN_STRING)
        try:
            cmd = "select congress, number, version from documents, congress_meta_document \
            where documents.congress_meta_document = congress_meta_document.id \
            and documents.id = %s"
            cur = conn.cursor()
            cur.execute(cmd, (doc_id,) )
            record = cur.fetchone()
            return self.get_bill_path( record[0], record[1], record[2])

        except Exception as ex:
            print ex
            raise ex
        finally:
            conn.close()

class ReportPathUtils():

    def __init__(self, path="", rootDir=configuration.get_path_to_reports()):
        self.path = path
        self.rootDir = rootDir
        self.CONN_STRING = configuration.get_connection_string()
        if not self.rootDir.endswith('/'):
            self.rootDir += '/'
        self.pathParts = self.path[len(self.rootDir):].split('/')

    def congress(self):
        return int(self.path[len(self.rootDir):len(self.rootDir)+3])

    def chamber(self):
        return self.pathParts[1]

    def report_number(self):
        return self.pathParts[2]

    def version(self):
        return self.pathParts[-1]

    def get_report_path(self, congress, chamber, number, version):
        return "%s%d/%s/%s/%s"%(self.rootDir, congress, chamber, number, version)

    def get_all_versions(self, path_to_report):
        """
        get all the versions of the report
        note that report has only one version, however some reports are split into
        parts and we modle a part as a version
        path_to_report: absolute path to the report directory
        """
        return [ fname for fname in os.listdir(path_to_report) if fname != 'mods.xml']


    def get_db_document_id(self):
         """
         returns the database document id for the current object that represents a path
         """
         import psycopg2
         conn = psycopg2.connect(self.CONN_STRING)
         try:
             cmd = "select documents.id from documents, congress_meta_document \
             where congress_meta_document.id = documents.congress_meta_document \
             and congress = %s and version = %s and senate = %s and bill= false \
             and number = %s"
             cur = conn.cursor()
             cur.execute(cmd, (self.congress(), self.version(), self.chamber()=='senate', self.report_number()))
             return cur.fetchone()[0]
         except Exception as ex:
             #print ex
             raise ex
         finally:
             conn.close()

    def get_path_from_doc_id(self, doc_id):
        """
        given document id of a row in the documents table, returns the path to the file
        """
        import psycopg2
        conn = psycopg2.connect(self.CONN_STRING)
        try:
            cmd = "select congress, number, version, senate from documents, congress_meta_document \
            where documents.congress_meta_document = congress_meta_document.id \
            and documents.id = %s"
            cur = conn.cursor()
            cur.execute(cmd, (doc_id,) )
            record = cur.fetchone()
            chamber= 'senate'
            if not record[3]:
                chamber='house'
            return self.get_report_path( record[0], chamber, record[1], record[2] )

        except Exception as ex:
            #print ex
            raise ex
        finally:
            conn.close()


def doc_id_to_path(doc_id):
    import psycopg2
    b = BillPathUtils()
    r = ReportPathUtils()
    conn = psycopg2.connect(b.CONN_STRING)
    try:
        cmd = "select congress, number, version, senate, bill from documents, congress_meta_document \
        where documents.congress_meta_document = congress_meta_document.id \
        and documents.id = %s"
        cur = conn.cursor()
        cur.execute(cmd, (doc_id,) )
        record = cur.fetchone()
        chamber= 'senate'
        if not record[3]:
            chamber='house'
        if record[4]:
            return b.get_bill_path( record[0], record[1], record[2])
        else:
            return r.get_report_path(record[0], chamber, record[1], record[2] )

    except Exception as ex:
        #traceback.print_stack()
        #print ex
        raise ex
    finally:
        conn.close()

def get_report_date(document_id):
    """
    document_id: document id of a report only
    """
    from bs4 import BeautifulSoup
    path = doc_id_to_path(document_id)
    path = path[:path.rfind('/')] + '/mods.xml'
    with codecs.open(path,'r','utf8') as f:
        soup = BeautifulSoup(f)
        return soup.find('mods').find('origininfo').find('dateissued').text.strip()

def get_report_year(document_id):
    return get_report_date(document_id)[:4]


if __name__=="__main__":
    if len(sys.argv) > 1:
        print doc_id_to_path(int(sys.argv[1]))
    else:
        print "USAGE: python %s <doc_id>" %(sys.argv[0])
