AWS deployable lambda function for processing strings with a model from HuggingFace

See demo.py for example invocation of lambda

For deploying you will need an AWS account, a NLP model from HuggingFace hosted in an s3 bucket,
and a mongodb account. When deploying you will need to fill these parameters in 
for the lambda to function.

Deploy using:
    sam deploy --guided