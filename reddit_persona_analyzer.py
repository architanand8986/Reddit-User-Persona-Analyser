import os
import re
import json
import time
import requests
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from langchain.schema import BaseMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field


# Load environment variables
load_dotenv()


@dataclass
class RedditPost:
    """Data class for Reddit post/comment"""
    title: str
    content: str
    subreddit: str
    timestamp: str
    post_type: str
    url: str
    upvotes: int = 0


@dataclass
class Citation:
    """Data class for citation information"""
    content: str
    url: str
    post_type: str
    relevance: str


class UserPersona(BaseModel):
    """Pydantic model for structured user persona output"""
    name: str = Field(description="Inferred or placeholder name")
    age_range: str = Field(description="Estimated age range")
    location: str = Field(description="Geographic location if mentioned")
    occupation: str = Field(description="Job or profession")
    interests: List[str] = Field(description="Main interests and hobbies")
    personality_traits: List[str] = Field(description="Key personality characteristics")
    goals_motivations: List[str] = Field(description="Goals and motivations")
    pain_points: List[str] = Field(description="Challenges and frustrations")
    technology_usage: str = Field(description="Technology comfort level and usage")
    communication_style: str = Field(description="How they communicate online")
    values_beliefs: List[str] = Field(description="Core values and beliefs")
    lifestyle: str = Field(description="General lifestyle description")
    
    
class PersonaWithCitations(BaseModel):
    """User persona with citations for each characteristic"""
    persona: UserPersona
    citations: Dict[str, List[Citation]] = Field(description="Citations for each persona field")


class RedditScraper:
    """Reddit profile scraper"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def extract_username(self, profile_url: str) -> str:
        """Extract username from Reddit profile URL"""
        parsed = urlparse(profile_url)
        path_parts = parsed.path.strip('/').split('/')
        
        if 'user' in path_parts:
            user_index = path_parts.index('user')
            if user_index + 1 < len(path_parts):
                return path_parts[user_index + 1]
        
        raise ValueError("Invalid Reddit profile URL")
    
    def scrape_profile(self, profile_url: str, max_posts: int = 50) -> List[RedditPost]:
        """Scrape Reddit user profile for posts and comments"""
        username = self.extract_username(profile_url)
        posts = []
        
        try:
            # Scrape submitted posts
            posts.extend(self._scrape_posts(username, max_posts // 2))
            
            # Scrape comments
            posts.extend(self._scrape_comments(username, max_posts // 2))
            
        except Exception as e:
            print(f"Error scraping profile: {e}")
            
        return posts
    
    def _scrape_posts(self, username: str, max_posts: int) -> List[RedditPost]:
        """Scrape user's submitted posts"""
        posts = []
        url = f"https://www.reddit.com/user/{username}/submitted.json"
        
        try:
            response = self.session.get(url)
            if response.status_code == 200:
                data = response.json()
                
                for post_data in data.get('data', {}).get('children', [])[:max_posts]:
                    post = post_data.get('data', {})
                    
                    reddit_post = RedditPost(
                        title=post.get('title', ''),
                        content=post.get('selftext', ''),
                        subreddit=post.get('subreddit', ''),
                        timestamp=datetime.fromtimestamp(post.get('created_utc', 0)).isoformat(),
                        post_type='post',
                        url=f"https://www.reddit.com{post.get('permalink', '')}",
                        upvotes=post.get('ups', 0)
                    )
                    posts.append(reddit_post)
                    
        except Exception as e:
            print(f"Error scraping posts: {e}")
            
        return posts
    
    def _scrape_comments(self, username: str, max_comments: int) -> List[RedditPost]:
        """Scrape user's comments"""
        comments = []
        url = f"https://www.reddit.com/user/{username}/comments.json"
        
        try:
            response = self.session.get(url)
            if response.status_code == 200:
                data = response.json()
                
                for comment_data in data.get('data', {}).get('children', [])[:max_comments]:
                    comment = comment_data.get('data', {})
                    
                    reddit_comment = RedditPost(
                        title=f"Comment in r/{comment.get('subreddit', '')}",
                        content=comment.get('body', ''),
                        subreddit=comment.get('subreddit', ''),
                        timestamp=datetime.fromtimestamp(comment.get('created_utc', 0)).isoformat(),
                        post_type='comment',
                        url=f"https://www.reddit.com{comment.get('permalink', '')}",
                        upvotes=comment.get('ups', 0)
                    )
                    comments.append(reddit_comment)
                    
        except Exception as e:
            print(f"Error scraping comments: {e}")
            
        return comments


class PersonaAnalyzer:
    """LLM-based persona analyzer using Groq"""
    
    def __init__(self):
        self.llm = ChatGroq(
            groq_api_key=os.getenv('GROQ_API_KEY'),
            model_name="llama3-70b-8192",
            temperature=0.1
        )
        
    def analyze_persona(self, posts: List[RedditPost], username: str) -> PersonaWithCitations:
        """Analyze Reddit posts to create user persona with citations"""
        
        # Prepare content for analysis
        content_summary = self._prepare_content_summary(posts)
        
        # Create persona analysis prompt
        persona_prompt = self._create_persona_prompt(content_summary, username)
        
        # Get persona analysis
        persona_response = self.llm.invoke([HumanMessage(content=persona_prompt)])
        
        # Parse persona from response
        persona = self._parse_persona_response(persona_response.content)
        
        # Generate citations for each persona field
        citations = self._generate_citations(persona, posts)
        
        return PersonaWithCitations(
            persona=persona,
            citations=citations
        )
    
    def _prepare_content_summary(self, posts: List[RedditPost]) -> str:
        """Prepare content summary for LLM analysis"""
        summary = []
        
        for i, post in enumerate(posts[:30]):  # Limit to avoid token limits
            summary.append(
                f"Post {i+1} ({post.post_type}):\n"
                f"Subreddit: r/{post.subreddit}\n"
                f"Title: {post.title}\n"
                f"Content: {post.content[:500]}...\n"
                f"Timestamp: {post.timestamp}\n"
                f"---\n"
            )
            
        return "\n".join(summary)
    
    def _create_persona_prompt(self, content_summary: str, username: str) -> str:
        """Create comprehensive persona analysis prompt"""
        return f"""
        You are an expert user researcher analyzing Reddit user data to create a comprehensive user persona.
        
        Analyze the following Reddit posts and comments from user '{username}' and create a detailed user persona.
        
        REDDIT CONTENT:
        {content_summary}
        
        Based on this content, create a comprehensive user persona including:
        
        1. **Name**: Use the Reddit username or create a realistic placeholder name
        2. **Age Range**: Estimate based on language, interests, and references
        3. **Location**: Any geographic indicators mentioned
        4. **Occupation**: Job or profession mentioned or inferred
        5. **Interests**: Main hobbies, interests, and activities
        6. **Personality Traits**: Key personality characteristics observed
        7. **Goals & Motivations**: What drives this person
        8. **Pain Points**: Challenges, frustrations, complaints mentioned
        9. **Technology Usage**: Comfort level with technology and digital tools
        10. **Communication Style**: How they express themselves online
        11. **Values & Beliefs**: Core principles and beliefs expressed
        12. **Lifestyle**: General lifestyle and habits
        
        Format your response as a valid JSON object with these exact keys:
        {{
            "name": "string",
            "age_range": "string", 
            "location": "string",
            "occupation": "string",
            "interests": ["array", "of", "strings"],
            "personality_traits": ["array", "of", "strings"],
            "goals_motivations": ["array", "of", "strings"],
            "pain_points": ["array", "of", "strings"],
            "technology_usage": "string",
            "communication_style": "string", 
            "values_beliefs": ["array", "of", "strings"],
            "lifestyle": "string"
        }}
        
        IMPORTANT: Return ONLY the JSON object, no additional text or explanation.
        Be specific and evidence-based. If information isn't available, use "Not specified" or make reasonable inferences marked as "(inferred)".
        """
    
    def _parse_persona_response(self, response: str) -> UserPersona:
        """Parse LLM response into UserPersona object"""
        try:
            # Clean the response to extract JSON
            response = response.strip()
            
            # Find JSON boundaries more carefully
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No valid JSON found in response")
            
            json_str = response[start_idx:end_idx]
            
            # Try to fix common JSON issues
            json_str = re.sub(r',\s*}', '}', json_str)  # Remove trailing commas
            json_str = re.sub(r',\s*]', ']', json_str)  # Remove trailing commas in arrays
            
            persona_data = json.loads(json_str)
            
            # Ensure all required fields are present with defaults
            defaults = {
                "name": "Unknown User",
                "age_range": "Not specified",
                "location": "Not specified", 
                "occupation": "Not specified",
                "interests": ["Not specified"],
                "personality_traits": ["Not specified"],
                "goals_motivations": ["Not specified"],
                "pain_points": ["Not specified"],
                "technology_usage": "Not specified",
                "communication_style": "Not specified",
                "values_beliefs": ["Not specified"],
                "lifestyle": "Not specified"
            }
            
            # Merge with defaults
            for key, default_value in defaults.items():
                if key not in persona_data or not persona_data[key]:
                    persona_data[key] = default_value
            
            return UserPersona(**persona_data)
            
        except Exception as e:
            print(f"Error parsing persona response: {e}")
            print(f"Raw response: {response[:500]}...")
            
            # Return default persona
            return UserPersona(
                name="Unknown User",
                age_range="Not specified",
                location="Not specified",
                occupation="Not specified",
                interests=["Not specified"],
                personality_traits=["Not specified"],
                goals_motivations=["Not specified"],
                pain_points=["Not specified"],
                technology_usage="Not specified",
                communication_style="Not specified",
                values_beliefs=["Not specified"],
                lifestyle="Not specified"
            )
    
    def _generate_citations(self, persona: UserPersona, posts: List[RedditPost]) -> Dict[str, List[Citation]]:
        """Generate citations for each persona characteristic"""
        citations = {}
        
        # Define persona fields to cite
        persona_fields = [
            'age_range', 'location', 'occupation', 'interests',
            'personality_traits', 'goals_motivations', 'pain_points',
            'technology_usage', 'communication_style', 'values_beliefs', 'lifestyle'
        ]
        
        for field in persona_fields:
            field_value = getattr(persona, field)
            if field_value and field_value != "Not specified":
                citations[field] = self._find_relevant_posts(field, field_value, posts)
        
        return citations
    
    def _find_relevant_posts(self, field: str, field_value, posts: List[RedditPost]) -> List[Citation]:
        """Find posts relevant to a specific persona field"""
        relevant_posts = []
        
        # Create field-specific search prompt
        search_prompt = f"""
        Find Reddit posts/comments that support this persona characteristic:
        Field: {field}
        Value: {field_value}
        
        From these posts, identify the most relevant ones:
        
        {self._prepare_content_summary(posts[:10])}
        
        Return the post numbers (1-based) that best support this characteristic.
        Format: Just list the numbers separated by commas (e.g., "1, 3, 5")
        """
        
        try:
            response = self.llm.invoke([HumanMessage(content=search_prompt)])
            relevant_indices = [int(x.strip()) - 1 for x in response.content.split(',') if x.strip().isdigit()]
            
            for idx in relevant_indices[:3]:  # Max 3 citations per field
                if 0 <= idx < len(posts):
                    post = posts[idx]
                    citation = Citation(
                        content=f"{post.title}: {post.content[:200]}...",
                        url=post.url,
                        post_type=post.post_type,
                        relevance=f"Supports {field}: {field_value}"
                    )
                    relevant_posts.append(citation)
                    
        except Exception as e:
            print(f"Error finding relevant posts for {field}: {e}")
            
        return relevant_posts


class PersonaReportGenerator:
    """Generate formatted persona report"""
    
    def generate_report(self, persona_data: PersonaWithCitations, username: str) -> str:
        """Generate comprehensive persona report"""
        
        report = f"""
# User Persona Analysis Report
## Reddit User: {username}
## Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## User Persona Overview

**Name:** {persona_data.persona.name}
**Age Range:** {persona_data.persona.age_range}
**Location:** {persona_data.persona.location}
**Occupation:** {persona_data.persona.occupation}

---

## Detailed Characteristics

### 🎯 Interests & Hobbies
{self._format_list(persona_data.persona.interests)}

{self._format_citations('interests', persona_data.citations)}

### 🧠 Personality Traits
{self._format_list(persona_data.persona.personality_traits)}

{self._format_citations('personality_traits', persona_data.citations)}

### 🎯 Goals & Motivations
{self._format_list(persona_data.persona.goals_motivations)}

{self._format_citations('goals_motivations', persona_data.citations)}

### 😤 Pain Points & Frustrations
{self._format_list(persona_data.persona.pain_points)}

{self._format_citations('pain_points', persona_data.citations)}

### 💻 Technology Usage
{persona_data.persona.technology_usage}

{self._format_citations('technology_usage', persona_data.citations)}

### 💬 Communication Style
{persona_data.persona.communication_style}

{self._format_citations('communication_style', persona_data.citations)}

### 💝 Values & Beliefs
{self._format_list(persona_data.persona.values_beliefs)}

{self._format_citations('values_beliefs', persona_data.citations)}

### 🏠 Lifestyle
{persona_data.persona.lifestyle}

{self._format_citations('lifestyle', persona_data.citations)}

---

## Summary

This persona was generated by analyzing Reddit posts and comments from user {username}. 
The analysis used natural language processing to identify patterns in communication style,
interests, values, and behavior to create a comprehensive user profile.

**Analysis Date:** {datetime.now().strftime('%Y-%m-%d')}
**Total Posts Analyzed:** Varied based on available data
**Confidence Level:** Based on available Reddit activity
"""
        
        return report
    
    def _format_list(self, items: List[str]) -> str:
        """Format list items for report"""
        if not items or (len(items) == 1 and items[0] == "Not specified"):
            return "- Not specified or insufficient data"
        
        return "\n".join([f"- {item}" for item in items])
    
    def _format_citations(self, field: str, citations: Dict[str, List[Citation]]) -> str:
        """Format citations for a specific field"""
        if field not in citations or not citations[field]:
            return "\n**Sources:** No specific citations available\n"
        
        citation_text = "\n**Sources:**\n"
        for i, citation in enumerate(citations[field], 1):
            citation_text += f"{i}. {citation.content}\n"
            citation_text += f"   Source: {citation.url}\n"
            citation_text += f"   Type: {citation.post_type}\n\n"
        
        return citation_text


def main():
    """Main function to run the persona analysis"""
    
    # Check for required environment variables
    if not os.getenv('GROQ_API_KEY'):
        print("Error: GROQ_API_KEY environment variable not set")
        return
    
    # Get user input
    profile_url = input("Enter Reddit profile URL: ").strip()
    
    if not profile_url:
        print("Error: No profile URL provided")
        return
    
    try:
        # Initialize components
        scraper = RedditScraper()
        analyzer = PersonaAnalyzer()
        report_generator = PersonaReportGenerator()
        
        # Extract username
        username = scraper.extract_username(profile_url)
        print(f"Analyzing profile for user: {username}")
        
        # Scrape Reddit profile
        print("Scraping Reddit profile...")
        posts = scraper.scrape_profile(profile_url)
        
        if not posts:
            print("Error: No posts found. The profile might be private or doesn't exist.")
            return
        
        print(f"Found {len(posts)} posts and comments")
        
        # Analyze persona
        print("Analyzing persona with LLM...")
        persona_data = analyzer.analyze_persona(posts, username)
        
        # Generate report
        print("Generating persona report...")
        report = report_generator.generate_report(persona_data, username)
        
        # Save report to file
        output_filename = f"persona_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"Persona report saved to: {output_filename}")
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()