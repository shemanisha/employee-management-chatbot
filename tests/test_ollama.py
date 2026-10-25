import asyncio
from dotenv import load_dotenv
from agent.llm import get_llm

load_dotenv()


async def main():
    llm = get_llm()

    response = await llm.ainvoke(
        "What is employee leave management?"
    )

    print(response.content)


if __name__ == "__main__":
    asyncio.run(main())