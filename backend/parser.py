import re
import json
from pathlib import Path

def parse_transcript(file_path: str) -> dict:
    """
    Reads a raw text transcript and converts it into a structured dictionary
    containing metadata and timestamped dialogue blocks.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # The raw text contains zero-width spaces and varied spacing. 
    # This regex captures the standard "MM:SS" timestamp pattern.
    pattern = r'(\d{2}:\d{2})\s*'
    parts = re.split(pattern, content)
    
    preamble = parts[0]
    expert_name = "Unknown"
    market = "Unknown"
    
    # Extract Expert metadata from the header
    name_match = re.search(r'Expert\s*\d*\s*[-–]\s*(.+)', preamble)
    market_match = re.search(r'Market:\s*(.+)', preamble)
    
    if name_match: 
        expert_name = name_match.group(1).strip()
    if market_match: 
        market = market_match.group(1).strip()

    blocks = []
    block_id = 1
    
    # re.split creates a list where parts[1] is a timestamp, parts[2] is the text, etc.
    for i in range(1, len(parts), 2):
        time = parts[i]
        text_block = parts[i+1].strip()
        
        # Isolate the speaker from their dialogue using the colon (e.g., "Interviewer: ...")
        speaker_match = re.match(r'^([^:]+):\s*(.*)', text_block, re.DOTALL)
        if speaker_match:
            speaker = speaker_match.group(1).strip()
            text = speaker_match.group(2).strip().replace('\n', ' ')
        else:
            speaker = "Unknown"
            text = text_block.replace('\n', ' ')
            
        # Ignore empty blocks
        if text:
            blocks.append({
                "id": block_id,
                "time": time,
                "speaker": speaker,
                "text": text
            })
            block_id += 1
            
    return {
        "expert_name": expert_name,
        "market": market,
        "dialogue": blocks
    }