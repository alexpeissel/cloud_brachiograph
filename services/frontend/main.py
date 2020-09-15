import uuid
import os
import datetime
import google.auth

from flask import abort, render_template
from google.auth import compute_engine
from google.cloud import storage

bucketName = os.environ.get('BUCKET_NAME','YOU_FORGOT_TO_SET_THE_BUCKET_NAME_ENV_VAR')
client = storage.Client()
bucket = client.get_bucket(bucketName)

def router(request):
    path = (request.path)
    method = (request.method)

    if (path == "/" and method == "GET"):
        session_uuid = uuid.uuid1()
        return render_template('index.html', session_uuid=session_uuid)

    elif (path == "/status"):
        # TODO
        return "status"

    elif (path == "/get_signed_url"):
        filename = request.args.get('filename')
        blob = bucket.blob(filename)
        print(f'Generating signed URL for filename: {filename}')

        # https://gist.github.com/jezhumble/91051485db4462add82045ef9ac2a0ec#file-python_cloud_function_get_signed_url-py-L12
        auth_request = google.auth.transport.requests.Request()
        signing_credentials = compute_engine.IDTokenCredentials(auth_request, "")

        url = blob.generate_signed_url(
            expiration=datetime.timedelta(minutes=60),
            method="PUT",
            version="v4",
            content_type="application/octet-stream",
            credentials=signing_credentials
        )
        print(f'Signed URL: {url}')

        return url

    else:
        abort (404)
