import os

# Logging Libraries
from google.cloud import logging
from google.cloud.logging.resource import Resource
# Tracing Libraries
from opencensus.trace import tracer as tracer_module
from opencensus.trace.exporters import stackdriver_exporter
from opencensus.trace.exporters.transports.background_thread import \
    BackgroundThreadTransport

# Fetch project id from the GCF env variables
PROJECT_ID = os.environ.get("GCP_PROJECT")
REGION = os.environ.get("FUNCTION_REGION")
FUNC_NAME = os.environ.get("FUNCTION_NAME")
TRACE = f"projects/{PROJECT_ID}/traces/382d4f4c6b7bb2f4a972559d9085001d"

# instantiate trace exporter
exporter = stackdriver_exporter.StackdriverExporter(
    project_id=PROJECT_ID, transport=BackgroundThreadTransport)



log_name = 'cloudfunctions.googleapis.com%2Fcloud-functions'

test_dict = {"a": 1, "b": 2, "c": 3}
# Inside the resource, nest the required labels specific to the resource type
resource = Resource(type="cloud_function",  # must be cloud_function, in GKE put k8s_pod/k8s_container
                    labels={
                        "function_name": FUNC_NAME,
                        "region": REGION
                    })

def gcf_trace_test(request):
    # Create logging client
    log_client = logging.Client()
    logger = log_client.logger(log_name.format(PROJECT_ID))

    # Stackdriver Tracer to be created, we will be passing the exporter and the sampler
    tracer = tracer_module.Tracer(
        exporter=exporter, sampler=tracer_module.samplers.AlwaysOnSampler())

    # Generic span, with nested spans to have better insights of the latency for each of the steps we want to execute
    with tracer.span(name='trace_function') as function_exec:
        # Span 1
        with function_exec.span(name='nested_loop') as span:
            logger.log_struct(
                test_dict, trace=TRACE, span_id=span.span_id, resource=resource, severity='WARNING')

        # Span 2
        with function_exec.span(name='nested_logs_preparation'):
            logger.log_struct(
                {"foo": 5}, trace=TRACE, span_id=span.span_id, resource=resource, severity='DEBUG')

        # Span 3
        with function_exec.span(name='logs_output') as span:
            logger.log_struct(test_dict, trace=TRACE, span_id=span.span_id,
                              resource=resource, severity='ERROR')

    # We return a string as a result of our GCF execution
    # Return cloud function response
    return 'Wrote logs to {}.'.format(logger.name)
