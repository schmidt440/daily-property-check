import os
import openai
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Read environment variables (these will be set in GitHub Actions secrets)
openai.api_key = os.getenv("OPENAI_API_KEY")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")

def fetch_new_properties():
    """
    Fetch new property listings.
    Replace this dummy data with a call to an actual API if desired.
    """
    return [
        {
            "city": "Indianapolis, IN",
            "sqft": 1600,
            "beds": 3,
            "baths": 2,
            "price": 150000,
            "rental_yield": 9.5,
            "vacancy_rate": 6,
            "economic_growth": 8,
            "population_trend": 8,
            "local_amenities": 8,
            "landlord_friendly": True,
            "future_development": 8,
            "url": "http://example.com/property1"
        },
        # Add more properties or integrate with a real data source
    ]

def analyze_property(property_data):
    """
    Use ChatGPT (gpt-3.5-turbo) to analyze the property.
    We look for a line starting with 'Score:' in the response.
    """
    prompt = f"""
You are a real estate investment analyst. Based on the following property details, 
determine if this property is a great value for rental investment given these criteria:
- Economic & Job Growth
- Population Trends
- Affordability vs. Rental Yield
- Vacancy Rates & Tenant Demand
- Local Amenities & Infrastructure
- Regulatory Environment (landlord friendly, easy eviction)
- Future Development

Property Details:
City: {property_data['city']}
Square Footage: {property_data['sqft']}
Beds: {property_data['beds']}
Baths: {property_data['baths']}
Price: ${property_data['price']}
Estimated Rental Yield: {property_data['rental_yield']}%
Vacancy Rate: {property_data['vacancy_rate']}%
Economic Growth Score: {property_data['economic_growth']} (scale 1-10)
Population Trend Score: {property_data['population_trend']} (scale 1-10)
Local Amenities Score: {property_data['local_amenities']} (scale 1-10)
Future Development Score: {property_data['future_development']} (scale 1-10)
Landlord Friendly: {'Yes' if property_data['landlord_friendly'] else 'No'}

Please provide a brief analysis and then output a final score on a scale of 1 to 10,
where 10 is the best investment opportunity. 
Include the score in a line starting with "Score:".
"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful real estate investment analyst."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.5,
        )
        return response.choices[0].message['content']
    except Exception as e:
        return f"Error analyzing property: {e}"

def select_best_properties(properties):
    """
    For each property, we parse the ChatGPT analysis,
    look for a "Score:" line, and keep only properties with score >= 8.
    """
    best_props = []
    for prop in properties:
        analysis = analyze_property(prop)
        if not analysis:
            continue
        
        score = None
        for line in analysis.splitlines():
            if "Score:" in line:
                try:
                    # e.g., "Score: 8.5" or "Score: 9"
                    score_str = line.split("Score:")[-1].strip().split("/")[0]
                    score = float(score_str)
                except:
                    pass
        
        if score is not None and score >= 8:
            prop["analysis"] = analysis
            prop["score"] = score
            best_props.append(prop)
    return best_props

def send_email(best_properties):
    """
    Sends an email summarizing the best properties found.
    Returns a string indicating success or error.
    """
    if not best_properties:
        return "No best properties found today."
    
    subject = "Daily Best Property Investments"
    body = "Hello,\n\nHere are the top property investment opportunities for today:\n\n"
    
    for prop in best_properties:
        body += f"City: {prop['city']}\n"
        body += f"Price: ${prop['price']}\n"
        body += f"Beds: {prop['beds']}, Baths: {prop['baths']}, Sqft: {prop['sqft']}\n"
        body += f"Analysis Score: {prop.get('score', 'N/A')}\n"
        body += f"Analysis: {prop.get('analysis', '').strip()}\n"
        body += f"More info: {prop.get('url', '')}\n"
        body += "-------------------------\n\n"
    
    body += "Happy Investing!\n"
    
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, RECIPIENT_EMAIL, msg.as_string())
        return "Email sent successfully!"
    except Exception as e:
        return f"Error sending email: {e}"

def main():
    properties = fetch_new_properties()
    best_props = select_best_properties(properties)
    result = send_email(best_props)
    print(result)

if __name__ == "__main__":
    main()

