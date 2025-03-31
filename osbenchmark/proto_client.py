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
    # """
    # Replace REST client bulk with proto call to gRPC transport
    # """
    # async def bulk(self, body = None, index = None, params = None, headers = None):
    #     print("body" + str(len(body)))
    #     print("index" + str(len(index)))
    #     print("params" + str(len(params)))
    #     print("headers" + str(len(headers)))
    #
    #     lineSplitBody = body.split('\n')
    #     lineList = []
    #     opList = []
    #     docList = []
    #     indexPattern = '{"index":'
    #     for lineBody in lineSplitBody:
    #         lineList.append(lineBody)
    #         if indexPattern in lineBody:
    #             opList.append(lineBody)
    #         else:
    #             docList.append(lineBody)
    #
    #     # Remove empty line at end of body
    #     docList = docList[:-1]
    #
    #     # Request building
    #     request = document_pb2.BulkRequest()
    #     request.index = index
    #     for doc in docList:
    #         requestBody = document_pb2.BulkRequestBody()
    #         requestBody.doc = doc.encode('utf-8')
    #         index_op = document_pb2.IndexOperation()
    #         requestBody.index.CopyFrom(index_op)
    #         request.request_body.append(requestBody)
    #
    #     # Send request
    #     with grpc.insecure_channel('localhost:9400') as PROTO_CHANNEL:
    #         PROTO_DOC_STUB = DocumentServiceStub(PROTO_CHANNEL)
    #         return PROTO_DOC_STUB.Bulk(request)

    """
    To ease testing for this POC intercept params and save pickle them
    """
    async def bulk(self, body = None, index = None, params = None, headers = None):
        self.pickle_input("body", body)
        self.pickle_input("index", index)
        self.pickle_input("params", params)
        self.pickle_input("headers", headers)
        exit()

    def pickle_input(self, input_name, input_value):
        path = input_name + '.pickle'
        if os.path.exists(path):
            os.remove(path)
        with open(path, 'wb') as file:
            pickle.dump(input_value, file)

#########################################
#########################################
#########################################

async def do_bulk(params):
    return await proto_client.bulk(params=params)

if __name__ == "__main__":
    proto_client = ProtobufBenchmarkAsyncOpenSearch()

    # Test with pickled OSB bulk request
    pick = "bulk_args_20250331_080241.pkl"
    result = None
    with open(pick, 'rb') as file:
        data = pickle.load(file)
        result = asyncio.run(do_bulk(data))


    # Small result verify
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