# cloud_brachiograph

```bash
####################################################################
# Fresh setup
####################################################################
# Vars
PROJECT_NAME="<PROJECT_NAME>"
REGION="<REGION>"
CLOUD_RUN_REGION="<CLOUD_RUN_REGION>"
UPLOAD_BUCKET_NAME="${PROJECT_NAME}_uploaded_images"
PROCESSED_BUCKET_NAME="${PROJECT_NAME}_processed_images"

# General
gcloud auth login
gcloud config set project "${PROJECT_NAME}"
PROJECT_NUMBER="$(gcloud projects describe "${PROJECT_NAME}" --format="value(projectNumber)")"

# APIs
gcloud services enable \
   pubsub.googleapis.com \
   cloudfunctions.googleapis.com \
   iam.googleapis.com \
   cloudbuild.googleapis.com \
   run.googleapis.com

# Buckets
gsutil mb -p "${PROJECT_NAME}" \
   -l "${REGION}" \
   "gs://${UPLOAD_BUCKET_NAME}"
gsutil mb -p "${PROJECT_NAME}" \
   -l "${REGION}" \
   "gs://${PROCESSED_BUCKET_NAME}"

# Frontend
gcloud iam service-accounts create url-signer \
   --display-name="GCS URL Signer"
gcloud iam service-accounts keys create service_account.json \
   --iam-account=url-signer@${PROJECT_NAME}.iam.gserviceaccount.com
gcloud projects add-iam-policy-binding ${PROJECT_NAME} \
   --member serviceAccount:url-signer@${PROJECT_NAME}.iam.gserviceaccount.com \
   --role roles/iam.serviceAccountTokenCreator
gsutil iam ch serviceAccount:url-signer@${PROJECT_NAME}.iam.gserviceaccount.com:roles/storage.admin "gs://${UPLOAD_BUCKET_NAME}"
gsutil cors set services/frontend/cors.txt "gs://${UPLOAD_BUCKET_NAME}"
gcloud functions deploy frontend \
   --region "${REGION}" \
   --entry-point router \
   --runtime python37 \
   --trigger-http \
   --allow-unauthenticated \
   --service-account url-signer@${PROJECT_NAME}.iam.gserviceaccount.com \
   --set-env-vars BUCKET_NAME="${UPLOAD_BUCKET_NAME}" \
   --source ./services/frontend

# Image processor
gcloud builds submit ./services/image_to_lines --tag "gcr.io/${PROJECT_NAME}/image_to_lines"
gcloud run deploy image-to-lines \
   --region="${CLOUD_RUN_REGION}" \
   --image gcr.io/${PROJECT_NAME}/image_to_lines \
   --set-env-vars=PROCESSED_IMAGE_BUCKET_NAME=${PROCESSED_BUCKET_NAME} \
   --platform managed \
   --no-allow-unauthenticated
gcloud projects add-iam-policy-binding ${PROJECT_NAME} \
     --member=serviceAccount:service-${PROJECT_NUMBER}@gcp-sa-pubsub.iam.gserviceaccount.com \
     --role=roles/iam.serviceAccountTokenCreator
gcloud iam service-accounts create cloud-run-pubsub-invoker \
     --display-name "Cloud Run Pub/Sub Invoker"
gcloud run services add-iam-policy-binding image-to-lines \
   --member=serviceAccount:cloud-run-pubsub-invoker@${PROJECT_NAME}.iam.gserviceaccount.com \
   --role=roles/run.invoker \
   --region="${CLOUD_RUN_REGION}" \
   --platform managed
gcloud pubsub topics create image_uploaded
gcloud pubsub subscriptions create image_to_lines-sub \
   --topic image_uploaded \
   --push-endpoint=$(gcloud run services describe image-to-lines --platform managed --region ${CLOUD_RUN_REGION} --format 'value(status.url)') \
   --push-auth-service-account=cloud-run-pubsub-invoker@${PROJECT_NAME}.iam.gserviceaccount.com \
   --ack-deadline 600
gsutil notification create -t image_uploaded -f json gs://${UPLOAD_BUCKET_NAME}

# Pi print PubSub
gcloud iam service-accounts create drawbot-client \
   --display-name="BrachioGraph client account"
gcloud iam service-accounts keys create drawbot-client_sa.json \
   --iam-account=drawbot-client@${PROJECT_NAME}.iam.gserviceaccount.com
# Copy key to Pi and export: export GOOGLE_APPLICATION_CREDENTIALS=drawbot-client_sa.json
gcloud pubsub topics create image_processed
gsutil notification create -t image_processed -f json -e OBJECT_FINALIZE gs://${PROCESSED_BUCKET_NAME}
gcloud pubsub subscriptions create drawbot_client_sub \
   --topic image_processed \
   --ack-deadline 30
gcloud pubsub subscriptions add-iam-policy-binding drawbot_client_sub \
   --member=serviceAccount:drawbot-client@${PROJECT_NAME}.iam.gserviceaccount.com \
   --role=roles/pubsub.subscriber
gsutil iam ch serviceAccount:drawbot-client@${PROJECT_NAME}.iam.gserviceaccount.com:roles/storage.objectViewer gs://${PROCESSED_BUCKET_NAME} 
```