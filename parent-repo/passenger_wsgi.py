import sys
import os

# Add your project directory to the Python path
project_home = '/home/yourusername/macra-stock-analyzer'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variables
os.environ['OPENAI_API_KEY'] = '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'

from app import app as application

if __name__ == '__main__':
    application.run()