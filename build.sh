git submodule update
cp -r ./googleapis/google ./java-tron/protocol/src/main/protos/google
python3 -m grpc_tools.protoc -I=./java-tron/protocol/src/main/protos --python_out=./ --grpc_python_out=./  ./java-tron/protocol/src/main/protos/**/*.proto ./java-tron/protocol/src/main/protos/**/**/*.proto
rm -rf ./java-tron/protocol/src/main/protos/google