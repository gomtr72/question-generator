def format_questions(questions: list) -> str:
    """
    질문 리스트를 Markdown 형식으로 변환합니다.
    """
    markdown = "# 생성된 질문\n\n"
    
    # 분석 질문 섹션
    markdown += "## 분석 질문\n\n"
    analysis_questions = [q for q in questions if q['type'] == 'analysis']
    for q in analysis_questions:
        markdown += q['content'] + "\n\n"
    
    # 종합 질문 섹션
    markdown += "## 종합 질문\n\n"
    synthesis_questions = [q for q in questions if q['type'] == 'synthesis']
    for q in synthesis_questions:
        markdown += q['content'] + "\n\n"
    
    # 학습 순서 및 피드백 전략
    markdown += "## 학습 순서 및 피드백 전략\n\n"
    markdown += "1. 분석 질문부터 시작하여 기본적인 이해를 다집니다.\n"
    markdown += "2. 종합 질문으로 심화 학습을 진행합니다.\n"
    markdown += "3. 각 질문에 대한 답변을 작성한 후, 평가요소를 기준으로 자가 평가를 진행합니다.\n"
    markdown += "4. 작성 팁을 참고하여 답변을 개선합니다.\n"
    
    return markdown 