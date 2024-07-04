import os
import httpx
import traceback
from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv()

async def generate_orange_reel(request, context):
    agenda = request.agenda
    mood = request.mood
    additional_input = request.additional_input
    
    writing_style = f"""
    Objective:
    
    From your knowledge from the book Alchemy, and employing minimalism, craft a compelling Facebook post with agenda as agenda, mood and other details as in input
    """
    
    print("Processing with Orange Reel")
    api_key = os.getenv("OPENAI_API_KEY")

    try:
        timeout = httpx.Timeout(1500.0, connect=6000.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                'https://api.openai.com/v1/chat/completions',
                json={
                    "model": "gpt-4-turbo-2024-04-09",
                    "messages": [
                        {"role": "system", "content": f"{writing_style}\n\nClient: {request.client}\nAdditional Input: {additional_input}"},
                        {"role": "user", "content": f"Below is the user input \n Agenda: {agenda} \n Mood: {mood} \n About Our Company: {context} \n Additional Input: {additional_input} \n Use this information to create the content as per the provided strategy and guidelines. Strictly follow instructions. Keep the language simple and business professional. Use limited yet effective emojis."}
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
            print(f"Orange Reel Input: {input_cost}, Orange Reel Output: {output_cost}, Orange Reel Total Cost: {total_cost}, Orange Reel Cost in INR: {cost_in_inr} ")
            return result
            # print("Generated Reel Content:", result)
        else:
            print("No Reel generated")
    except asyncio.CancelledError:
        return "Task cancelled"
    except Exception as e:
        print(f"Unexpected error in Orange Reel: {e}")
        traceback.print_exc()
        return "Error generating content"
