import time
import psycopg2
import tacc_stats.cfg as cfg
from tacc_stats.analysis.gen.utils import read_sql

class jid_table:

    def __init__(self, jid):
        CONNECTION = "dbname=ls6_db1 host=localhost user=postgres port=5432"

        print("Initializing table for job {0}".format(jid))

        self.jid = jid

        # Open temporary connection
        self.conj = psycopg2.connect(CONNECTION)

        # Get job accounting data
        acct_data = read_sql("""select * from job_data where jid = '{0}'""".format(jid), self.conj)
        # job_data accounting host names must be converted to fqdn
        self.acct_host_list = [h + '.' + cfg.host_name_ext for h in acct_data["host_list"].values[0]]
    
        self.start_time = acct_data["start_time"].dt.tz_convert('US/Central').dt.tz_localize(None).values[0]
        self.end_time = acct_data["end_time"].dt.tz_convert('US/Central').dt.tz_localize(None).values[0]
    
        # Get stats data and use accounting data to narrow down query
        qtime = time.time()
        sql = """drop table if exists job_{0}; select * into temp job_{0} from host_data where time between '{1}' and '{2}' and jid = '{0}'""".format(jid, self.start_time, self.end_time)

        with self.conj.cursor() as cur:
            cur.execute(sql)
        print("query time: {0:.1f}".format(time.time()-qtime))

        # Compare accounting host list to stats host list
        htime = time.time()
        self.host_list = list(set(read_sql("select distinct on(host) host from job_{0};".format(self.jid), self.conj)["host"].values))
        if len(self.host_list) == 0: return 
        print("host selection time: {0:.1f}".format(time.time()-htime))

        # Build Schema for navigation to Type Detail view
        etime = time.time()
        schema_df = read_sql("""select distinct on (type,event) type,event from job_{0} where host = '{1}'""".format(self.jid, next(iter(self.host_list))), self.conj)
        types = sorted(list(set(schema_df["type"].values)))
        self.schema = {}
        for t in types:
            self.schema[t] = list(sorted(schema_df[schema_df["type"] == t]["event"].values))
        print("schema time: {0:.1f}".format(time.time()-etime))

    def __del__(self):
        sql = """drop table if exists job_{0};""".format(self.jid)
        with self.conj.cursor() as cur:
            cur.execute(sql)
        self.conj.close() 
