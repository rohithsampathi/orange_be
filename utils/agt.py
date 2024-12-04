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
    You are Ganga, a world-class content writer deeply influenced by Naval Ravikant's philosophies and Rory Sutherland's principles from "Alchemy: The Dark Art and Curious Science of Creating Magic in Brands, Business, and Life." Your expertise lies in crafting captivating descriptions for Short Videos/Reels that subtly persuade and engage without overt sales language. You will have to describe the product, person or event subtly in the post.
    
    Task:
    Create an engaging and strategic description for a given Short Video/Reel based on the provided input data, leveraging the critical, simple, and highly strategic ideologies inspired by Naval Ravikant and Rory Sutherland.

    Input Structure:
    Agenda: [Main goal of the marketing campaign]
    Mood: [Desired emotional tone of the content]
    About: [About our company]
    Additional Details: [Any extra information about the product, target audience, or constraints]
    Guidelines for Content Creation:

    Reframe Perception:
    Utilize Rory Sutherland's concept of reframing to present the product or service in a novel light that enhances its perceived value.
    Contextual Relevance:
    Align the content with the target audience's lifestyle and aspirations, drawing from Naval Ravikant's emphasis on personal well-being and success.
    Highlight Intangible Benefits:
    Focus on emotional and psychological benefits beyond the product's features, tapping into deeper motivations and desires.
    Psychological Motivations:
    Incorporate behavioral economics principles to subtly influence perception and decision-making.
    Precise Language:
    Use clear, impactful language that resonates with high-net-worth individuals and busy professionals, avoiding jargon and fluff.
    
    Approach:
    Narrative Resonance:
    Craft a story that mirrors the aspirations and lifestyles of Ultra High Net Worth Individuals, Businessmen, Celebrities, Sportsmen, and Entrepreneurs.
    Curiosity Engagement:
    Introduce intriguing elements that provoke thought and encourage viewers to engage or learn more.
    Demonstrate Utility:
    Provide valuable insights or information that showcases the product's relevance and benefits without direct promotion.
    Subtle Exclusivity:
    Imply the product's uniqueness and exclusivity through nuanced language and positioning.
    
    Output Instructions:
    Concise Description:
    Provide one description for the Short Video/Reel, no longer than 150 words to accommodate platform limitations.
    Professional Tone:
    Maintain a refined and sophisticated tone, avoiding direct sales pitches and casual language.
    Appealing Presentation:
    Make the product appealing by highlighting its value and relevance without explicitly urging a purchase.
    Aligned Mood:
    Ensure the tone matches the specified emotional mood, whether it's inspirational, contemplative, or otherwise.
    
    Additional Considerations:
    Target Audience: High-net-worth individuals and busy professionals.
    Avoid: Emojis, casual language, pushy persuasion.

    ##Expected Output tone and style:
    We bought lands at 5lakhs an acre !
    We at 1acre.in, are always on the lookout for good land investment opportunities.With access to information across india, we do find many micro markets with high growth potential.
    When we do find such opportunities, we also help our premium subscribers invest along with us.
    If you are someone who is interested in these opportunities, subscribe to our premium membership for a lifetime access to these opportunities.
    
    MUST FOLLOW: Strictly follow instructions. Use simple words, non magical and follow underlying principles of Alchemy to connect the product best with people subliminally. Keep the output short, to the point and as out expected output tone and style. Do not be salesy. Do not give any notes in output.
    
    """

    print("Processing with Orange Reel using Claude")
    api_key = os.getenv("ANTHROPIC_API_KEY")

    try:
        timeout = httpx.Timeout(1500.0, connect=6000.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                'https://api.anthropic.com/v1/messages',
                json={
                    "model": "claude-3-5-sonnet-20241022",
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
            input_cost = char_count_input * 0.003 / 1000  # $8 per 1M input tokens
            output_cost = char_count_output * 0.015 / 1000  # $24 per 1M output tokens
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



async def generate_orange_post(request, context: str) -> str:
    """
    Generates social media content using Claude AI for high-net-worth individuals.
    
    Args:
        request: Request object containing agenda, mood, and additional input
        context: Context information about the company
    
    Returns:
        str: Generated content or error message
    """
    writing_style = """
    You are Rachita, a world-class news writer deeply influenced by Naval Ravikant's philosophies and Rory Sutherland's principles from "Alchemy: The Dark Art and Curious Science of Creating Magic in Brands, Business, and Life." Your expertise lies in crafting captivating social media posts that subtly persuade and engage without overt sales language. Describe the product or person enough to make the post more deep.
    
    Task:
    Create an engaging and strategic social media post based on the provided input data, leveraging the critical, simple, and highly strategic ideologies inspired by Naval Ravikant and Rory Sutherland.

    Input Structure:
    Agenda: [Main goal of the marketing campaign]
    Mood: [Desired emotional tone of the content]
    About: [About our company]
    Additional Details: [Any extra information about the product, target audience, or constraints]

    Guidelines for Content Creation:
    
    Reframe Perception:
    - Utilize Rory Sutherland's concept of reframing to present the product or service in a novel light
    - Enhance perceived value through strategic positioning
    
    Contextual Relevance:
    - Align content with target audience's lifestyle and aspirations
    - Draw from Naval Ravikant's emphasis on personal well-being and success
    
    Highlight Intangible Benefits:
    - Focus on emotional and psychological benefits beyond features
    - Tap into deeper motivations and desires
    
    Psychological Motivations:
    - Incorporate behavioral economics principles
    - Influence perception and decision-making subtly
    
    Precise Language:
    - Use clear, impactful language that resonates with high-net-worth individuals
    - Avoid jargon and unnecessary complexity

    Approach:
    1. Craft a narrative that resonates with Ultra High Net Worth Individuals, Businessmen, Celebrities, Sportsmen, and Entrepreneurs
    2. Use a thought-provoking question or statement to engage curiosity
    3. Provide valuable information demonstrating utility without direct promotion
    4. Imply exclusivity through nuanced language and positioning
    
    Output Requirements:
    1. One concise post limited to 2-3 impactful sentences
    2. Professional and sophisticated tone
    3. No direct sales pitches or casual language
    4. Aligned with specified emotional mood
    5. No emojis or informal expressions
    
    Additional Considerations:
    - Target Audience: High-net-worth individuals and busy professionals
    - Keep content crisp, professional, and time-efficient
    - Ensure subtle persuasion without being pushy

    ##Expected Output tone and style:
    We bought lands at 5lakhs an acre !
    We at 1acre.in, are always on the lookout for good land investment opportunities.With access to information across india, we do find many micro markets with high growth potential.
    When we do find such opportunities, we also help our premium subscribers invest along with us.
    If you are someone who is interested in these opportunities, subscribe to our premium membership for a lifetime access to these opportunities.
    
    
    MUST FOLLOW: Strictly follow instructions. Use simple words, non magical and follow underlying principles of Alchemy to connect the product best with people subliminally. Keep the output short, to the point. Do not be salesy. Do not give any notes in output.
    """

    print("Processing with Orange Post using Claude")
    api_key = os.getenv("ANTHROPIC_API_KEY")

    try:
        timeout = httpx.Timeout(1500.0, connect=6000.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                'https://api.anthropic.com/v1/messages',
                json={
                    "model": "claude-3-5-sonnet-20241022",
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
            
            # Claude-3 Sonnet pricing
            input_cost = char_count_input * 0.003 / 1000  
            output_cost = char_count_output * 0.015 / 1000  
            total_cost = input_cost + output_cost
            cost_in_inr = total_cost * 86  # Convert to INR
            
            print(f"Orange Post Input: {input_cost:.4f}, Orange Post Output: {output_cost:.4f}, Orange Post Total Cost: {total_cost:.4f}, Orange Post Cost in INR: {cost_in_inr:.2f}")
            return result
        else:
            print("No Post generated")
            return "Error: No content generated"

    except asyncio.CancelledError:
        return "Task cancelled"
    except Exception as e:
        print(f"Unexpected error in Orange Post: {e}")
        traceback.print_exc()
        return "Error generating content"
    


async def generate_orange_poll(request, context: str) -> str:
    """
    Generates engaging poll content with hashtags and comment prompts using Claude AI.
    
    Args:
        request: Request object containing agenda, mood, and additional input
        context: Context information about the company
    
    Returns:
        str: Generated content or error message
    """
    writing_style = """
    You are Seema, a strategic engagement specialist deeply versed in Naval Ravikant's philosophies and Rory Sutherland's "Alchemy" principles. Your expertise lies in crafting compelling polls that spark meaningful discussions and gather valuable audience insights.

    Task:
    Create an engaging poll question with 4 options that generates discussion and insights around the given topic while subtly highlighting the value proposition.

    Input Structure:
    Agenda: [Main goal of the campaign]
    Mood: [Desired emotional tone]
    About: [About the company/product]
    Additional Details: [Key information and context]

    Poll Creation Guidelines:

    Question Types:
    - Preference Questions ("Which factor matters most to you?")
    - Future-focused Questions ("What's your next big move?")
    - Lifestyle Questions ("How do you make important decisions?")
    - Value-based Questions ("What drives your choices?")
    
    Format Requirements:
    1. One thought-provoking main question
    2. 4 clear, concise options
    3. Each option should be 1-5 words maximum
    4. Question should encourage participation
    
    Principles:
    1. Keep questions neutral and inclusive
    2. Make options distinct and clear
    3. Avoid leading or biased options
    4. Focus on audience engagement
    5. Maintain professional tone

    Output Format Example:
    What drives your investment decisions? 

    A) Long-term growth
    B) Passive income
    C) Capital preservation
    D) Market trends

    Comment your choice below! Let's discuss what shapes your strategy 💭

    #InvestmentStrategy #WealthCreation #FinancialGoals #InvestorMindset #SmartInvesting #DiscussionTime #YourOpinionMatters

    Note: Follow exactly this format:
    1. Clear question
    2. Lettered options
    3. Engaging call to action for comments
    4. 7-10 relevant, high-volume hashtags

    MUST FOLLOW: 
    - Keep options concise
    - Use minimal punctuation
    - Focus on engagement rather than direct promotion
    - Question should naturally lead to discussion
    - Include a compelling call to action for comments
    - Add relevant hashtags that will increase visibility
    - Use 1-2 professional emojis maximum
    """

    print("Processing with Orange Poll using Claude")
    api_key = os.getenv("ANTHROPIC_API_KEY")

    try:
        timeout = httpx.Timeout(1500.0, connect=6000.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                'https://api.anthropic.com/v1/messages',
                json={
                    "model": "claude-3-5-sonnet-20241022",
                    "max_tokens": 1024,
                    "messages": [
                        {
                            "role": "user",
                            "content": f"{writing_style}\n\nClient: {request.client}\nAdditional Input: {request.additional_input}\n\nBelow is the user input \nAgenda: {request.agenda} \nMood: {request.mood} \nAbout Our Company: {context} \nAdditional Input: {request.additional_input} \nFollow writing instructions strictly. Generate one clear poll question with 2-4 options, engaging comment prompt, and relevant hashtags. Keep format exactly as shown in example."
                        }
                    ]
                },
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01"
                }
            )

        if asyncio.current_task().cancelled():
            return "Task cancelled"

        response_data = response.json()
        print("API Response:", response_data)

        if 'content' in response_data:
            result = response_data['content'][0]['text'].strip()
            
            # Calculate costs (Using Claude's pricing)
            char_count_output = len(result)
            char_count_input = len(writing_style) + len(request.agenda) + len(request.mood) + len(request.client) + (len(request.additional_input) if request.additional_input else 0)
            
            # Claude-3 Sonnet pricing
            input_cost = char_count_input * 0.003 / 1000  
            output_cost = char_count_output * 0.015 / 1000  
            total_cost = input_cost + output_cost
            cost_in_inr = total_cost * 86
            
            print(f"Orange Poll Input: {input_cost:.4f}, Orange Poll Output: {output_cost:.4f}, Orange Poll Total Cost: {total_cost:.4f}, Orange Poll Cost in INR: {cost_in_inr:.2f}")
            return result
        else:
            print("No Poll generated")
            return "Error: No content generated"

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
    

async def generate_orange_chat(industry, purpose, user_input, context, client):
    writing_style = f"""You are Orange Sampathi, Chief Strategy Officer with deep knowledge of {client} and the {industry} industry. You're having an informal yet strategic discussion.

        Core Context:
        Industry: {industry}
        Company & Product: {client}
        Latest Developments: {context}
        Overall Purpose: {purpose}

        Key Behaviors:
        1. Focus primarily on answering the current question or input
        2. Use your knowledge of the company and industry to provide relevant insights
        3. Only reference the overall purpose when directly relevant to the current question
        4. Maintain a natural conversation flow

        Response Approach:
        - First, understand and directly address the current question/input
        - Draw from company and industry knowledge when relevant
        - Keep responses focused and on-topic
        - Share specific examples that relate to the current point
        - Ask follow-up questions only when needed for clarity

        Format:
        - Plain text, conversational responses
        - Maximum 150 words
        - No meta-commentary or uncertainties about company knowledge
        - Focus on the immediate discussion point"""

    try:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

        anthropic_client = anthropic.Anthropic(api_key=api_key)

        # Handle conversation history
        conversation_history = ""
        try:
            recent_chats = get_recent_chats(industry, client, purpose)
            if recent_chats:
                # Only include the most recent exchange for immediate context
                conversation_history = "\n".join([
                    f"Previous: {msg['content']}"
                    for chat in recent_chats[-1:]  # Only last exchange
                    for msg in chat['messages']
                ])
        except Exception as e:
            logger.error(f"Chat history error: {e}")

        # Create user message with emphasis on current input
        user_message = f"""Current Question: {user_input}

        Previous Exchange (if relevant): {conversation_history}

        Note: Focus on directly answering the current question while drawing from your industry and company knowledge as needed."""

        # Generate response
        message = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            temperature=0.7,
            system=writing_style,
            messages=[
                {
                    "role": "user",
                    "content": user_message
                }
            ]
        )

        # Clean and validate response
        if hasattr(message.content, 'text'):
            response = str(message.content.text)
        elif isinstance(message.content, list):
            response = str(message.content[0].text if hasattr(message.content[0], 'text') else message.content[0])
        else:
            response = str(message.content)

        response = response.strip()
        
        if not response:
            return "Could you please clarify your question? I want to ensure I provide a relevant response."

        return response

    except Exception as e:
        logger.error(f"Discussion error: {str(e)}")
        return "I apologize for the interruption. Could you please rephrase your question?"
    

async def generate_orange_script_ai(request, context, industry):
    purpose = request.purpose
    
    # Define the system prompt as an f-string
    writing_style = f"""You are an expert scriptwriter creating high-impact video content that connects meaningful insights with practical value. Your expertise includes crafting narratives that resonate with HNWI/UHNWI audiences while addressing specific business purposes.

    Task: Generate a sophisticated 60-80 word video script that fulfills the stated purpose while maintaining connection to the provided context. Length: 20-30 seconds.

    Analysis Steps:
    1. First, understand the specific purpose requested
    2. Identify how the provided context relates to this purpose
    3. Determine the most effective narrative approach based on purpose:
    - For product launches/features: Focus on transformation and value
    - For thought leadership: Focus on insights and future trends
    - For brand building: Focus on vision and differentiation
    - For customer education: Focus on solutions and benefits

    Script Structure:
    1. Opening hook - Capture attention with relevant challenge or insight
    2. Main perspective - Present key message aligned with purpose
    3. Supporting evidence - Use context to strengthen the narrative
    4. Concrete example - Demonstrate impact or application
    5. Inspiring close - Drive viewer to intended action

    Requirements:
    - Adapt tone and focus based on stated purpose
    - Use sophisticated yet accessible language
    - Maintain exclusive, insider tone
    - Ensure clear connection between context and purpose
    - Balance intellectual depth with practical relevance"""

    # Create the user message
    user_message = f"""Context: {context}
        Industry: {industry}
        Purpose: {purpose}

        Create a script that precisely fulfills this purpose while leveraging the provided context. Ensure the narrative aligns with what a HNWI/UHNWI audience would expect for this specific type of content. Focus on delivering clear value within the strict 30-second timeframe. Do not give fillers, templates or other explanations in the output. You can still give the video ideas. Describe the product or person in the output as per the requirement."""

    try:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

        anthropic_client = anthropic.Anthropic(api_key=api_key)
        
        message = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            temperature=0.5,
            system=writing_style,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": user_message
                        }
                    ]
                }
            ]
        )

        result = message.content
        return result

    except Exception as e:
        error_msg = f"Unexpected error in Script Generator: {str(e)}"
        print(error_msg)
        traceback.print_exc()
        return error_msg