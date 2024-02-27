
import json
import base64
import random
import string
import boto3
from sigv4 import SigV4HttpRequester

# Bedrock Variable
agentId = os.environ['BEDROCK_AGENT_ID']
# agentId = "PRTQZRJKMV"
agentAliasId = os.environ['BEDROCK_AGENT_ALIAS_ID']
# agentAliasId = "STCJZQXFDO"

session = boto3.Session("us-east-1")
agent_client = boto3.client('bedrock-agent-runtime')


# create a function get_response_from_agent that can be exported and used in another python file    
def get_response_from_agent(query, sessionId):
    if query is not None:

        agent_query = {
            "inputText": query,   
            "enableTrace": True,
        }

        # send request
        print("Invoking Agent with query: " + query)
        agent_url = f'https://bedrock-agent-runtime.us-east-1.amazonaws.com/agents/{agentId}/agentAliases/{agentAliasId}/sessions/{sessionId}/text'
        requester = SigV4HttpRequester()
        response = requester.send_signed_request(
            url=agent_url,
            method='POST',
            service='bedrock',
            headers={
                'content-type': 'application/json', 
                'accept': 'application/json',
            },
            region='us-east-1',
            body=json.dumps(agent_query)
        )
        
        if response.status_code == 200:
            # Parse sig4_request Response
            response_string = ""
            for line in response.iter_content():
                try:
                    response_string += line.decode(encoding='utf-8')
                except:
                    continue

            split_response = response_string.split(":message-type")
            last_response = split_response[-1]
            try:
                encoded_last_response = last_response.split("\"")[3]
                print("encoded_last_response: " + str(encoded_last_response))
                if encoded_last_response == "citations":
                    # Find the start and end indices of the JSON content
                    start_index = last_response.find('{')
                    end_index = last_response.rfind('}')

                    # Extract the JSON content
                    json_content = last_response[start_index:end_index + 1]

                    try:
                        data = json.loads(json_content)
                        final_response = data['attribution']['citations'][0]['generatedResponsePart']['textResponsePart']['text']
                    except json.decoder.JSONDecodeError as e:
                        print(f"JSON decoding error: {e}")
                    except KeyError as e:
                        print(f"KeyError: {e}")
                else:
                    decoded = base64.b64decode(encoded_last_response)
                    final_response = decoded.decode('utf-8')
            except base64.binascii.Error as e:
                print(f"Base64 decoding error: {e}")
                final_response = last_response  # Or assign a default value

        print("Agent Response: " + final_response)
        return final_response.replace("$", "\$")
    
def session_generator():
    # Generate random characters and digits
    digits = ''.join(random.choice(string.digits) for _ in range(4))  # Generating 4 random digits
    chars = ''.join(random.choice(string.ascii_lowercase) for _ in range(3))  # Generating 3 random characters
    
    # Construct the pattern (1a23b-4c)
    pattern = f"{digits[0]}{chars[0]}{digits[1:3]}{chars[1]}-{digits[3]}{chars[2]}"
    print("Session ID: " + str(pattern))

    return pattern