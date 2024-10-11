from langchain_openai import ChatOpenAI

model = ChatOpenAI(model_name="gpt-3.5-turbo-0125",
                   openai_api_key="sk-FyQrmncG5JvDAxO48JoYprNPES4omOdP",
                   base_url= "https://api.proxyapi.ru/openai/v1"
                   )
print(model.invoke("What is the capital of France?").content)