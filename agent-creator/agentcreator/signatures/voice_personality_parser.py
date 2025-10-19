"""
Voice Personality Parser Signature

Converts unstructured voice personality text into a structured format
for Nova Sonic voice agent configuration.
"""

import dspy
from typing import Optional


class VoicePersonalityParser(dspy.Signature):
    """
    Parse unstructured voice personality description into structured fields.
    
    INPUT: Unstructured text describing the agent's voice personality
    OUTPUT: Structured voice personality configuration
    
    INSTRUCTIONS:
    1. Extract or infer the following attributes from the input text:
       - identity: Who is the agent? (role, expertise, background)
       - task: What is the agent's primary purpose?
       - demeanor: How does the agent behave? (professional, friendly, empathetic, etc.)
       - tone: What is the speaking tone? (warm, authoritative, casual, formal)
       - formality_level: How formal is the language? (very_formal, formal, neutral, casual, very_casual)
       - enthusiasm_level: How enthusiastic is the agent? (very_low, low, moderate, high, very_high)
       - filler_words: What filler words to use? (um, uh, like, you know, etc.) or "none"
       - pacing: How fast should the agent speak? (very_slow, slow, moderate, fast, very_fast)
       - additional_instructions: Any other specific instructions for voice behavior
    
    2. If a field is not explicitly mentioned, infer it based on:
       - The agent's role and task
       - The overall context and tone of the description
       - Best practices for the agent's domain
    
    3. Be specific and actionable in your output
    4. Ensure consistency across all fields
    
    EXAMPLES:
    
    Input: "A friendly customer support agent who helps users with technical issues. 
            Should be patient and empathetic, speaking clearly and not too fast."
    Output:
    {
      "identity": "Technical customer support specialist with expertise in troubleshooting",
      "task": "Help users resolve technical issues with patience and clarity",
      "demeanor": "Friendly, patient, and empathetic",
      "tone": "Warm and reassuring",
      "formality_level": "neutral",
      "enthusiasm_level": "moderate",
      "filler_words": "none",
      "pacing": "moderate",
      "additional_instructions": "Always acknowledge user frustration and provide step-by-step guidance"
    }
    
    Input: "Professional financial advisor for high-net-worth clients. 
            Sophisticated, confident, and authoritative."
    Output:
    {
      "identity": "Senior financial advisor specializing in wealth management for high-net-worth individuals",
      "task": "Provide sophisticated financial guidance and investment strategies",
      "demeanor": "Professional, confident, and authoritative",
      "tone": "Authoritative and sophisticated",
      "formality_level": "very_formal",
      "enthusiasm_level": "low",
      "filler_words": "none",
      "pacing": "moderate",
      "additional_instructions": "Use financial terminology appropriately, maintain gravitas, and project expertise"
    }
    """
    
    # Input
    voice_personality_text: str = dspy.InputField(
        desc="Unstructured text describing the agent's voice personality and behavior"
    )
    sop: str = dspy.InputField(
        desc="Standard Operating Procedure to understand agent's role and context"
    )
    knowledge_base_description: str = dspy.InputField(
        desc="Description of the agent's knowledge domain"
    )
    
    # Output - structured voice personality
    identity: str = dspy.OutputField(
        desc="Who is the agent? (role, expertise, background) - be specific and detailed"
    )
    task: str = dspy.OutputField(
        desc="What is the agent's primary purpose? - clear and actionable"
    )
    demeanor: str = dspy.OutputField(
        desc="How does the agent behave? (e.g., professional, friendly, empathetic, authoritative)"
    )
    tone: str = dspy.OutputField(
        desc="What is the speaking tone? (e.g., warm, authoritative, casual, formal, reassuring)"
    )
    formality_level: str = dspy.OutputField(
        desc="How formal is the language? Choose: very_formal, formal, neutral, casual, very_casual"
    )
    enthusiasm_level: str = dspy.OutputField(
        desc="How enthusiastic is the agent? Choose: very_low, low, moderate, high, very_high"
    )
    filler_words: str = dspy.OutputField(
        desc="What filler words to use? (e.g., 'um', 'uh', 'like', 'you know') or 'none' for no filler words"
    )
    pacing: str = dspy.OutputField(
        desc="How fast should the agent speak? Choose: very_slow, slow, moderate, fast, very_fast"
    )
    additional_instructions: str = dspy.OutputField(
        desc="Any other specific instructions for voice behavior, communication style, or special considerations"
    )

