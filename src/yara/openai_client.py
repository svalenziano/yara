from openai import OpenAI
from config import env

client = OpenAI(api_key=env['OPENAI_API_KEY'])