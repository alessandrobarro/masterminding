import os
import json
import openai
import requests
import smtplib
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import base64
import json
import time
from youtubesearchpython import *


"""
To start run:
model1="gpt-4-turbo-preview"
answers_dic, learning_path, df=start(model1)
"""

model1="gpt-4-turbo-preview"

# API tokens setup
openai_api_key = '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'
tf_api_key = 'tfp_8ef1kHHzkRcL692B81tjMV4EkVCU37N3xnN5BEXENtAV_3pc49KjG6t6xjR'
openai.api_key = openai_api_key

#-------------------- GET INITIAL TF OUTPUT ----------------------------------------------------
def TypeForm_Output_InitialForm(tf_api_key):
    variable_names = ["Grade", "Goal", "Sub_topic_(bool)", "Sub_topic_(Text)", "preparation", "length", "School", "First_Name", "Last_name", "Email"]
    form_id = "TbTudQc6"
    # Mapping of variable names to their corresponding refs
    variable_refs = [
        "0522e664-763b-442d-9958-e6537b61a0f0",  # Grade
        "cba3f4b2-58b7-449d-8a32-4d9c9e3484d3",  # Goal
        "0e8ca688-7973-452e-ac1d-1b93438b7a22",  # Sub topic (bool)
        "9cd502df-18b2-4a82-8e53-a574ce688345",  # Sub topic (Text)
        "0918e7f7-7d81-40e2-9f84-5eeafa247cdf",  # preparation
        "9208e731-a9a4-4a70-9e40-365c5ffc250a",  # length
        "601f7f0a-066b-4157-b98e-966ec8932119",  # School
        "c751e53d-306d-483a-a410-fa8f24e2fb2a",  # Name
        "be8c03c9-c530-45ee-924e-0a0dc4f29f46",  # Last name
        "e85ddde2-4e7b-425f-8a8a-bc2149fa9a9e"   # Email
        
    ]
    headers = {
        "Authorization": f"Bearer {tf_api_key}",
        "Content-Type": "application/json",
    }

    response = requests.get(
        f"https://api.typeform.com/forms/{form_id}/responses", headers=headers
    )

    if response.status_code == 200:
        responses = response.json().get("items", [])
        if responses:
            # Get the most recent response
            latest_response = responses[0]
            answers_dic = find_answers([latest_response], variable_refs, variable_names)
            print("TypeForm information retrived")
            return answers_dic, latest_response
    else:
        print(f"Error: {response.status_code}")
        return None, responses

def find_answers(responses, variable_refs, variable_names):
    answers_dic = {name: None for name in variable_names}  # Initialize dictionary with None values
    
    for response in responses:
        for answer in response.get('answers', []):
            ref = answer.get('field', {}).get('ref')
            if ref in variable_refs:
                # Find the corresponding variable name for the ref
                name = variable_names[variable_refs.index(ref)]
                # Update the answer in the dictionary based on the type of answer
                answer_type = answer.get('type')
                if answer_type == 'choice':
                    answers_dic[name] = answer.get('choice', {}).get('label')
                elif answer_type == 'boolean':
                    answers_dic[name] = answer.get('boolean')
                elif answer_type == 'number':
                    answers_dic[name] = answer.get('number')
                elif answer_type == 'email':
                    answers_dic[name] = answer.get('email')
                else:
                    answers_dic[name] = answer.get('text')
    return answers_dic

#-------------------- SUBTOPICS ----------------------------------------------------
def generate_subtopics(answers_dic, model):

    teacher=f"Act as a teacher that explain things in the most simple way to student of {answers_dic.get('Grade')} that from 0 (don't know anything) to 10 (know everything about) are prepared student of {answers_dic.get('preparation')}. You MUST output only the content without any introduction."

    if answers_dic.get('Sub_topic_(bool)'):
        prompt = f"""Given the following topic/question/learning goal {answers_dic.get('Goal')}, generate the optimal learning path with 10 sub-topics for student of {answers_dic.get('Grade')} that from 0 (don't know anything about) to 10 (know everything about) are prepared {answers_dic.get('preparation')}. 
                    Pay more attention to the subtopic: {answers_dic.get('Sub_topic_(Text)')}. 
                    Each sub-topic must be descriptive and detail of the sub-learning goal that must be achive in order to achieve the learning goal {answers_dic.get('Goal')}
                    Each sub-topic must be separated only by a single '/' character among subtopics, in a single line of prompt (no dot lists, etc.)
                    The output should strictly adhere to this format for it to be directly convertible into an array:
                    "sub-topic1/sub-topic2/sub-topic3/.../sub-topic10"
                    Your output MUST be formatted EXACTLY as the array with "/" as described before, with NO DEVIATION, NO ADDITIONAL CONTENT. Adherence to this structured format is non-negotiable.
                    """
    else:
        prompt = f"""Given the following topic/question/learning goal {answers_dic.get('Goal')}, generate the optimal learning path with 10 sub-topics for student of {answers_dic.get('Grade')} that from 0 (don't know anything about) to 10 (know everything about) are prepared {answers_dic.get('preparation')}. 
                    Each sub-topic must be descriptive and detail of the sub-learning goal that must be achive in order to achieve the learning goal {answers_dic.get('Goal')}
                    Each sub-topic must be separated only by a single '/' character among subtopics, in a single line of prompt (no dot lists, etc.)
                    The output should strictly adhere to this format for it to be directly convertible into an array:
                    "sub-topic1/sub-topic2/sub-topic3/.../sub-topic10"
                    Your output MUST be formatted EXACTLY as the array with "/" as described before, with NO DEVIATION, NO ADDITIONAL CONTENT. Adherence to this structured format is non-negotiable.
                    """
    
    response = openai.ChatCompletion.create(
    model=model,  # Update the model name based on current availability
    messages=[
        {"role": "system","content": teacher },
        {"role": "user", "content": prompt}
    ],temperature=1,max_tokens=1024,top_p=1,frequency_penalty=0,presence_penalty=0)
    learning_path_response = response['choices'][0]['message']['content']
    learning_path = learning_path_response.split("/")
    count=0
    print("Learning path created. Checking the structures...")
    if len(learning_path) != 10:
        print("Structure wrong")
        learning_path = adjust_format_learning_path(answers_dic,learning_path_response,count)
    print("structure ok")
    return learning_path, response

def adjust_format_learning_path(answers_dic,learning_path_response,count):
    count+=1
    if count==5:
        return None
    adjustment_prompt = f"""Given the learning goal "{answers_dic.get('Goal')}" for a student of grade "{answers_dic.get('Grade')}" who is currently at a preparation level of "{answers_dic.get('preparation')}" on a scale from 0 (know nothing) to 10 (know everything), generate an optimal learning path. This path should be structured as a sequence of 10 sub-topics that transition from basic to advanced, catering to the specified preparation level.

                        YOUR GOAL is to REFORMAT the LEARNING_PATH attached below as a single-line string, listing exactly 10 sub-topics separated only by a '/' character with no spaces before or after each '/'. Do not include any punctuation or additional characters within or between sub-topics. Each sub-topic should succinctly describe a step in the learning progression necessary to achieve the overall goal "{answers_dic.get('Goal')}".

                        The output should strictly adhere to this format for it to be directly convertible into an array:

                        "sub-topic1/sub-topic2/sub-topic3/.../sub-topic10"

                        Ensure that the sequence logically progresses in complexity and relevance, offering a comprehensive roadmap from a beginner's perspective to full mastery.

                        Note: The output MUST RIGOROUSLY conform to the described format. Adherence to this structured format is critical and non-negotiable. Adjustments should reorganize the provided content to precisely fit this structure, maintaining the original question and answer essence.
                        
                        LEARNING_PATH: {learning_path_response}
                        """

    adjustment_response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0125",  # Update the model name based on current availability
        messages=[
            {"role": "system","content": "Validate the structured output from ChatGPT against the expected format. The output must be a single line string with 10 sub-topics separated by '/' without spaces. Ensure there are exactly 10 sub-topics, each representing a step towards achieving the learning goal. Confirm the special emphasis on the specified sub-topic. If the output matches the criteria, mark it as valid for array conversion; otherwise, provide feedback on discrepancies." },
            {"role": "user", "content": adjustment_prompt}
        ],temperature=0.5,max_tokens=2048,top_p=1,frequency_penalty=0,presence_penalty=0)
    learning_path_response = adjustment_response['choices'][0]['message']['content'].split("/")
    learning_path = learning_path_response.split("/")
    print("Checking the the structure readjusted..")
    if len(learning_path) != 10:
            print(f"Structure generated wrongly. Attempt: {count}")
            adjust_format_learning_path(answers_dic,learning_path_response,count)
    return learning_path


#-------------------- FIND YT VIDEO ----------------------------------------------------
def find_best_matching_video(keywords, answers_dic=None):
    print("Starting to find the best matching video...")
    if answers_dic != None:
        grade = answers_dic.get('Grade')
        if grade:
            keywords += " " + grade

    videosSearch = VideosSearch(keywords, limit=10)  
    search_results = videosSearch.result()

    matching_videos = []

    for video in search_results['result']:
        # Calculate matching score based on title, description, and keywords
        view_count_text = video.get('viewCount', {}).get('text', '0').replace(' views', '').replace(',', '')
        if not view_count_text.isdigit() or int(view_count_text) < 100000:
            continue
        matching_score = 0
        try:
            matching_score += sum(word in video['title'].lower() for word in keywords.lower().split())
        except:
            print("Error in processing video title")
            pass
        try:
            matching_score += sum(word in video['descriptionSnippet'][0]['text'].lower() for word in keywords.lower().split())
        except:
            print("Error in processing video description")
            pass
        # Assuming 'keywords' field exists and is a list of keywords for each video
        try:
            matching_score += sum(word in video.get('keywords', '').lower() for word in keywords.lower().split())
        except:
            print("Error in processing video keywords")
            pass
        duration = video['duration']
        # Convert duration to seconds
        total_seconds = sum(x * int(t) for x, t in zip([3600, 60, 1], re.findall(r'\d+', duration)))

        matching_videos.append((video['id'], matching_score, total_seconds))

    # Sort videos by matching score and duration
    matching_videos.sort(key=lambda x: -x[1])

    # Select the top 3 videos with the highest matching score
    top_videos = matching_videos[:3]

    # Return the shortest video among the top 3
    if top_videos:
        video_id = top_videos[0][0]
        info= Video.getInfo(video_id)
        video_link = info.get("link")
        video_title = info.get("title")
        video_description = info.get("description")
        try:
            transcript = Transcript.get(video_link)
        except:
            transcript=video_description

        print("Video found. Retrieving information...")
        return info, video_link, video_title, video_description, transcript
    return None

#-------------------- VIDEO DESCRIPTION ----------------------------------------------------
def generate_description(video_transcript, answers_dic):
    teacher=f"Act as a teacher that explain things in the most simple way to student of {answers_dic.get('Grade')} that from 0 (don't know anything) to 10 (know everything about) are prepared student of {answers_dic.get('preparation')}. You MUST output only the content without any introduction."
    
    description_prompt = f"""Generate a structured description of the VIDEO give the VIDEO TRANSCRIPT reported at the end, as a student from {answers_dic.get('Grade')} can easily understand. This description must be didactic, teaching about the content of the video.
                                VIDEO TRANSCRIPT : {video_transcript}"""
    try:
        # Make the API call
        description_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0125",  # Update the model name based on current availability
            messages=[
                {"role": "system", "content": teacher},
                {"role": "user", "content": description_prompt}
            ],temperature=1,max_tokens=1024,top_p=1,frequency_penalty=0,presence_penalty=0)

        # Extract the structured description
        structured_description = description_response.choices[0].message['content']  # Update based on actual response structure if needed
    except:
        description_response = openai.ChatCompletion.create(
            model="gpt-4-0125-preview",  # Update the model name based on current availability
            messages=[
                {"role": "system", "content": teacher},
                {"role": "user", "content": description_prompt}
            ],temperature=1,max_tokens=1024,top_p=1,frequency_penalty=0,presence_penalty=0)

        # Extract the structured description
        structured_description = description_response.choices[0].message['content']  # Update based on actual response structure if needed

    print("Structured description generated successfully.")
    return structured_description

#-------------------- CREATE QUIZ ----------------------------------------------------
def generate_quiz_json(video_transcript, answers_dic, subtopic, model):
    print("Start generating quiz...")
    teacher=f"Act as a teacher that explains things most simply to students of {answers_dic.get('Grade')} that from 0 (don't know anything) to 10 (know everything about) are prepared student of {answers_dic.get('preparation')}. You MUST output only the content without any introduction. If you have to write math formulas, write them using mathematical symbols"    
    
    quiz_prompt = f"Using the provided VIDEO TRANSCRIPT at the end, meticulously construct a JSON-formatted quiz comprising 10 questions, segmented into 3 inquiries about the video content based on the VIDEO TRANSCRIPT and 7 didactic question about {subtopic} ; for student of {answers_dic.get('Grade')} that from 0 (don't know anything) to 10 (know everything about) are prepared student of {answers_dic.get('preparation')}. Each question must present 4 answer options, with the imperative that the first answer MUST BE the correct answer. The formatting MUST be exact, employing a JSON structure conducive to straightforward transformation into a matrix format. Adherence to this structured format is non-negotiable, demanding precision in the layout and content of each question and answer set." + """
                    For each question, adhere to the following strict structure:
                    {"question": "Specify the main subject of the video.", "answers": ["Linear equations with variables on both sides","Quadratic equations","Fundamentals of geometry","Introduction to calculus"]}
                    This structured format is mandatory for all 10 questions, with no deviations permitted. The output must align perfectly with these guidelines DO NOT output anything else than the final structure.
                    """+f"VIDEO TRANSCRIPT: {video_transcript}"
    
   
    
    quiz_response = openai.ChatCompletion.create(
        model=model,  # Update the model name based on current availability
        messages=[
            {"role": "system","content": teacher + " You must create ONLY the quiz, without any non-related or accessory word." },
            {"role": "user", "content": quiz_prompt}
        ],temperature=0.75,max_tokens=2048,top_p=1,frequency_penalty=0,presence_penalty=0)

    
    
    try:
        quiz_json_str = quiz_response['choices'][0]['message']['content']
    except KeyError as err:
        print("KeyError: 'text' not found in quiz response.")
        return quiz_response, None
    except AttributeError as err:
        print("AttributeError: 'text' not found in quiz response.")
        return quiz_response, None
    
    try:
        print("Attempting to load quiz_json...")
        quiz_json = json.loads(quiz_json_str)
        print("Quiz JSON loaded successfully.")
    except json.JSONDecodeError:
        print("JSONDecodeError occurred. Attempting to adjust quiz_json_str...")
        quiz_json_str = quiz_json_str.replace("json", "", 1).replace("JSON", "", 1).replace("quiz", "", 1).replace("Quiz", "", 1).replace("QUIZ", "", 1).strip()
        try:
            quiz_json = json.loads(quiz_json_str)
            print("Adjusted quiz_json_str loaded successfully.")
        except json.JSONDecodeError:
            flag=1
            count = 5
            while flag==1 or count<5:
                quiz_json, flag = adjust_quiz_format_toJSON(quiz_json_str, flag)
                if flag==1:
                    quiz_json, flag =adjust_quiz_format_toJSON(quiz_json, flag)
                count +=1

    print("Quiz JSON loaded successfully.")
    
    quiz_matrix = []
    try:
        for question in quiz_json:
            row = [question['question']]
            row.extend(question['answers'])
            quiz_matrix.append(row)
    except: 
        try:
            for question in quiz_json['questions']:
                row = [question['question']]
                row.extend(question['answers'])
                quiz_matrix.append(row)
        except:
            return quiz_json, None

    print("Quiz matrix created.")
    
    if quiz_matrix:
        return quiz_json, quiz_matrix
    else:
        j=0
        while not quiz_matrix or j<5 or flag==1:
            quiz_json, flag = adjust_quiz_format_toJSON(quiz_json_str, flag)
        return quiz_json, quiz_matrix

def adjust_quiz_format_toJSON(quiz_response_content, flag):
    print("Starting quiz format adjustment...")
    
    adjustment_prompt = """
                        Please precisely format the following quiz responses into a strict and specific structure for seamless integration into an educational matrix. Each question MUST be formatted EXACTLY as shown below, with NO DEVIATION, NO ADDITIONAL CONTENT:

                        {"question": "INSER THE QUESTION", "answers": ["INSERT THE FIRST ANSWER","INSERT THE SECOND ANSWER","INSERT THE THIRD ANSWER","INSERT THE FOURTH ANSWER"]}

                        A total of 10 questions must be meticulously reorganized to follow this structure. Ensure all necessary components are present, correctly positioned, and strictly adhere to the format without altering the essence of the questions or answers. Below are the quiz responses that require formatting:

                        """ + f"{quiz_response_content}" + """

                        Note: The output MUST RIGOROUSLY conform to the described format. The structure is critical for the content's direct transformation into an educational matrix. Adjustments should reorganize the provided content to precisely fit this structure, maintaining the original question and answer essence.
                        """

    adjustment_response = openai.ChatCompletion.create(
        model="davinci-002",  # Update the model name based on current availability
        messages=[
            {"role": "system","content": "You are a JSON expert that will output ONLY the JSON structure" },
            {"role": "user", "content": adjustment_prompt}
        ],temperature=0.5,max_tokens=2048,top_p=1,frequency_penalty=0,presence_penalty=0)

    try:
        adjusted_quiz_response = adjustment_response['choices'][0]['message']['content']
    except:
        flag=-1
        print("Error: Adjusted quiz response not obtained. Redo")
        adjust_quiz_format_toJSON(quiz_response_content, flag)
   
    try:
        quiz_json = json.loads(adjusted_quiz_response)
    except json.JSONDecodeError:
        flag=1
        print("JSONDecodeError occurred while loading adjusted quiz response.")
        return None, flag

    flag=0
    print("Quiz format adjustment completed successfully.")
    return quiz_json,flag

#-------------------- CREATE TYPE FORM ----------------------------------------------------
def create_quiz_with_scoring(tf_api_key, answers_dic, subtopic, video_link,video_description, quiz_matrix, counter):
    
    workspace_name = f"{answers_dic.get('School')}-{answers_dic.get('Surname')}"
    workspace_name = workspace_name.lower().replace(' ', '_')
    workspace_id = find_or_create_workspace(workspace_name)
    
    typeform_api_url = "https://api.typeform.com/forms"
    headers = {
        "Authorization": f"Bearer {tf_api_key}",
        "Content-Type": "application/json"
    }

    # Initialize the form data structure
    form_data = {
        "title": f"{answers_dic.get('School')}_{answers_dic.get('Surname')}_{answers_dic.get('Grade')}_{counter}",
        "workspace": {
            "href": f"https://api.typeform.com/workspaces/{workspace_id}"
        },
        "type": "score",
        "welcome_screens": [{
            "title": f"Welcome to the Quiz on {subtopic}",
            "properties": {
                "description": "This quiz will test your knowledge.",
                "show_button": True,
                "button_text": "Start"
            }
        }],
        "fields": [],
        "logic": [],
        "thankyou_screens": [{
            "title": "Thanks for participating!",
            "properties": {
                "show_button": False,
                "description": "You got {{var:score}}/10"
            }
        }],
        "variables": {
            "score": 0
        }
    }

    # Add a video field if a video link is provided
    if video_link:
        form_data["fields"].append({
            "title": "Watch this video before starting the quiz",
            "properties": {
                "description": video_description,
                "button_text": "Continue",
                "hide_marks": False
            },
            "type": "statement",
            "attachment": {
                "type": "video",
                "href": video_link
            }
        })


    for i, (question, *options) in enumerate(quiz_matrix):
        question_ref = re.sub(r'[^a-zA-Z0-9_-]', '', question)[:254] or f"question_{i}"
        choices = []
        for j, option in enumerate(options):
            # Generate a unique reference for each choice
            option_ref = f"{question_ref}_option_{j}"
            choices.append({
                "label": option,
                "ref": option_ref  # Add a reference for each choice
            })
            
        question_field = {
            "title": question,
            "ref": question_ref,
            "type": "multiple_choice",
            "properties": {
                "description": "Your actual score is: {{var:score}}",
                "randomize": True,
                "allow_multiple_selection": False,
                "allow_other_choice": False,
                "vertical_alignment": True,
                "choices": choices
            }
        }
        form_data["fields"].append(question_field)

        # Assuming the first option is correct, save its ref for the correct_option_ref
        correct_option_ref = choices[0]["ref"]  # Use the ref of the first choice as the correct option ref

        logic_action = {
            "type": "field",
            "ref": question_ref,
            "actions": [{
                "action": "add",
                "details": {
                    "target": {
                        "type": "variable",
                        "value": "score"
                    },
                    "value": {
                        "type": "constant",
                        "value": 1
                    }
                },
                "condition": {
                    "op": "is",
                    "vars": [
                        {"type": "field", "value": question_ref},
                        {"type": "choice", "value": correct_option_ref}  # Use the generated choice ref
                    ]
                }
            }]
        }
        form_data["logic"].append(logic_action)

    response = requests.post(typeform_api_url, json=form_data, headers=headers)
    
    if response.status_code == 201:
        form_url = response.json().get("_links", {}).get("display", "")
        print("Form created successfully:", form_url)
        return form_url
    else:
        print(f"Failed to create the quiz. Error: {response.text}")
        return response

def find_or_create_workspace(workspace_name):
    """
    Find an existing workspace by name or create a new one if it doesn't exist.
    The workspace name should be given by answers_dic.get('School') + answers_dic.get('Surname') + answers_dic.get('Grade')
    """    
    
    headers = {
        "Authorization": f"Bearer {tf_api_key}",
        "Content-Type": "application/json"
    }
    url = "https://api.typeform.com/workspaces"
    
    # Fetch existing workspaces
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        workspaces = response.json().get('items', [])
        for workspace in workspaces:
            if workspace['name'] == workspace_name:
                return workspace['id']  # Return existing workspace ID

    # Create a new workspace if not found
    data = {
        "name": workspace_name
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        workspace = response.json()
        return workspace['id']  # Return new workspace ID
    else:
        print(f"Failed to create workspace. Error: {response.text}")
        return None

#-------------------- SEND EMAIL ----------------------------------------------------
def send_email_with_form_link(answers_dic, subtopics, form_urls):
    email=answers_dic.get('Email')

    with open("Omini blu in un quadrato.jpg", "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')
    # Sender's email and app-specific password
    sender_email = "info.masterminding@gmail.com"
    sender_password = "sgwj tnsf sdzx fsjm"

    # Email server configuration
    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    # Create the email message
    message = MIMEMultipart()
    message["From"] = f"Francesco from Masterminding <sender_email>"
    message["To"] = email
    message["Subject"] = f"Masterminding Educational Intelligence for {answers_dic.get("First_Name")} {answers_dic.get("Last_name")}"
    
    # Generating the list items for each subtopic and form_url with "Module n" prefix
    links_list = "".join([f'<li>Module {i+1}: <a href="{url}" target="_blank">{topic}</a></li>' for i, (topic, url) in enumerate(zip(subtopics, form_urls))])


    # Email body
    body = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Masterminding: Educational Intelligence</title>
    <style>
        body {
            font-family: Helvetica, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f4f4f4;
        }
        .container {
            max-width: 600px;
            margin: auto;
            background-color: #fff;
            padding: 20px;
        }
        .footer {
            width: 100%;
            background-color: #fff; /* Adjust this if you have a specific footer background color */
            margin-top: 30px;
        }
        .footer img {
            width: 100%;
            height: auto;
        }
        h2 {
            color: #000fff;
            text-align: center;
        }
        h3, h4 {
            color: #000000;
        }
        p {
            color: ##000000;
        }
        .bold {
            font-weight: bold;
        }
    </style>
    </head>
    <body>
    <div class="container">
        <div style="text-align: center;">
        <h3>Enhance Your Classroom Experience with</h3>
        <h2>Masterminding Educational Intelligence</h2>
        </div>
        """f"""
        <p style="white-space: pre-wrap;"> Dear Teacher {answers_dic.get('Last_name')},</p>
        <p>I hope this email finds you well. 
        <p>Leveraging the insights from your curriculum data submitted on our website, we've meticulously crafted interactive learning modules. These modules, enriched with captivating videos and quizzes, are tailored to deepen students' grasp of {answers_dic.get('Goal')}, resonating with your educational goals.</p>
        <h4>Highlights of Your Customized Toolkit</h4>
        <ul>
            <li><strong>10 Form Links:</strong> Each form link leads to a dedicated learning module designed around a key concept or learning objective within your curriculum. Here’s what each module offers:
                <ul>
                    <li><strong>Engaging Videos:</strong> Short, compelling videos that capture essential concepts and demonstrate real-world applications.</li>
                    <li><strong>Interactive Quizzes:</strong> A series of quizzes following each video to test comprehension and reinforce learning, providing immediate feedback.</li>
                </ul>
            </li>
        </ul>
        <br>
        <p><strong>Your Learning Goals, Our Priority:</strong></p>
        <p>Our aim is to support your educational objectives by providing resources that cater to diverse learning styles. Whether it's simplifying complex theories or offering practice exercises, these modules are designed to help your students achieve mastery in the subject matter.</p>
        <br>
        <p><strong>Getting Started:</strong></p>
        <p>To access these resources, simply click on the links below:</p>"""f"""
        <ul>
            {links_list}
        </ul>
        <br>
        <p><strong>Support and Questions:</strong></p>"""f"""
        <p>Should you have any questions or require further assistance, please do not hesitate to contact our support team at info.masterminding@gmail.com</p>
        <p>We are committed to your success and the academic achievements of your students. Thank you for your dedication to education and for considering Masterminding as a partner in your teaching journey.</p>
        <p>Warm regards,</p>
        <p class="bold">Francesco Rosciano<br>Masterminding Team<br>info.masterminding@gmail.com</p>
        <img src="data:image/jpeg;base64,{base64_image}" alt="Masterminding Logo" style="width: 100px; display: float: left;">
    </div>
    
    
    </body>
    </html>
    """
    message.attach(MIMEText(body, "html"))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Upgrade the connection to secure TLS
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, email, message.as_string())
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

#-------------------- START ----------------------------------------------------
def start(model):
    start_time = time.time()
    
    answers_dic, latest_response = TypeForm_Output_InitialForm(tf_api_key)
    learning_path, response = generate_subtopics(answers_dic, model)
    counter = 0
    list_of_form_urls = []
    df_values = []

    for subtopic in learning_path:
        counter += 1
        print(f"Counter: {counter}, Time Spent: {time.time() - start_time} seconds")
        info, video_link, video_title, video_description, video_transcript = find_best_matching_video(subtopic, answers_dic)
        structured_description = generate_description(video_transcript, answers_dic)
        quiz_json, quiz_matrix = generate_quiz_json(video_transcript, answers_dic, subtopic, model)
        if time.time() - start_time > 360:
            print("Kernel interrupted due to long processing time")
            break
        if quiz_matrix is None:
            start(model="gpt-3.5-turbo-0125")
            break
        form_url = create_quiz_with_scoring(tf_api_key, answers_dic, subtopic, video_link, structured_description, quiz_matrix, counter)
        list_of_form_urls.append(form_url)
        df_values.append([subtopic, info, video_link, video_title, video_description, video_transcript, structured_description, quiz_json, quiz_matrix, form_url])

    df_columns = ['Subtopic', 'Info', 'Video Link', 'Video Title', 'Video Description', 'Video Transcript', 'Structured Description', 'Quiz JSON', 'Quiz Matrix', 'Form URL']
    df = pd.DataFrame(df_values, columns=df_columns)

    send_email_with_form_link(answers_dic, learning_path, list_of_form_urls)
    return answers_dic, learning_path, df


answers_dic, learning_path, df=start(model1)
