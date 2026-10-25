import asyncio
from getpass import getpass

import httpx
from dotenv import load_dotenv


load_dotenv()

CHAT_API_URL = "http://127.0.0.1:8000/chat"


async def main():
    """Talk to the agent through the API and keep using the same chat session."""
    access_token = getpass("Enter your access token: ").strip()

    if not access_token:
        print("An access token is required.")
        return

    saved_session_id = input(
        "Enter a chat session ID to continue, or press Enter for a new chat: "
    ).strip()

    if saved_session_id:
        try:
            session_id = int(saved_session_id)
        except ValueError:
            print("The session ID must be a number.")
            return
    else:
        session_id = None

    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    print("\nChat is ready. Type 'exit' to stop.")

    async with httpx.AsyncClient(timeout=120) as client:
        while True:
            message = input("\nYou: ").strip()

            if message.lower() == "exit":
                break

            if not message:
                continue

            request_data: dict[str, str | int] = {"message": message}
            if session_id is not None:
                request_data["session_id"] = session_id

            try:
                response = await client.post(
                    CHAT_API_URL,
                    headers=headers,
                    json=request_data,
                )
                response.raise_for_status()
                result = response.json()

                session_id = result["session_id"]
                print(f"\nChat session ID: {session_id}")
                print(f"Assistant: {result['reply']}")

            except httpx.HTTPStatusError as error:
                try:
                    detail = error.response.json().get(
                        "detail",
                        "The chat request failed.",
                    )
                except ValueError:
                    detail = "The chat request failed."

                print(f"\nError: {detail}")

            except httpx.HTTPError as error:
                print(f"\nCould not connect to the API: {error}")


if __name__ == "__main__":
    asyncio.run(main())
