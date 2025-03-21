import os
import openai
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Read environment variables (set in GitHub Actions Secrets)
openai.api_key = os.getenv("OPENAI_API_KEY")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")

def fetch_new_properties():
    """
    Fetch new property listings.
    For this example, we use dummy data across several cities.
    """
    properties = [
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
        {
            "city": "Memphis, TN",
            "sqft": 1500,
            "beds": 3,
            "baths": 2,
            "price": 140000,
            "rental_yield": 10,
            "vacancy_rate": 5,
            "economic_growth": 7,
            "population_trend": 7,
            "local_amenities": 7,
            "landlord_friendly": True,
            "future_development": 8,
            "url": "http://example.com/property2"
        },
        {
            "city": "Kansas City, MO",
            "sqft": 1600,
            "beds": 3,
            "baths": 2,
            "price": 145000,
            "rental_yield": 8.5,
            "vacancy_rate": 6,
            "economic_growth": 8,
            "population_trend": 7,
            "local_amenities": 8,
            "landlord_friendly": True,
            "future_development": 8,
            "url": "http://example.com/property3"
        },
        {
            "city": "Detroit, MI",
            "sqft": 1100,  # Below minimum sqft
            "beds": 3,
            "baths": 2,
            "price": 130000,
            "rental_yield": 10,
            "vacancy_rate": 9,
            "economic_growth": 6,
            "population_trend": 6,
            "local_amenities": 7,
            "landlord_friendly": True,
            "future_development": 7,
            "url": "http://example.com/property4"
        },
        {
            "city": "Cleveland, OH",
            "sqft": 1400,
            "beds": 2,  # Below minimum beds
            "baths": 2,
            "price": 120000,
            "rental_yield": 8,
            "vacancy_rate": 7,
            "economic_growth": 6,
            "population_trend": 6,
            "local_amenities": 7,
            "landlord_friendly": True,
            "future_development": 7,
            "url": "http://example.com/property5"
        }
    ]
    return properties

def filter_properties(properties):
    """
    Filter properties based on minimum criteria:
      - At least 1200 sqft
      - At least 3 bedrooms
      - At least 2 bathrooms
      - Price under $200,000
    """
    filtered = []
    for prop in properties:
        if prop["sqft"] >= 1200 and prop["beds"] >= 3 and prop["baths"] >= 2 and prop["price"] < 200000:
            filtered.append(prop)
    return filtered

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
    Then we sort the properties by score in descending order.
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
                    score_str = line.split("Score:")[-1].strip().split("/")[0]
                    score = float(score_str)
                except:
                    pass
        
        if score is not None and score >= 8:
            prop["analysis"] = analysis
            prop["score"] = score
            best_props.append(prop)
    
    # Sort highest scoring properties at the top
    best_props.sort(key=lambda x: x["score"], reverse=True)
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
    # Fetch all dummy properties
    properties = fetch_new_properties()
    # Filter based on our criteria: at least 1200 sqft, 3 beds, 2 baths, and under $200k
    filtered_properties = filter_properties(properties)
    # Analyze and select best properties (only those scoring >= 8)
    best_props = select_best_properties(filtered_properties)
    # Send an email with the results
    result = send_email(best_props)
    print(result)

if __name__ == "__main__":
    main()
