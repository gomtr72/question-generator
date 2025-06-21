from typing import Any, Dict, List
from openai import OpenAI
from openai.types.chat import ChatCompletion
from config import get_config
import tiktoken
import time
import json

class QuestionGenerator:
    def __init__(self):
        config = get_config()
        self.client = OpenAI(api_key=config.OPENAI.API_KEY)
        self.model = config.OPENAI.MODEL
        self.max_tokens = config.OPENAI.MAX_TOKENS
        self.temperature = config.OPENAI.TEMPERATURE
        self.encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        self.chunk_size = 1000  # 청크 크기를 1000 토큰으로 줄임

    def count_tokens(self, text: str) -> int:
        """주어진 텍스트의 토큰 수를 계산합니다."""
        return len(self.encoding.encode(text))

    def split_text(self, text: str) -> List[str]:
        """텍스트를 토큰 제한에 맞게 나눕니다."""
        chunks = []
        current_chunk = []
        current_length = 0
        
        # 문단 단위로 먼저 나누기
        paragraphs = text.split('\n\n')
        
        for paragraph in paragraphs:
            # 문단이 너무 길면 문장 단위로 나누기
            if self.count_tokens(paragraph) > self.chunk_size:
                sentences = paragraph.split('. ')
                for sentence in sentences:
                    sentence = sentence.strip() + '. '
                    sentence_tokens = self.count_tokens(sentence)
                    
                    # 문장이 chunk_size를 초과하면 단어 단위로 나누기
                    if sentence_tokens > self.chunk_size:
                        words = sentence.split()
                        temp_chunk = []
                        temp_length = 0
                        for word in words:
                            word_tokens = self.count_tokens(word + ' ')
                            if temp_length + word_tokens > self.chunk_size:
                                chunks.append(' '.join(temp_chunk))
                                temp_chunk = [word]
                                temp_length = word_tokens
                            else:
                                temp_chunk.append(word)
                                temp_length += word_tokens
                        if temp_chunk:
                            chunks.append(' '.join(temp_chunk))
                    else:
                        if current_length + sentence_tokens > self.chunk_size:
                            chunks.append(''.join(current_chunk))
                            current_chunk = [sentence]
                            current_length = sentence_tokens
                        else:
                            current_chunk.append(sentence)
                            current_length += sentence_tokens
            else:
                paragraph_tokens = self.count_tokens(paragraph)
                if current_length + paragraph_tokens > self.chunk_size:
                    chunks.append(''.join(current_chunk))
                    current_chunk = [paragraph]
                    current_length = paragraph_tokens
                else:
                    current_chunk.append(paragraph)
                    current_length += paragraph_tokens
        
        if current_chunk:
            chunks.append(''.join(current_chunk))
        
        return chunks

    def generate_summary_and_topics(self, content: str) -> str:
        """콘텐츠를 요약하고 핵심 주제를 추출합니다."""
        try:
            # 텍스트가 너무 길면 나누어 처리
            if self.count_tokens(content) > self.chunk_size:
                chunks = self.split_text(content)
                summaries = []
                all_topics = set()
                
                for i, chunk in enumerate(chunks):
                    # API 호출 간 딜레이 추가
                    if i > 0:
                        time.sleep(1)  # 1초 대기
                    
                    prompt = f"""다음 텍스트 조각을 간단히 요약하고 주요 주제를 추출해주세요.
                    반드시 아래 JSON 형식으로 작성해주세요:

                    {{
                        "요약": "2-3문장으로 된 간단한 요약",
                        "핵심 주제": ["주제1", "주제2"]
                    }}

                    텍스트:
                    \"\"\"{chunk}\"\"\"
                    """

                    try:
                        response = self.client.chat.completions.create(
                            model=self.model,
                            messages=[{"role": "user", "content": prompt}],
                            max_tokens=500,  # 토큰 수 제한
                            temperature=0.3  # 더 일관된 결과를 위해 온도 낮춤
                        )
                        
                        result = response.choices[0].message.content
                        parsed = json.loads(result)
                        summaries.append(parsed["요약"])
                        all_topics.update(parsed["핵심 주제"])
                    except Exception as e:
                        continue
                
                # 최종 요약 생성 (3초 대기 후)
                time.sleep(3)
                
                # 요약문들을 더 작은 청크로 나누어 처리
                combined_summary = " ".join(summaries)
                if self.count_tokens(combined_summary) > self.chunk_size:
                    summary_chunks = self.split_text(combined_summary)
                    final_summary = []
                    for chunk in summary_chunks:
                        prompt = f"""다음 요약을 2-3문장으로 압축해주세요:

                        {chunk}
                        """
                        response = self.client.chat.completions.create(
                            model=self.model,
                            messages=[{"role": "user", "content": prompt}],
                            max_tokens=200,
                            temperature=0.3
                        )
                        final_summary.append(response.choices[0].message.content)
                        time.sleep(1)
                    
                    final_text = " ".join(final_summary)
                else:
                    final_text = combined_summary

                return json.dumps({
                    "요약": final_text,
                    "핵심 주제": list(all_topics)[:5]  # 상위 5개 주제만 선택
                }, ensure_ascii=False)
            
            # 텍스트가 충분히 짧으면 바로 처리
            prompt = f"""다음 콘텐츠를 요약하고 핵심 주제를 추출해주세요.
            반드시 아래 JSON 형식으로 작성해주세요:

            {{
                "요약": "여기에 전체 내용 요약을 작성",
                "핵심 주제": ["주제1", "주제2", "주제3"]
            }}

            분석할 콘텐츠:
            \"\"\"{content}\"\"\"
            """

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"요약 생성 중 오류 발생: {str(e)}")

    def generate_questions(self, summary: str, topics: List[str]) -> str:
        """
        요약과 주제를 바탕으로 핵심 개념 선택 문제를 생성합니다.
        
        Args:
            summary: 콘텐츠 요약
            topics: 핵심 주제 리스트
            
        Returns:
            JSON 형식의 질문 목록
        """
        topics_str = "\n".join([f"- {topic}" for topic in topics])
        prompt = f"""당신은 교육 전문가이자 개념 분류에 능한 평가 디자이너입니다.
        주어진 요약문과 핵심 주제를 바탕으로 3개의 서로 다른 핵심 개념을 평가하는 문제를 생성해주세요.

        반드시 아래 JSON 형식으로 작성해주세요:
        {{
            "questions": [
                {{
                    "질문": "아래 보기 중 입력된 내용의 첫 번째 핵심 개념에 가장 가까운 주제를 고르시오.",
                    "보기": {{
                        "A": {{"질문": "첫 번째 의미 있는 질문", "근접도": 85}},
                        "B": {{"질문": "두 번째 의미 있는 질문", "근접도": 70}},
                        "C": {{"질문": "세 번째 의미 있는 질문", "근접도": 60}},
                        "D": {{"질문": "네 번째 의미 있는 질문", "근접도": 45}},
                        "E": {{"질문": "다섯 번째 의미 있는 질문", "근접도": 30}}
                    }},
                    "정답": "A",
                    "해설": {{
                        "정답_설명": "정답이 왜 핵심 개념에 가장 가까운지 설명",
                        "오답_설명": "다른 보기들이 왜 핵심에서 벗어나 있는지 설명"
                    }}
                }},
                {{
                    "질문": "아래 보기 중 입력된 내용의 두 번째 핵심 개념에 가장 가까운 주제를 고르시오.",
                    "보기": {{
                        "A": {{"질문": "첫 번째 의미 있는 질문", "근접도": 65}},
                        "B": {{"질문": "두 번째 의미 있는 질문", "근접도": 90}},
                        "C": {{"질문": "세 번째 의미 있는 질문", "근접도": 55}},
                        "D": {{"질문": "네 번째 의미 있는 질문", "근접도": 40}},
                        "E": {{"질문": "다섯 번째 의미 있는 질문", "근접도": 25}}
                    }},
                    "정답": "B",
                    "해설": {{
                        "정답_설명": "정답이 왜 핵심 개념에 가장 가까운지 설명",
                        "오답_설명": "다른 보기들이 왜 핵심에서 벗어나 있는지 설명"
                    }}
                }},
                {{
                    "질문": "아래 보기 중 입력된 내용의 세 번째 핵심 개념에 가장 가까운 주제를 고르시오.",
                    "보기": {{
                        "A": {{"질문": "첫 번째 의미 있는 질문", "근접도": 35}},
                        "B": {{"질문": "두 번째 의미 있는 질문", "근접도": 50}},
                        "C": {{"질문": "세 번째 의미 있는 질문", "근접도": 95}},
                        "D": {{"질문": "네 번째 의미 있는 질문", "근접도": 70}},
                        "E": {{"질문": "다섯 번째 의미 있는 질문", "근접도": 40}}
                    }},
                    "정답": "C",
                    "해설": {{
                        "정답_설명": "정답이 왜 핵심 개념에 가장 가까운지 설명",
                        "오답_설명": "다른 보기들이 왜 핵심에서 벗어나 있는지 설명"
                    }}
                }}
            ]
        }}

        주의사항:
        1. 각 보기는 반드시 의미 있는 질문 형태로 작성해주세요.
        2. 근접도 점수는 100점 만점 기준으로 작성해주세요.
        3. 정답은 반드시 가장 높은 근접도 점수를 가진 보기여야 합니다.
        4. 해설은 각 보기의 근접도 차이를 명확하게 설명해주세요.
        5. 근접도 점수는 반드시 정수로 작성해주세요.
        6. 세 문제는 서로 다른 핵심 개념을 다루어야 합니다.

        [요약문]
        {summary}

        [핵심 주제]
        {topics_str}
        """

        response: ChatCompletion = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=self.max_tokens,
            temperature=self.temperature
        )
        
        # 응답을 JSON 객체로 파싱하여 반환
        result = json.loads(response.choices[0].message.content)
        return json.dumps(result, ensure_ascii=False)

    def generate_multiple_choice(self, question: str) -> str:
        """이 메서드는 더 이상 사용되지 않습니다."""
        pass

    def generate_feedback(self, question: str, gpt_level: str, user_level: str) -> str:
        """
        GPT와 사용자의 수준 판단 차이에 대한 피드백을 생성합니다.
        
        Args:
            question: 평가된 질문
            gpt_level: GPT가 판단한 수준
            user_level: 사용자가 선택한 수준
            
        Returns:
            교육적 피드백
        """
        prompt = f"""[질문]: {question}
        [GPT 판단 수준]: {gpt_level}
        [사용자 선택 수준]: {user_level}

        이 차이를 바탕으로 친절하고 교육적인 피드백을 작성해주세요."""

        response: ChatCompletion = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=self.max_tokens,
            temperature=self.temperature
        )
        return response.choices[0].message.content 