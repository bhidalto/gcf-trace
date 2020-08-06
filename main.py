import os
#Logging Libraries
from google.cloud import logging
from google.cloud.logging.resource import Resource
#Tracing Libraries
from opencensus.trace import tracer as tracer_module
from opencensus.trace.exporters import stackdriver_exporter
from opencensus.trace.exporters.transports.background_thread \
    import BackgroundThreadTransport

#Fetch project id from the GCF env variables 
PROJECT_ID=os.environ.get("GCP_PROJECT_ID")
 
# instantiate trace exporter
exporter = stackdriver_exporter.StackdriverExporter(
project_id=PROJECT_ID, transport=BackgroundThreadTransport)
 
def hello_world(request):
    #Create logging client
    log_client = logging.Client()
    
    #Stackdriver Tracer to be created, we will be passing the exporter and the sampler
    tracer = tracer_module.Tracer(exporter=exporter, sampler=tracer_module.samplers.AlwaysOnSampler())

    #Generic span, with nested spans to have better insights of the latency for each of the steps we want to execute
    with tracer.span(name='trace_function') as function_exec:
        #Span 1, bold loop so we see a first step in GCF trace execution
        with function_exec.span(name='nested_loop'):
            for i in range(100):
                pass
        #Span 2, simple example on how to log a JSON to Stackdriver logging by using a Resource
        with function_exec.span(name='nested_logs_preparation'):
            # This is the resource type of the log
            log_name = 'cloudfunctions.googleapis.com%2Fcloud-functions' 
            test_dict = {"a": 1, "b" : 2, "c" : 3}
            # Inside the resource, nest the required labels specific to the resource type
            res = Resource(type="cloud_function", 
                        labels={
                            "function_name": "logging-levels", 
                            "region": "europe-west1"
                        },
                        )
            logger = log_client.logger(log_name.format(PROJECT_ID))

        #Span 3, outputting logs to Stackdriver, as a struct
        with function_exec.span(name='logs_output'):    
            logger.log_struct(test_dict, resource=res, severity='ERROR')
    
    # We return a string as a result of our GCF execution
    return 'Wrote logs to {}.'.format(logger.name) # Return cloud function response
