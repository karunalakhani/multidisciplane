import streamlit as st
import json
import requests


medical_specialties = [
    "general-practice",
    "neurology",
    "cardiology",
    "dermatology",
    "endocrinology",
    "gastroenterology",
    "hematology-and-oncology",
    "internal-medicine",
    "obstetrics-and-gynaecology",
    "general-surgery",
    "psychiatry",
    "oncology",
    "paediatrics",
    "emergency-medicine",
    "nephrology",
    "urology",
    "medication",
    "clinical-pathology",
    "histopathology",
    "orthopaedics",
    "rheumatology",
    "geriatrics",
    "critical-care",
    "sexual-medicine",
    "spine-surgery",
    "colorectal-surgery",
    "nursing",
    "ophthalmology",
    "pulmonary-and-critical-care"
]


# Step 1: Query the Determiner Bot
def query_bot(bot_name, input_prompt,anything_key):
    """
    Send a prompt to a specified bot and retrieve the response.
    """
    # Simulated API request to the bot
    if bot_name == "determiner-bot":
        promptt="""You are a medical assistant. Based on the provided medical condition, suggest the most appropriate medical specialty or specialties from the following list: 
        ["general-practice", "neurology", "cardiology", "dermatology", "endocrinology", "gastroenterology", "hematology-and-oncology", "internal-medicine", "obstetrics-and-gynaecology", "general-surgery", "psychiatry", "oncology", "paediatrics", "emergency-medicine", "nephrology", "urology", "medication", "clinical-pathology", "histopathology", "orthopaedics", "rheumatology", "geriatrics", "critical-care", "sexual-medicine", "spine-surgery", "colorectal-surgery", "nursing", "ophthalmology", "pulmonary-and-critical-care"].If the condition requires more than one specialty, suggest all relevant specialties. Provide the response in the following format:

        { 
           "Specialists": ["<specialty1>", "<specialty2>", ...]
        }

        Where:
        
        - "Specialists" is an array of specialties relevant to the given medical condition. Add General Practitioner if needed.

        For example:
        If the medical condition is "chronic headaches with vision issues", the response should be:
        {
          
            "Specialists": ["neurologist", "ophthalmologist"]
        }
        Make sure it is from provided list only with same name.

        Medical Condition:"""
        # Replace this section with actual API calls to the determiner bot
        response = query_model('determiner-bot',promptt,input_prompt,anything_key)
        return response
    return {}

# Step 2: Generate Prompts for Each Specialist
def generate_specialist_prompt(specialty, payload, user_prompt):
    """
    Create a custom prompt for the given specialty based on the input payload.
    """
    return f"""
    You are a {specialty}. Given the patient's details:
    - Symptoms: {payload}
    - Medical history: (if applicable)
    - Current medications: (if applicable)
    - Known allergies: (if applicable)
    
    Task:
    {user_prompt}
    """

# Step 3: Query a Model

def query_model(workspace_name, message,input_data,anything_key):
    url = f"https://anythingllm.axonichealth.com/api/v1/workspace/{workspace_name}/chat"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {anything_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "message": message + " " + input_data,
        "mode": "chat"
        
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        print(response)
        return response.json().get("textResponse", "No response received.")
    else:
        print(response.json())
        return "Error querying the workspace." + response.json().get("error")

# Step 4: Aggregate Responses
# Step 4: Aggregate Responses
def aggregate_responses(responses):
    """
    Aggregate responses from different specialists into a structured format.
    """
    aggregated = {"Responses": []}
    
    for response in responses:
        aggregated["Responses"].append(response)
    return aggregated

# Step 5: Generate Final Prompt
def generate_final_prompt(aggregated_response):
    """
    Generate a prompt for the final model to create a unified report.
    """
    responses_summary = "\n".join(
        [f"{r['response']}" for r in aggregated_response["Responses"]]
    )
    return f"""
    Given the following specialist recommendations:
    {responses_summary}
    
    Task:
    Integrate these into a single, comprehensive medication report as per the initial instructions.
    """

# Step 6: Output Final Response
def output_response(response):
    """
    Handle the output of the final model, e.g., save as JSON.
    """
    with open("final_report.json", "w") as f:
        json.dump(response, f, indent=4)
    print("Final report saved to 'final_report.json'")


# Streamlit application



def main():
    st.title("Specialty Recommendation and Aggregation App")

    # Input form
    with st.form("input_form"):
        api_key = "EPCJ137-M454740-N6ZJV6H-MA38PA9"
        input_prompt = st.text_area("Enter Medical Condition")
        user_prompt = st.text_area("Enter user prompt/Task for model")
   
        submitted = st.form_submit_button("Submit")

    if submitted:
        if not api_key or not input_prompt:
            st.error("Please fill in all fields.")
            return

        st.write("Querying the Determiner Bot...")
        determiner_response = query_bot("determiner-bot", input_prompt, api_key)
 


        try:
            determiner_response = json.loads(determiner_response)
            specialists = determiner_response["Specialists"]
            st.success(f"Determiner Bot suggested specialties: {specialists}")
        except json.JSONDecodeError:
            st.error("Failed to decode the determiner response.")
            return

        # Get responses from all specialists
        st.write("Fetching responses from specialists...")
        specialist_responses = []
        for specialty in specialists:
            prompt = generate_specialist_prompt(specialty, input_prompt,user_prompt)

            response = query_model(specialty, prompt, input_prompt, api_key)
            specialist_responses.append({"Specialty": specialty, "Response": response,"response":response})

        # Display responses from specialists
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Responses from Specialists")
            for resp in specialist_responses:
                st.markdown(f"### {resp['Specialty']}")
                st.write(resp["Response"])

        # Aggregate responses
        aggregated_response = aggregate_responses(specialist_responses)
        final_prompt = generate_final_prompt(aggregated_response)
        final_response = query_model("medical-advanced", final_prompt, '',anything_key)
        
        # Step 5: Output the final response
        output_response(final_response)


        with col2:
            st.subheader("Aggregated Response")

            st.text_area("Aggregated Response", final_response, height=400)

        # Option to download the aggregated response
        aggregated_json = json.dumps(final_response, indent=4)
        st.download_button(
            label="Download Aggregated Response",
            data=aggregated_json,
            file_name="aggregated_response.json",
            mime="application/json"
        )


if __name__ == "__main__":
    main()
