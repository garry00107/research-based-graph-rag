from llama_index.llms.nvidia import NVIDIA
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("NVIDIA_API_KEY")

models_to_test = [
    "nvidia/llama-3.1-nemotron-70b-instruct",
    "meta/llama3-70b-instruct",
    "nvidia/nemotron-mini-4b-instruct",
    "nvidia/mistral-nemo-minitron-8b-8k-instruct",
    "nvidia/llama-3.1-nemotron-51b-instruct"
]

print("Testing models...")
for model in models_to_test:
    print(f"\nTesting {model}...")
    try:
        llm = NVIDIA(model=model, api_key=api_key)
        response = llm.complete("Hello")
        print(f"SUCCESS: {model} works! Response: {response}")
        break
    except Exception as e:
        print(f"FAILED: {model} - {e}")
