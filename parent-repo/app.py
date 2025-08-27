import os
os.environ['FLASK_SKIP_DOTENV'] = '1'

from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests

# Create templates directory if it doesn't exist
os.makedirs('templates', exist_ok=True)

app = Flask(__name__)
CORS(app)

class StockAnalyzer:
    def __init__(self):
        self.news_api_key = 'demo_key'
        # Use environment variable for API key in production
        self.openai_api_key = os.environ.get('OPENAI_API_KEY', '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')
    
    # ... rest of your existing code stays the same ...
    def get_stock_data(self, symbol):
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period="1y")
            info = stock.info
            
            return {
                'symbol': symbol,
                'name': info.get('longName', 'N/A'),
                'current_price': info.get('currentPrice', hist['Close'][-1] if len(hist) > 0 else 0),
                'change': info.get('regularMarketChangePercent', 0),
                'volume': info.get('volume', 0),
                'market_cap': info.get('marketCap', 'N/A'),
                'pe_ratio': info.get('trailingPE', 'N/A'),
                'dividend_yield': info.get('dividendYield', 0),
                'historical_data': hist.tail(30).to_dict('records') if len(hist) > 0 else []
            }
        except Exception as e:
            return {'error': str(e)}
    
    def analyze_stock(self, symbol):
        stock_data = self.get_stock_data(symbol)
        if 'error' in stock_data:
            return stock_data
            
        # Enhanced AI-like analysis
        price = stock_data['current_price']
        change = stock_data['change']
        volume = stock_data['volume']
        pe_ratio = stock_data['pe_ratio']
        
        # Multi-factor scoring system
        score = 50  # Base score
        factors = []
        
        # Price momentum analysis
        if change > 5:
            score += 25
            sentiment = "🚀 Strong Buy"
            analysis = "Excellent momentum! Stock showing strong upward trend with great buying opportunity."
            factors.append("Strong positive momentum (+5%)")
        elif change > 0:
            score += 15
            sentiment = "📈 Buy"
            analysis = "Positive trend detected. Good entry point for investors."
            factors.append("Positive price movement")
        elif change > -5:
            score += 5
            sentiment = "⚖️ Hold"
            analysis = "Neutral market conditions. Monitor for trend changes."
            factors.append("Stable price action")
        else:
            score -= 15
            sentiment = "📉 Sell"
            analysis = "Downward trend detected. Consider risk management strategies."
            factors.append("Negative price momentum")
        
        # Volume analysis
        if volume > 1000000:
            score += 10
            factors.append("High trading volume (strong interest)")
        elif volume > 100000:
            score += 5
            factors.append("Moderate trading activity")
        
        # Valuation analysis
        if isinstance(pe_ratio, (int, float)) and pe_ratio > 0:
            if pe_ratio < 15:
                score += 10
                factors.append("Attractive valuation (low P/E)")
            elif pe_ratio < 25:
                score += 5
                factors.append("Fair valuation")
            else:
                score -= 5
                factors.append("High valuation (expensive)")
        
        # Risk assessment
        risk_level = 'Low' if score >= 70 else 'Medium' if score >= 50 else 'High'
        
        return {
            'symbol': symbol,
            'sentiment': sentiment,
            'analysis': analysis,
            'factors': factors,
            'score': max(0, min(100, score)),
            'recommendation': f"Based on comprehensive analysis: {sentiment.split(' ')[1].lower()} recommendation.",
            'confidence': min(95, abs(change) * 8 + 65),
            'risk_level': risk_level
        }
    
    def get_news(self, symbol):
        # Fallback news since we removed the API dependency
        return [
            {
                'title': f'{symbol} Market Analysis Update',
                'description': f'Stay updated with the latest {symbol} market trends, financial performance, and investment insights.',
                'url': f'https://finance.yahoo.com/quote/{symbol}/news',
                'publishedAt': datetime.now().isoformat()
            },
            {
                'title': f'{symbol} Stock Performance Review',
                'description': 'Monitor key financial metrics, technical indicators, and market sentiment for informed investment decisions.',
                'url': f'https://finance.yahoo.com/quote/{symbol}',
                'publishedAt': datetime.now().isoformat()
            },
            {
                'title': f'{symbol} Investment Research',
                'description': 'Access professional analysis, earnings reports, and market commentary from financial experts.',
                'url': f'https://finance.yahoo.com/quote/{symbol}/analysis',
                'publishedAt': datetime.now().isoformat()
            }
        ]
    
    def get_ai_response(self, user_message, stock_context=None):
        """Get AI response using OpenRouter API"""
        try:
            headers = {
                'Authorization': f'Bearer {self.openai_api_key}',
                'Content-Type': 'application/json',
                'HTTP-Referer': os.environ.get('FLASK_HOST', 'http://localhost:5000'),
                'X-Title': 'MACRA Market Analyzer'
            }
            
            # Create context-aware system message
            system_message = """You are MACRA AI, an expert financial advisor and stock market analyst. You help users understand stock investing, market trends, and financial concepts in simple, beginner-friendly terms. 

Key guidelines:
- Provide clear, educational responses about stocks and investing
- Use emojis to make responses engaging  
- Always remind users that this is not financial advice
- Focus on educational content and risk awareness
- Be encouraging but realistic about investing risks
- Keep responses concise and easy to understand
- If asked about specific stocks, provide educational analysis based on general market principles

You are integrated into the MACRA Market Analyzer platform that provides real-time stock data and AI analysis."""
            
            # Add stock context if provided
            if stock_context:
                system_message += f"\n\nCurrent stock context: {stock_context}"
            
            # Try different model options in case one fails
            models_to_try = [
                "meta-llama/llama-3.1-8b-instruct:free",
                "microsoft/phi-3-mini-128k-instruct:free", 
                "google/gemma-2-9b-it:free"
            ]
            
            for model in models_to_try:
                try:
                    data = {
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_message},
                            {"role": "user", "content": user_message}
                        ],
                        "max_tokens": 400,
                        "temperature": 0.7
                    }
                    
                    response = requests.post(
                        'https://openrouter.ai/api/v1/chat/completions',
                        headers=headers,
                        json=data,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if 'choices' in result and len(result['choices']) > 0:
                            return result['choices'][0]['message']['content']
                    elif response.status_code == 429:
                        continue  # Try next model if rate limited
                    else:
                        print(f"API Error {response.status_code}: {response.text}")
                        continue
                        
                except requests.exceptions.RequestException as e:
                    print(f"Request error with model {model}: {str(e)}")
                    continue
            
            # If all models fail, return a helpful fallback response
            return self.get_fallback_response(user_message, stock_context)
                
        except Exception as e:
            print(f"AI Response Error: {str(e)}")
            return self.get_fallback_response(user_message, stock_context)
    
    def get_fallback_response(self, user_message, stock_context=None):
        """Provide intelligent fallback responses when AI API is unavailable"""
        message_lower = user_message.lower()
        
        # Stock-specific questions
        if any(word in message_lower for word in ['buy', 'sell', 'invest', 'good stock']):
            return """📈 Great question! When evaluating any stock, consider these key factors:

• **Financial Health**: Look at revenue growth, profit margins, and debt levels
• **Valuation**: Check if the P/E ratio is reasonable compared to competitors  
• **Market Position**: Strong brand, competitive advantages
• **Future Prospects**: Growth potential in their industry

💡 **Remember**: This is educational content, not financial advice. Always do your own research and consider consulting a financial advisor!

🔍 Use our analyzer above to get detailed metrics and AI scoring for any stock."""

        # P/E ratio questions
        elif 'p/e' in message_lower or 'pe ratio' in message_lower or 'price to earnings' in message_lower:
            return """📊 **P/E Ratio Explained Simply:**

The Price-to-Earnings ratio compares a stock's price to its annual earnings per share.

• **Low P/E (under 15)**: Potentially undervalued, but verify why
• **Medium P/E (15-25)**: Generally fair valuation  
• **High P/E (over 25)**: May be overvalued or high-growth company

💡 **Example**: If a stock costs $100 and earns $5 per share annually, P/E = 20

⚠️ **Tip**: Compare P/E ratios within the same industry for better context!"""

        # Risk questions
        elif any(word in message_lower for word in ['risk', 'safe', 'dangerous']):
            return """🛡️ **Stock Investment Risks:**

• **Market Risk**: Prices fluctuate with overall market conditions
• **Company Risk**: Business-specific challenges or failures
• **Sector Risk**: Industry-wide problems (tech crash, oil prices)
• **Inflation Risk**: Purchasing power erosion over time

🎯 **Risk Management Tips**:
• Diversify across different stocks and sectors
• Only invest money you can afford to lose
• Start small and learn gradually
• Consider your time horizon

📊 Our AI analysis includes risk assessment for each stock!"""

        # Beginner questions
        elif any(word in message_lower for word in ['beginner', 'start', 'how to', 'new']):
            return """🌟 **Getting Started with Stock Investing:**

**Step 1**: Learn the basics (you're doing great! 📚)
**Step 2**: Open a brokerage account with reputable firms
**Step 3**: Start with index funds or blue-chip stocks
**Step 4**: Invest regularly, not just once

💡 **Beginner-Friendly Stocks**: Look for established companies like:
• Apple (AAPL) • Microsoft (MSFT) • Google (GOOGL)

⚠️ **Golden Rule**: Never invest more than you can afford to lose!

🚀 Try analyzing these stocks with our tool above!"""

        # Market trend questions  
        elif any(word in message_lower for word in ['market', 'trend', 'economy']):
            return """📈 **Understanding Market Trends:**

• **Bull Market**: Prices rising, investor confidence high 🐂
• **Bear Market**: Prices falling 20%+ from highs 🐻  
• **Correction**: 10-20% decline, often healthy

🔍 **Key Indicators to Watch**:
• Economic data (GDP, employment, inflation)
• Company earnings reports
• Federal Reserve policy changes
• Global events and sentiment

💡 **Pro Tip**: Focus on long-term investing rather than trying to time the market!"""

        # Default response with stock context
        elif stock_context:
            return f"""🤖 I'm here to help with stock and investing questions! 

📊 **Current Analysis Context**: {stock_context}

💭 **Ask me about:**
• How to interpret the analysis results
• What the risk level means
• Investment strategies for beginners
• How to use P/E ratios and other metrics

🚀 What specific aspect of investing would you like to learn about?"""

        # General fallback
        else:
            return """🤖 Hi! I'm your MACRA AI assistant, here to help you learn about stocks and investing! 

💡 **I can help you with:**
• Understanding stock analysis and metrics
• Explaining investment concepts for beginners  
• Risk assessment and management strategies
• Market trends and economic indicators

📈 **Popular Questions:**
• "How do I start investing?"
• "What does P/E ratio mean?"
• "Is [STOCK] a good buy?"
• "How risky is this investment?"

What would you like to learn about? 🚀"""

analyzer = StockAnalyzer()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/stock/<symbol>')
def get_stock(symbol):
    return jsonify(analyzer.get_stock_data(symbol.upper()))

@app.route('/api/analyze/<symbol>')
def analyze(symbol):
    return jsonify(analyzer.analyze_stock(symbol.upper()))

@app.route('/api/news/<symbol>')
def news(symbol):
    return jsonify(analyzer.get_news(symbol.upper()))

@app.route('/api/chat', methods=['POST'])
def chat_with_ai():
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        stock_context = data.get('stock_context', None)
        
        if not user_message.strip():
            return jsonify({'error': 'Please provide a message'})
        
        ai_response = analyzer.get_ai_response(user_message, stock_context)
        
        return jsonify({
            'response': ai_response,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': f'Chat service temporarily unavailable: {str(e)}'})

@app.route('/api/portfolio', methods=['POST'])
def analyze_portfolio():
    symbols = request.json.get('symbols', [])
    portfolio_analysis = []
    total_score = 0
    
    for symbol in symbols:
        analysis = analyzer.analyze_stock(symbol.upper())
        if 'error' not in analysis:
            portfolio_analysis.append(analysis)
            total_score += analysis.get('score', 50)
    
    avg_score = total_score / len(portfolio_analysis) if portfolio_analysis else 50
    
    return jsonify({
        'individual_analysis': portfolio_analysis,
        'portfolio_score': round(avg_score, 2),
        'portfolio_sentiment': '🚀 Strong Portfolio' if avg_score >= 70 else '📈 Good Portfolio' if avg_score >= 50 else '⚖️ Balanced Portfolio',
        'total_stocks': len(portfolio_analysis)
    })

@app.route('/api/trending')
def trending_stocks():
    trending = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA']
    trending_data = []
    
    for symbol in trending:
        try:
            data = analyzer.get_stock_data(symbol)
            if 'error' not in data:
                trending_data.append(data)
        except:
            continue
    
    return jsonify(trending_data)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port, load_dotenv=False)