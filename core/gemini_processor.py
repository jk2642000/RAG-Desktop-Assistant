import os
import google.generativeai as genai
from typing import List, Dict
from dotenv import load_dotenv
from .logger import rag_logger
from .tools import ToolRegistry
import atexit
import gc
import json

class GeminiProcessor:
    def __init__(self):
        load_dotenv()
        api_key = os.getenv('GEMINI_API_KEY')
        
        rag_logger.info(f"Initializing Gemini processor...")
        rag_logger.debug(f"API key present: {bool(api_key)}")
        
        if not api_key:
            error_msg = "GEMINI_API_KEY not found in environment variables. Please set it in .env file."
            rag_logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            genai.configure(api_key=api_key)
            rag_logger.info("Gemini API configured successfully")
            
            # Test API connection first
            test_model = genai.GenerativeModel('gemini-1.5-flash-latest')
            test_response = test_model.generate_content("Hello")
            rag_logger.info(f"Gemini API test successful: {test_response.text[:50]}...")
            
            # Initialize model with tools (fixed schema)
            tools = ToolRegistry.get_tool_definitions()
            self.model = genai.GenerativeModel(
                'gemini-1.5-flash-latest',
                tools=tools
            )
            self._active = True
            atexit.register(self.cleanup)
            rag_logger.info("Google Gemini initialized with function calling support")
            print("[OK] Google Gemini initialized with function calling support")
            
        except Exception as e:
            error_msg = f"Failed to initialize Gemini: {str(e)}"
            rag_logger.error(error_msg)
            print(f"[ERROR] {error_msg}")
            raise
    
    def process_question(self, question: str, context: str, search_results: List[Dict], stream_callback=None) -> str:
        """Process question using Google Gemini with RAG context"""
        
        # Get source documents for citation
        sources = list(set([result['metadata']['filename'] for result in search_results]))
        source_info = f"Sources: {', '.join(sources)}" if sources else ""
        
        rag_logger.info(f"Processing question with Gemini. Context length: {len(context)}, Sources: {sources}")
        rag_logger.debug(f"Question: {question[:100]}...")
        # Clean context for logging to avoid unicode errors
        clean_context = context[:500].encode('ascii', 'ignore').decode('ascii')
        rag_logger.debug(f"Full context sent to Gemini: {clean_context}...")
        
        # Extract entities and context for enhanced prompting
        entities_info = self._extract_context_entities(context)
        
        # Create enhanced prompt for Gemini
        prompt = f"""You are a helpful AI assistant that answers questions based on provided document context.

Document Context (analyze ALL sections):
{context}

{entities_info}

Question: {question}

Instructions:
- Carefully read ALL context sections [Context 1], [Context 2], etc.
- Pay attention to named entities, relationships, and semantic connections
- For questions about totals/summaries, combine information from multiple sections
- Answer using ONLY the information provided in the context
- Be thorough for complex questions (total experience, overall summary, etc.)
- If asking about totals, add up all relevant information from different sections
- Cite specific details when possible
- If context is insufficient, clearly state what's missing
- Understand nuances, implications, and logical inferences from the context
- Provide abstractive summaries when requested, not just extractive quotes
- You have access to tools for calculations, date operations, and text analysis - use them when needed
- For mathematical calculations, use the calculator tool
- For date-related questions (current date, current time, date differences), use the date_calculator tool
- For text analysis tasks (word count, character count, extract data), use the text_analyzer tool
- If the document context doesn't contain the answer and you have a relevant tool, use the tool instead

Answer (use tools when appropriate):"""

        try:
            rag_logger.debug("Starting Gemini content generation...")
            if stream_callback:
                # Streaming response with function calling
                response_text = ""
                response = self.model.generate_content(prompt, stream=True)
                
                for chunk in response:
                    if chunk.text:
                        response_text += chunk.text
                        stream_callback(chunk.text)
                    elif hasattr(chunk, 'function_calls') and chunk.function_calls:
                        # Handle function calls during streaming
                        for func_call in chunk.function_calls:
                            tool_result = self._execute_function_call(func_call)
                            stream_callback(f"\n\n[Tool: {func_call.name}] {tool_result}\n\n")
                            response_text += f"\n\n[Tool: {func_call.name}] {tool_result}\n\n"
                
                if response_text:
                    rag_logger.info(f"Gemini streaming response completed. Length: {len(response_text)} chars")
                    return response_text.strip()
                else:
                    return "I couldn't generate a response. Please try rephrasing your question."
            else:
                # Non-streaming response with function calling
                response = self.model.generate_content(prompt)
                
                # Handle function calls
                if hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate.content, 'parts'):
                        response_parts = []
                        
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text:
                                response_parts.append(part.text)
                            elif hasattr(part, 'function_call'):
                                tool_result = self._execute_function_call(part.function_call)
                                response_parts.append(f"\n\n[Tool: {part.function_call.name}] {tool_result}\n\n")
                        
                        if response_parts:
                            final_response = ''.join(response_parts)
                            rag_logger.info(f"Gemini response with tools completed. Length: {len(final_response)} chars")
                            return final_response.strip()
                
                # Fallback to regular text response
                if response.text:
                    rag_logger.info(f"Gemini response generated successfully. Length: {len(response.text)} chars")
                    rag_logger.debug(f"Gemini response: {response.text[:200]}...")
                    return response.text.strip()
                else:
                    rag_logger.warning("Gemini returned empty response")
                    return "I couldn't generate a response. Please try rephrasing your question."
                
        except Exception as e:
            rag_logger.error(f"Gemini API Error: {str(e)}")
            return f"Error processing with Gemini: {str(e)}"
    
    def _extract_context_entities(self, context: str) -> str:
        """Extract key entities and relationships from context for enhanced prompting"""
        try:
            # Use simple regex patterns for key entity types
            entities = {
                'dates': re.findall(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b', context),
                'numbers': re.findall(r'\b\d+(?:\.\d+)?(?:%|\$|€|£)?\b', context),
                'organizations': re.findall(r'\b[A-Z][a-z]+ (?:Inc|Corp|LLC|Ltd|Company|Organization)\b', context),
                'proper_nouns': re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', context)
            }
            
            # Filter and format entities
            entity_summary = []
            for entity_type, items in entities.items():
                if items:
                    unique_items = list(set(items))[:5]  # Top 5 unique items
                    if unique_items:
                        entity_summary.append(f"{entity_type.title()}: {', '.join(unique_items)}")
            
            if entity_summary:
                return f"Key Entities Identified:\n{chr(10).join(entity_summary)}\n"
            return ""
            
        except Exception as e:
            rag_logger.debug(f"Entity extraction error: {e}")
            return ""
    
    def _execute_function_call(self, function_call):
        """Execute a function call and return the result"""
        try:
            func_name = function_call.name
            func_args = {}
            
            # Extract arguments
            if hasattr(function_call, 'args'):
                for key, value in function_call.args.items():
                    func_args[key] = value
            
            # Execute the tool
            result = ToolRegistry.execute_tool(func_name, func_args)
            rag_logger.info(f"Function call executed: {func_name} -> {result[:100]}...")
            return result
            
        except Exception as e:
            error_msg = f"Function execution error: {str(e)}"
            rag_logger.error(error_msg)
            return error_msg
    
    def test_connection(self) -> bool:
        """Test if Gemini API is working"""
        try:
            response = self.model.generate_content("Hello, respond with 'OK' if you can hear me.")
            return "OK" in response.text if response.text else False
        except:
            return False
    
    def cleanup(self):
        """Clean up resources"""
        if hasattr(self, '_active') and self._active:
            self._active = False
            try:
                self.model = None
            except:
                pass
            gc.collect()
    
    def __del__(self):
        try:
            self.cleanup()
        except:
            pass