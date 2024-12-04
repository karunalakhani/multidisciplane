import streamlit as st
import json
import requests
import markdown
import io
import pdfkit



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
    mode = st.radio("Select Mode", ["Dynamic", "Static"])

    # Input form
    with st.form("input_form"):
        api_key = "EPCJ137-M454740-N6ZJV6H-MA38PA9"
        input_prompt = st.text_area("Enter Medical Condition")
        user_prompt = st.text_area("Enter user prompt/Task for model")
   
        
        if mode == "Static":
            custom_specialties = st.text_area(
                "Enter a custom list of specialties (comma-separated)"
            )
            specialists = [s.strip() for s in custom_specialties.split(",") if s.strip()]
        submitted = st.form_submit_button("Submit")

    if submitted:
        if not api_key or not input_prompt or not user_prompt:
            st.error("Please fill in all fields.")
            return

        st.write("Querying the Determiner Bot...")
        if mode != "Static":
            determiner_response = query_bot("determiner-bot", input_prompt, api_key)
     
    
    
            try:
                determiner_response = json.loads(determiner_response)
                specialists = determiner_response["Specialists"]
                st.success(f"Determiner Bot suggested specialties: {specialists}")
            except json.JSONDecodeError:
                st.error("Failed to decode the determiner response.")
                return
        else:
            st.success(f"Static flow specialties: {specialists}")
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
        final_response = query_model("medical-advanced", final_prompt, '',api_key)
        
        # Step 5: Output the final response
        output_response(final_response)


        with col2:
            st.subheader("Aggregated Response")

            st.markdown(final_response)
    
        # Generate and download PDF
        if st.button("Download as PDF"):
            try:
                # Convert Markdown to HTML
                html_content = markdown.markdown(final_response)
                html_full = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <style>
                        body {{
                            font-family: Arial, sans-serif;
                            line-height: 1.6;
                        }}
                        pre {{
                            background: #f4f4f4;
                            padding: 10px;
                            border-radius: 5px;
                        }}
                    </style>
                </head>
                <body>
                    {html_content}
                </body>
                </html>
                """
    
                # Generate PDF from HTML
                pdf_bytes = pdfkit.from_string(html_full, False)
    
                # Create a download button for the PDF
                st.download_button(
                    label="Download Aggregated Response as PDF",
                    data=pdf_bytes,
                    file_name="aggregated_response.pdf",
                    mime="application/pdf",
                )
            except Exception as e:
                st.error(f"Error generating PDF: {str(e)}")


if __name__ == "__main__":
    main()
