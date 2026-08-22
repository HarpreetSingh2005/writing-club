import os
import re
from datetime import datetime
from pathlib import Path
from utils.pipeline_logger import format_log

def get_article_name(state: dict) -> str:
    """Extract and sanitize the article name/title from the draft or proposed flow."""
    # 1. Try to extract from the first line of the draft
    draft = state.get("draft", "")
    if draft:
        first_line = draft.split("\n")[0].strip()
        # Clean markdown headers like #, ##, **, etc.
        first_line = re.sub(r'^[#*_\-\s]+', '', first_line)
        first_line = re.sub(r'[#*_\-\s]+$', '', first_line)
        if 3 < len(first_line) < 100:
            return first_line
            
    # 2. Try to get from proposed_flow title_direction
    flow = state.get("proposed_flow")
    if flow:
        title_dir = getattr(flow, "title_direction", "") if not isinstance(flow, dict) else flow.get("title_direction", "")
        if title_dir and len(title_dir) > 3:
            return title_dir
            
    # 3. Fallback
    return "Untitled Article"

def sanitize_filename(name: str) -> str:
    """Remove invalid filename characters for Windows compatibility."""
    # Remove characters not allowed in Windows filenames: < > : " / \ | ? *
    clean_name = re.sub(r'[<>:"/\\|?*]', '', name)
    clean_name = clean_name.strip()
    return clean_name or "untitled_article"

def save_project_dump(state: dict) -> str:
    """
    Creates a new project log file containing the summary, transcript, 
    perspectives, flow, expert research, final draft, and pipeline logs.
    Saves inside a folder called 'articles'.
    """
    # Create the 'articles' directory if it doesn't exist
    articles_dir = Path("articles")
    articles_dir.mkdir(exist_ok=True)
    
    article_name = get_article_name(state)
    filename = sanitize_filename(article_name) + ".txt"
    file_path = articles_dir / filename
    
    # Format the content
    lines = []
    lines.append("=" * 80)
    lines.append(f" ARTICLE PROJECT LOG: {article_name.upper()}")
    lines.append("=" * 80)
    lines.append(f"Timestamp:           {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Status:              Final Approved")
    lines.append(f"Filename:            {filename}")
    lines.append(f"Audio File Path:     {state.get('audio_file_path', 'None (Direct Text Input)')}")
    lines.append(f"Review Stage:        {state.get('review_stage', 'N/A')}")
    lines.append(f"Revision Count:      {state.get('revision_count', 0)}")
    lines.append(f"Auto Revision Count: {state.get('auto_revision_count', 0)}")
    lines.append(f"Feedback Route:      {state.get('feedback_route', 'N/A')}")
    lines.append("=" * 80 + "\n")
    
    # 1. Final Draft
    lines.append("## 📄 FINAL APPROVED ARTICLE DRAFT")
    lines.append("-" * 40)
    lines.append(state.get("draft", "").strip())
    lines.append("\n" + "=" * 80 + "\n")
    
    # 2. Last Feedback Logged
    lines.append("## 🛠️ LAST FEEDBACK LOGGED")
    lines.append("-" * 40)
    feedback = state.get("user_feedback", "").strip()
    lines.append(feedback if feedback else "No feedback logged (Clean Approval).")
    lines.append("\n" + "=" * 80 + "\n")
    
    # 3. Cleaned Summary
    lines.append("## 📝 INTAKE CLEANED SUMMARY")
    lines.append("-" * 40)
    lines.append(state.get("summary", "").strip())
    lines.append("\n" + "=" * 80 + "\n")
    
    # 4. Original Transcript
    lines.append("## 🎤 ORIGINAL TRANSCRIPT / IDEA")
    lines.append("-" * 40)
    lines.append(state.get("transcript", "").strip())
    lines.append("\n" + "=" * 80 + "\n")
    
    # 5. Proposed Flow
    flow = state.get("proposed_flow", {})
    lines.append("## 📐 PROPOSED WRITING FLOW")
    lines.append("-" * 40)
    if isinstance(flow, dict):
        lines.append(f"Title Direction: {flow.get('title_direction', 'N/A')}")
        lines.append(f"Tone:            {flow.get('tone', 'N/A')}")
        lines.append(f"Core Argument:   {flow.get('core_argument', 'N/A')}")
        lines.append("Sections:")
        for sec in flow.get("sections", []):
            lines.append(f"  - {sec}")
    else:
        lines.append(f"Title Direction: {getattr(flow, 'title_direction', 'N/A')}")
        lines.append(f"Tone:            {getattr(flow, 'tone', 'N/A')}")
        lines.append(f"Core Argument:   {getattr(flow, 'core_argument', 'N/A')}")
        lines.append("Sections:")
        for sec in getattr(flow, "sections", []):
            lines.append(f"  - {sec}")
    lines.append("\n" + "=" * 80 + "\n")
    
    # 6. Writing Style & Profile
    lines.append("## 🎨 WRITING STYLE PROFILE")
    lines.append("-" * 40)
    style_name = state.get("writing_style", "N/A")
    style_profile = state.get("style_profile", {})
    lines.append(f"Style Name:         {style_name}")
    lines.append(f"Tone:               {style_profile.get('tone', 'N/A')}")
    lines.append(f"Narrative Distance: {style_profile.get('narrative_distance', 'N/A')}")
    lines.append(f"Pacing:             {style_profile.get('pacing', 'N/A')}")
    lines.append(f"Examples Seen:      {style_profile.get('examples_seen', 0)}")
    sig_rules = style_profile.get("signature_rules", [])
    if sig_rules:
        lines.append("Signature Rules:")
        for rule in sig_rules:
            lines.append(f"  - {rule}")
    avoid_rules = style_profile.get("avoid", [])
    if avoid_rules:
        lines.append("Avoid:")
        for rule in avoid_rules:
            lines.append(f"  - {rule}")
    lines.append("\n" + "=" * 80 + "\n")
    
    # 7. Organized Departments & Topics
    lines.append("## 🏛️ ORGANIZED DEPARTMENTS & TOPICS")
    lines.append("-" * 40)
    dept_topics = state.get("departments_topics", {})
    if dept_topics:
        for dept, perspectives in dept_topics.items():
            lines.append(f"Department: {dept}")
            for p in perspectives:
                if isinstance(p, dict):
                    lines.append(f"  - Perspective: {p.get('name', 'N/A')}")
                    lines.append(f"    Reasoning:   {p.get('reason', 'N/A')}")
                else:
                    lines.append(f"  - Perspective: {getattr(p, 'name', 'N/A')}")
                    lines.append(f"    Reasoning:   {getattr(p, 'reason', 'N/A')}")
            lines.append("")
    else:
        lines.append("No department grouping performed.")
        
    new_depts = state.get("new_department", [])
    if new_depts:
        lines.append("Newly Generated Departments on this Run:")
        for nd in new_depts:
            lines.append(f"  - {nd}")
    lines.append("\n" + "=" * 80 + "\n")
    
    # 8. Discovered Perspectives
    lines.append("## 🔍 DISCOVERED PERSPECTIVES")
    lines.append("-" * 40)
    perspectives = state.get("discovered_perspectives", [])
    if perspectives:
        for p in perspectives:
            if isinstance(p, dict):
                lines.append(f"Department:  {p.get('department', 'N/A')}")
                lines.append(f"Perspective: {p.get('name', 'N/A')}")
                lines.append(f"Reasoning:   {p.get('reason', 'N/A')}\n")
            else:
                lines.append(f"Department:  {getattr(p, 'department', 'N/A')}")
                lines.append(f"Perspective: {getattr(p, 'name', 'N/A')}")
                lines.append(f"Reasoning:   {getattr(p, 'reason', 'N/A')}\n")
    else:
        lines.append("None discovered.")
    lines.append("\n" + "=" * 80 + "\n")
    
    # 9. Expert Research Reports
    lines.append("## 🔬 EXPERT RESEARCH REPORTS")
    lines.append("-" * 40)
    reports = state.get("research_reports", [])
    if reports:
        for r in reports:
            if isinstance(r, dict):
                lines.append(f"Perspective: {r.get('perspective', 'N/A')} ({r.get('department', 'N/A')})")
                lines.append("Key Observations:")
                for obs in r.get("key_observations", []):
                    lines.append(f"  - {obs}")
                lines.append("Risks or Blindspots:")
                for rsk in r.get("risks_or_blindspots", []):
                    lines.append(f"  - {rsk}")
                lines.append("Writing Suggestions:")
                for sug in r.get("writing_suggestions", []):
                    lines.append(f"  - {sug}")
                lines.append("")
            else:
                lines.append(f"Perspective: {getattr(r, 'perspective', 'N/A')} ({getattr(r, 'department', 'N/A')})")
                lines.append("Key Observations:")
                for obs in getattr(r, "key_observations", []):
                    lines.append(f"  - {obs}")
                lines.append("Risks or Blindspots:")
                for rsk in getattr(r, "risks_or_blindspots", []):
                    lines.append(f"  - {rsk}")
                lines.append("Writing Suggestions:")
                for sug in getattr(r, "writing_suggestions", []):
                    lines.append(f"  - {sug}")
                lines.append("")
    else:
        lines.append("None generated.")
    lines.append("\n" + "=" * 80 + "\n")

    # 10. Curated Insights
    lines.append("## ✂️ CURATED KEY INSIGHTS")
    lines.append("-" * 40)
    insights = state.get("curated_insights", [])
    if insights:
        for ins in insights:
            lines.append(f"  - {ins}")
    else:
        lines.append("No curated insights.")
    lines.append("\n" + "=" * 80 + "\n")
    
    # 11. Pipeline Activity Log
    lines.append("## 📋 FULL PIPELINE LOG")
    lines.append("-" * 40)
    lines.append(format_log(state.get("pipeline_log", [])))
    lines.append("\n" + "=" * 80 + "\n")
    
    content = "\n".join(lines)
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    print(f"\n💾 Project details successfully written to: {file_path}")
    return str(file_path)
