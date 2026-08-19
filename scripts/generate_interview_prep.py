#!/usr/bin/env python3
"""
AI Interview Preparation & STAR Method .docx Generator
Generates comprehensive role-specific interview preparation packets (.docx & markdown)
containing STAR stories, difficult technical questions, deep engineering answers,
and reverse questions to ask the interviewer.
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
CONFIG_DIR = REPO_ROOT / "config"
PREP_DIR = REPO_ROOT / "interview_prep"
APPS_DIR = REPO_ROOT / "applications"

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def load_candidate_profile():
    profile_file = CONFIG_DIR / "candidate_profile.json"
    if not profile_file.exists():
        profile_file = CONFIG_DIR / "candidate_profile.json.example"
    try:
        return json.loads(profile_file.read_text(encoding="utf-8"))
    except Exception:
        return {}

def generate_interview_prep(company: str, role: str, job_text: str = "") -> dict:
    PREP_DIR.mkdir(parents=True, exist_ok=True)
    profile = load_candidate_profile()
    personal = profile.get("personal", {})
    name = personal.get("full_name", "Engineering Candidate")
    
    clean_company = re.sub(r'\W+', '_', company).strip('_')
    clean_role = re.sub(r'\W+', '_', role).strip('_')
    docx_path = PREP_DIR / f"{clean_company}_{clean_role}_Interview_Prep.docx"
    
    doc = docx.Document()
    
    # Page setup
    for section in doc.sections:
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)

    # Styles & Colors
    NAVY = RGBColor(15, 32, 67)       # #0F2043
    SLATE = RGBColor(70, 80, 95)      # #46505F
    GOLD = RGBColor(197, 145, 22)     # #C59116
    BLACK = RGBColor(20, 20, 20)

    # Title
    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_before = Pt(0)
    title_p.paragraph_format.space_after = Pt(4)
    r_title = title_p.add_run(f"🎯 INTERVIEW PREPARATION DOSSIER")
    r_title.bold = True
    r_title.font.size = Pt(22)
    r_title.font.color.rgb = NAVY

    sub_p = doc.add_paragraph()
    sub_p.paragraph_format.space_after = Pt(14)
    r_sub = sub_p.add_run(f"{company} — {role} | Candidate: {name} | Generated: {datetime.now().strftime('%B %d, %Y')}")
    r_sub.font.size = Pt(11)
    r_sub.font.color.rgb = SLATE

    # Section 1: Executive 2-Minute Pitch
    h1 = doc.add_heading(level=1)
    r = h1.add_run("1. 'Tell Me About Yourself' (2-Minute Executive Pitch)")
    r.font.color.rgb = NAVY
    r.font.size = Pt(14)

    pitch_text = (
        f"I am an engineer passionate about building reliable, high-performance systems at the intersection of "
        f"software, firmware, and scalable architecture. Over the past several years, I have focused on solving complex "
        f"technical problems—from low-level register interfaces and real-time control algorithms to distributed telemetry services.\n\n"
        f"Most recently, as Lead Firmware and Systems Engineer, I architected the complete autonomous navigation stack for a competitive "
        f"embedded platform. I engineered dual-loop cascade PID controllers fusing 100 Hz IMU and ToF distance data on dual-core microcontrollers, "
        f"while optimizing pathfinding algorithms to operate within strict embedded memory limits.\n\n"
        f"I am deeply impressed by {company}'s engineering culture and technical rigor. I am excited about this {role} position because it "
        f"directly leverages my experience in deterministic control, performance optimization, and end-to-end system validation to solve high-impact challenges."
    )
    p_pitch = doc.add_paragraph(pitch_text)
    p_pitch.paragraph_format.space_after = Pt(12)

    # Section 2: STAR Story Bank
    h2 = doc.add_heading(level=1)
    r = h2.add_run("2. Comprehensive STAR Story Bank")
    r.font.color.rgb = NAVY
    r.font.size = Pt(14)

    stories = [
        {
            "title": "Story A: Autonomous Navigation & Cascade PID Control (Technical Rigor & Problem Solving)",
            "situation": "During high-speed autonomous maze speedruns, motor torque asymmetry and wheel slip caused cumulative angular drift, resulting in wall collisions at speeds exceeding 1.5 m/s.",
            "task": "I owned the control architecture and was tasked with designing a deterministic closed-loop feedback controller that guaranteed sub-millimeter lateral centering under dynamic acceleration.",
            "action": "I engineered a dual-loop cascade PID feedback controller in modern C++. The inner loop regulated 100 Hz angular velocity using quaternion orientation data from a 9-DOF IMU, while the outer loop fused lateral distance errors from VL53L1X Time-of-Flight laser sensors via exponential moving average (EMA) filtering. I validated state transitions inside a custom POSIX simulation environment before flashing the dual-core ESP32-S3 microcontroller.",
            "result": "Completely eliminated accumulated motor drift, reduced autonomous maze traversal time by 20%, and achieved reliable sub-millimeter centering across 50+ consecutive competition runs."
        },
        {
            "title": "Story B: Automated Packaging Line Optimization (Root-Cause Analysis & Throughput)",
            "situation": "At LPT-KEYPAK, automated high-speed packaging machinery commissioned for the Gates Foundation suffered intermittent jams during high-volume pilot production runs.",
            "task": "I was assigned to identify root causes of electromechanical failures, restore target throughput, and standardize operational procedures.",
            "action": "I applied structured 5-Whys root-cause analysis, tracing timing jitter to sensor relay bounce and PLC signal latency. I diagnosed 20+ industrial electrical schematics, recalibrated optical sensors, and authored comprehensive standard operating procedures (SOPs) for maintenance technicians.",
            "result": "Boosted packaging line throughput by 30%, reduced manufacturing defect rates by 15%, and ensured on-time deployment for global distribution."
        },
        {
            "title": "Story C: Cross-Functional Systems Integration & Club Leadership (Leadership & Delivery)",
            "situation": "Our collegiate robotics club lacked structured onboarding and version control, leading to siloed hardware and firmware teams and delayed competition deliverables.",
            "task": "As Lead Engineer and Co-President, I needed to restructure technical workflows, establish code reviews, and scale active project participation.",
            "action": "I established modular hardware abstraction layers in Git, instituted weekly sprint reviews with automated CI linting, and created structured hands-on firmware/PCB training workshops for 40+ engineering students.",
            "result": "Grew active membership by 900%, secured $2,500 in corporate sponsorship, and delivered our competition platform 3 weeks ahead of schedule."
        }
    ]

    for st in stories:
        tbl = doc.add_table(rows=5, cols=2)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        tbl.autofit = False
        tbl.columns[0].width = Inches(1.2)
        tbl.columns[1].width = Inches(5.8)

        # Header row
        hdr_cell = tbl.cell(0, 0)
        hdr_cell.merge(tbl.cell(0, 1))
        set_cell_background(hdr_cell, "0F2043")
        p_hdr = hdr_cell.paragraphs[0]
        p_hdr.paragraph_format.space_before = Pt(4)
        p_hdr.paragraph_format.space_after = Pt(4)
        r_h = p_hdr.add_run(st['title'])
        r_h.bold = True
        r_h.font.color.rgb = RGBColor(255, 255, 255)
        r_h.font.size = Pt(10.5)

        star_parts = [
            ("SITUATION", st["situation"], "F4F6F8"),
            ("TASK", st["task"], "FFFFFF"),
            ("ACTION", st["action"], "F4F6F8"),
            ("RESULT", st["result"], "EBF3FC")
        ]

        for idx, (label, desc_text, bg_color) in enumerate(star_parts, start=1):
            c_lbl = tbl.cell(idx, 0)
            c_val = tbl.cell(idx, 1)
            set_cell_background(c_lbl, bg_color)
            set_cell_background(c_val, bg_color)
            set_cell_margins(c_lbl, 80, 80, 100, 100)
            set_cell_margins(c_val, 80, 80, 100, 100)

            p_l = c_lbl.paragraphs[0]
            p_l.paragraph_format.space_before = Pt(2)
            p_l.paragraph_format.space_after = Pt(2)
            r_lbl = p_l.add_run(label)
            r_lbl.bold = True
            r_lbl.font.size = Pt(9.5)
            r_lbl.font.color.rgb = NAVY

            p_v = c_val.paragraphs[0]
            p_v.paragraph_format.space_before = Pt(2)
            p_v.paragraph_format.space_after = Pt(2)
            r_val = p_v.add_run(desc_text)
            r_val.font.size = Pt(9.5)
            r_val.font.color.rgb = BLACK

        doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # Section 3: Difficult Technical Questions & Deep Answers
    h3 = doc.add_heading(level=1)
    r = h3.add_run("3. Difficult Technical & Domain Questions (Deep Engineering Answers)")
    r.font.color.rgb = NAVY
    r.font.size = Pt(14)

    tech_qa = [
        (
            "Q1: How do you prevent priority inversion in real-time multithreaded systems (e.g. FreeRTOS)?",
            "Priority inversion occurs when a low-priority task holds a shared mutex needed by a high-priority task, while medium-priority tasks preempt the low-priority task, starving the high-priority task. "
            "To solve this: 1) Use Priority Inheritance Mutexes (e.g. xSemaphoreCreateMutex in FreeRTOS), which temporarily boosts the low-priority task's priority to match the blocked high-priority task. "
            "2) Keep critical sections minimal and non-blocking. 3) Utilize lockless lock-free ring buffers (atomic head/tail pointers) or FreeRTOS direct-to-task notifications for single-producer single-consumer queues instead of heavy mutexes."
        ),
        (
            "Q2: How do you diagnose and resolve I2C / SPI signal integrity issues on high-speed microcontroller buses?",
            "When encountering I2C bus lockups or NACK errors: 1) Attach a digital storage oscilloscope to SDA and SCL to inspect edge transition rise times (t_r). High bus capacitance (>400 pF) causes slow RC rise times; calculate pull-up resistor sizing R_min = (V_DD - V_OL) / I_OL and R_max = t_r / (0.8473 * C_b). "
            "2) Check for bus contention or missing ACK pulses with a logic analyzer protocol decoder. 3) Implement bus-recovery routines: if SDA is held LOW by a stuck slave, toggle SCL up to 9 clock pulses and issue a STOP condition to force slave reset."
        ),
        (
            "Q3: How do you balance memory constraints vs. algorithm speed on embedded platforms (e.g. A* / Flood Fill)?",
            "In microcontrollers with limited SRAM (e.g. 320 KB), standard graph representations consume excessive memory. "
            "1) Pack wall and visited states into bitwise bitmasks (4 bits per cell for N/S/E/W walls, 4 bits for distance metrics), reducing memory footprint by 87%. "
            "2) Use static flat arrays or fixed-size circular memory pools rather than dynamic heap allocation (malloc/new) to prevent heap fragmentation and non-deterministic allocation latency. "
            "3) Optimize cache locality by storing 2D grid coordinates in contiguous 1D row-major order."
        )
    ]

    for q, a in tech_qa:
        p_q = doc.add_paragraph()
        p_q.paragraph_format.space_before = Pt(6)
        p_q.paragraph_format.space_after = Pt(2)
        r_q = p_q.add_run(q)
        r_q.bold = True
        r_q.font.size = Pt(11)
        r_q.font.color.rgb = NAVY

        p_a = doc.add_paragraph()
        p_a.paragraph_format.space_after = Pt(8)
        r_a = p_a.add_run(a)
        r_a.font.size = Pt(10)
        r_a.font.color.rgb = BLACK

    # Section 4: Behavioral Curveballs & Weakness Answers
    h4 = doc.add_heading(level=1)
    r = h4.add_run("4. Behavioral Curveball & Weakness Questions")
    r.font.color.rgb = NAVY
    r.font.size = Pt(14)

    curveballs = [
        (
            "Q: What is your greatest weakness?",
            "Earlier in my engineering work, I had a tendency to dive directly into optimizing code performance and edge cases before validating the minimum viable prototype with the broader team. For example, during our initial robot simulator build, I spent days micro-optimizing inter-process pipe serialization before our physics model was fully settled. I recognized that premature optimization can slow down team velocity, so I adopted an iterative milestone approach: build and benchmark an end-to-end working baseline first, identify empirical bottlenecks using profilers, and only then optimize the critical path."
        ),
        (
            "Q: Tell me about a time you had a technical disagreement with a teammate.",
            "During a hardware redesign, a team member wanted to use a software-emulated bit-banged SPI interface to save PCB traces, while I advocated for dedicated hardware SPI with a small demux. Rather than debating opinions, I set up a bench test measuring CPU overhead and latency under heavy sensor polling. The empirical data showed bit-banging consumed 45% of CPU cycles, creating jitter in our PID loop. Seeing the data, we agreed on the hardware bus design, and I helped route the additional differential traces to keep our board compact."
        )
    ]

    for q, a in curveballs:
        p_q = doc.add_paragraph()
        p_q.paragraph_format.space_before = Pt(4)
        p_q.paragraph_format.space_after = Pt(2)
        r_q = p_q.add_run(q)
        r_q.bold = True
        r_q.font.size = Pt(10.5)
        r_q.font.color.rgb = NAVY

        p_a = doc.add_paragraph()
        p_a.paragraph_format.space_after = Pt(6)
        r_a = p_a.add_run(a)
        r_a.font.size = Pt(10)
        r_a.font.color.rgb = BLACK

    # Section 5: Reverse Questions to Ask Interviewer
    h5 = doc.add_heading(level=1)
    r = h5.add_run("5. High-Impact Questions to Ask the Engineering Team")
    r.font.color.rgb = NAVY
    r.font.size = Pt(14)

    questions = [
        "1. For the Hiring Manager: What does a standout performance look like for an engineer in this role in their first 90 days?",
        "2. For Senior Engineers: What is currently the most challenging technical bottleneck or architectural trade-off your team is solving this quarter?",
        "3. For the Team: How does the team manage hardware-in-the-loop validation and CI/CD testing across firmware and hardware revisions?",
        "4. Culture & Growth: What opportunities exist for junior engineers to participate in system architecture reviews and cross-functional design discussions?"
    ]
    for q in questions:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(3)
        r_q = p.add_run(q)
        r_q.font.size = Pt(10)
        r_q.font.color.rgb = NAVY

    doc.save(str(docx_path))
    print(f"[✓] Generated Interview Prep Document (.docx): {docx_path}")
    return {"docx_path": str(docx_path)}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate STAR Interview Prep .docx packet.")
    parser.add_argument("--company", type=str, required=True, help="Target company name")
    parser.add_argument("--role", type=str, required=True, help="Target role title")
    parser.add_argument("--job-text", type=str, default="", help="Job description text")
    args = parser.parse_args()

    generate_interview_prep(args.company, args.role, args.job_text)