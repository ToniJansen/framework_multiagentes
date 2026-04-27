from __future__ import annotations

import chainlit as cl
from dotenv import load_dotenv

load_dotenv()

WELCOME = """**framework_multiagentes** — AI Agents Platform

Choose a case:
- `/spec <path>` — Case 1: generate a PR draft from a spec file
- `/qa <question>` — Case 2: answer a business question with SQL + semantic search

Example: `/qa Qual a média de avaliação dos produtos?`
"""


@cl.on_chat_start
async def start():
    await cl.Message(content=WELCOME).send()


@cl.on_message
async def handle(message: cl.Message):
    text = message.content.strip()

    if text.startswith("/spec "):
        spec_path = text[6:].strip()
        await cl.Message(content=f"Running spec_to_pr on `{spec_path}`...").send()
        try:
            from cases.spec_to_pr.main import run
            result = run(spec_path)
            await cl.Message(
                content=f"Done.\n\n**diff:** `{result['diff_path']}`\n**PR:** `{result['pr_path']}`"
            ).send()
        except Exception as exc:
            await cl.Message(content=f"Error: {exc}").send()

    elif text.startswith("/qa "):
        question = text[4:].strip()
        await cl.Message(content=f"Researching: *{question}*...").send()
        try:
            from cases.shop_qa.main import run
            answer = run(question)
            await cl.Message(content=answer).send()
        except Exception as exc:
            await cl.Message(content=f"Error: {exc}").send()

    else:
        await cl.Message(
            content="Unknown command. Use `/spec <path>` or `/qa <question>`."
        ).send()
