# Reddit User Persona Analyser

A comprehensive tool that analyzes Reddit user profiles to create detailed user personas using AI/LLM analysis. This tool scrapes a user's posts and comments, then uses natural language processing to identify patterns in communication style, interests, values, and behavior.

## Features

- **Automated Reddit Scraping**: Extracts posts and comments from any public Reddit profile
- **AI-Powered Analysis**: Uses Groq's LLM to analyze content and generate detailed personas
- **Comprehensive Reports**: Creates detailed persona reports with citations and sources
- **Easy to Use**: Simple command-line interface with clear prompts
- **Privacy Focused**: Only analyzes publicly available Reddit content

## Prerequisites

- Python 3.7 or higher
- Groq API key (free tier available)
- Internet connection for Reddit scraping and LLM analysis

## Installation

### Step 1: Clone or Download the Script

Save the Python script as `reddit_persona_analyzer.py` in your desired directory.

### Step 2: Install Required Dependencies

Open your terminal/command prompt and run:

```bash
pip install python-dotenv requests beautifulsoup4 langchain langchain-community langchain-groq pydantic
```

### Step 3: Get Your Groq API Key

1. Visit [Groq Console](https://console.groq.com/)
2. Sign up for a free account
3. Navigate to the API Keys section
4. Create a new API key
5. Copy the API key for the next step

### Step 4: Set Up Environment Variables

Create a `.env` file in the same directory as your script:

```env
GROQ_API_KEY=your_groq_api_key_here
```

Replace `your_groq_api_key_here` with your actual Groq API key.

**Alternative method**: You can also set the environment variable directly:

**On Windows:**
```cmd
set GROQ_API_KEY=your_groq_api_key_here
```

**On macOS/Linux:**
```bash
export GROQ_API_KEY=your_groq_api_key_here
```

## Usage

### Running the Script

1. Open your terminal/command prompt
2. Navigate to the directory containing the script
3. Run the script:

```bash
python reddit_persona_analyzer.py
```

### Using the Tool

1. **Enter Reddit Profile URL**: When prompted, enter the full Reddit profile URL
   - Format: `https://www.reddit.com/user/username`
   - Example: `https://www.reddit.com/user/johndoe`

2. **Wait for Analysis**: The tool will:
   - Extract the username from the URL
   - Scrape the user's posts and comments
   - Analyze the content using AI
   - Generate a comprehensive persona report

3. **View Results**: The tool will save a detailed report as:
   - `persona_username_YYYYMMDD_HHMMSS.txt`

## Sample Output

The generated report includes:

```
# User Persona Analysis Report
## Reddit User: username
## Generated on: 2024-01-15 14:30:25

---

## User Persona Overview

**Name:** John Doe
**Age Range:** 25-35 years
**Location:** San Francisco, CA
**Occupation:** Software Developer

---

## Detailed Characteristics

### 🎯 Interests & Hobbies
- Programming and software development
- Video games (especially RPGs)
- Cryptocurrency and blockchain technology
- Hiking and outdoor activities

**Sources:**
1. Posted about debugging Python code in r/programming
2. Active discussions in r/gaming about favorite RPG mechanics
3. Multiple posts in r/cryptocurrency about market trends
```

## Configuration Options

You can modify the script behavior by changing these parameters in the `main()` function:

- `max_posts`: Maximum number of posts/comments to analyze (default: 50)
- `max_posts // 2`: Split between posts and comments (25 each by default)

## Troubleshooting

### Common Issues

**1. "GROQ_API_KEY environment variable not set"**
- Solution: Make sure you've created the `.env` file with your API key or set the environment variable

**2. "No posts found. The profile might be private or doesn't exist."**
- Solution: Verify the Reddit profile URL is correct and the profile is public

**3. "Invalid Reddit profile URL"**
- Solution: Ensure the URL format is correct: `https://www.reddit.com/user/username`

**4. Import errors**
- Solution: Install missing dependencies using pip install commands above

**5. Connection errors**
- Solution: Check your internet connection and try again

### Rate Limiting

- Reddit may rate limit requests if you run the script too frequently
- If you encounter rate limiting, wait a few minutes before trying again
- The script includes appropriate delays to minimize rate limiting issues

## Limitations

- Only analyzes public Reddit profiles
- Limited to recent posts/comments (Reddit API limitations)
- Analysis quality depends on the amount and quality of available content
- Requires active internet connection for both scraping and LLM analysis

## Privacy and Ethics

- This tool only accesses publicly available Reddit content
- No personal data is stored beyond the generated report
- Users should respect Reddit's terms of service and user privacy
- Consider the ethical implications of analyzing user content

## API Costs

- Groq offers a generous free tier for API usage
- The script is optimized to minimize API calls
- Typical analysis costs less than $0.01 per user profile

## Contributing

Feel free to enhance the script with:
- Additional persona characteristics
- Better error handling
- Support for other social media platforms
- Improved citation methods

## License

This tool is provided as-is for educational and research purposes. Please use responsibly and in accordance with Reddit's terms of service.

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Ensure all dependencies are installed correctly
3. Verify your Groq API key is valid
4. Check that the Reddit profile is public and accessible

---

**Note**: This tool is for educational and research purposes. Always respect user privacy and platform terms of service.
