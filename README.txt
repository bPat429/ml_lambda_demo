AWS deployable lambda function for processing strings with a model from HuggingFace
Demo model used is t5-base-finetuned-emotion
for emotion recognition in text, fine-tuned by mrm8488
https://huggingface.co/mrm8488/t5-base-finetuned-emotion?text=I+wish+you+were+here+but+it+is+impossible

See demo.py for example invocation of lambda
Note: The running lambda is not publically available by default for security reasons. For a demonstration please
email me at pathak.ban@gmail.com

For deploying you will need an AWS account, a NLP model from HuggingFace hosted in an s3 bucket,
and a mongodb account. When deploying you will need to fill these parameters in 
for the lambda to function.

Deploy using:
    sam deploy --guided