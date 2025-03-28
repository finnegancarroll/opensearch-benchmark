#!/usr/bin/env python3

import json
import grpc
from opensearch_protos.protos.schemas import document_pb2
from opensearch_protos.document_service_pb2_grpc import DocumentServiceStub

def proto_bulk(params):
    with grpc.insecure_channel('localhost:9400') as channel:
        stub = DocumentServiceStub(channel)
        request = document_pb2.BulkRequest()
        request.index = "test-index"
        index_op = document_pb2.BulkRequestBody()
        index_operation = document_pb2.IndexOperation()
        index_operation.id = "doc1"
        index_operation.index = "test-index"
        index_op.index.CopyFrom(index_operation)
        doc_data = {"title": "Test Document", "content": "This is a test document"}
        index_op.doc = json.dumps(doc_data).encode('utf-8')
        request.request_body.append(index_op)
        request.refresh = document_pb2.BulkRequest.Refresh.REFRESH_TRUE
        request.timeout = "30s"
        response = stub.Bulk(request)
        print(response)

def main():
    params = {
        "index": "test-index",
        "documents": [
            {"id": "doc1", "data": {"title": "Test Document", "content": "This is a test document"}}
        ]
    }

    result = proto_bulk(params)

if __name__ == "__main__":
    main()
