import math
import datetime
import re
from typing import Dict, Any, List

class ToolRegistry:
    """Registry of available tools for Gemini function calling"""
    
    @staticmethod
    def get_tool_definitions():
        """Return tool definitions for Gemini"""
        return [
            {
                "name": "calculator",
                "description": "Perform mathematical calculations",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "expression": {
                            "type": "STRING",
                            "description": "Mathematical expression to evaluate (e.g., '2+2', 'sqrt(16)', 'sin(30)')"
                        }
                    },
                    "required": ["expression"]
                }
            },
            {
                "name": "date_calculator",
                "description": "Calculate dates, time differences, or get current date/time",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "operation": {
                            "type": "STRING",
                            "enum": ["current_date", "current_time", "date_diff", "add_days"],
                            "description": "Type of date operation"
                        },
                        "date1": {
                            "type": "STRING",
                            "description": "First date in YYYY-MM-DD format (for date_diff, add_days)"
                        },
                        "date2": {
                            "type": "STRING",
                            "description": "Second date in YYYY-MM-DD format (for date_diff)"
                        },
                        "days": {
                            "type": "INTEGER",
                            "description": "Number of days to add (for add_days)"
                        }
                    },
                    "required": ["operation"]
                }
            },
            {
                "name": "text_analyzer",
                "description": "Analyze text for word count, character count, or extract specific patterns",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "text": {
                            "type": "STRING",
                            "description": "Text to analyze"
                        },
                        "analysis_type": {
                            "type": "STRING",
                            "enum": ["word_count", "char_count", "extract_numbers", "extract_emails"],
                            "description": "Type of analysis to perform"
                        }
                    },
                    "required": ["text", "analysis_type"]
                }
            }
        ]
    
    @staticmethod
    def execute_tool(tool_name: str, parameters: Dict[str, Any]) -> str:
        """Execute a tool with given parameters"""
        try:
            if tool_name == "calculator":
                return ToolRegistry._calculator(parameters["expression"])
            elif tool_name == "date_calculator":
                return ToolRegistry._date_calculator(parameters)
            elif tool_name == "text_analyzer":
                return ToolRegistry._text_analyzer(parameters["text"], parameters["analysis_type"])
            else:
                return f"Unknown tool: {tool_name}"
        except Exception as e:
            return f"Tool execution error: {str(e)}"
    
    @staticmethod
    def _calculator(expression: str) -> str:
        """Safe mathematical calculator"""
        # Clean expression
        expression = expression.replace(" ", "")
        
        # Allow only safe mathematical operations
        allowed_chars = set("0123456789+-*/.()sincotanlogqrtpie")
        if not all(c.lower() in allowed_chars for c in expression):
            return "Invalid characters in expression"
        
        try:
            # Replace common math functions
            expression = expression.replace("sin", "math.sin")
            expression = expression.replace("cos", "math.cos")
            expression = expression.replace("tan", "math.tan")
            expression = expression.replace("log", "math.log")
            expression = expression.replace("sqrt", "math.sqrt")
            expression = expression.replace("pi", "math.pi")
            expression = expression.replace("e", "math.e")
            
            # Evaluate safely
            result = eval(expression, {"__builtins__": {}, "math": math})
            return f"Result: {result}"
        except Exception as e:
            return f"Calculation error: {str(e)}"
    
    @staticmethod
    def _date_calculator(params: Dict[str, Any]) -> str:
        """Date and time calculations"""
        operation = params["operation"]
        
        try:
            if operation == "current_date":
                return f"Current date: {datetime.date.today()}"
            elif operation == "current_time":
                return f"Current time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            elif operation == "date_diff":
                date1 = datetime.datetime.strptime(params["date1"], "%Y-%m-%d").date()
                date2 = datetime.datetime.strptime(params["date2"], "%Y-%m-%d").date()
                diff = (date2 - date1).days
                return f"Date difference: {diff} days"
            elif operation == "add_days":
                date1 = datetime.datetime.strptime(params["date1"], "%Y-%m-%d").date()
                result_date = date1 + datetime.timedelta(days=params["days"])
                return f"Result date: {result_date}"
            else:
                return "Unknown date operation"
        except Exception as e:
            return f"Date calculation error: {str(e)}"
    
    @staticmethod
    def _text_analyzer(text: str, analysis_type: str) -> str:
        """Text analysis functions"""
        try:
            if analysis_type == "word_count":
                words = len(text.split())
                return f"Word count: {words}"
            elif analysis_type == "char_count":
                chars = len(text)
                return f"Character count: {chars}"
            elif analysis_type == "extract_numbers":
                numbers = re.findall(r'\d+(?:\.\d+)?', text)
                return f"Numbers found: {', '.join(numbers)}"
            elif analysis_type == "extract_emails":
                emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
                return f"Emails found: {', '.join(emails)}"
            else:
                return "Unknown analysis type"
        except Exception as e:
            return f"Text analysis error: {str(e)}"