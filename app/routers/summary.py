import textwrap
from typing import List
from fastapi import APIRouter

import openai
from pydantic import BaseModel

import kss


class Input_Text(BaseModel):
    text: List[str]
    max_summarize_chars: int = 9000
    max_chars_per_request: int = 4000
    summary_length: int = 1000


router = APIRouter()


async def generate_summary_turbo(text: str, max_token: int = 500):
    prompt = f"summarize this for a student in Korean : {text}"

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        temperature=0.7,
        top_p=1.0,
        frequency_penalty=0.0,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant for text summarization.",
            },
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    summary = completion.choices[0].message["content"]
    return summary


async def generate_summary_davinci(text: str, max_length: int = 1000):
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=f"summarize the following sentence in Korean : {text}",
        max_tokens=2000,
        temperature=1,
    )
    summary = response.choices[0].text.strip()
    return summary


async def generate_refine_gpt3(text: str, max_length: int = 1000):
    prompt = f"한국어로 아래 글을 읽기 쉽게 수정해줘. : {text}"
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        temperature=0.7,
        top_p=1.0,
        frequency_penalty=0.0,
        messages=[
            {
                "role": "system",
                "content": "당신은 유능한 작가 어시스던트입니다.",
            },
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    refine = completion.choices[0].message["content"]
    return refine


async def extract_table(text: str, max_length: int = 1000):
    prompt = f"아래 글에서 가장 추천하는 단 하나의 목차 추출해줘 : {text}"

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        temperature=0.7,
        top_p=1.0,
        frequency_penalty=0.0,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    extract = completion.choices[0].message["content"]
    return extract


async def handle_large_text(purpose, input_data: Input_Text, process_function: callable):
    text = input_data.text  # 텍스트 가져오기 리스트
    max_summarize_chars = input_data.max_summarize_chars
    max_chars_per_request = input_data.max_chars_per_request
    output_length = input_data.summary_length
    final_output_texts = []

    for text_chunk in text:
        wrapped_text = textwrap.wrap(text_chunk, max_chars_per_request)
        length = max_summarize_chars // max_chars_per_request
        wrapped_text = wrapped_text[:length]
        output_chunks = []
        for sub_chunk in enumerate(wrapped_text):
            processed_text = await process_function(sub_chunk, output_length)
            output_chunks.append(processed_text)
            split = await split_sentences(output_chunks)
        final_output_texts.append(split)
    return {f"{purpose}": final_output_texts}


async def split_sentences(input_data):
    split_sentence = kss.split_sentences(input_data)
    return split_sentence


@router.post("/summarize_large_text_davinci")
async def summary_large_text_davinci(input_data: Input_Text):
    result = await handle_large_text("summary", input_data, generate_summary_davinci)  # summarize_large_text 함수를 호출하여 결과를 받아옴
    return result


@router.post("/summarize_large_text_GPT3.5_Turbo")
async def summary_large_text_turbo(input_data: Input_Text):
    result = await handle_large_text("summary", input_data, generate_summary_turbo)  # summarize_large_text 함수를 호출하여 결과를 받아옴
    return result


@router.post("/refine_large_text_GPT3.5_Turbo")
async def refine_large_text(input_data: Input_Text):
    result = await handle_large_text("refine", input_data, generate_refine_gpt3)  # summarize_large_text 함수를 호출하여 결과를 받아옴
    return result


#@router.post("/one_task_refine_extract")
async def extract_table_large_text(input_data: Input_Text):
    #summary = await handle_large_text("summary", input_data, generate_summary_turbo)
    refine = await handle_large_text("refine", input_data, generate_refine_gpt3)
    extract = await handle_large_text("extract", input_data, extract_table)
    return refine, extract


@router.post("/extract_table_GPT3.5")
async def extract_table_large_text(input_data: Input_Text):
    result = await handle_large_text("extract", input_data, extract_table)  # summarize_large_text 함수를 호출하여 결과를 받아옴
    return result
