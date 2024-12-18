import os
import httpx
import traceback
from dotenv import load_dotenv
import asyncio
from datetime import datetime, timedelta
from .config import client, index
import time
from utils.database import get_recent_chats, save_chat
import logging
import anthropic



logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def parse_timestamp(ts):
    if isinstance(ts, (int, float)):
        return ts
    elif isinstance(ts, str):
        try:
            dt = datetime.strptime(ts, "%d/%m/%Y %H:%M")
            return dt.timestamp()
        except ValueError:
            return None
    else:
        return None

def retrieve_and_generate_answer_3d(query):
    current_date = datetime(2024, 3, 15)
    cutoff_date = current_date - timedelta(days=180)
    

    cutoff_timestamp = cutoff_date.timestamp()

    xq = client.embeddings.create(input=[query], model="text-embedding-ada-002").data[0].embedding
    
    res_no_filter = index.query(vector=xq, top_k=10, include_metadata=True)

    filter_dict = {
        "timestamp": {"$gte": cutoff_timestamp}
    }
    
    res = index.query(vector=xq, top_k=7, include_metadata=True, filter=filter_dict)
    
    if len(res['matches']) == 0:
        res = res_no_filter

    contexts = []
    earliest_timestamp = float('inf')
    latest_timestamp = float('-inf')
    
    for match in res['matches']:
        if 'Analysis' in match['metadata']:
            contexts.append(match['metadata']['Analysis'])
        else:
            contexts.append("No Analysis Found")
        
        if 'timestamp' in match['metadata']:
            ts = parse_timestamp(match['metadata']['timestamp'])
            if ts:
                earliest_timestamp = min(earliest_timestamp, ts)
                latest_timestamp = max(latest_timestamp, ts)

    return contexts

#Anthropic Implementation

async def generate_orange_reel(request, context: str) -> str:
    """
    Generates marketing content using Claude AI for YouTube descriptions.
    
    Args:
        request: Request object containing agenda, mood, and additional input
        context: Context information about the company
    
    Returns:
        str: Generated content or error message
    """
    writing_style = """
    Objective:
    
    You are Ganga, a world class content writer, well-versed in Rory Sutherland's "Alchemy: The Dark Art and Curious Science of Creating Magic in Brands, Business, and Life." 

    Your task is to create compelling Youtube description content for a given data without using direct sales language. 

    Input structure: 
    1. Agenda: [Main goal of the marketing campaign] 
    2. Mood: [Desired emotional tone of the ads] 
    3. About: [About our company]
    4. Additional Details: [Any extra information about the product, target audience, or constraints] 

    Guidelines for content creation:
    1. Reframe the product or service to enhance perception
    2. Consider the context and its relevance to the target audience's lifestyle
    3. Highlight intangible benefits beyond obvious features
    4. Tap into deeper psychological motivations
    5. Use precise language to alter perception effectively

    Approach: 
    1. Create a narrative that resonates with Ultra High Net Worth Individuals, Businessmen, Celebrities, Sportsmen, and Entrepreneurs
    2. Engage curiosity through thought-provoking content
    3. Demonstrate the product's utility with valuable information
    4. Imply exclusivity or uniqueness subtly

    Output instructions: 
    1. Provide one concise YouTube description, no longer than 100 words
    2. Use professional, refined language that avoids direct sales pitches
    3. Make the product appealing without explicitly asking to buy
    4. Ensure the tone is informative, engaging, and aligned with the specified mood

    Remember, your target audience consists of high-net-worth individuals and busy professionals. Keep the content crisp, professional, and time-efficient. Avoid using emojis or casual language. Your description should be subtle in its persuasion and thought-provoking without being pushy.
    """

    print("Processing with Orange Reel using Claude")
    api_key = os.getenv("ANTHROPIC_API_KEY")

    try:
        timeout = httpx.Timeout(1500.0, connect=6000.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                'https://api.anthropic.com/v1/messages',
                json={
                    "model": "claude-3-sonnet-20240229",
                    "max_tokens": 1024,
                    "messages": [
                        {
                            "role": "user",
                            "content": f"{writing_style}\n\nClient: {request.client}\nAdditional Input: {request.additional_input}\n\nBelow is the user input \nAgenda: {request.agenda} \nMood: {request.mood} \nAbout Our Company: {context} \nAdditional Input: {request.additional_input} \nFollow writing instructions strictly. Use less and very professional emojis. Do not give ** in the output. Give 5 high volume and related hashtags"
                        }
                    ]
                },
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01"
                }
            )

        # Check if task was cancelled
        if asyncio.current_task().cancelled():
            return "Task cancelled"

        response_data = response.json()
        print("API Response:", response_data)

        if 'content' in response_data:
            result = response_data['content'][0]['text'].strip()
            
            # Calculate costs (Using Claude's pricing)
            char_count_output = len(result)
            char_count_input = len(writing_style) + len(request.agenda) + len(request.mood) + len(request.client) + (len(request.additional_input) if request.additional_input else 0)
            
            # Claude-3 Sonnet pricing (adjust as needed)
            input_cost = char_count_input * 0.008 / 1000  # $8 per 1M input tokens
            output_cost = char_count_output * 0.024 / 1000  # $24 per 1M output tokens
            total_cost = input_cost + output_cost
            cost_in_inr = total_cost * 86  # Convert to INR
            
            print(f"Orange Reel Input: {input_cost:.4f}, Orange Reel Output: {output_cost:.4f}, Orange Reel Total Cost: {total_cost:.4f}, Orange Reel Cost in INR: {cost_in_inr:.2f}")
            return result
        else:
            print("No Reel generated")
            return "Error: No content generated"

    except asyncio.CancelledError:
        return "Task cancelled"
    except Exception as e:
        print(f"Unexpected error in Orange Reel: {e}")
        traceback.print_exc()
        return "Error generating content"


#OpenAI Implementation
# async def generate_orange_reel(request, context):
#     agenda = request.agenda
#     mood = request.mood
#     additional_input = request.additional_input
    
#     writing_style = f"""
#     Objective:
    
#     You are Ganga, a world class content writer, well-versed in Rory Sutherland's "Alchemy: The Dark Art and Curious Science of Creating Magic in Brands, Business, and Life." 

#     Your task is to create compelling Youtube description content for a given data without using direct sales language. 

#     Input structure: 
#     1. Agenda: [Main goal of the marketing campaign] 
#     2. Mood: [Desired emotional tone of the ads] 
#     3. About: [About our company]
#     4. Additional Details: [Any extra information about the product, target audience, or constraints] 

#    Guidelines for content creation:
#     1. Reframe the product or service to enhance perception
#     2. Consider the context and its relevance to the target audience's lifestyle
#     3. Highlight intangible benefits beyond obvious features
#     4. Tap into deeper psychological motivations
#     5. Use precise language to alter perception effectively

#     Approach: 
#     1. Create a narrative that resonates with Ultra High Net Worth Individuals, Businessmen, Celebrities, Sportsmen, and Entrepreneurs
#     2. Engage curiosity through thought-provoking content
#     3. Demonstrate the product's utility with valuable information
#     4. Imply exclusivity or uniqueness subtly

#     Output instructions: 
#     1. Provide one concise YouTube description, no longer than 100 words
#     2. Use professional, refined language that avoids direct sales pitches
#     3. Make the product appealing without explicitly asking to buy
#     4. Ensure the tone is informative, engaging, and aligned with the specified mood

#     Remember, your target audience consists of high-net-worth individuals and busy professionals. Keep the content crisp, professional, and time-efficient. Avoid using emojis or casual language. Your description should be subtle in its persuasion and thought-provoking without being pushy.

#     """
    
#     print("Processing with Orange Reel")
#     api_key = os.getenv("OPENAI_API_KEY")

#     try:
#         timeout = httpx.Timeout(1500.0, connect=6000.0)
#         async with httpx.AsyncClient(timeout=timeout) as client:
#             response = await client.post(
#                 'https://api.openai.com/v1/chat/completions',
#                 json={
#                     "model": "gpt-4o-2024-05-13",
#                     "messages": [
#                         {"role": "system", "content": f"{writing_style}\n\nClient: {request.client}\nAdditional Input: {additional_input}"},
#                         {"role": "user", "content": f"Below is the user input \n Agenda: {agenda} \n Mood: {mood} \n About Our Company: {context} \n Additional Input: {additional_input} \n Follow writing instructions strictly. Use less and very professional emojis. Do not give ** in the output. Give 5 high volume and realated hashtags"}
#                     ]
#                 },
#                 headers={"Authorization": f"Bearer {api_key}"}
#             )
#         # Check if the task has been cancelled
#             if asyncio.current_task().cancelled():
#                 return "Task cancelled"
#         response_data = response.json()
#         print("API Response:", response_data)

#         if 'choices' in response_data and response_data['choices']:
#             result = response_data['choices'][0].get('message', {}).get('content', '').strip()
#             char_count_output = len(result)
#             char_count_input = len(writing_style) + len(agenda) + len(mood) + len(request.client) + (len(additional_input) if additional_input else 0)
#             input_cost = char_count_input * 0.01 / 4000
#             output_cost = char_count_output * 0.03 / 4000
#             total_cost = input_cost + output_cost
#             cost_in_inr = total_cost * 86
#             print(f"Orange Reel Input: {input_cost}, Orange Reel Output: {output_cost}, Orange Reel Total Cost: {total_cost}, Orange Reel Cost in INR: {cost_in_inr} ")
#             return result
#             # print("Generated Reel Content:", result)
#         else:
#             print("No Reel generated")
#     except asyncio.CancelledError:
#         return "Task cancelled"
#     except Exception as e:
#         print(f"Unexpected error in Orange Reel: {e}")
#         traceback.print_exc()
#         return "Error generating content"


async def generate_orange_post(request, context):
    agenda = request.agenda
    mood = request.mood
    additional_input = request.additional_input
    
    writing_style = f"""
    Objective:
    
    You are Rachita, a world-class news writer specializing in creating compelling social media content for high-net-worth individuals. Your expertise lies in applying principles from Rory Sutherland's "Alchemy: The Dark Art and Curious Science of Creating Magic in Brands, Business, and Life" to craft engaging, subtle, and persuasive messages.

    Your task is to create one concise, impactful social media post based on this information. Follow these guidelines:

    Input structure: 
    1. Agenda: [Main goal of the marketing campaign] 
    2. Mood: [Desired emotional tone of the ads] 
    3. About: [About our company]
    4. Additional Details: [Any extra information about the product, target audience, or constraints] 
    
    Apply These Principles
    1. Reframe the product or service to enhance perception
    2. Consider how it fits into the lives of ultra-high-net-worth individuals
    3. Emphasize intangible benefits beyond obvious features
    4. Tap into deeper psychological motivations
    5. Use precise language to alter perception subtly

    MUST FOLLOW When crafting the post:
    1. Create a narrative that resonates with the target audience (Ultra High Net Worth Individuals, Businessmen, Celebrities, Sportsmen, and Entrepreneurs)
    2. Use a thought-provoking question or statement to engage curiosity
    3. Provide valuable information demonstrating the product's utility
    4. Imply exclusivity or uniqueness subtly
    5. Keep the language natural, humble, and free of direct sales pitches
    6. Ensure the tone is informative, engaging, and aligned with the specified mood
    7. Limit the post to 2-3 sentences for maximum impact


    Do not use emojis or informal language. Maintain a professional tone throughout.

    Remember, your audience consists of busy, sophisticated individuals. Your post should be concise, intriguing, and respectful of their time and intelligence.

    """
    
    print("Processing with Orange Post")
    api_key = os.getenv("OPENAI_API_KEY")

    try:
        timeout = httpx.Timeout(1500.0, connect=6000.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                'https://api.openai.com/v1/chat/completions',
                json={
                    "model": "gpt-4o-2024-05-13",
                    "messages": [
                        {"role": "system", "content": f"{writing_style}\n\nClient: {request.client}\nAdditional Input: {additional_input}"},
                        {"role": "user", "content": f"Below is the user input \n Agenda: {agenda} \n Mood: {mood} \n About Our Company: {context} \n Additional Input: {additional_input} \n Follow writing instructions strictly. Use less and very professional emojis only. Do not give ** in the output. Give 5 high volume and realated hashtags"}
                    ]
                },
                headers={"Authorization": f"Bearer {api_key}"}
            )
        # Check if the task has been cancelled
            if asyncio.current_task().cancelled():
                return "Task cancelled"
        response_data = response.json()
        print("API Response:", response_data)

        if 'choices' in response_data and response_data['choices']:
            result = response_data['choices'][0].get('message', {}).get('content', '').strip()
            char_count_output = len(result)
            char_count_input = len(writing_style) + len(agenda) + len(mood) + len(request.client) + (len(additional_input) if additional_input else 0)
            input_cost = char_count_input * 0.01 / 4000
            output_cost = char_count_output * 0.03 / 4000
            total_cost = input_cost + output_cost
            cost_in_inr = total_cost * 86
            print(f"Orange Post Input: {input_cost}, Orange Post Output: {output_cost}, Orange Post Total Cost: {total_cost}, Orange Post Cost in INR: {cost_in_inr} ")
            return result
            # print("Generated Reel Content:", result)
        else:
            print("No Post generated")
    except asyncio.CancelledError:
        return "Task cancelled"
    except Exception as e:
        print(f"Unexpected error in Orange Post: {e}")
        traceback.print_exc()
        return "Error generating content"
    


async def generate_orange_poll(request, context):
    agenda = request.agenda
    mood = request.mood
    additional_input = request.additional_input
    
    writing_style = f"""
    Objective:
    You are Seema, a marketing strategist applying Rory Sutherland's "Alchemy" principles to real estate marketing. Create a brief, focused social media post for a given property listing.
    
    Input structure:
    Property details: [Key facts about the property]
    Target audience: [Who the post is aimed at]
    Unique selling point: [What makes this property special]

    
    Apply these "Alchemy" principles:
    Reframe the property to change perception
    Consider how it fits into people's lives
    Emphasize intangible benefits
    Tap into deeper motivations
    Use language to alter perception subtly

    Approach:
    Create a concise narrative that resonates with the target audience
    Use one interst generating question or statement
    Highlight the property's utility and unique aspects
    Imply exclusivity without being overt

    Output instructions:
    Provide 1 social media post of 4-6 lines
    Use plain, clear language without sales pitches
    Make the property interesting without explicitly asking to buy
    Include only essential details and make the user call +91 9959994737 to get in touch. Else, user can DM us for more queries on buyinf, selling or partnerships.

    Ensure the tone is:
    Informative and straightforward
    Subtly persuasive
    Aligned with the property's character

    Output Format:
    40 acres | ₹7 lakhs per acre | Near Yavatmal, Maharashtra | Link in bio 

    - Verified and facilitated by 1acre.in
    - Extremely fertile, canal-irrigated land
    - Only 6 hours from Hyderabad
    - Well-connected to national highways, expressways, and railways
    - Ideal for active agriculture and investment
    \n
    Interested? Get in touch now! 📞 +91 9959994737
    \n
    📬📩 DM us for more queries on buying, selling, or partnerships



    """
    
    print("Processing with Orange Poll")
    api_key = os.getenv("OPENAI_API_KEY")

    try:
        timeout = httpx.Timeout(1500.0, connect=6000.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                'https://api.openai.com/v1/chat/completions',
                json={
                    "model": "gpt-4o-2024-05-13",
                    "messages": [
                        {"role": "system", "content": f"{writing_style}\n\nClient: {request.client}\nAdditional Input: {additional_input}"},
                        {"role": "user", "content": f"Below is the user input \n Agenda: {agenda} \n Mood: {mood} \n About Our Company: {context} \n Additional Input: {additional_input} \n Follow writing instructions strictly. Use limited and professional emojis. Do not give ** in the output. Give 20 high volume and realated hashtags"}
                    ]
                },
                headers={"Authorization": f"Bearer {api_key}"}
            )
        # Check if the task has been cancelled
            if asyncio.current_task().cancelled():
                return "Task cancelled"
        response_data = response.json()
        print("API Response:", response_data)

        if 'choices' in response_data and response_data['choices']:
            result = response_data['choices'][0].get('message', {}).get('content', '').strip()
            char_count_output = len(result)
            char_count_input = len(writing_style) + len(agenda) + len(mood) + len(request.client) + (len(additional_input) if additional_input else 0)
            input_cost = char_count_input * 0.01 / 4000
            output_cost = char_count_output * 0.03 / 4000
            total_cost = input_cost + output_cost
            cost_in_inr = total_cost * 86
            print(f"Orange Poll Input: {input_cost}, Orange Poll Output: {output_cost}, Orange Poll Total Cost: {total_cost}, Orange Poll Cost in INR: {cost_in_inr} ")
            return result
            # print("Generated Reel Content:", result)
        else:
            print("No Poll generated")
    except asyncio.CancelledError:
        return "Task cancelled"
    except Exception as e:
        print(f"Unexpected error in Orange Poll: {e}")
        traceback.print_exc()
        return "Error generating content"
    

async def generate_orange_strategy(request, context):
    agenda = request.agenda
    mood = request.mood
    additional_input = request.additional_input
    
    writing_style = f"""
    Objective:
    
    You are Seema, a marketing strategist well-versed in Rory Sutherland's "Alchemy: The Dark Art and Curious Science of Creating Magic in Brands, Business, and Life." 

    Your task is to create compelling strategy for a given data without using direct sales language. 

    Input structure: 
    1. Agenda: [Main goal of the marketing campaign] 
    2. Mood: [Desired emotional tone of the ads] 
    3. About: [About our company]
    4. Additional Details: [Any extra information about the product, target audience, or constraints] 

    Apply the following principles from "Alchemy": 
    1. Reframe the product or service to change perception 
    2. Consider the context and how it fits into people's lives 
    3. Emphasize intangible benefits beyond obvious features 
    4. Understand and tap into deeper psychological motivations 
    5. Use small changes in language to significantly alter perception 

    Approach: 
    1. Create a narrative around the product that resonates with the target audience of Ultra High Net Worth Individuals, Businessmen, Celebrities, Sportsmen and Entrepreneurs
    2. Use questions to engage curiosity and encourage self-reflection 
    3. Provide valuable information that demonstrates the product's utility 
    4. Share relatable scenarios or stories 
    5. Imply exclusivity or uniqueness subtly 

    Output instructions: 
    1. Provide 1 distinct social post, focusing on the best approach 
    2. Use natural, humble language that avoids direct sales pitches 
    3. Incorporate emojis sparingly if appropriate for the brand 
    4. Make the product appealing without explicitly asking to buy 

    Ensure the tone is: - Informative without being pushy - Engaging and thought-provoking - Aligned with the specified mood - Subtle in its persuasion 

    """
    
    print("Processing with Orange Strategy")
    api_key = os.getenv("OPENAI_API_KEY")

    try:
        timeout = httpx.Timeout(1500.0, connect=6000.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                'https://api.openai.com/v1/chat/completions',
                json={
                    "model": "gpt-4o-2024-05-13",
                    "messages": [
                        {"role": "system", "content": f"{writing_style}\n\nClient: {request.client}\nAdditional Input: {additional_input}"},
                        {"role": "user", "content": f"Below is the user input \n Agenda: {agenda} \n Mood: {mood} \n About Our Company: {context} \n Additional Input: {additional_input} \n Follow writing instructions strictly. Use limited and professional emojis. Do not give ** in the output. Give 20 high volume and realated hashtags"}
                    ]
                },
                headers={"Authorization": f"Bearer {api_key}"}
            )
        # Check if the task has been cancelled
            if asyncio.current_task().cancelled():
                return "Task cancelled"
        response_data = response.json()
        print("API Response:", response_data)

        if 'choices' in response_data and response_data['choices']:
            result = response_data['choices'][0].get('message', {}).get('content', '').strip()
            char_count_output = len(result)
            char_count_input = len(writing_style) + len(agenda) + len(mood) + len(request.client) + (len(additional_input) if additional_input else 0)
            input_cost = char_count_input * 0.01 / 4000
            output_cost = char_count_output * 0.03 / 4000
            total_cost = input_cost + output_cost
            cost_in_inr = total_cost * 86
            print(f"Orange Strategy Input: {input_cost}, Orange Strategy Output: {output_cost}, Orange Strategy Total Cost: {total_cost}, Orange Strategy Cost in INR: {cost_in_inr} ")
            return result
            # print("Generated Reel Content:", result)
        else:
            print("No Strategy generated")
    except asyncio.CancelledError:
        return "Task cancelled"
    except Exception as e:
        print(f"Unexpected error in Orange Strategy: {e}")
        traceback.print_exc()
        return "Error generating content"
    


async def generate_orange_email(request, context, industry):
    receiver = request.receiver
    client_company = request.client_company
    additional_input = request.additional_input
    
    writing_style = f"""
        # CEO-to-CEO Outreach Message Generator

        ## Context
        You are Rohith Sampathi, founder of Montaigne Smart Business Solutions, a company specializing in strategic growth and market expansion across various industries, with particular expertise in real estate. Your task is to craft a brief, personalized outreach message to the CEO of a target company.

        ## Input
        You will receive the following information:
        1. Target CEO's name and company
        2. Brief description of the target company's recent achievements or challenges
        3. Relevant industry trends or market developments
        4. Any specific Montaigne achievements or insights related to the target company's industry

        ## Output Guidelines
        Generate a concise, personalized message with the following characteristics:

        1. Length: 100-150 words maximum
        2. Tone: Casual yet professional, CEO-to-CEO conversation
        3. Structure:
        - Brief acknowledgment of the CEO's recent achievement or challenge
        - Introduce yourself and Montaigne with a relevant accomplishment
        - Share 2-3 concise, thought-provoking insights or questions related to their industry
        - End with a low-pressure invitation to connect

        4. Style:
        - Use short, punchy sentences
        - Avoid jargon or overly formal language
        - Include a mix of statements and questions to engage the reader
        - Maintain a humble yet confident tone

        5. Content:
        - Focus on providing value through insights or questions
        - Subtly demonstrate your expertise without being boastful
        - Tailor the content to the specific industry and company situation
        - Avoid explicit sales pitches or lengthy service descriptions

        6. Closing:
        - Include a brief, friendly sign-off
        - Provide your name, company name, and email only

        ## Example
        Use the following as a general template, adapting the content to fit the specific input:

    """
    
    print("Processing with Orange Email")
    api_key = os.getenv("OPENAI_API_KEY")

    try:
        timeout = httpx.Timeout(1500.0, connect=6000.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                'https://api.openai.com/v1/chat/completions',
                json={
                    "model": "gpt-4o-2024-05-13",
                    "messages": [
                        {"role": "system", "content": f"{writing_style}\n\nClient: {request.client}\nAdditional Input: {additional_input}"},
                        {"role": "user", "content": f"Below is the user input \n Receipient: {receiver} \n Receiver Company: {client_company} \n About Our Company: {context} \n Latest Industry Development: {industry} \n Follow writing instructions strictly. Do not give ** in the output. "}
                    ]
                },
                headers={"Authorization": f"Bearer {api_key}"}
            )
        # Check if the task has been cancelled
            if asyncio.current_task().cancelled():
                return "Task cancelled"
        response_data = response.json()
        print("API Response:", response_data)

        if 'choices' in response_data and response_data['choices']:
            result = response_data['choices'][0].get('message', {}).get('content', '').strip()
            char_count_output = len(result)
            char_count_input = len(writing_style) + len(receiver) + len(client_company) + len(request.client) + + len(industry) + len(context) + (len(additional_input) if additional_input else 0)
            input_cost = char_count_input * 0.01 / 4000
            output_cost = char_count_output * 0.03 / 4000
            total_cost = input_cost + output_cost
            cost_in_inr = total_cost * 86
            print(f"Orange Email Input: {input_cost}, Orange Email Output: {output_cost}, Orange Email Total Cost: {total_cost}, Orange Email Cost in INR: {cost_in_inr} ")
            return result
            # print("Generated Reel Content:", result)
        else:
            print("No Email generated")
    except asyncio.CancelledError:
        return "Task cancelled"
    except Exception as e:
        print(f"Unexpected error in Orange Email: {e}")
        traceback.print_exc()
        return "Error generating content"
    

async def generate_orange_chat(industry, purpose, client, user_input, context):
    api_key = os.getenv("OPENAI_API_KEY")

    try:
        # Attempt to fetch recent chats, but continue if it fails
        try:
            recent_chats = get_recent_chats(industry, client, purpose)
            fetched_talks = "\n".join([f"User: {msg['role'] == 'user'}\nOrange: {msg['role'] == 'assistant'}" for chat in recent_chats for msg in chat['messages']])
        except Exception as e:
            logger.error(f"Failed to fetch recent chats: {e}")
            fetched_talks = ""  # Continue with empty chat history if fetching fails
    
        writing_style = f"""
        As Orange Sampathi, the Chief Strategy Officer at {client}. You're engaging in a deep brain storm conversation with your most promosing associate about the {industry} industry. You're leveraging the latest market developments below {context}, and doing the discussion to solve the below purpose {purpose}

        Begin the discussion by greeting the client warmly, setting a relaxed tone. Use the following approach to guide the conversation:

        1. **Engage with Contextual Insights:**
        - "It's great to see you! I've been following the recent moves by [major player], and their latest innovation is fascinating. It seems like it could shift the market dynamics quite a bit. What do you think?"
        - "We've seen some interesting shifts in customer behavior lately. For example, there's a growing trend towards [trend/feature]. It seems like customers are really embracing this change. Have you noticed this as well?"

        2. **Discuss Strategic Focus:**
        - "Given these market changes, I've been thinking about how we can position ourselves to stay ahead. Focusing on [strategic focus] might be crucial. This could really set us apart and address the evolving needs of our customers. How does that align with your vision?"
        - "One thing that stands out is the power of creating a compelling narrative around our strategy. Stories resonate more deeply than mere data points. How do you think we can weave our strategy into a story that engages our stakeholders?"

        3. **Explore Unconventional Approaches:**
        - "Sometimes, the most effective strategies come from thinking outside the conventional framework. Instead of just following the data, we might consider the psychological aspects that drive customer decisions. What unique insights have you gathered from your interactions with customers?"
        - "Innovation often stems from challenging the status quo. By looking at things differently, we can uncover opportunities that others might miss. How can we apply this kind of thinking to our current strategy?"

        4. **Summarize and Invite Further Discussion:**
        - "So, it seems like innovation, understanding customer behavior, and strategic storytelling are key areas for us. Does this resonate with your perspective?"
        - "I'd love to hear any additional thoughts or questions you might have. What else should we consider as we move forward?"

        Use this structure to keep the conversation natural and engaging, ensuring the client feels involved and informed throughout the discussion. Your language should be story-driven, reflecting key strategic insights to provide a unique and compelling perspective.

        """

        timeout = httpx.Timeout(120.0, connect=180.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                'https://api.openai.com/v1/chat/completions',
                json={
                    "model": "gpt-4o-2024-05-13",
                    "messages": [
                        {"role": "system", "content": f"Writing Style: {writing_style} \n\n End of Instructions --------- Our Conversation so far: {fetched_talks}. Do not give irrelevant answers even if the contextual has irrelevant information. Use Sentence case for output. Start new paragraphs with ** and \n\n. Answer only to user question."},
                        {"role": "user", "content": user_input}
                    ]
                },
                headers={"Authorization": f"Bearer {api_key}"}
            )
            response.raise_for_status()
            response_data = response.json()
            
            if 'choices' in response_data and response_data['choices']:
                result = response_data['choices'][0].get('message', {}).get('content', '').strip()
                logger.info("Processed Orange Chat")
                
                # Attempt to save the chat, but continue if it fails
                try:
                    new_messages = [
                        {'role': 'user', 'content': user_input},
                        {'role': 'assistant', 'content': result}
                    ]
                    save_chat(industry, client, purpose, new_messages)
                except Exception as e:
                    logger.error(f"Failed to save chat: {e}")
                
                return result
            else:
                return "No Orange analysis generated"
    except Exception as e:
        logger.error(f"Unexpected error in Orange Chat: {e}")
        traceback.print_exc()
        return f"Unexpected Error: {str(e)}"
    

async def generate_orange_script(request, context, client):
    purpose = request.purpose
    
    writing_style = f"""
    User Inputs:

    About our Company: {client}
    Industry Developments: {context}
    Target Audience: Entrepreneurs, Business Decision Makers and Startup founders in Global Business hubs like Silicon Valley
    Purpose: {purpose}

    Using the above inputs, You are tasked with creating a concise, thought-provoking 30 second video script for a high-net-worth and ultra-high-net-worth audience, including entrepreneurs, business decision-makers, and startup founders in global business hubs like Silicon Valley. The script should be engaging, memorable, and aligned with Montaigne's principles of critical thinking and personal observation.
    
    Using this information, create a script that follows this structure:
    1. Open with a thought-provoking industry-related question or scenario
    2. Present a common industry challenge from an unexpected angle
    3. Introduce the company's approach as a fresh perspective, without directly promoting it
    4. Provide a concrete, counterintuitive example that challenges conventional thinking
    5. Close with an inspiring message that encourages rethinking industry norms

    Adhere to these content and tone guidelines:
    - Use clear, accessible language with a conversational yet professional tone
    - Avoid direct promotion or mention of company services
    - Balance analytical observations with surprising or emotionally resonant elements
    - Maintain an air of intellectual curiosity and discovery throughout

    Your output should radiate the learning from below:

    1. Insights from Montaigne's essays, emphasizing:
    - Critical thinking and questioning assumptions
    - The importance of personal experience and observation
    - How cultural and societal norms shape our perceptions
    - The role of skepticism in decision-making
    - Balancing tradition and innovation in business

    2. Inspiration from key works in business and complexity theory, including:
    - "The Innovators" by Walter Isaacson
    - "Chaos: The Amazing Science of the Unpredictable" by James Gleick
    - "The Black Swan" by Nassim Nicholas Taleb
    - "Zero to One" by Peter Thiel
    - "The Lean Startup" by Eric Ries
    - "Business Model Generation" by Alexander Osterwalder
    - "Cybernetics in Management" by F.H. George

    Post Overall IMPACT:
    - Prompts the audience to question their current perspective
    - Presents a fresh viewpoint that adds unique value to industry thinking
    - Aligns with Montaigne's principles of critical thinking and personal observation

    Output your script within 30 seconds when read aloud at a natural pace.
    
    
    """
    
    print("Processing with Anthropic Script Generator")
    api_key = os.getenv("ANTHROPIC_API_KEY")

    try:
        anthropic = Anthropic(api_key=api_key)
        
        prompt = f"{writing_style}\n\nClient: {client}\n\nBelow is the user input:\nPurpose: {purpose}\nAbout Our Company: {context}\n\nFollow writing instructions strictly. Craft the script as if it's a thought leadership piece, inspired by Montaigne's approach to critical thinking. The final product should be clear, compelling, and offer a fresh perspective on the industry, very subtly positioning around the purpose. Do not mention specific books or authors in the output. Strictly restrict the output to 30 seconds of content. Deliver the narration in a thoughtful, engaging business tone that provokes reflection."

        completion = anthropic.completions.create(
            model="claude-3-opus-20240229",
            max_tokens_to_sample=1000,
            prompt=prompt
        )

        result = completion.completion.strip()
        
        char_count_output = len(result)
        char_count_input = len(prompt)
        input_cost = char_count_input * 0.015 / 1000  # Anthropic's pricing may differ, adjust as needed
        output_cost = char_count_output * 0.015 / 1000
        total_cost = input_cost + output_cost
        cost_in_inr = total_cost * 86
        print(f"Anthropic Script Input: {input_cost}, Anthropic Script Output: {output_cost}, Anthropic Script Total Cost: {total_cost}, Anthropic Script Cost in INR: {cost_in_inr}")
        
        return result
    except asyncio.CancelledError:
        return "Task cancelled"
    except Exception as e:
        print(f"Unexpected error in Anthropic Script Generator: {e}")
        traceback.print_exc()
        return f"Error generating content: {str(e)}"
    


async def generate_orange_script_ai(request, context, client):
    purpose = request.purpose
    
    writing_style = f"""
    You are tasked with creating a concise, thought-provoking video script for a high-net-worth individual (HNWI) and ultra-high-net-worth individual (UHNWI) audience. The script should be engaging, intellectually stimulating, and tailored for busy business leaders and entrepreneurs. Your goal is to challenge conventional thinking and present fresh perspectives without directly promoting the company.

    Here are the key inputs for your script:

    <client>
    {client}
    </client>

    <context>
    {context}
    </context>

    <purpose>
    {purpose}
    </purpose>

    Create a script following this structure:
    1. Open with a thought-provoking industry-related question or scenario (1 sentence)
    2. Present a common industry challenge from an unexpected angle (1-2 sentences)
    3. Introduce a fresh perspective, subtly inspired by the company's approach (1-2 sentences)
    4. Provide a concrete, counterintuitive example that challenges conventional thinking (1-2 sentences)
    5. Close with a brief, inspiring message that encourages rethinking industry norms (1 sentence)

    Content and tone requirements:
    - Use clear, concise language with a sophisticated yet accessible tone
    - Avoid direct promotion or mention of company services
    - Balance analytical insights with surprising or emotionally resonant elements
    - Maintain an air of exclusivity and insider knowledge

    Your script should be approximately 60-80 words long, suitable for a 20-30 second video.

    After creating the script, generate 3-5 background stock video ideas that complement and enhance the narration. These ideas should be visually striking, relevant to the script's content, and help illustrate the concepts discussed. Focus on unique and thought-provoking imagery that aligns with the script's innovative approach and appeals to a HNWI/UHNWI audience.

    Present your final output in the following format:

    <output>
    [Video Script]

    Background Video Ideas:
    1. [First video idea]
    2. [Second video idea]
    3. [Third video idea]
    [Add more if necessary]
    </output>

    Remember to create a script that is sophisticated, minimal, and impactful, while incorporating subtle elements that create a sense of exclusivity and insider knowledge for the target audience. The background video ideas should complement this approach and enhance the overall impact of the video.
        
    """
    print("Processing with Anthropic Script Generator")
    api_key = os.getenv("ANTHROPIC_API_KEY")

    try:
        anthropic_client = anthropic.Anthropic(api_key=api_key)
        
        message = anthropic_client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            temperature=0.5,
            system=writing_style,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Client: {client}\n\nBelow is the user input:\nPurpose: {purpose}\nAbout Our Company: {context}\n\nFollow writing instructions strictly. Craft the script as if it's a thought leadership piece, inspired by Montaigne's approach to critical thinking. The final product should be clear, compelling, and offer a fresh perspective on the industry, very subtly positioning around the purpose. Do not mention specific books or authors in the output. Strictly restrict the output to 30 seconds of content. Deliver the narration in a thoughtful, engaging business tone that provokes reflection."
                        }
                    ]
                }
            ]
        )

        result = message.content

        char_count_output = len(result)
        char_count_input = len(writing_style) + len(client) + len(purpose) + len(context)
        input_cost = char_count_input * 0.015 / 1000  # Anthropic's pricing may differ, adjust as needed
        output_cost = char_count_output * 0.015 / 1000
        total_cost = input_cost + output_cost
        cost_in_inr = total_cost * 86
        print(f"Anthropic Script Input: {input_cost}, Anthropic Script Output: {output_cost}, Anthropic Script Total Cost: {total_cost}, Anthropic Script Cost in INR: {cost_in_inr}")
        
        return result
    except Exception as e:
        print(f"Unexpected error in Anthropic Script Generator: {e}")
        traceback.print_exc()
        return f"Error generating content: {str(e)}"