import requests, json
import pandas as pd
from datetime import datetime
import time
import os
from flask import Flask, request, jsonify
from flask_cors import cross_origin
from ibm_watsonx_ai.foundation_models.utils.enums import ModelTypes


app = Flask(__name__)

IAM_URL = "https://iam.cloud.ibm.com"
DATAPLATFORM_URL = "https://api.dataplatform.cloud.ibm.com"
SERVICE_URL = "https://au-syd.aiopenscale.cloud.ibm.com"
CLOUD_API_KEY = "<EDIT THIS>" # YOUR_CLOUD_API_KEY
WML_CREDENTIALS = {
                "url": "https://au-syd.ml.cloud.ibm.com",
                "apikey": CLOUD_API_KEY
}
PROJECT_ID = "<EDIT THIS>" # YOUR_PROJECT_ID

use_existing_space = True

from ibm_watsonx_ai import APIClient

wml_client = APIClient(WML_CREDENTIALS)
print(wml_client.version)

existing_space_id = "<EDIT THIS>" # YOUR_SPACE_ID
space_id = existing_space_id

def generate_access_token():
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    data = {
        "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
        "apikey": CLOUD_API_KEY,
        "response_type": "cloud_iam"
    }
    
    response = requests.post(IAM_URL + "/identity/token", data=data, headers=headers)
    
    if response.status_code == 200:
        json_data = response.json()
        return json_data.get("access_token")
    else:
        raise Exception(f"Failed to get access token: {response.text}")


iam_access_token = generate_access_token()

from ibm_aigov_facts_client import AIGovFactsClient

facts_client = AIGovFactsClient(
    api_key=CLOUD_API_KEY,
    container_id=PROJECT_ID,
    container_type="project",
    region="sydney",
    disable_tracing=True
)

prompt_input="""
[INST] <>You are an assistant named Voyager who helps customers of a global travel agency. Your job is to assist customers with travel-related queries. You should only use the provided information from the document to generate your answer. If the answer to the question is not in the provided document, reply with: "I am sorry, but unfortunately, I do not have information to help you." Always maintain a friendly, professional, and informative tone.<> 

Here is the document you should use to answer the user:
{context1}\n{context2}\n{context3}

### **Rules for the Interaction:**
- Always stay in character as **Voyager, the travel assistant**, and respond in first person.
- If you are unsure how to respond, say: **"I am sorry, but unfortunately, I do not have information to help you."**
- If someone asks something **irrelevant** (not related to travel), respond with:  
  **"Sorry, I am Voyager, and I can help with travel-related queries. Do you have a travel-related question today that I can assist you with?"**
- Never suggest calling, emailing, or contacting customer service unless explicitly mentioned in the provided document.
- If the document provides step-by-step instructions, ensure you **list them out clearly** so that the user understands the process.
- If no specific travel service (flights, hotels, tours, visa assistance, etc.) is mentioned in the user’s question, provide a **general answer** covering all relevant aspects.
- If the question is about a **specific service (flights, hotel booking, travel insurance, visa, etc.)**, respond **only** with information related to that service.
- Assume that users have **already checked the travel agency’s website**, so do not direct them there. Instead, provide helpful information directly.
- Use polite and helpful language, ensuring that responses are clear and easy to follow.

---

### ** Example Interactions:**
#### **Example 1:**
**User’s question:** *"Hi, do you offer travel insurance for international trips?"* [/INST]  
**Step 1:** Check if the question is related to travel services. **Yes**, the question is about travel insurance.  
**Step 2:** Check if the answer can be found in the provided document. **Yes**, the document contains information about travel insurance.  
**Step 3:** Provide the answer in structured JSON.  

**ANSWER:**  
```json
{
  "answer": "Yes! We offer travel insurance for international trips, covering medical emergencies, trip cancellations, lost baggage, and more. Coverage details depend on the specific plan you choose. Let me know if you’d like more details on available options!"
}

Example 2:
User’s question: "Can you help me book a hotel in Paris?" [/INST]
Step 1: Check if the question is related to travel services. Yes, the user is asking about hotel booking.
Step 2: Check if the answer can be found in the provided document. Yes, hotel booking services are mentioned.
Step 3: Provide the answer in structured JSON.

ANSWER:
{
  "answer": "Absolutely! We offer hotel booking services in Paris and other locations worldwide. Let me know your travel dates and preferences, and I’d be happy to assist you with recommendations and reservations!"
}

Example 3:
User’s question: "Can I book a flight and a visa through you?" [/INST]
Step 1: Check if the question is related to travel services. Yes, it concerns flights and visa services.
Step 2: Check if the answer can be found in the provided document. Partially, flight booking is covered, but visa services are not mentioned.
Step 3: Provide the answer in structured JSON.

ANSWER:
{
  "answer": "Yes! We can assist with booking flights to your destination. However, for visa applications, we recommend checking with the respective embassy or consulate, as our agency does not directly handle visa processing. Let me know your travel details, and I’ll be happy to assist with your flight booking!"
}

"""

def get_latest_or_last_record(records):
    if not records:
        return None 

    records_with_timestamps = []
    for record in records:
        try:
            timestamp = record['metadata']['created_at']
            if timestamp:
                dt = datetime.fromisoformat(timestamp.replace('Z', '')) 
                records_with_timestamps.append((dt, record))
        except (KeyError, TypeError, ValueError):
            continue  

    if records_with_timestamps:
        return max(records_with_timestamps, key=lambda x: x[0])[1] 

    return records[-1]



from ibm_aigov_facts_client import DetachedPromptTemplate, PromptTemplate

detached_information = DetachedPromptTemplate(
    prompt_id="detached_prompt",
    model_id="GPT-4o",
    model_provider="OpenAI",
    model_name="GPT-4o",
    model_url="https://us-south.ml.cloud.ibm.com/ml/v1/deployments/insurance_test_deployment/text/generation?version=2021-05-01",
    prompt_url="prompt_url",
    prompt_additional_info={"SAP AI Core": "us-east1"}
)

task_id = "retrieval_augmented_generation"
name = "SAP Email Insights Application Prompt"
description = "SAP Email Insights use case integration with x.gov"
model_id = "GPT_4o"

# define parameters for PromptTemplate
prompt_variables = {"context1": "","context2": "","context3": "","question": ""}
input = prompt_input
input_prefix= ""
output_prefix= ""

prompt_template = PromptTemplate(
    input=input,
    prompt_variables=prompt_variables,
    input_prefix=input_prefix,
    output_prefix=output_prefix,
)

pta_details = facts_client.assets.create_detached_prompt(
    model_id=model_id,
    task_id=task_id,
    name=name,
    description=description,
    prompt_details=prompt_template,
    detached_information=detached_information)
project_pta_id = pta_details.to_dict()["asset_id"]

from ibm_cloud_sdk_core.authenticators import IAMAuthenticator, CloudPakForDataAuthenticator
from ibm_watson_openscale import *
from ibm_watson_openscale.supporting_classes.enums import *
from ibm_watson_openscale.supporting_classes import *


SERVICE_INSTANCE_ID = "<EDIT THIS>" # Update this to refer to a particular service instance

def get_wos_client(api_key, iam_url, service_url, service_instance_id):
    
    authenticator = IAMAuthenticator(
        apikey=api_key,
        url=iam_url,
        disable_ssl_verification=True
    )
    import certifi,os
    os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()
    
    wos_client = APIClient(
        authenticator=authenticator,
        service_url=service_url,
        service_instance_id=service_instance_id
    )

    return wos_client

wos_client = get_wos_client(CLOUD_API_KEY,IAM_URL,SERVICE_URL,SERVICE_INSTANCE_ID)

gen_ai_evaluator = wos_client.integrated_systems.add(
    name="SAP-Gov-Evaluator",
    description="Evaluating the prompt for SAP use case",
    type="generative_ai_evaluator",
    parameters={"evaluator_type": "watsonx.ai", "model_id": "ibm/granite-3-8b-instruct"},
    credentials={
        "wml_location": "cloud",
        "apikey": CLOUD_API_KEY,
        "url": "https://au-syd.ml.cloud.ibm.com",
        "auth_url": IAM_URL
    },
)

# get evaluator integrated system ID
result = gen_ai_evaluator.result._to_dict()
evaluator_id = result["metadata"]["id"]
print("evaluatorId is: ")
print(evaluator_id)

data_mart_id = wos_client.service_instance_id


label_column = "answer"
context_fields = ["context1", "context2", "context3"]
question_field = "question"
operational_space_id = "development"
problem_type= "retrieval_augmented_generation"
input_data_type= "unstructured_text"


monitors = {
    "generative_ai_quality": {
        "parameters": {
            "generative_ai_evaluator": { # global LLM as judge configuration
               "enabled": True,
               "evaluator_id": evaluator_id,
            },
            "min_sample_size": 1,
            "metrics_configuration": {  
                "pii" : {},
                "pii_input": {},
                "hap_score" : {},
                "answer_relevance": {},
                "retrieval_quality": {
                    "generative_ai_evaluator": {
                        "enabled": True,
                        "evaluator_id": evaluator_id,
                    },
                    "context_relevance": {
                    }
                           
                }
            }
        }
    }
}

response = wos_client.monitor_instances.mrm.execute_prompt_setup(
    prompt_template_asset_id=project_pta_id, 
    project_id=PROJECT_ID,
    label_column=label_column,
    context_fields = context_fields,     
    question_field = question_field,     
    operational_space_id=operational_space_id, 
    problem_type=problem_type,
    input_data_type=input_data_type, 
    supporting_monitors=monitors, 
    background_mode=False
)

result = response.result
result.to_dict()

response = wos_client.monitor_instances.mrm.get_prompt_setup(
    prompt_template_asset_id=project_pta_id,
    project_id=PROJECT_ID
)

result = response.result
result_json = result.to_dict()

if result_json["status"]["state"] == "FINISHED":
    print("Finished prompt setup. The response is {}".format(result_json))
else:
    print("Prompt setup failed. The response is {}".format(result_json))
    
subscription_id = result_json["subscription_id"]
print(subscription_id)
mrm_monitor_instance_id = result_json["mrm_monitor_instance_id"]
print(mrm_monitor_instance_id)


@app.route('/evaluate', methods=['POST'])
@cross_origin()
def evaluate():
    try:

        data = request.json
        if not data:
            return jsonify({"error": "Invalid input, JSON expected"}), 400
        
        llm_data = {
            "question": data.get("question", ""),
            "answer": data.get("answer", ""),
            "generated_text": data.get("generated_text", ""),
            "context1": data.get("context1", ""),
            "context2": data.get("context2", ""),
            "context3": data.get("context3", ""),
        }

        df = pd.DataFrame([llm_data])

        test_data_path = "test_data.csv"

        df.to_csv(test_data_path, index=False)
        
        wos_client = get_wos_client(CLOUD_API_KEY,IAM_URL,SERVICE_URL,SERVICE_INSTANCE_ID)

        start_time = time.time()
        
        response = wos_client.monitor_instances.mrm.evaluate_risk(
            monitor_instance_id=mrm_monitor_instance_id,
            test_data_set_name="test_data",
            test_data_path=test_data_path,
            content_type="multipart/form-data",
            body={},
            project_id=PROJECT_ID,
            includes_model_output=True,
            background_mode=False
        )
        
        evaluate_risk_time = time.time() - start_time
        print(f"evaluate_risk API took {evaluate_risk_time:.2f} seconds")
        
        start_time = time.time()
        
        result = wos_client.data_sets.list(
          target_target_id=subscription_id,
          target_target_type="subscription",
          type="gen_ai_quality_metrics"
        ).result

        list_datasets_time = time.time() - start_time
        print(f"list datasets API took {list_datasets_time:.2f} seconds")
        genaiq_dataset_id = result.data_sets[0].metadata.id
        
        print(genaiq_dataset_id)
        
        start_time = time.time()
        
        result = wos_client.data_sets.get_list_of_records(data_set_id = genaiq_dataset_id).result
        latest_record = get_latest_or_last_record(result["records"])
        
        get_records_time = time.time() - start_time
        print(f"get_list_of_records API took {get_records_time:.2f} seconds") 
        
        return jsonify(latest_record), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))  # Default to 5000 for local dev
    app.run(host="0.0.0.0", port=port)

    