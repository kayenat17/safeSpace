document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('questionnaire-form');
    if (form) {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(form);
            const data = {
                relationship_type: formData.get('relationship_type'),
                person_name: formData.get('person_name'),
                responses: []
            };
            
            // Collect all responses
            const questions = document.querySelectorAll('.question-card');
            console.log('Found questions:', questions.length);
            
            questions.forEach((question, index) => {
                const radioInput = question.querySelector('input[type="radio"]:checked');
                const textareaInput = question.querySelector('textarea');
                
                if (radioInput) {
                    data.responses.push(radioInput.value);
                    console.log(`Question ${index + 1}: Radio selected - ${radioInput.value}`);
                } else if (textareaInput) {
                    data.responses.push(textareaInput.value);
                    console.log(`Question ${index + 1}: Textarea - ${textareaInput.value}`);
                } else {
                    data.responses.push(''); // Add empty string for unanswered questions
                    console.log(`Question ${index + 1}: No input found`);
                }
            });
            
            console.log('Collected data:', data);
            
            try {
                const response = await fetch('/pinging/analyze', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                });
                
                if (response.ok) {
                    const analysis = await response.json();
                    displayResults(analysis);
                } else {
                    const errorData = await response.json();
                    throw new Error(errorData.error || 'Analysis failed');
                }
            } catch (error) {
                console.error('Error details:', error);
                console.error('Error message:', error.message);
                console.error('Error stack:', error.stack);
                alert(`Error: ${error.message || 'An error occurred while analyzing the relationship. Please try again.'}`);
            }
        });
    }
});

function displayResults(analysis) {
    // Create results container
    const resultsContainer = document.createElement('div');
    resultsContainer.className = 'results-container';
    
    // Create card
    const card = document.createElement('div');
    card.className = 'card';
    
    // Add title
    const title = document.createElement('h2');
    title.textContent = 'Relationship Analysis Results';
    card.appendChild(title);
    
    // Add score section
    const scoreSection = document.createElement('div');
    scoreSection.className = 'score-section';
    
    const scoreTitle = document.createElement('h3');
    scoreTitle.textContent = 'Overall Score';
    scoreSection.appendChild(scoreTitle);
    
    const scoreDisplay = document.createElement('div');
    scoreDisplay.className = 'score-display';
    
    const scoreCircle = document.createElement('div');
    scoreCircle.className = 'score-circle';
    scoreCircle.style.background = `linear-gradient(to right, var(--primary-color) ${analysis.overall_score * 20}%, #e9ecef ${analysis.overall_score * 20}%)`;
    
    const scoreValue = document.createElement('span');
    scoreValue.textContent = analysis.overall_score.toFixed(1);
    scoreCircle.appendChild(scoreValue);
    
    const scoreLabel = document.createElement('p');
    scoreLabel.className = 'score-label';
    scoreLabel.textContent = 'out of 5';
    
    scoreDisplay.appendChild(scoreCircle);
    scoreDisplay.appendChild(scoreLabel);
    scoreSection.appendChild(scoreDisplay);
    card.appendChild(scoreSection);
    
    // Add strengths section
    if (analysis.strengths && analysis.strengths.length > 0) {
        const strengthsSection = createAnalysisSection('Strengths', analysis.strengths, 'strengths');
        card.appendChild(strengthsSection);
    }
    
    // Add weaknesses section
    if (analysis.weaknesses && analysis.weaknesses.length > 0) {
        const weaknessesSection = createAnalysisSection('Areas for Improvement', analysis.weaknesses, 'weaknesses');
        card.appendChild(weaknessesSection);
    }
    
    // Add recommendations section
    if (analysis.recommendations && analysis.recommendations.length > 0) {
        const recommendationsSection = createAnalysisSection('Recommendations', analysis.recommendations, 'recommendations');
        card.appendChild(recommendationsSection);
    }
    
    // Add insights section
    if (analysis.insights && analysis.insights.length > 0) {
        const insightsSection = createAnalysisSection('Additional Insights', analysis.insights, 'insights');
        card.appendChild(insightsSection);
    }
    
    // Add action buttons
    const actionButtons = document.createElement('div');
    actionButtons.className = 'action-buttons';
    
    const newAnalysisBtn = document.createElement('a');
    newAnalysisBtn.href = '/pinging/questionnaire';
    newAnalysisBtn.className = 'btn btn-secondary';
    newAnalysisBtn.textContent = 'Take Another Analysis';
    
    const homeBtn = document.createElement('a');
    homeBtn.href = '/pinging/';
    homeBtn.className = 'btn btn-primary';
    homeBtn.textContent = 'Return Home';
    
    actionButtons.appendChild(newAnalysisBtn);
    actionButtons.appendChild(homeBtn);
    card.appendChild(actionButtons);
    
    // Add results to page
    resultsContainer.appendChild(card);
    
    // Replace form with results
    const form = document.getElementById('questionnaire-form');
    form.parentNode.replaceChild(resultsContainer, form);
}

function createAnalysisSection(title, items, className) {
    const section = document.createElement('div');
    section.className = `analysis-section ${className}`;
    
    const sectionTitle = document.createElement('h3');
    sectionTitle.textContent = title;
    section.appendChild(sectionTitle);
    
    const list = document.createElement('ul');
    items.forEach(item => {
        const listItem = document.createElement('li');
        listItem.textContent = item;
        list.appendChild(listItem);
    });
    
    section.appendChild(list);
    return section;
} 