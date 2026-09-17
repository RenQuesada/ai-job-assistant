from dotenv import find_dotenv, load_dotenv
from openai import AsyncOpenAI
import os

load_dotenv(find_dotenv())

client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)