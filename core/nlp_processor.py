import nltk
import re
import numpy as np
from typing import List, Dict, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter
import string
from .tools import ToolRegistry
from .memory_manager import memory_manager
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

class NLPProcessor:
    def __init__(self):
        self._download_nltk_data()
        self.tfidf = TfidfVectorizer(stop_words='english', max_features=1000)
        
    def _download_nltk_data(self):
        """Download required NLTK data"""
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('corpora/stopwords')
            nltk.data.find('taggers/averaged_perceptron_tagger')
            nltk.data.find('chunkers/maxent_ne_chunker')
            nltk.data.find('corpora/words')
        except LookupError:
            print("Downloading NLTK data...")
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk.download('averaged_perceptron_tagger', quiet=True)
            nltk.download('maxent_ne_chunker', quiet=True)
            nltk.download('words', quiet=True)
        
        # Lazy load spaCy
        self.nlp = None
        self.spacy_loaded = False
    
    def process_question(self, question: str, context: str, search_results: List[Dict], stream_callback=None) -> str:
        """Dynamically process any question using NLP techniques"""
        
        # Check if question needs tools
        tool_result = self._check_and_execute_tools(question, context)
        if tool_result:
            if stream_callback:
                stream_callback(tool_result)
            return tool_result
        
        # Clean and prepare text
        question_clean = self._clean_text(question)
        context_sentences = self._split_into_sentences(context)
        
        # Detect question intent and type
        question_type = self._detect_question_type(question_clean)
        
        # Handle different question types dynamically
        if question_type == 'summary':
            return self._generate_summary(context, question_clean)
        elif question_type == 'factual':
            return self._extract_facts(question_clean, context_sentences, search_results)
        elif question_type == 'numerical':
            return self._extract_numerical_info(question_clean, context_sentences)
        elif question_type == 'definition':
            return self._extract_definition(question_clean, context_sentences)
        elif question_type == 'comparison':
            return self._handle_comparison(question_clean, context_sentences)
        else:
            return self._semantic_search_answer(question_clean, context_sentences)
    
    def _detect_question_type(self, question: str) -> str:
        """Detect question type using NLP patterns"""
        question_lower = question.lower()
        
        # Summary indicators
        if any(word in question_lower for word in ['summary', 'summarize', 'overview', 'brief', 'main points']):
            return 'summary'
        
        # Numerical/quantitative indicators
        if any(word in question_lower for word in ['how many', 'how much', 'number', 'count', 'age', 'years', 'percent', 'percentage']):
            return 'numerical'
        
        # Definition indicators
        if any(word in question_lower for word in ['what is', 'define', 'definition', 'meaning', 'means']):
            return 'definition'
        
        # Comparison indicators
        if any(word in question_lower for word in ['compare', 'difference', 'versus', 'vs', 'better', 'worse']):
            return 'comparison'
        
        # Default to factual
        return 'factual'
    
    def _generate_summary(self, context: str, question: str) -> str:
        """Generate abstractive-style summary"""
        sentences = self._split_into_sentences(context)
        
        if len(sentences) <= 3:
            return f"Summary:\n\n{context}"
        
        # Use abstractive summary generation
        abstractive_summary = self._generate_abstractive_summary(sentences)
        
        return f"Summary:\n\n{abstractive_summary}"
    
    def _extract_facts(self, question: str, sentences: List[str], search_results: List[Dict]) -> str:
        """Extract factual information using NER and semantic similarity"""
        if not sentences:
            return "No relevant information found."
        
        # Extract entities from question
        question_entities = self._extract_entities(question)
        
        # Calculate semantic similarity with entity boosting
        question_words = set(self._extract_keywords(question))
        scored_sentences = []
        
        for sentence in sentences:
            sentence_words = set(self._extract_keywords(sentence.lower()))
            sentence_entities = self._extract_entities(sentence)
            
            # Base Jaccard similarity
            intersection = len(question_words.intersection(sentence_words))
            union = len(question_words.union(sentence_words))
            similarity = intersection / union if union > 0 else 0
            
            # Boost score for entity matches
            entity_boost = 0
            for q_ent in question_entities:
                for s_ent in sentence_entities:
                    if q_ent.lower() in s_ent.lower() or s_ent.lower() in q_ent.lower():
                        entity_boost += 0.3
            
            final_score = similarity + min(entity_boost, 0.5)
            
            if final_score > 0:
                scored_sentences.append((sentence, final_score))
        
        # Sort by similarity and return top results
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        
        if scored_sentences:
            top_sentences = [s[0] for s in scored_sentences[:3]]
            
            # Add entity context
            entity_info = self._format_entities(question_entities) if question_entities else ""
            
            if any(word in question.lower() for word in ['document', 'file', 'this']):
                doc_info = self._get_document_info(search_results)
                return f"{doc_info}\n{entity_info}\nRelevant information:\n\n" + "\n\n".join(top_sentences)
            else:
                return f"Based on the documents:\n{entity_info}\n\n" + "\n\n".join(top_sentences)
        else:
            return "I couldn't find specific information to answer your question."
    
    def _extract_numerical_info(self, question: str, sentences: List[str]) -> str:
        """Extract numerical information"""
        number_pattern = r'\b\d+(?:\.\d+)?(?:\s*%|\s*percent|\s*years?|\s*months?|\s*days?)?\b'
        
        numerical_sentences = []
        for sentence in sentences:
            if re.search(number_pattern, sentence, re.IGNORECASE):
                # Check if sentence is relevant to question
                question_words = set(self._extract_keywords(question))
                sentence_words = set(self._extract_keywords(sentence.lower()))
                
                if question_words.intersection(sentence_words):
                    numerical_sentences.append(sentence)
        
        if numerical_sentences:
            return "Numerical information found:\n\n" + "\n\n".join(numerical_sentences[:3])
        else:
            return "No specific numerical information found for your question."
    
    def _extract_definition(self, question: str, sentences: List[str]) -> str:
        """Extract definitions using NER and POS tagging"""
        # Extract entities and nouns from question
        entities = self._extract_entities(question)
        pos_tags = self._get_pos_tags(question)
        
        # Find main terms (entities or important nouns)
        main_terms = entities if entities else [word for word, pos in pos_tags if pos.startswith('NN') and len(word) > 3]
        
        if not main_terms:
            return self._semantic_search_answer(question, sentences)
        
        # Look for definition patterns with entity matching
        definition_sentences = []
        for sentence in sentences:
            sentence_lower = sentence.lower()
            sentence_entities = self._extract_entities(sentence)
            
            for term in main_terms:
                term_lower = term.lower()
                
                # Entity-based matching
                entity_match = any(term_lower in ent.lower() or ent.lower() in term_lower 
                                 for ent in sentence_entities)
                
                # Pattern-based matching
                pattern_match = (term_lower in sentence_lower and 
                               any(pattern in sentence_lower for pattern in 
                                   [' is ', ' are ', ' means ', ' refers to ', ' defined as ', ' called ']))
                
                if entity_match or pattern_match:
                    definition_sentences.append(sentence)
                    break
        
        if definition_sentences:
            main_term = main_terms[0]
            return f"Definition of '{main_term}':\n\n" + "\n\n".join(definition_sentences[:2])
        else:
            return f"No clear definition found for the requested terms in the documents."
    
    def _handle_comparison(self, question: str, sentences: List[str]) -> str:
        """Handle comparison questions"""
        comparison_sentences = []
        comparison_words = ['compare', 'difference', 'versus', 'vs', 'better', 'worse', 'than', 'while', 'whereas']
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(word in sentence_lower for word in comparison_words):
                comparison_sentences.append(sentence)
        
        if comparison_sentences:
            return "Comparison information:\n\n" + "\n\n".join(comparison_sentences[:3])
        else:
            return self._semantic_search_answer(question, sentences)
    
    def _semantic_search_answer(self, question: str, sentences: List[str]) -> str:
        """Fallback semantic search for any question"""
        question_keywords = self._extract_keywords(question)
        
        scored_sentences = []
        for sentence in sentences:
            sentence_keywords = self._extract_keywords(sentence.lower())
            
            # Calculate keyword overlap score
            overlap = len(set(question_keywords).intersection(set(sentence_keywords)))
            if overlap > 0:
                # Boost score for longer overlaps
                score = overlap + (len(sentence) / 1000)  # Slight preference for longer sentences
                scored_sentences.append((sentence, score))
        
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        
        if scored_sentences:
            top_sentences = [s[0] for s in scored_sentences[:3]]
            return "Most relevant information:\n\n" + "\n\n".join(top_sentences)
        else:
            return "I couldn't find relevant information to answer your question."
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text"""
        # Remove punctuation and convert to lowercase
        text = text.translate(str.maketrans('', '', string.punctuation)).lower()
        
        # Tokenize
        words = nltk.word_tokenize(text)
        
        # Remove stopwords and short words
        stopwords = set(nltk.corpus.stopwords.words('english'))
        keywords = [word for word in words if len(word) > 2 and word not in stopwords]
        
        return keywords
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        sentences = nltk.sent_tokenize(text)
        return [s.strip() for s in sentences if len(s.strip()) > 10]
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _check_and_execute_tools(self, question: str, context: str) -> str:
        """Check if question needs tools and execute them"""
        question_lower = question.lower()
        
        # Enhanced math patterns
        math_patterns = ['calculate', 'compute', 'math', 'what is', 'how much', 'add', 'subtract', 'multiply', 'divide']
        if any(word in question_lower for word in math_patterns) or re.search(r'[0-9+\-*/().%]', question):
            # Extract math expression with better parsing
            math_expressions = re.findall(r'[0-9+\-*/().\s%]+', question)
            for expr in math_expressions:
                if any(op in expr for op in ['+', '-', '*', '/', '%']) and len(expr.strip()) > 2:
                    clean_expr = expr.replace('%', '/100').strip()
                    result = ToolRegistry.execute_tool('calculator', {'expression': clean_expr})
                    return f"Calculation: {result}"
        
        # Enhanced date patterns
        date_patterns = ['date', 'today', 'current time', 'what time', 'days between', 'add days', 'subtract days']
        if any(word in question_lower for word in date_patterns):
            if 'today' in question_lower or 'current date' in question_lower:
                return ToolRegistry.execute_tool('date_calculator', {'operation': 'current_date'})
            elif 'current time' in question_lower or 'what time' in question_lower:
                return ToolRegistry.execute_tool('date_calculator', {'operation': 'current_time'})
            elif 'days between' in question_lower:
                # Try to extract dates
                dates = re.findall(r'\d{4}-\d{2}-\d{2}', question)
                if len(dates) >= 2:
                    return ToolRegistry.execute_tool('date_calculator', {
                        'operation': 'date_diff',
                        'date1': dates[0],
                        'date2': dates[1]
                    })
        
        # Enhanced text analysis patterns
        text_patterns = ['word count', 'character count', 'count words', 'count characters', 'how many words', 'how many characters']
        if any(pattern in question_lower for pattern in text_patterns):
            if context:
                if any(word in question_lower for word in ['word', 'words']):
                    return ToolRegistry.execute_tool('text_analyzer', {'text': context, 'analysis_type': 'word_count'})
                elif any(word in question_lower for word in ['character', 'characters', 'char']):
                    return ToolRegistry.execute_tool('text_analyzer', {'text': context, 'analysis_type': 'char_count'})
        
        # Email extraction
        if 'email' in question_lower and 'extract' in question_lower and context:
            return ToolRegistry.execute_tool('text_analyzer', {'text': context, 'analysis_type': 'extract_emails'})
        
        # Number extraction
        if 'number' in question_lower and 'extract' in question_lower and context:
            return ToolRegistry.execute_tool('text_analyzer', {'text': context, 'analysis_type': 'extract_numbers'})
        
        return None
    
    def _get_spacy_model(self):
        """Lazy load spaCy model"""
        if not self.spacy_loaded and SPACY_AVAILABLE:
            try:
                if memory_manager.should_unload_models():
                    memory_manager.cleanup_unused_models()
                
                self.nlp = spacy.load('en_core_web_sm')
                memory_manager.register_model('spacy_nlp', self.nlp, 50)  # ~50MB
                self.spacy_loaded = True
                print("✓ spaCy NER model loaded on demand")
            except OSError:
                print("⚠ spaCy model not found, using NLTK NER")
        return self.nlp
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract named entities from text"""
        entities = []
        
        nlp_model = self._get_spacy_model()
        if nlp_model:  # Use spaCy if available
            doc = nlp_model(text)
            entities = [ent.text for ent in doc.ents if ent.label_ in ['PERSON', 'ORG', 'GPE', 'PRODUCT', 'EVENT']]
        else:  # Fallback to NLTK
            try:
                tokens = nltk.word_tokenize(text)
                pos_tags = nltk.pos_tag(tokens)
                chunks = nltk.ne_chunk(pos_tags, binary=False)
                
                for chunk in chunks:
                    if hasattr(chunk, 'label'):
                        entity = ' '.join([token for token, pos in chunk.leaves()])
                        entities.append(entity)
            except:
                pass
        
        return entities
    
    def _get_pos_tags(self, text: str) -> List[Tuple[str, str]]:
        """Get POS tags for text"""
        try:
            tokens = nltk.word_tokenize(text)
            return nltk.pos_tag(tokens)
        except:
            return []
    
    def _format_entities(self, entities: List[str]) -> str:
        """Format entities for display"""
        if not entities:
            return ""
        return f"Key entities: {', '.join(entities[:5])}\n"
    
    def _generate_abstractive_summary(self, sentences: List[str], max_sentences: int = 3) -> str:
        """Generate abstractive-style summary using extractive + synthesis"""
        if len(sentences) <= max_sentences:
            return ' '.join(sentences)
        
        # Extract key information
        entities_all = []
        key_phrases = []
        
        for sentence in sentences:
            entities_all.extend(self._extract_entities(sentence))
            # Extract noun phrases
            pos_tags = self._get_pos_tags(sentence)
            noun_phrases = [word for word, pos in pos_tags if pos.startswith('NN')]
            key_phrases.extend(noun_phrases)
        
        # Get most common entities and phrases
        common_entities = [item for item, count in Counter(entities_all).most_common(3)]
        common_phrases = [item for item, count in Counter(key_phrases).most_common(5)]
        
        # Select sentences with most key information
        scored_sentences = []
        for sentence in sentences:
            score = 0
            sentence_lower = sentence.lower()
            
            # Score based on entities and key phrases
            for entity in common_entities:
                if entity.lower() in sentence_lower:
                    score += 2
            for phrase in common_phrases:
                if phrase.lower() in sentence_lower:
                    score += 1
            
            scored_sentences.append((sentence, score))
        
        # Return top sentences
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        top_sentences = [s[0] for s in scored_sentences[:max_sentences]]
        
        # Add entity context
        entity_context = f"Key topics: {', '.join(common_entities + common_phrases[:3])}. " if common_entities or common_phrases else ""
        
        return entity_context + ' '.join(top_sentences)
    
    def _get_document_info(self, search_results: List[Dict]) -> str:
        """Get document information"""
        if not search_results:
            return "No documents found."
        
        filenames = list(set([result['metadata']['filename'] for result in search_results]))
        
        if len(filenames) == 1:
            return f"Document: {filenames[0]}"
        else:
            return f"Documents: {', '.join(filenames)}"
    
    def cleanup(self):
        """Clean up NLP resources"""
        if self.nlp:
            memory_manager.unload_model('spacy_nlp')
            self.nlp = None
            self.spacy_loaded = False