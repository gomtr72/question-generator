from flask import Flask, render_template, jsonify, Response
from flask_cors import CORS
from routes.generator import generator_bp
from utils.logger import logger, log_error
from utils.exceptions import QuestionGeneratorError
from werkzeug.exceptions import NotFound
from config import get_config
import os

def create_app(config_name: str = None) -> Flask:
    """
    Flask 애플리케이션 팩토리 함수
    """
    app = Flask(__name__)
    CORS(app)  # CORS 설정 추가
    
    # 설정 로드
    config_name = config_name or os.getenv("FLASK_ENV", "development")
    app.config.from_object(get_config())
    
    # 파일 업로드 설정
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 최대 16MB
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # 블루프린트 등록
    app.register_blueprint(generator_bp)
    
    # 에러 핸들러 등록
    @app.errorhandler(QuestionGeneratorError)
    def handle_question_generator_error(error: QuestionGeneratorError) -> tuple[Response, int]:
        log_error(error)
        return jsonify({
            "error": True,
            "message": error.message,
            "error_code": error.error_code,
            "details": error.details
        }), error.status_code
    
    @app.errorhandler(NotFound)
    def handle_404_error(error: NotFound) -> tuple[Response, int]:
        log_error(error)
        return jsonify({
            "error": True,
            "message": str(error),
            "error_code": "NOT_FOUND"
        }), 404
    
    @app.errorhandler(Exception)
    def handle_generic_error(error: Exception) -> tuple[Response, int]:
        log_error(error)
        return jsonify({
            "error": True,
            "message": "내부 서버 오류가 발생했습니다.",
            "error_code": "INTERNAL_SERVER_ERROR"
        }), 500
    
    @app.route('/')
    def index() -> str:
        return render_template('form.html')
    
    # 애플리케이션 시작 로그
    logger.info(
        "application_started",
        environment=app.config["ENV"],
        debug=app.config["DEBUG"]
    )
    
    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.getenv('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=True)  # 디버그 모드 활성화 