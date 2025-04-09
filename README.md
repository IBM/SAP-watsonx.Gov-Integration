<b>LLM Output Evaluation with Watsonx.governance</b><br>
This project provides an API to evaluate LLM-generated outputs using IBM Watsonx.governance APIs. It sends a question, context, and generated text to the governance layer and 
retrieves quality metrics such as answer relevance, PII detection, and context relevance.


<b>Features</b><br>
Evaluates LLM-generated responses using evaluate_risk API from Watsonx.governance<br>
Monitors metrics such as:<br>
Answer Relevance<br>
PII detection<br>
Context Relevance<br>
Prepares monitoring setup using a Prompt Template<br>
Supports prompt creation via AIGovFactsClient<br>


<b>Prerequisites</b><br>
Ensure you have the following before starting:<br>

IBM Cloud account with access to:<br>
IBM Watson Machine Learning<br>
IBM Watson OpenScale (Watsonx.governance)<br>
Python 3.11<br>
An IBM Cloud API Key<br>
Existing IBM Watson project and space<br>
Required Python libraries<br>


<b>Installation</b><br>
Install the required packages:<br>
pip install -r requirements.txt<br>


<b>Configuration</b><br>
Edit the following placeholders in the script with your credentials and details:<br>
CLOUD_API_KEY = "<EDIT THIS>"<br>
PROJECT_ID = "<EDIT THIS>"<br>
existing_space_id = "<EDIT THIS>"<br>
SERVICE_INSTANCE_ID = "<EDIT THIS>"<br>


<b>Running the Application</b><br>
To start the app locally:<br>
python Gov_Evaluation.py<br>


<b>API Usage</b><br>
POST /evaluate<br>

Evaluates an LLM output for quality metrics.<br>
<b>Request Payload (JSON):</b><br>
{
  "question": "What is the capital of France?",
  "generated_text": "The capital of France is Paris.",
  "context1": "France is a country in Europe.",
  "context2": "France capital is Paris.",
  "context3": "Eiffel Tower is located in Paris"
}



