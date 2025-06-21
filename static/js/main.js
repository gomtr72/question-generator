document.getElementById('questionForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const topic = document.getElementById('topic').value;
    const numQuestions = document.getElementById('numQuestions').value;
    
    try {
        const response = await fetch('/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                topic,
                num_questions: parseInt(numQuestions)
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const questionsDiv = document.getElementById('questions');
            questionsDiv.innerHTML = marked.parse(data.questions);
            document.getElementById('result').style.display = 'block';
        } else {
            alert(data.error || '질문 생성 중 오류가 발생했습니다.');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('질문 생성 중 오류가 발생했습니다.');
    }
}); 