import os
import dspy  # type: ignore
from dotenv import load_dotenv # type: ignore


load_dotenv()

# Direct Third Party api key servies use 

# API_KEY = os.getenv("API_KEY")
# print(API_KEY)
# LLM_MODEL = os.getenv("LLM_MODEL")
# print(LLM_MODEL)


# llm = dspy.LM(
#     model=f"{LLM_MODEL}",
#     api_key=API_KEY,
#     temperature=1.0,
#     max_tokens=10000,
#     cache=True,
# )

# # Separate LLM for planning phase - lower token limit for efficiency
# PLANNING_API_KEY = os.getenv("PLANNING_API_KEY")
# PLANNING_MODEL = os.getenv("PLANNING_MODEL")
# planning_llm = dspy.LM(
#     model=f"{PLANNING_MODEL}",
#     api_key=PLANNING_API_KEY,
#     temperature=1.0,
#     max_tokens=2000,  # Planning outputs are much smaller (JSON only)
#     cache=True,
# )

# # Separate LLM for update/edit operations - moderate token limit for efficiency
# UPDATE_API_KEY = os.getenv("UPDATE_API_KEY")
# UPDATE_MODEL = os.getenv("UPDATE_MODEL")
# update_llm = dspy.LM(
#     model=f"{UPDATE_MODEL}",
#     api_key=UPDATE_API_KEY,
#     temperature=1.0,
#     max_tokens=8000,  # Planning outputs are much smaller (JSON only)
#     cache=True,
# )

# Use Azure model for full generation 

API_KEY = os.getenv("AZURE_AI_TOKEN")
print(API_KEY)
API_BASE = os.getenv("AZURE_AI_ENDPOINT_URL")
print(API_BASE)
LLM_MODEL = os.getenv("AZURE_AI_DEPLOYMENT_NAME")
print(LLM_MODEL)

API_VERSION = os.getenv("AZURE_AI_APP_VERSION")
print(API_VERSION)

llm = dspy.LM(
    f'azure/{LLM_MODEL}',
    api_key=API_KEY,
    api_base=API_BASE,
    api_version=API_VERSION,
    temperature=1.0,
    max_tokens=16000,
    cache=True
)

planning_llm = llm
update_llm = llm

dspy.settings.configure(lm=llm)
