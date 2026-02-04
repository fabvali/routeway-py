import os
import asyncio
from routeway import (
    RoutewayClient,
    AsyncRoutewayClient,
    create_user_message,
    create_assistant_message,
    create_system_message,
    create_function,
    create_tool,
    ReasoningConfig,
    StreamOptions,
)


# ============================================================================
# Example 1: Basic Chat Completion
# ============================================================================

def basic_chat():
    """Simple chat completion example."""
    client = RoutewayClient(api_key="your-api-key")
    
    response = client.chat_completion(
        model="gpt-4",
        messages=[
            {"role": "user", "content": "What is the capital of France?"}
        ],
    )
    
    print(response["choices"][0]["message"]["content"])
    client.close()


# ============================================================================
# Example 2: Chat with Message Helpers
# ============================================================================

def chat_with_helpers():
    """Using message helper functions."""
    with RoutewayClient(api_key="your-api-key") as client:
        messages = [
            create_system_message("You are a helpful assistant."),
            create_user_message("Tell me a joke about programming."),
        ]
        
        response = client.chat_completion(
            model="gpt-4",
            messages=messages,
            temperature=0.8,
        )
        
        print(response["choices"][0]["message"]["content"])


# ============================================================================
# Example 3: Streaming Responses
# ============================================================================

def streaming_chat():
    """Stream chat completion chunks."""
    client = RoutewayClient(api_key="your-api-key")
    
    stream = client.chat_completion(
        model="gpt-4",
        messages=[
            {"role": "user", "content": "Write a short poem about AI."}
        ],
        stream=True,
        stream_options=StreamOptions(include_usage=True),
    )
    
    print("Streaming response:")
    for chunk in stream:
        if chunk["choices"]:
            delta = chunk["choices"][0].get("delta", {})
            if content := delta.get("content"):
                print(content, end="", flush=True)
    
    print()  # Newline after streaming
    client.close()


# ============================================================================
# Example 4: Extended Thinking/Reasoning
# ============================================================================

def reasoning_example():
    """Using extended thinking/reasoning mode."""
    with RoutewayClient(api_key="your-api-key") as client:
        response = client.chat_completion(
            model="gpt-4",
            messages=[
                {
                    "role": "user",
                    "content": "Solve this logic puzzle: If all roses are flowers, "
                               "and some flowers fade quickly, can we conclude that "
                               "some roses fade quickly?"
                }
            ],
            reasoning=ReasoningConfig(
                type="enabled",
                max_tokens=1000,
            ).to_dict(),
        )
        
        message = response["choices"][0]["message"]
        
        # Check for reasoning content
        if "reasoning_content" in message:
            print("Reasoning process:")
            print(message["reasoning_content"])
            print("\nFinal answer:")
        
        print(message["content"])
        
        # Usage information
        if usage := response.get("usage"):
            print(f"\nTokens used:")
            print(f"  Prompt: {usage.get('prompt_tokens')}")
            print(f"  Completion: {usage.get('completion_tokens')}")
            print(f"  Reasoning: {usage.get('reasoning_tokens', 0)}")


# ============================================================================
# Example 5: Function/Tool Calling
# ============================================================================

def function_calling():
    """Using function calling/tools."""
    # Define a function
    get_weather_func = create_function(
        name="get_weather",
        description="Get the current weather in a location",
        parameters={
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city and state, e.g. San Francisco, CA",
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                },
            },
            "required": ["location"],
        },
    )
    
    tool = create_tool(get_weather_func)
    
    with RoutewayClient(api_key="your-api-key") as client:
        response = client.chat_completion(
            model="gpt-4",
            messages=[
                {"role": "user", "content": "What's the weather like in Paris?"}
            ],
            tools=[tool.to_dict()],
            tool_choice="auto",
        )
        
        message = response["choices"][0]["message"]
        
        # Check if model wants to call a function
        if tool_calls := message.get("tool_calls"):
            print("Model wants to call:")
            for tool_call in tool_calls:
                print(f"  Function: {tool_call['function']['name']}")
                print(f"  Arguments: {tool_call['function']['arguments']}")


# ============================================================================
# Example 6: Multi-turn Conversation
# ============================================================================

def multi_turn_conversation():
    """Multi-turn conversation with context."""
    with RoutewayClient(api_key="your-api-key") as client:
        conversation = [
            create_system_message("You are a math tutor."),
            create_user_message("What is 15 * 7?"),
        ]
        
        # First turn
        response = client.chat_completion(
            model="gpt-4",
            messages=conversation,
        )
        
        assistant_reply = response["choices"][0]["message"]["content"]
        print(f"Assistant: {assistant_reply}")
        
        # Add to conversation
        conversation.append(create_assistant_message(assistant_reply))
        conversation.append(create_user_message("Now multiply that by 3"))
        
        # Second turn
        response = client.chat_completion(
            model="gpt-4",
            messages=conversation,
        )
        
        print(f"Assistant: {response['choices'][0]['message']['content']}")


# ============================================================================
# Example 7: Async Chat Completion
# ============================================================================

async def async_chat():
    """Async chat completion example."""
    async with AsyncRoutewayClient(api_key="your-api-key") as client:
        response = await client.chat_completion(
            model="gpt-4",
            messages=[
                {"role": "user", "content": "What is async programming?"}
            ],
        )
        
        print(response["choices"][0]["message"]["content"])


# ============================================================================
# Example 8: Async Streaming
# ============================================================================

async def async_streaming():
    """Async streaming example."""
    async with AsyncRoutewayClient(api_key="your-api-key") as client:
        stream = await client.chat_completion(
            model="gpt-4",
            messages=[
                {"role": "user", "content": "Count from 1 to 5 slowly."}
            ],
            stream=True,
        )
        
        print("Streaming response:")
        async for chunk in stream:
            if chunk["choices"]:
                delta = chunk["choices"][0].get("delta", {})
                if content := delta.get("content"):
                    print(content, end="", flush=True)
        print()


# ============================================================================
# Example 9: Concurrent Async Requests
# ============================================================================

async def concurrent_requests():
    """Make multiple async requests concurrently."""
    async with AsyncRoutewayClient(api_key="your-api-key") as client:
        questions = [
            "What is Python?",
            "What is JavaScript?",
            "What is Rust?",
        ]
        
        tasks = [
            client.chat_completion(
                model="gpt-4",
                messages=[{"role": "user", "content": q}],
                max_tokens=50,
            )
            for q in questions
        ]
        
        responses = await asyncio.gather(*tasks)
        
        for q, r in zip(questions, responses):
            answer = r["choices"][0]["message"]["content"]
            print(f"Q: {q}")
            print(f"A: {answer}\n")


# ============================================================================
# Example 10: Error Handling
# ============================================================================

def error_handling():
    """Proper error handling example."""
    from routeway import (
        RoutewayAuthError,
        RoutewayRateLimitError,
        RoutewayServerError,
        RoutewayError,
    )
    
    client = RoutewayClient(api_key="your-api-key")
    
    try:
        response = client.chat_completion(
            model="gpt-4",
            messages=[{"role": "user", "content": "Hello!"}],
        )
        print(response["choices"][0]["message"]["content"])
        
    except RoutewayAuthError as e:
        print(f"Authentication failed: {e}")
    except RoutewayRateLimitError as e:
        print(f"Rate limit exceeded: {e}")
        print("Please wait and try again...")
    except RoutewayServerError as e:
        print(f"Server error: {e}")
    except RoutewayError as e:
        print(f"API error: {e}")
    finally:
        client.close()


# ============================================================================
# Example 11: Custom Parameters
# ============================================================================

def custom_parameters():
    """Using various custom parameters."""
    with RoutewayClient(api_key="your-api-key") as client:
        response = client.chat_completion(
            model="gpt-4",
            messages=[
                {"role": "user", "content": "Write a creative story."}
            ],
            temperature=1.2,
            max_tokens=500,
            top_p=0.9,
            frequency_penalty=0.5,
            presence_penalty=0.5,
            stop=["\n\n", "The End"],
        )
        
        print(response["choices"][0]["message"]["content"])


# ============================================================================
# Example 12: List Available Models
# ============================================================================

def list_models():
    """List all available models."""
    with RoutewayClient(api_key="your-api-key") as client:
        models = client.models_list()
        
        print("Available models:")
        for model in models.get("data", []):
            print(f"  - {model['id']}")


# ============================================================================
# Example 13: Get Model Information
# ============================================================================

def get_model_info():
    """Get information about a specific model."""
    with RoutewayClient(api_key="your-api-key") as client:
        model_info = client.model_retrieve("gpt-4")
        
        print(f"Model: {model_info['id']}")
        print(f"Owner: {model_info['owned_by']}")
        print(f"Created: {model_info['created']}")


if __name__ == "__main__":
    print("Choose an example to run:")
    print("1. Basic chat")
    print("2. Streaming chat")
    print("3. Reasoning example")
    print("4. Function calling")
    print("5. Multi-turn conversation")
    print("6. Async chat (requires asyncio)")
    print("7. Error handling")
    
    # Uncomment to run specific examples:
    # basic_chat()
    # streaming_chat()
    # reasoning_example()
    # function_calling()
    # multi_turn_conversation()
    # asyncio.run(async_chat())
    # error_handling()