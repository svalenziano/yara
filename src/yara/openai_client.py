from openai import OpenAI
from yara.config import env

client = OpenAI(api_key=env['OPENAI_API_KEY'])