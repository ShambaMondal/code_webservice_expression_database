from suds.client import Client
import sys
import base64
import readline
import logging

if not sys.argv[1] == None:
    job_id = sys.argv[1]
else:
    sys.stdout.write("\n*** Please provide the JOB_ID as the argument. Required. ***\n")

client = Client("biquad.mimuw.edu.pl:8080/bnfinder_ws/bws?wsdl", timeout=10000, cache=None) #Client("http://212.87.20.248:7789/expression?wsdl", timeout=10000, cache=None)
logging.getLogger('suds.client').setLevel(logging.CRITICAL)

# check status of the job

job_status = client.service.getJobState(jobId= job_id)
if job_status == "finished":
    sys.stdout.write("\n*** Job Status: %s ***\n"%(job_status))
    result = client.service.getNet(jobId= job_id)
    with open("final_result_bnfinder.txt", "w") as f:
        f.write(str(result))

elif job_status == "running":
    sys.stdout.write("\n*** Job Status: %s . Please check later. You can get the result when the job is finished."%(job_status))

