import json
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


def get_article_folder(state: dict) -> Path:
    """Return the article-specific folder path, creating the parent articles dir."""
    articles_dir = Path("articles")
    articles_dir.mkdir(exist_ok=True)

    article_name = get_article_name(state)
    folder = articles_dir / sanitize_filename(article_name)
    folder.mkdir(exist_ok=True)
    return folder


def _flow_lines(flow) -> list[str]:
    lines = []
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
    return lines


def save_review_packet(state: dict) -> str:
    """
    Writes the current draft and review context before asking the user for
    final approval, so the user can review the article with the system's
    assumptions and pipeline context visible.
    """
    folder = get_article_folder(state)
    article_name = get_article_name(state)

    draft_path = folder / "draft_for_review.txt"
    report_path = folder / "review_context_report.txt"

    draft_lines = [
        article_name,
        "=" * len(article_name),
        "",
        state.get("draft", "").strip(),
        "",
    ]
    with open(draft_path, "w", encoding="utf-8") as f:
        f.write("\n".join(draft_lines))

    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append(f" REVIEW CONTEXT REPORT: {article_name.upper()}")
    report_lines.append("=" * 80)
    report_lines.append(f"Timestamp:         {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"Requested Tone:    {state.get('requested_tone', 'N/A')}")
    report_lines.append(f"Target Word Count: {state.get('article_length', 'N/A')}")
    report_lines.append(f"Review Stage:      Draft Approval")
    report_lines.append(f"Draft File:        {draft_path.name}")
    report_lines.append("=" * 80 + "\n")

    report_lines.append("## RAW SOURCE / TRANSCRIPT")
    report_lines.append("-" * 40)
    report_lines.append(state.get("transcript", "").strip() or "No raw transcript available.")
    report_lines.append("\n" + "=" * 80 + "\n")

    if state.get("incomplete_draft_reason"):
        report_lines.append("## ⚠️ DRAFT STATUS: INCOMPLETE")
        report_lines.append("-" * 40)
        report_lines.append(f"The generated draft was flagged as truncated/incomplete: {state.get('incomplete_draft_reason')}")
        report_lines.append("\n" + "=" * 80 + "\n")

    report_lines.append("## WHAT THE AI THINKS YOU ASKED FOR")
    report_lines.append("-" * 40)
    report_lines.append(state.get("summary", "").strip() or "No cleaned summary available.")
    report_lines.append("\nQuestion for you: Is this understanding correct, or did the AI miss your real intent?")
    report_lines.append("\n" + "=" * 80 + "\n")

    report_lines.append("## APPROVED FLOW")
    report_lines.append("-" * 40)
    report_lines.extend(_flow_lines(state.get("proposed_flow", {})))
    report_lines.append("\n" + "=" * 80 + "\n")

    report_lines.append("## STYLE PROFILE")
    report_lines.append("-" * 40)
    style_profile = state.get("style_profile", {}) or {}
    report_lines.append(f"Tone:               {style_profile.get('tone', 'N/A')}")
    report_lines.append(f"Narrative Distance: {style_profile.get('narrative_distance', 'N/A')}")
    report_lines.append(f"Pacing:             {style_profile.get('pacing', 'N/A')}")
    if style_profile.get("signature_rules"):
        report_lines.append("Signature Rules:")
        for rule in style_profile.get("signature_rules", []):
            report_lines.append(f"  - {rule}")
    if style_profile.get("avoid"):
        report_lines.append("Avoid:")
        for rule in style_profile.get("avoid", []):
            report_lines.append(f"  - {rule}")
    report_lines.append("\n" + "=" * 80 + "\n")

    report_lines.append("## AUTO-CRITIC / PIPELINE LOG")
    report_lines.append("-" * 40)
    report_lines.append(format_log(state.get("pipeline_log", [])))
    report_lines.append("\n" + "=" * 80 + "\n")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    print(f"\nReview packet written to: {folder}")
    return str(folder)


def save_project_dump(state: dict) -> dict:
    """
    Creates an archive of the completed project: summary, transcript,
    perspectives, flow, expert research, final review, draft, and pipeline logs.
    Saves inside an article-specific folder under 'articles'.
    """
    article_name = get_article_name(state)
    folder = get_article_folder(state)
    article_path = folder / "article.txt"
    report_path = folder / "improvement_report.txt"
    full_log_path = folder / "project_log.txt"
    
    # Format the content
    lines = []
    lines.append("=" * 80)
    lines.append(f" ARTICLE PROJECT LOG: {article_name.upper()}")
    lines.append("=" * 80)
    lines.append(f"Timestamp:           {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Status:              Final Approved")
    lines.append(f"Folder:              {folder}")
    lines.append(f"User Idea:           {state.get('user_idea', 'N/A')}")
    lines.append(f"Requested Tone:      {state.get('requested_tone', 'N/A')}")
    lines.append(f"Target Word Count:   {state.get('article_length', 'N/A')}")
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

    # 2. Final Review Storage
    lines.append("## FINAL ARTICLE REVIEW STORAGE")
    lines.append("-" * 40)
    final_review = state.get("final_review", {}) or {}
    if final_review:
        lines.append(f"Idea Preservation: {final_review.get('idea_preservation', 'N/A')}")
        lines.append(f"Tone Match:        {final_review.get('tone_match', 'N/A')}")
        lines.append(f"Length Fit:        {final_review.get('length_fit', 'N/A')}")
        for label, key in [
            ("What Went Well", "went_well"),
            ("What Needs Redo", "needs_redo"),
            ("AI Assumptions", "ai_assumptions"),
        ]:
            lines.append(f"{label}:")
            items = final_review.get(key, [])
            if items:
                for item in items:
                    lines.append(f"  - {item}")
            else:
                lines.append("  - None")
    else:
        lines.append("No final review generated.")
    lines.append("\n" + "=" * 80 + "\n")
    
    # 3. Last Feedback Logged
    lines.append("## 🛠️ LAST FEEDBACK LOGGED")
    lines.append("-" * 40)
    feedback = state.get("user_feedback", "").strip()
    lines.append(feedback if feedback else "No feedback logged (Clean Approval).")
    lines.append("\n" + "=" * 80 + "\n")
    
    # 4. Cleaned Summary
    lines.append("## 📝 INTAKE CLEANED SUMMARY")
    lines.append("-" * 40)
    lines.append(state.get("summary", "").strip())
    lines.append("\n" + "=" * 80 + "\n")
    
    # 5. Original Transcript
    lines.append("## 🎤 ORIGINAL TRANSCRIPT / IDEA")
    lines.append("-" * 40)
    lines.append(state.get("transcript", "").strip())
    lines.append("\n" + "=" * 80 + "\n")
    
    # 6. Proposed Flow
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
    
    # 7. Writing Style & Profile
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
    
    # 8. Organized Departments & Topics
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
    
    # 9. Discovered Perspectives
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
    
    # 10. Expert Research Reports
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
                web_sources = r.get("web_sources", [])
                if web_sources:
                    lines.append("Web Sources:")
                    for ws in web_sources:
                        lines.append(f"  - {ws.get('title', 'N/A')}")
                        lines.append(f"    URL:   {ws.get('url', 'N/A')}")
                        lines.append(f"    Query: {ws.get('query', 'N/A')}")
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
                web_sources = getattr(r, "web_sources", [])
                if web_sources:
                    lines.append("Web Sources:")
                    for ws in web_sources:
                        lines.append(f"  - {ws.get('title', 'N/A')}")
                        lines.append(f"    URL:   {ws.get('url', 'N/A')}")
                        lines.append(f"    Query: {ws.get('query', 'N/A')}")
                lines.append("")
    else:
        lines.append("None generated.")
    lines.append("\n" + "=" * 80 + "\n")

    # 11. Curated Insights
    lines.append("## ✂️ CURATED KEY INSIGHTS")
    lines.append("-" * 40)
    insights = state.get("curated_insights", [])
    if insights:
        for ins in insights:
            lines.append(f"  - {ins}")
    else:
        lines.append("No curated insights.")
    lines.append("\n" + "=" * 80 + "\n")
    
    # 12. Pipeline Activity Log
    lines.append("## 📋 FULL PIPELINE LOG")
    lines.append("-" * 40)
    lines.append(format_log(state.get("pipeline_log", [])))
    lines.append("\n" + "=" * 80 + "\n")
    
    content = "\n".join(lines)

    with open(article_path, "w", encoding="utf-8") as f:
        f.write(state.get("draft", "").strip() + "\n")

    final_review = state.get("final_review", {}) or {}
    improvement_lines = [
        f"Improvement Report: {article_name}",
        "=" * (20 + len(article_name)),
        "",
        f"Requested Tone:    {state.get('requested_tone', 'N/A')}",
        f"Target Word Count: {state.get('article_length', 'N/A')}",
        "",
        "## Final Review",
        "",
    ]
    if final_review:
        improvement_lines.append(f"Idea Preservation: {final_review.get('idea_preservation', 'N/A')}")
        improvement_lines.append(f"Tone Match:        {final_review.get('tone_match', 'N/A')}")
        improvement_lines.append(f"Length Fit:        {final_review.get('length_fit', 'N/A')}")
        for label, key in [
            ("What Went Well", "went_well"),
            ("What Needs Redo", "needs_redo"),
            ("AI Assumptions", "ai_assumptions"),
        ]:
            improvement_lines.append("")
            improvement_lines.append(f"{label}:")
            items = final_review.get(key, [])
            if items:
                for item in items:
                    improvement_lines.append(f"  - {item}")
            else:
                improvement_lines.append("  - None")
    else:
        improvement_lines.append("No final review generated.")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(improvement_lines) + "\n")

    with open(full_log_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"\nProject details successfully written to: {folder}")
    return {
        "folder": str(folder),
    }