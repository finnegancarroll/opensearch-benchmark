import pickle
import grpc

def proto_bulk(bulk_args):
    import grpc
    from opensearch_protos.protos.schemas import document_pb2
    from opensearch_protos.document_service_pb2_grpc import DocumentServiceStub

    reqBody = bulk_args['body']
    strReqBody = reqBody.decode('utf-8')
    lineSplitBody = strReqBody.split('\n')

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

    print("len(docList) " + str(len(docList)))
    print("len(opList) " + str(len(opList)))

    # Request building
    request = document_pb2.BulkRequest()
    request.index = bulk_args["index"]

    # Does OSB set this true on default?
    request.refresh = document_pb2.BulkRequest.Refresh.REFRESH_TRUE

    for doc in docList:
        requestBody = document_pb2.BulkRequestBody()
        requestBody.doc = doc.encode('utf-8')
        # requestBody.index = document_pb2.IndexOperation()

        index_op = document_pb2.IndexOperation()
        requestBody.index.CopyFrom(index_op)

        request.request_body.append(requestBody)

    # Send request
    response = None
    with grpc.insecure_channel('localhost:9400') as PROTO_CHANNEL:
        PROTO_DOC_STUB = DocumentServiceStub(PROTO_CHANNEL)
        response = PROTO_DOC_STUB.Bulk(request)

    respSuccess = None
    which_field = response.WhichOneof('response')
    if which_field == 'bulk_response_body':
        respSuccess = response.bulk_response_body
    elif which_field == 'bulk_error_response':
        print("Got an error response")
        print(response.bulk_error_response)
        exit() # Exit on any error
    else:
        print("Response has no data set")
        exit() # Exit on any error

    stats = {
        "took": respSuccess.took,
        "success": not respSuccess.errors, # true if an op failed
        "success-count": len(docList),
        "error-count": 0 # We will exit() on any error
    }

    print(stats)

if __name__ == "__main__":
    pick = "bulk_args_20250331_080241.pkl"
    with open(pick, 'rb') as file:
        data = pickle.load(file)
        proto_bulk(data)
