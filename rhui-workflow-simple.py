import rhuilib
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

rs = rhuilib.RHUIsetup()
rs.setupFromRolesfile()
rs.RHUA.initialRun()
for cds in rs.CDS:
    rs.RHUA.addCds("Cluster1", cds.hostname)
