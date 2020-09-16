import tempfile
import json
import pprint
import os
import time

from brachiograph import BrachioGraph
from concurrent.futures import TimeoutError
from google.cloud import pubsub_v1
from google.cloud import storage

# TODO(developer)
project_id = "static-site-test-289118"
subscription_id = "cb_client_sub"
timeout = None

# Create our brachiograph
print("Starting brachiograph")
bg = BrachioGraph(inner_arm=8, outer_arm=8, bounds=[-9, 4, 7, 13], pw_up=900, pw_down=1220)

# Google storage client
storage_client = storage.Client()

# Create PubSub client
subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(project_id, subscription_id)

# When we are printing, don't acknowledge any messages
is_printing = False


def callback(message):
    global is_printing

    # Validate the message and parse
    try:
        data = json.loads(message.data)

    except Exception as e:
        msg = ('Invalid Pub/Sub message: '
               'data property is not valid JSON')
        print(f'error: {e}')
        return

    # Validate the message is a Cloud Storage event
    if not data["name"] or not data["bucket"]:
        msg = ('Invalid Cloud Storage notification: '
                'expected name and bucket properties')
        print(f'error: {msg}')
        return

    pprint.pprint(data)
    file_name = data['name']
    bucket_name =  data['bucket']

    if (".json" not in file_name):
        print("File is not a vector JSON file, skipping...")
        message.ack()
        return

    if (is_printing):
        print("Brachiograph is busy, ignoring messages")
        return

    is_printing = True
    message.ack()

    print("Downloading file")
    print(f'bucket: {bucket_name}, file_name: {file_name}')
    blob = storage_client.bucket(bucket_name).get_blob(file_name)

    file_name = blob.name
    _, temp_local_filename = tempfile.mkstemp()

    blob.download_to_filename(temp_local_filename)
    print(f'Image {file_name} was downloaded to {temp_local_filename}.')

    print("Starting the print...")
    bg.plot_file(temp_local_filename)
    print("Finished printing!  Becoming ready again in 10 seconds...")

    time.sleep(10)

    os.remove(temp_local_filename)
    is_printing = False

# Limit the subscriber to only have five outstanding messages at a time.
flow_control = pubsub_v1.types.FlowControl(max_messages=5)

streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
print("Listening for messages on {}..\n".format(subscription_path))

# Wrap subscriber in a 'with' block to automatically call close() when done.
with subscriber:
    try:
        # When `timeout` is not set, result() will block indefinitely,
        # unless an exception is encountered first.
        streaming_pull_future.result(timeout=timeout)
    except TimeoutError:
        streaming_pull_future.cancel()
