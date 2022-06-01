from suds.client import Client
import argparse
import sys
import base64
import readline
import logging

def throw_exception(val):
    if val == "":
        raise Exception("This Field Can Not Be Blank!")
        fl = 0
    else:
        fl = 1
    return fl

def rlinput(prompt, default=''):
    readline.set_startup_hook(lambda: readline.insert_text(default))
    flag = 0
    while not flag == 1:
        try:
            v = raw_input(prompt)
            flag = throw_exception(v)
            return v
        except Exception as e:
            print "Attention!: ", e.args[0]
        finally:
            readline.set_startup_hook()

def client_bnfinder(expression_cluster_obj):
    client_bnf = Client("http://biquad.mimuw.edu.pl:8080/bnfinder_ws/bws?wsdl", timeout=10000, cache=None)
    logging.getLogger('suds.client').setLevel(logging.CRITICAL)
    
    sys.stdout.write("\n*** There are three choices for the main species: 1. hsap (human), 2. mmus (mouse), 3. rnor (rat) ***\n")
    ### set up for 'buildGenomicInputDataFromDB' ###
    main_species = rlinput("\nPlease choose the main species: ", "hsap")
    if main_species.lower() == "hsap":
        mainAreaDatasetId = 1034
        mainSpeciesDatabase = "71_1_hsap_public"
        orthologAreaDatasetId = 137
        orthologSpeciesDatabase = "71_1_mmus_public"
    elif main_species.lower() == "mmus":
        mainAreaDatasetId = 137
        mainSpeciesDatabase = "71_1_mmus_public"
        orthologAreaDatasetId = 1034
        orthologSpeciesDatabase = "71_1_hsap_public"
    elif main_species.lower() == "rnor":
        mainAreaDatasetId = 3
        mainSpeciesDatabase = "71_1_rnor_public"
        orthologAreaDatasetId = 1035
        orthologSpeciesDatabase = "71_1_hsap_public"

    motifClass = "JASPAR-CORE"
    result_bGID = client_bnf.service.buildGenomicInputDataFromDB(motifClass=motifClass, mainSpeciesDatabase=mainSpeciesDatabase, mainAreadatasetId=mainAreaDatasetId, orthologSpeciesDatabase=orthologSpeciesDatabase, orthologAreaDatasetId=orthologAreaDatasetId)
    result_bGID = base64.decodestring(result_bGID)

    ### set up for "buildExpressionInputDataFromDB"
    result_bEID = client_bnf.service.buildExpressionInputDataFromDB(expression_cluster_obj, result_bGID)
    result_bEID = base64.decodestring(result_bEID)

    ### Set up for "joinInputData"
    result_jID = client_bnf.service.joinInputData(genomicDatasetId= result_bGID, expressionDatasetId= result_bEID)

    ### Now for: "buildNet"
    job_id_buildNet = client_bnf.service.buildNet(datasetId= result_jID)
    sys.stdout.write("\n*** Please save this JOB_ID. You will need this JOB_ID to retrieve the result when the job is finished. ***\n")
    return job_id_buildNet

