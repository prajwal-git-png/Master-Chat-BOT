from flask import Flask, render_template, request,jsonify
import requests
import json
import google.generativeai as genai

# app = Flask(__name__)
app = Flask(__name__)

# COHERE IS IMPLEMENTED HERE

def cohere_ai_r_plus(query, temperature=0.7, web_search=False):
    url = "https://production.api.os.cohere.ai/coral/v1/chat"
    auth = "Bearer [add your key]"
    model = "command-r-plus"

    headers = {
        "Authorization": auth,
    }

    payload = {
        "message": query,
        "model": model,
        "temperature": temperature,
        "citationQuality": "CITATION_QUALITY_ACCURATE",
    }

    if web_search:
        payload["connectorsSearchOptions"] = {
            "preamble": "## Task And Context\n\nYou help people answer their questions and other requests interactively. You will be asked a very wide array of requests on all kinds of topics. You will be equipped with a wide range of search engines or similar tools to help you, which you use to research your answer. You should focus on serving the user's needs as best you can, which will be wide-ranging. The current date and time is Thursday, April 4, 2024\n\n## Style Guide\n\nUnless the user asks for a different style of answer, you should answer in full sentences, using proper grammar and spelling."
        }
        payload["connectors"] = [{"id": "web-search"}]

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        return "Sorry, I couldn't understand that."
    else:    
        final_output = json.loads(response.text.strip().split('\n')[-1])["result"]["chatStreamEndEvent"]["response"]["text"]
        return final_output

# END HERE - COHERE

# IMAGE GEN IS IMPLEMENTED HERE 

class StabilityAI:
    def __init__(self):
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer [ Add your key ]"
        }

    def text_to_image(self, text):
        description_body = {"text_prompts": [{"text": text}]}
        response = requests.post(
            "https://api.stability.ai/v1/generation/stable-diffusion-v1-6/text-to-image", 
            json=description_body, headers=self.headers)
        json_response = response.json()
        if "message" in json_response:    
            raise Exception(json_response["message"])
        result = json_response["artifacts"][0]["base64"]
        return "data:image/png;base64," + result

# IMAGE GEN ENDS HERE


#PAI AI HAS BEEN IMPLEMENTED HERE

API_URL = "https://pi.ai/api/chat"
HEADERS_TEMPLATE = {
    "Accept": "text/event-stream",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
    "Content-Type": "application/json",
    "Dnt": "1",
    "Origin": "https://pi.ai",
    "Priority": "u=1, i",
    "Referer": "https://pi.ai/talk",
    "Sec-Ch-Ua": "\"Chromium\";v=\"124\", \"Google Chrome\";v=\"124\", \"Not-A.Brand\";v=\"99\"",
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": "\"Windows\"",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "X-Api-Version": "3"

}

# Add yours credentials 

session_id = "NNbWJodLsKxGYpuw2teEa"
conversation_id = "eMY6drciyAn7SszcweVMW"

def get_new_session_cookie():
    response = requests.get("https://pi.ai")
    return list(response.cookies)[0].value if response.cookies else None

def generate_response(user_query, session_cookie="MINE"):
    headers = HEADERS_TEMPLATE.copy()
    headers["Cookie"] = f"__Host-session={session_id}; __cf_bm={session_cookie}"
    
    payload = {
        "text": user_query,
        "conversation": conversation_id
    }

    with requests.Session() as session:
        response = session.post(API_URL, json=payload, headers=headers, stream=True)
        
        if response.status_code in (401, 403):
            new_session_cookie = get_new_session_cookie()
            return generate_response(user_query, new_session_cookie)

        complete_response = {"text": ""}

        if response.status_code == 200:
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    try:
                        json_data = json.loads(line.lstrip("data:"))
                        content = json_data.get("text", "")
                        with_emoji = content.encode("latin1").decode("utf-8")
                        complete_response["text"] += with_emoji
                    except json.JSONDecodeError:
                        continue

    return complete_response


# PAI ENDS HERE

# GEMINI IMPLEMENTED HERE 

genai.configure(api_key="ADd yours")

instruction = (
    "Imagine you are a person named gem , response to the user request as a human - help them to analyze there mental state and help them to enhance their mood , and make responses shorter and meaning full"
)

model = genai.GenerativeModel(
    "models/gemini-1.5-pro-latest",
    system_instruction=instruction
)

# ENDS HERE 

# DEFINING FUNCTIONS TO GET RESPONSE

# FOR PAI 
@app.route('/pai')
def index_pai():
    return render_template('pai.html')

@app.route('/api/chat', methods=['POST'])
def chat_pai():
    user_input = request.json.get('query')
    response = generate_response(user_input)
    text_response = response["text"]
    return jsonify({"response": text_response})

# PAI ENDS

# GEMINI 
@app.route('/chat_gem')
def home_gemini():
    return render_template('gemini.html')

@app.route('/chat_gem', methods=['POST'])
def chat_gem():
    user_input = request.form['user_input']
    if user_input.lower() == "exit":
        response = "Goodbye!"
    else:
        response = model.generate_content(user_input).text
    return response

# ENDS 

# IMG GEN 

@app.route("/imggen", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        user_input = request.json["text"]
        stability_ai = StabilityAI()
        image_src = stability_ai.text_to_image(user_input)
        return jsonify({"image_src": image_src})
    return render_template("imggen.html")

# ENDS HERE 

# COHERE IS DEFINED HERE

@app.route('/cohere')
def index_cohere():
    return render_template('cohere.html')

@app.route('/chat', methods=['POST'])
# @app.route('/cohere_chat', methods=["GET",'POST'])
def chat():
    user_input = request.json['user_input']
    response = cohere_ai_r_plus(user_input)
    return response
# END OF COHERE 

# MAIN ROOT IS HERE OR MAIN ROUTE
@app.route('/')
def index():
    return render_template('pai.html')  

if __name__ == '__main__':
    app.run(debug=True)
