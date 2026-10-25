from pydantic_settings import BaseSettings

class Settings(BaseSettings):


    app_name: str = "Employee Management Chatbot"
    
    # Postgres database url
    database_url : str


    #Jwt settings
    jwt_secret_key : str
    jwt_algorithm : str
    access_token_expire_minutes : int

    # Ollama settings
    ollama_model : str

    MCP_SERVER_URL : str

    class Config:
        #Read environment variables from a .env file
        env_file = ".env"
        env_file_encoding = "utf-8"

# Create an instance of the Settings class to access the configuration values
settings = Settings()
