import os
import pickle
import grpc
import asyncio

from opensearchpy import AsyncOpenSearch
from opensearch_protos.protos.schemas import document_pb2
from opensearch_protos.document_service_pb2_grpc import DocumentServiceStub

#########################################
##### PROTOBUF CLIENT DEFINITION ########
#########################################

class ProtobufBenchmarkAsyncOpenSearch(AsyncOpenSearch):
    async def bulk(self, body = None, index = None, params = None, headers = None):
        return self.bulk_proto(body=body, index=index, params=params, headers=headers)

    """
    Replace REST client bulk with proto call to gRPC transport
    """
    def bulk_proto(self, body = None, index = None, params = None, headers = None):
        lineSplitBody = body.decode('utf-8').split('\n')
        lineList = []
        opList = []
        docList = []
        indexPattern = '{"index":'
        for lineBody in lineSplitBody:
            lineList.append(lineBody)
            if indexPattern in lineBody:
                opList.append(lineBody)
            else:
                docList.append(lineBody)

        # Remove empty line at end of body
        docList = docList[:-1]

        # Request building
        request = document_pb2.BulkRequest()
        request.index = index
        for doc in docList:
            requestBody = document_pb2.BulkRequestBody()
            requestBody.doc = doc.encode('utf-8')
            index_op = document_pb2.IndexOperation()
            requestBody.index.CopyFrom(index_op)
            request.request_body.append(requestBody)

        # Send request
        with grpc.insecure_channel('localhost:9400') as PROTO_CHANNEL:
            PROTO_DOC_STUB = DocumentServiceStub(PROTO_CHANNEL)
            return PROTO_DOC_STUB.Bulk(request)

    # """
    # To ease testing for this POC intercept params and save pickle them
    # """
    # async def bulk(self, body = None, index = None, params = None, headers = None):
    #     pickle_input("body", body)
    #     pickle_input("index", index)
    #     pickle_input("params", params)
    #     pickle_input("headers", headers)
    #     exit()

#########################################
#########################################
#########################################

#########################################
##### TEST DEFINITIONS ##################
#########################################

proto_client = ProtobufBenchmarkAsyncOpenSearch()

def pickle_input(input_name, input_value):
    path = input_name + '.pickle'
    if os.path.exists(path):
        os.remove(path)
    with open(path, 'wb') as file:
        pickle.dump(input_value, file)

def get_pickle_input(input_name):
    path = input_name + '.pickle'
    with open(path, 'rb') as file:
        return pickle.load(file)

async def do_bulk_with_pickles():
    body = get_pickle_input("body")
    index = get_pickle_input("index")
    params = get_pickle_input("params")
    headers = get_pickle_input("headers")
    return await proto_client.bulk(body=body, index=index, params=params, headers=headers)

if __name__ == "__main__":
    result = asyncio.run(do_bulk_with_pickles())

    # Validate stats
    respSuccess = None
    which_field = result.WhichOneof('response')
    if which_field == 'bulk_response_body':
        respSuccess = result.bulk_response_body
    elif which_field == 'bulk_error_response':
        print(result.bulk_error_response)
        exit()  # Exit on any error
    else:
        print("PROTO ERR - No OneOf set in response")
        exit()  # Exit on any error

    stats = {
        "took": respSuccess.took,
        "success": not respSuccess.errors,  # true if an op failed
        "success-count": 500, # Hard code here
        "error-count": 0  # We will exit() on any error
    }

    print(stats)

#########################################
##### TEST DEFINITIONS ##################
#########################################