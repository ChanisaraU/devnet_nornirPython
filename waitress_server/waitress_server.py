from waitress import serve
import predict
serve(predict.app, host='localhost')