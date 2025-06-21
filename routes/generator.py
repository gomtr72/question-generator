from typing import Dict, Any, List, Union
from flask import Blueprint, request, jsonify, render_template, Response
from werkzeug.utils import secure_filename
from services.content_processor import ContentProcessor
from services.question_generator import QuestionGenerator
from utils.logger import log_request, log_error
from utils.exceptions import (
    QuestionGeneratorError,
    ValidationError,
    ContentProcessingError
)
import json
import os

generator_bp = Blueprint('generator', __name__)
content_processor = ContentProcessor()
question_generator = QuestionGenerator()

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_content_request(data: Dict[str, Any]) -> None:
    """
    콘텐츠 처리 요청 데이터를 검증합니다.
    
    Args:
        data: 요청 데이터
        
    Raises:
        ValidationError: 데이터가 유효하지 않은 경우
    """
    if not data:
        raise ValidationError("요청 데이터가 없습니다.")
        
    content_type = data.get('type')
    
    if not content_type:
        raise ValidationError("콘텐츠 타입이 지정되지 않았습니다.")
        
    if content_type not in ['text', 'pdf', 'youtube', 'website', 'image']:
        raise ValidationError("지원하지 않는 콘텐츠 타입입니다.")

def validate_feedback_request(data: Dict[str, Any]) -> None:
    """
    피드백 요청 데이터를 검증합니다.
    
    Args:
        data: 요청 데이터
        
    Raises:
        ValidationError: 데이터가 유효하지 않은 경우
    """
    if not data:
        raise ValidationError("요청 데이터가 없습니다.")
        
    if not data.get('question'):
        raise ValidationError("질문이 없습니다.")
        
    if not data.get('gpt_level'):
        raise ValidationError("GPT 판단 수준이 없습니다.")
        
    if not data.get('user_level'):
        raise ValidationError("사용자 선택 수준이 없습니다.")

@generator_bp.route('/process', methods=['POST'])
@log_request
def process_content() -> Union[Response, tuple[Response, int]]:
    """
    콘텐츠를 처리하고 질문을 생성합니다.
    
    Returns:
        JSON 응답 또는 에러 응답
    """
    try:
        content_type = request.form.get('type')
        if not content_type:
            data = request.get_json()
            if not data:
                raise ValidationError("요청 데이터가 없습니다.")
            content_type = data.get('type')
            content = data.get('content')
        else:
            content = request.form.get('content')

        if not content_type:
            raise ValidationError("콘텐츠 타입이 지정되지 않았습니다.")

        # 콘텐츠 처리
        try:
            if content_type == 'text':
                if not content:
                    raise ValidationError("텍스트가 없습니다.")
                processed_content = content_processor.process_text(content)
            
            elif content_type in ['pdf', 'image']:
                if 'file' not in request.files:
                    raise ValidationError(f"파일이 제공되지 않았습니다.")
                
                file = request.files['file']
                if file.filename == '':
                    raise ValidationError(f"선택된 파일이 없습니다.")
                
                if not allowed_file(file.filename):
                    raise ValidationError(f"지원하지 않는 파일 형식입니다.")
                
                if content_type == 'pdf':
                    processed_content = content_processor.process_pdf(file)
                else:  # image
                    processed_content = content_processor.process_image(file)
            
            elif content_type == 'youtube':
                if not content:
                    raise ValidationError("유튜브 URL이 없습니다.")
                if not isinstance(content, str):
                    raise ValidationError("올바른 유튜브 URL이 제공되지 않았습니다.")
                processed_content = content_processor.process_youtube(content)
            
            else:  # website
                if not content:
                    raise ValidationError("웹사이트 URL이 없습니다.")
                if not isinstance(content, str):
                    raise ValidationError("올바른 웹사이트 URL이 제공되지 않았습니다.")
                processed_content = content_processor.process_website(content)

            # 오류 메시지 확인
            if isinstance(processed_content, str) and any(error_text in processed_content for error_text in [
                "처리 중 오류가 발생했습니다",
                "찾을 수 없습니다",
                "접근할 수 없습니다",
                "올바르지 않은",
                "제공되지 않았습니다"
            ]):
                raise ContentProcessingError(processed_content)

        except Exception as e:
            raise ContentProcessingError(f"콘텐츠 처리 중 오류 발생: {str(e)}")

        if not processed_content:
            raise ContentProcessingError("처리된 콘텐츠가 없습니다.")

        # 요약 및 주제 추출
        try:
            summary_and_topics = question_generator.generate_summary_and_topics(processed_content)
            summary_data = json.loads(summary_and_topics)
            
            if not isinstance(summary_data, dict) or '요약' not in summary_data or '핵심 주제' not in summary_data:
                raise QuestionGeneratorError(
                    message="잘못된 요약 데이터 형식입니다.",
                    error_code="INVALID_SUMMARY_FORMAT"
                )
        except json.JSONDecodeError as e:
            raise QuestionGeneratorError(
                message=f"요약 및 주제 데이터 파싱 중 오류 발생: {str(e)}",
                error_code="JSON_PARSE_ERROR"
            )
        except Exception as e:
            raise QuestionGeneratorError(
                message=f"요약 및 주제 추출 중 오류 발생: {str(e)}",
                error_code="SUMMARY_GENERATION_ERROR"
            )

        # 질문 생성
        try:
            questions = question_generator.generate_questions(
                summary_data['요약'],
                summary_data['핵심 주제']
            )
            questions_data = json.loads(questions)
            
            if not isinstance(questions_data, dict) or 'questions' not in questions_data:
                raise QuestionGeneratorError(
                    message="잘못된 질문 데이터 형식입니다.",
                    error_code="INVALID_QUESTIONS_FORMAT"
                )

            return jsonify({
                'summary': summary_data['요약'],
                'topics': summary_data['핵심 주제'],
                'questions': questions_data['questions']
            })

        except json.JSONDecodeError as e:
            raise QuestionGeneratorError(
                message=f"질문 데이터 파싱 중 오류 발생: {str(e)}",
                error_code="JSON_PARSE_ERROR"
            )
        except Exception as e:
            raise QuestionGeneratorError(
                message=f"질문 생성 중 오류 발생: {str(e)}",
                error_code="QUESTION_GENERATION_ERROR"
            )

        # 각 질문에 대한 객관식 문항 생성
        for question in questions_data['questions']:
            try:
                multiple_choice = question_generator.generate_multiple_choice(question['질문'])
                question['객관식'] = json.loads(multiple_choice)
            except Exception as e:
                raise QuestionGeneratorError(
                    message=f"객관식 문항 생성 중 오류 발생: {str(e)}",
                    error_code="MULTIPLE_CHOICE_GENERATION_ERROR"
                )

    except QuestionGeneratorError as e:
        log_error(e)
        return jsonify({'error': e.message}), e.status_code
    except Exception as e:
        log_error(e)
        return jsonify({'error': str(e)}), 500

@generator_bp.route('/feedback', methods=['POST'])
@log_request
def get_feedback() -> Union[Response, tuple[Response, int]]:
    """
    사용자의 답변에 대한 피드백을 생성합니다.
    
    Returns:
        JSON 응답 또는 에러 응답
    """
    try:
        data = request.json
        validate_feedback_request(data)

        feedback = question_generator.generate_feedback(
            data['question'],
            data['gpt_level'],
            data['user_level']
        )
        return jsonify({'feedback': feedback})

    except QuestionGeneratorError as e:
        log_error(e)
        return jsonify({'error': e.message}), e.status_code
    except Exception as e:
        log_error(e)
        return jsonify({'error': str(e)}), 500

@generator_bp.route('/form')
def form() -> str:
    """
    질문 생성 폼을 렌더링합니다.
    
    Returns:
        HTML 템플릿
    """
    return render_template('generator_form.html') 