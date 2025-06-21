import PyPDF2
from bs4 import BeautifulSoup
import requests
from pytube import YouTube
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
import io
import re
from PIL import Image
import pytesseract
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from config import get_config

class ContentProcessor:
    def __init__(self):
        self.config = get_config()
        if self.config.YOUTUBE.API_KEY:
            self.youtube = build('youtube', 'v3', developerKey=self.config.YOUTUBE.API_KEY)
        else:
            self.youtube = None

    @staticmethod
    def process_text(text):
        return text.strip()

    @staticmethod
    def process_pdf(pdf_file):
        """PDF 파일을 처리합니다."""
        try:
            if not pdf_file:
                raise ValueError("PDF 파일이 제공되지 않았습니다.")

            # 파일 객체로 처리
            if hasattr(pdf_file, 'read'):
                pdf_reader = PyPDF2.PdfReader(pdf_file)
            else:
                # 파일 경로로 처리
                with open(pdf_file, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
            
            text = []
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text.strip():  # 빈 페이지가 아닌 경우만 추가
                    text.append(page_text.strip())
            
            if not text:
                return "PDF에서 텍스트를 추출할 수 없습니다."
            
            return "\n\n".join(text)  # 페이지 간 구분을 위해 개행 추가
            
        except FileNotFoundError:
            return "PDF 파일을 찾을 수 없습니다."
        except PermissionError:
            return "PDF 파일에 접근할 수 없습니다."
        except PyPDF2.PdfReadError:
            return "올바르지 않은 PDF 파일입니다."
        except Exception as e:
            return f"PDF 처리 중 오류가 발생했습니다: {str(e)}"

    @staticmethod
    def process_image(image_file):
        """이미지 파일에서 텍스트를 추출합니다."""
        try:
            if isinstance(image_file, str):
                if '\x00' in image_file:  # null byte 체크
                    raise ValueError("올바르지 않은 이미지 파일입니다.")
                
                # 파일 경로인 경우
                image = Image.open(image_file)
            else:
                # 파일 객체인 경우
                image = Image.open(io.BytesIO(image_file.read()))
            
            # 이미지에서 텍스트 추출
            text = pytesseract.image_to_string(image, lang='kor+eng')
            
            if not text.strip():
                return "이미지에서 텍스트를 추출할 수 없습니다."
            
            return text.strip()
        except Exception as e:
            return f"이미지 처리 중 오류가 발생했습니다: {str(e)}"

    @staticmethod
    def extract_video_id(url: str) -> str:
        """유튜브 URL에서 비디오 ID를 추출합니다."""
        patterns = [
            r'(?:v=|/v/|/embed/|youtu\.be/)([^&?/]+)',
            r'(?:youtube\.com/watch\?v=)([^&?/]+)',
            r'(?:youtube\.com/shorts/)([^&?/]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def process_youtube(self, url: str) -> str:
        """유튜브 URL에서 자막과 정보를 추출합니다."""
        try:
            # URL 검증
            if not url:
                return "유튜브 URL이 제공되지 않았습니다."
                
            if not ('youtube.com' in url or 'youtu.be' in url):
                return "올바른 유튜브 URL이 아닙니다."

            video_id = self.extract_video_id(url)
            if not video_id:
                return "유튜브 동영상 ID를 추출할 수 없습니다."

            if not self.youtube:
                return "YouTube API 키가 설정되지 않았습니다. 관리자에게 문의하세요."

            try:
                # YouTube Data API를 사용하여 동영상 정보 가져오기
                video_response = self.youtube.videos().list(
                    part='snippet',
                    id=video_id
                ).execute()

                if not video_response['items']:
                    return "동영상을 찾을 수 없습니다."

                video_data = video_response['items'][0]['snippet']
                title = video_data.get('title', '제목 없음')
                description = video_data.get('description', '설명 없음')

            except HttpError as e:
                if e.resp.status == 403:
                    return "YouTube API 키가 유효하지 않거나 할당량이 초과되었습니다."
                elif e.resp.status == 404:
                    return "동영상을 찾을 수 없습니다."
                else:
                    print(f"YouTube API 오류: {str(e)}")
                    return "동영상 정보를 가져오는 중 오류가 발생했습니다."

            try:
                # 자막 가져오기
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                
                # 한국어 자막 우선, 없으면 영어 자막 시도
                transcript = None
                try:
                    transcript = transcript_list.find_transcript(['ko'])
                except:
                    try:
                        transcript = transcript_list.find_transcript(['en'])
                    except:
                        try:
                            # 자동 생성된 자막 시도
                            transcript = transcript_list.find_manually_created_transcript()
                        except:
                            try:
                                transcript = transcript_list.find_generated_transcript()
                            except:
                                pass

                if transcript:
                    # 자막을 텍스트로 변환
                    formatter = TextFormatter()
                    transcript_text = formatter.format_transcript(transcript.fetch())
                    
                    return f"""
제목: {title}
설명: {description}

내용:
{transcript_text.strip()}
                    """
                else:
                    return f"""
제목: {title}
설명: {description}
※ 자막을 찾을 수 없습니다.
                    """

            except Exception as e:
                error_msg = str(e).lower()
                if "transcript are disabled" in error_msg:
                    return f"""
제목: {title}
설명: {description}
※ 이 동영상은 자막이 비활성화되어 있습니다.
                    """
                elif "no transcript" in error_msg:
                    return f"""
제목: {title}
설명: {description}
※ 이 동영상에는 자막이 없습니다.
                    """
                else:
                    print(f"자막 처리 중 오류: {str(e)}")
                    return f"""
제목: {title}
설명: {description}
※ 자막을 가져오는 중 오류가 발생했습니다.
                    """

        except Exception as e:
            print(f"전체 처리 중 오류: {str(e)}")
            return "유튜브 동영상 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."

    @staticmethod
    def process_website(url):
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            # 메타 태그와 주요 콘텐츠 추출
            text = ""
            if soup.title:
                text += f"제목: {soup.title.string}\n\n"
            
            # 주요 콘텐츠 영역에서 텍스트 추출
            for tag in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                text += f"{tag.get_text()}\n"
            
            return text.strip()
        except Exception as e:
            return f"웹사이트 처리 중 오류가 발생했습니다: {str(e)}" 