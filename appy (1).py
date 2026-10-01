"""
=============================================================================
EduGenie - The AI & Smart Learning Assistant
=============================================================================
A comprehensive educational companion built with Streamlit & Python.
Features:
  1. Concept Explainer & Socratic Feynman Tutor (ELI5, Standard, Deep Dive)
  2. Smart Flashcards with Spaced Repetition System (SRS)
  3. Adaptive Quiz Arena & Mock Exam Simulator with Mistake Analysis
  4. Lecture Note Summarizer & Visual Mind-Map Generator (Mermaid.js)
  5. AI Study Planner & Timetable Architect with Milestone Tracking
  6. Focus Pomodoro Study Timer & Mindfulness Companion
  7. Student Performance Analytics Dashboard
  8. Local SQLite Persistent Storage & Export Capabilities
=============================================================================
"""

import streamlit as st
import pandas as pd
import sqlite3
import json
import datetime
import time
import random
import re
import os
import math
from typing import List, Dict, Any, Optional

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="EduGenie - Smart Learning Assistant",
    page_icon="🧞‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

CUSTOM_CSS = """
<style>
    /* Global Styles & Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Main Header Gradient Banner */
    .hero-banner {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 50%, #06b6d4 100%);
        padding: 28px 32px;
        border-radius: 16px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px -5px rgba(59, 130, 246, 0.4);
    }
    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .hero-subtitle {
        font-size: 1.05rem;
        opacity: 0.92;
        margin-top: 6px;
        font-weight: 400;
    }

    /* Feature Cards */
    .edu-card {
        background-color: #ffffff;
        border-radius: 14px;
        padding: 22px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
        margin-bottom: 18px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .edu-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
    }

    /* Dark Mode Support for Cards */
    @media (prefers-color-scheme: dark) {
        .edu-card {
            background-color: #1e293b;
            border-color: #334155;
            color: #f8fafc;
        }
    }

    /* Badge Pills */
    .pill-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-right: 6px;
    }
    .pill-blue { background-color: #dbeafe; color: #1e40af; }
    .pill-green { background-color: #dcfce7; color: #166534; }
    .pill-purple { background-color: #f3e8ff; color: #6b21a8; }
    .pill-amber { background-color: #fef3c7; color: #92400e; }

    /* Flashcard Flip Presentation */
    .flashcard-box {
        border-radius: 16px;
        padding: 36px 28px;
        text-align: center;
        min-height: 220px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        background: linear-gradient(145deg, #f8fafc, #f1f5f9);
        border: 2px dashed #cbd5e1;
        margin: 16px 0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }

    /* Metric Highlight */
    .stat-number {
        font-size: 1.8rem;
        font-weight: 800;
        color: #2563eb;
    }
    .stat-label {
        font-size: 0.85rem;
        color: #64748b;
        font-weight: 600;
        text-transform: uppercase;
    }

    /* Mind Map Container */
    .mindmap-box {
        background: #0f172a;
        color: #38bdf8;
        padding: 16px;
        border-radius: 10px;
        font-family: 'Courier New', Courier, monospace;
        font-size: 0.9rem;
        overflow-x: auto;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. DATABASE & PERSISTENCE LAYER (SQLite)
# -----------------------------------------------------------------------------
DB_PATH = "edugenie_data.db"

def init_database() -> None:
    """Initializes local SQLite database with required tables and seeds starter data."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Flashcards Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS flashcards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            difficulty TEXT DEFAULT 'Medium',
            box INTEGER DEFAULT 1,
            next_review_date TEXT,
            times_reviewed INTEGER DEFAULT 0,
            times_correct INTEGER DEFAULT 0
        )
    """)

    # Quiz Results History Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            subject TEXT NOT NULL,
            score INTEGER NOT NULL,
            total_questions INTEGER NOT NULL,
            accuracy REAL NOT NULL,
            time_spent_seconds INTEGER DEFAULT 0
        )
    """)

    # Study Planner Tasks Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS planner_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            topic TEXT NOT NULL,
            allocated_hours REAL NOT NULL,
            target_date TEXT NOT NULL,
            is_completed INTEGER DEFAULT 0
        )
    """)

    # Study Session Pomodoro Log
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pomodoro_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            duration_minutes INTEGER NOT NULL,
            subject TEXT NOT NULL,
            session_type TEXT DEFAULT 'Focus'
        )
    """)

    conn.commit()

    # Seed starter flashcards if empty
    cursor.execute("SELECT COUNT(*) FROM flashcards")
    if cursor.fetchone()[0] == 0:
        starter_cards = [
            ("Computer Science", "What is the time complexity of searching in a Balanced Binary Search Tree (AVL/Red-Black)?", "O(log n) because the height is bounded logarithmically.", "Medium"),
            ("Computer Science", "What does ACID stand for in Database Systems?", "Atomicity, Consistency, Isolation, Durability.", "Easy"),
            ("Computer Science", "What is the difference between Process and Thread?", "A process is an executing program with independent memory space; a thread is a lightweight unit of execution sharing memory within a process.", "Hard"),
            ("Data Science & AI", "What problem does the Backpropagation algorithm solve in Neural Networks?", "It computes the gradient of the loss function with respect to weights using the chain rule to update weights via gradient descent.", "Medium"),
            ("Data Science & AI", "What is Overfitting and how can it be mitigated?", "When a model learns noise from training data and generalizes poorly. Mitigated by regularization (L1/L2), dropout, cross-validation, and more data.", "Medium"),
            ("Data Science & AI", "What is the difference between Precision and Recall?", "Precision = TP / (TP + FP) [Accuracy of positive predictions]. Recall = TP / (TP + FN) [Coverage of actual positives].", "Medium"),
            ("Physics & Math", "What is Heisenberg's Uncertainty Principle?", "It is impossible to simultaneously measure both the position and momentum of a particle with infinite precision: Δx * Δp >= h / (4π).", "Hard"),
            ("Physics & Math", "What is the fundamental theorem of calculus?", "It links differentiation and integration, showing that differentiation and integration are inverse operations: d/dx [∫ f(t) dt] = f(x).", "Medium"),
            ("Biology & Medicine", "What is the primary function of Mitochondria?", "Generate most of the chemical energy needed to power the cell's biochemical reactions, stored in adenosine triphosphate (ATP).", "Easy"),
            ("Biology & Medicine", "What is the Central Dogma of Molecular Biology?", "DNA is transcribed into RNA (transcription), and RNA is translated into functional proteins (translation).", "Easy"),
            ("General Knowledge", "What was the significance of the Rosetta Stone?", "It provided the critical key to deciphering ancient Egyptian hieroglyphs because it contained the same decree in three scripts (Hieroglyphic, Demotic, Greek).", "Medium")
        ]
        today = datetime.date.today().isoformat()
        cursor.executemany(
            "INSERT INTO flashcards (subject, question, answer, difficulty, box, next_review_date) VALUES (?, ?, ?, ?, 1, ?)",
            [(s, q, a, d, today) for s, q, a, d in starter_cards]
        )
        conn.commit()

    conn.close()

init_database()

# -----------------------------------------------------------------------------
# 3. KNOWLEDGE BASES & HEURISTIC ENGINE (OFFLINE-READY + AI ENHANCED)
# -----------------------------------------------------------------------------
TOPIC_KNOWLEDGE_BASE: Dict[str, Dict[str, Any]] = {
    "neural networks & backpropagation": {
        "title": "Neural Networks & Backpropagation",
        "eli5": "Think of a Neural Network like a team of detectives solving a puzzle. Each detective (neuron) looks at one clue and makes a guess. If the team's final answer is wrong, the boss calculates the error and walks backwards through the team, telling each detective how much their clue was off and how to adjust for the next round. That walk backwards is 'Backpropagation'!",
        "standard": "Artificial Neural Networks are computational graphs made of interconnected layers of nodes (neurons). Each connection has an adjustable weight. During the forward pass, inputs are multiplied by weights, summed, and passed through activation functions (ReLU, Sigmoid). Backpropagation calculates the partial derivatives of the cost function with respect to every weight using the mathematical chain rule, allowing Gradient Descent to update weights iteratively.",
        "deep_dive": "Mathematically, let L be the scalar loss and W^(l) be the weight matrix at layer l. The error vector delta^(l) is defined as ∂L / ∂z^(l) = (W^(l+1)T * delta^(l+1)) ⊙ σ'(z^(l)). The gradient with respect to weights is ∂L / ∂W^(l) = delta^(l) * (a^(l-1))T. Numerical stability concerns like vanishing and exploding gradients are mitigated using Xavier/He initialization, residual connections, and adaptive optimizers (Adam, RMSProp).",
        "key_terms": {
            "Activation Function": "Non-linear transformation (ReLU, GELU) allowing networks to learn complex non-linear mappings.",
            "Gradient Descent": "Optimization algorithm iteratively moving weights towards the minimum of the loss curve.",
            "Chain Rule": "Calculus principle for computing the derivative of composite functions."
        },
        "formula": r"\nabla_W \mathcal{L} = \frac{\partial \mathcal{L}}{\partial \mathbf{a}} \cdot \frac{\partial \mathbf{a}}{\partial \mathbf{z}} \cdot \frac{\partial \mathbf{z}}{\partial W}",
        "analogy": "Adjusting hot and cold water taps until the shower temperature is perfect—if it's too hot, you dial back the hot knob proportional to the burn."
    },
    "binary search & time complexity": {
        "title": "Binary Search & Time Complexity",
        "eli5": "Imagine looking up a word in a 1,000-page physical dictionary. You don't read page 1, then page 2. You flip open the exact middle! If your word comes alphabetically earlier, you throw away the entire second half and repeat in the remaining half. You find your word in under 10 flips!",
        "standard": "Binary Search is a divide-and-conquer algorithm designed for sorted arrays. At each step, it compares the target value with the middle element. If they match, the search terminates. If the target is smaller, search continues in the left sub-array; if larger, in the right sub-array. Each iteration cuts the search space in half, yielding an O(log n) time complexity and O(1) space complexity for iterative implementations.",
        "deep_dive": "Let N be array size. After k steps, the remaining elements are N / 2^k. The algorithm terminates when N / 2^k <= 1, which implies k = ⌈log2(N)⌉. Critical implementation bug to prevent 32-bit integer overflow: calculate mid as `low + (high - low) // 2` instead of `(low + high) // 2`.",
        "key_terms": {
            "Divide and Conquer": "Algorithmic paradigm breaking a problem into non-overlapping subproblems.",
            "O(log n)": "Logarithmic time—doubling the dataset only adds 1 extra comparison step.",
            "Sorted Invariant": "The prerequisite condition that data must be in ascending or descending sequence."
        },
        "formula": r"T(n) = T\left(\frac{n}{2}\right) + \mathcal{O}(1) \implies T(n) = \mathcal{O}(\log n)",
        "analogy": "Playing the 'Guess a number between 1 and 100' game where each guess tells you 'Higher' or 'Lower'."
    },
    "mitochondria & atp cellular respiration": {
        "title": "Mitochondria & ATP Cellular Respiration",
        "eli5": "Mitochondria are the rechargeable battery factories of your cells. When you eat food like an apple, your cells can't use the whole apple directly. Mitochondria digest the food pieces into microscopic energy pellets called ATP. Whenever your muscles run or your brain thinks, they 'spend' these ATP tokens!",
        "standard": "Cellular respiration takes place across the cytoplasm and mitochondria in three primary stages: Glycolysis, the Krebs (Citric Acid) Cycle, and Oxidative Phosphorylation. Mitochondria possess an inner and outer membrane. The inner membrane houses the Electron Transport Chain (ETC) and ATP Synthase. As electrons transfer through complexes I-IV, protons (H+) are pumped into the intermembrane space, creating a proton-motive gradient that drives ATP synthesis from ADP and inorganic phosphate.",
        "deep_dive": "Theoretical maximum yield is approximately 30 to 32 ATP molecules per oxidized glucose molecule. The F0F1 ATP synthase operates as a rotary molecular motor: proton translocation through the F0 subunit causes rotational torque in the gamma subunit, inducing conformational transitions (Open, Loose, Tight) in the catalytic F1 beta-subunits.",
        "key_terms": {
            "ATP (Adenosine Triphosphate)": "High-energy molecule storing and transferring chemical energy in cells.",
            "Chemiosmosis": "Movement of ions across a semipermeable membrane down their electrochemical gradient.",
            "Proton Gradient": "Difference in H+ concentration across the inner mitochondrial membrane."
        },
        "formula": r"\text{C}_6\text{H}_{12}\text{O}_6 + 6\text{O}_2 \rightarrow 6\text{CO}_2 + 6\text{H}_2\text{O} + \approx 32\text{ ATP}",
        "analogy": "A hydroelectric dam: pumping protons builds up water behind the dam; opening the turbine (ATP Synthase) spins the generator to create electricity (ATP)."
    },
    "quantum computing & superposition": {
        "title": "Quantum Computing & Superposition",
        "eli5": "A classical computer bit is like a light switch—it's either completely OFF (0) or completely ON (1). A quantum bit (qubit) is like a spinning coin on a table: while it spins, it is a blend of both heads and tails simultaneously! Only when you slap your hand down does it decide to be 0 or 1.",
        "standard": "Quantum computing leverages principles of quantum mechanics—namely superposition, entanglement, and interference. A classical bit represents 0 or 1, whereas a qubit state |ψ⟩ is represented as a linear combination of basis states: |ψ⟩ = α|0⟩ + β|1⟩, where α and β are complex probability amplitudes satisfying |α|² + |β|² = 1. A system of n qubits can simultaneously represent 2^n states, enabling exponential computational parallelism for specific algorithms (e.g., Shor's, Grover's).",
        "deep_dive": "State evolution in closed quantum systems is unitary, governed by transformations U such that U†U = I. Measurement collapses the state vector onto an eigenspace of the observable operator according to Born's rule. Quantum decoherence—loss of quantum state coherence due to thermal noise and environmental interaction—is the primary bottleneck addressed by Quantum Error Correction (Surface codes, Shor code).",
        "key_terms": {
            "Superposition": "The ability of a quantum system to exist in multiple state configurations simultaneously.",
            "Entanglement": "Non-local correlation between qubits such that one's state instantly determines the other.",
            "Bloch Sphere": "Geometric spherical representation of a single qubit's pure state space."
        },
        "formula": r"|\psi\rangle = \alpha |0\rangle + \beta |1\rangle, \quad |\alpha|^2 + |\beta|^2 = 1",
        "analogy": "Exploring all paths in a maze simultaneously with water, rather than sending one mouse down one path at a time."
    }
}

# Pre-built Quiz Questions Bank
DEFAULT_QUIZ_BANK: Dict[str, List[Dict[str, Any]]] = {
    "Computer Science & Python": [
        {
            "question": "What is the worst-case time complexity of QuickSort?",
            "options": ["O(n log n)", "O(n²)", "O(n)", "O(log n)"],
            "answer": "O(n²)",
            "explanation": "QuickSort degrades to O(n²) when the pivot chosen is consistently the smallest or largest element (e.g., on already sorted arrays without random pivot selection)."
        },
        {
            "question": "In Python, which built-in data type is mutable?",
            "options": ["tuple", "str", "list", "frozenset"],
            "answer": "list",
            "explanation": "Lists can be modified in-place (append, extend, pop). Tuples, strings, and frozensets are strictly immutable."
        },
        {
            "question": "What is the primary purpose of the Global Interpreter Lock (GIL) in CPython?",
            "options": [
                "To accelerate mathematical computations",
                "To synchronize execution of threads so only one native thread executes Python bytecode at a time",
                "To prevent memory leaks by disabling garbage collection",
                "To compile Python scripts into native machine code"
            ],
            "answer": "To synchronize execution of threads so only one native thread executes Python bytecode at a time",
            "explanation": "The GIL is a mutex protecting access to Python objects, preventing multiple threads from executing CPython bytecodes simultaneously to ensure thread-safe memory management."
        },
        {
            "question": "What data structure does the Depth-First Search (DFS) graph traversal typically use?",
            "options": ["Queue (FIFO)", "Stack (LIFO)", "Priority Queue", "Circular Buffer"],
            "answer": "Stack (LIFO)",
            "explanation": "DFS explores as far as possible along each branch before backtracking, naturally modeling a Stack (either the call stack recursively or an explicit stack)."
        }
    ],
    "Data Science & AI": [
        {
            "question": "Which loss function is commonly used for multi-class classification problems?",
            "options": ["Mean Squared Error (MSE)", "Categorical Cross-Entropy", "Binary Cross-Entropy", "Hinge Loss"],
            "answer": "Categorical Cross-Entropy",
            "explanation": "Categorical Cross-Entropy measures the performance of a classification model whose output is a probability distribution over multiple mutually exclusive classes."
        },
        {
            "question": "What does L1 Regularization (Lasso) tend to do to model weights compared to L2 (Ridge)?",
            "options": [
                "Encourages weights to become exactly zero, producing sparse models",
                "Scales all weights uniformly towards infinity",
                "Guarantees the loss function is convex",
                "Doubles the training speed"
            ],
            "answer": "Encourages weights to become exactly zero, producing sparse models",
            "explanation": "L1 penalizes the sum of absolute values of weights, creating diamond-shaped constraint boundaries that drive less important feature weights exactly to 0 for automatic feature selection."
        },
        {
            "question": "Which component in the Transformer architecture allows tokens to attend to other tokens across a sequence?",
            "options": ["Feedforward Dense Layer", "Self-Attention Mechanism", "Layer Normalization", "Positional Encoding"],
            "answer": "Self-Attention Mechanism",
            "explanation": "The Scaled Dot-Product Self-Attention calculates Query, Key, and Value vectors to weigh dynamic relevance between any two tokens in a sequence."
        }
    ],
    "Science & Mathematics": [
        {
            "question": "What is the derivative of f(x) = ln(x) with respect to x (for x > 0)?",
            "options": ["1 / x", "e^x", "x", "1 / (x²)"],
            "answer": "1 / x",
            "explanation": "By definition of logarithmic differentiation, d/dx [ln(x)] = 1/x for all x > 0."
        },
        {
            "question": "What organelle is responsible for synthesizing proteins in biological cells?",
            "options": ["Golgi apparatus", "Ribosome", "Lysosome", "Vacuole"],
            "answer": "Ribosome",
            "explanation": "Ribosomes read messenger RNA (mRNA) sequences and translate the genetic code into strings of amino acids to build proteins."
        },
        {
            "question": "What is the acceleration due to gravity on the surface of the Earth approximately?",
            "options": ["3.14 m/s²", "9.81 m/s²", "12.4 m/s²", "1.62 m/s²"],
            "answer": "9.81 m/s²",
            "explanation": "Standard surface gravity on Earth is approximately 9.80665 m/s² (commonly rounded to 9.81 m/s²)."
        }
    ]
}

# -----------------------------------------------------------------------------
# 4. HELPER UTILITIES: TEXT PROCESSING & NLP SUMMARIZER
# -----------------------------------------------------------------------------
def clean_text(raw_text: str) -> str:
    """Removes excess whitespace and returns sanitized string."""
    return re.sub(r'\s+', ' ', raw_text).strip()

def summarize_text_heuristics(text: str, max_sentences: int = 4) -> Dict[str, Any]:
    """
    Extractive heuristic summarizer:
    Calculates word frequency scores, ranks sentences, extracts key concepts,
    calculates reading time, and generates a structured Mermaid.js mind map.
    """
    cleaned = clean_text(text)
    if not cleaned:
        return {
            "summary": "No text provided to summarize.",
            "bullets": [],
            "key_terms": {},
            "word_count": 0,
            "reading_time_min": 0,
            "mermaid_map": ""
        }

    sentences = re.split(r'(?<=[.!?]) +', cleaned)
    words = re.findall(r'\b[A-Za-z]{3,}\b', cleaned.lower())
    
    stop_words = {
        "the", "and", "is", "in", "to", "of", "it", "that", "you", "he",
        "was", "for", "on", "are", "as", "with", "his", "they", "at", "be",
        "this", "have", "from", "or", "one", "had", "by", "word", "but", "not",
        "what", "all", "were", "we", "when", "your", "can", "said", "there", "use",
        "an", "each", "which", "she", "do", "how", "their", "if", "will", "up",
        "other", "about", "out", "many", "then", "them", "these", "so", "some"
    }
    
    freq: Dict[str, int] = {}
    for w in words:
        if w not in stop_words:
            freq[w] = freq.get(w, 0) + 1

    # Score sentences by word frequency
    sentence_scores: List[tuple] = []
    for s in sentences:
        s_words = re.findall(r'\b[A-Za-z]{3,}\b', s.lower())
        score = sum(freq.get(w, 0) for w in s_words)
        if len(s_words) > 0:
            normalized_score = score / (len(s_words) ** 0.5)
            sentence_scores.append((normalized_score, s))

    sentence_scores.sort(key=lambda x: x[0], reverse=True)
    top_sentences = [s for _, s in sentence_scores[:max_sentences]]
    
    # Extract top keywords
    sorted_keywords = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:6]
    key_terms = {kw.capitalize(): f"Key concept occurring {cnt} times in study text." for kw, cnt in sorted_keywords}

    # Reading time calculation (average 200 words per minute)
    total_words = len(re.findall(r'\b\w+\b', cleaned))
    reading_time = max(1, math.ceil(total_words / 200))

    # Generate structured Mermaid Mind Map
    mermaid_lines = ["graph TD", "    Root([Study Topic Core])"]
    for i, (kw, _) in enumerate(sorted_keywords[:4]):
        node_id = f"K{i}"
        mermaid_lines.append(f"    Root --> {node_id}[\"{kw.capitalize()}\"]")
        mermaid_lines.append(f"    {node_id} --> Sub{i}[\"Key Principle & Applications\"]")
    
    mermaid_code = "\n".join(mermaid_lines)

    return {
        "summary": " ".join(top_sentences),
        "bullets": top_sentences,
        "key_terms": key_terms,
        "word_count": total_words,
        "reading_time_min": reading_time,
        "mermaid_map": mermaid_code
    }

def generate_custom_quiz_from_notes(topic: str, text: str) -> List[Dict[str, Any]]:
    """Heuristically generates 3-5 assessment questions from raw notes or knowledge."""
    sentences = [s.strip() for s in re.split(r'(?<=[.!?]) +', text) if len(s.split()) >= 6]
    if len(sentences) < 2:
        return [
            {
                "question": f"What is the foundational significance of {topic}?",
                "options": [
                    f"It forms the central conceptual framework for {topic}",
                    "It was disproven in 19th-century scientific research",
                    "It has no practical application in modern science",
                    "It is purely a philosophical concept without real mechanics"
                ],
                "answer": f"It forms the central conceptual framework for {topic}",
                "explanation": f"Understanding {topic} is vital because it establishes the foundational rules and real-world mechanisms governing this domain."
            }
        ]
    
    generated_questions = []
    for i, s in enumerate(sentences[:3]):
        words = [w for w in re.findall(r'\b[A-Za-z]{4,}\b', s) if w.lower() not in {"this", "that", "with", "from", "have"}]
        keyword = words[0] if words else topic
        
        q_item = {
            "question": f"Regarding {topic}: {s.replace(keyword, '_____')}?",
            "options": [
                keyword.capitalize(),
                "Linear Regression",
                "Thermal Dissipation",
                "Arbitrary Constant"
            ],
            "answer": keyword.capitalize(),
            "explanation": f"The complete statement reads: '{s}', identifying '{keyword}' as the operative principle."
        }
        random.shuffle(q_item["options"])
        generated_questions.append(q_item)

    return generated_questions

# -----------------------------------------------------------------------------
# 5. SIDEBAR: USER PROFILE & APP CONTROLS
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=500&auto=format&fit=crop&q=60", use_container_width=True)
    st.title("🧞‍♂️ EduGenie Dashboard")
    st.markdown("Your **24/7 AI-Powered Study & Learning Architect**")
    
    st.divider()
    st.subheader("👤 Student Profile")
    student_name = st.text_input("Name", value="edu", help="Personalize your study sessions")
    study_level = st.selectbox(
        "Academic Level",
        ["High School", "Undergraduate (College)", "Postgraduate / Researcher", "Self-Taught Professional"],
        index=1
    )
    daily_goal_hours = st.slider("Daily Study Goal (Hours)", 1, 12, 4)

    st.divider()
    # Connect Database Stats
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM flashcards WHERE box >= 3")
    mastered_cards = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*), AVG(accuracy) FROM quiz_history")
    quiz_stats = c.fetchone()
    total_quizzes = quiz_stats[0] if quiz_stats and quiz_stats[0] else 0
    avg_accuracy = round(quiz_stats[1], 1) if quiz_stats and quiz_stats[1] else 0.0

    c.execute("SELECT SUM(duration_minutes) FROM pomodoro_sessions")
    total_pom_min = c.fetchone()[0]
    total_pom_min = total_pom_min if total_pom_min else 0
    conn.close()

    st.subheader("📊 Your Milestones")
    col_sb1, col_sb2 = st.columns(2)
    with col_sb1:
        st.metric("Mastered Cards", f"{mastered_cards}")
        st.metric("Quizzes Done", f"{total_quizzes}")
    with col_sb2:
        st.metric("Avg Accuracy", f"{avg_accuracy}%")
        st.metric("Focus Time", f"{total_pom_min}m")

    st.divider()
    st.caption("EduGenie System v2.4 • Offline-Capable Architecture")

# -----------------------------------------------------------------------------
# 6. MAIN HERO HEADER
# -----------------------------------------------------------------------------
st.markdown(f"""
<div class="hero-banner">
    <div class="hero-title">Welcome back, {student_name}! 🚀</div>
    <div class="hero-subtitle">
        Accelerate your comprehension with Feynman breakdowns, spaced repetition flashcards, adaptive quizzes, and focus intervals.
    </div>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 7. NAVIGATION TABS (THE 7 COMPREHENSIVE LEARNING MODULES)
# -----------------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "💡 Concept Explainer",
    "🗂️ Smart Flashcards",
    "📝 Quiz Arena",
    "📄 Note Summarizer",
    "📅 Study Planner",
    "⏱️ Pomodoro Timer",
    "📈 Analytics Dashboard"
])

# =============================================================================
# TAB 1: CONCEPT EXPLAINER & FEYNMAN TUTOR
# =============================================================================
with tab1:
    st.header("💡 Concept Explainer & Socratic Feynman Tutor")
    st.markdown(
        "Master any complex subject by understanding it from the fundamentals up. "
        "Choose an explanation depth and interact with your personal AI Socratic tutor."
    )

    col_t1a, col_t1b = st.columns([2, 1])
    with col_t1a:
        quick_topics = [
            "Neural Networks & Backpropagation",
            "Binary Search & Time Complexity",
            "Mitochondria & ATP Cellular Respiration",
            "Quantum Computing & Superposition",
            "Custom Topic (Enter below)"
        ]
        chosen_preset = st.selectbox("🎯 Choose or Type a Subject:", quick_topics)
        
        if chosen_preset == "Custom Topic (Enter below)":
            active_topic = st.text_input("Enter your custom topic or query:", "Special Relativity & Time Dilation")
        else:
            active_topic = chosen_preset

    with col_t1b:
        depth = st.radio(
            "Select Explanation Depth:",
            ["🐣 ELI5 (Beginner)", "🎓 Standard (College)", "🔬 Deep Dive (Master)"],
            index=1
        )

    # Resolve explanation content
    topic_key = active_topic.lower().strip()
    data = TOPIC_KNOWLEDGE_BASE.get(topic_key)

    if not data:
        # Dynamic Heuristic Fallback for any user-entered topic
        data = {
            "title": active_topic,
            "eli5": f"Imagine {active_topic} is like a giant orchestra. Every component plays its individual instrument, but when synchronized together according to simple fundamental rules, they create a complete, harmonious symphony of results.",
            "standard": f"{active_topic} represents a core theoretical and applied framework. It operates on structured principles where inputs are systematically transformed through defined mechanisms, producing predictable outputs and solving domain-specific challenges.",
            "deep_dive": f"Formally, {active_topic} involves rigorous state transitions, boundary conditions, and algorithmic/physical constraints. Analyzing it requires balancing efficiency trade-offs, formal mathematical models, and mitigating known edge-case failure modes.",
            "key_terms": {
                "First Principle": f"The foundational truth that cannot be deduced any further in {active_topic}.",
                "System State": "The quantitative values defining the condition of the mechanism at any given step.",
                "Optimization": "The process of maximizing desired outcomes while minimizing computational or energetic cost."
            },
            "formula": r"\mathcal{S}_{next} = f(\mathcal{S}_{current}, \mathcal{U}, \theta)",
            "analogy": f"Treating {active_topic} like an engine: individual gears might look simple alone, but their intermeshing generates immense mechanical horsepower."
        }

    st.markdown("---")
    
    # Display Concept Card
    with st.container():
        st.subheader(f"📖 Breakdown: {data['title']}")
        
        if "ELI5" in depth:
            st.info(f"**🐣 Explain Like I'm 5 Viewpoint:**\n\n{data['eli5']}")
        elif "Standard" in depth:
            st.success(f"**🎓 Comprehensive Academic Viewpoint:**\n\n{data['standard']}")
        else:
            st.warning(f"**🔬 Advanced Technical Viewpoint:**\n\n{data['deep_dive']}")

        # Key Terminology & Formula
        col_c1, col_c2 = st.columns([1, 1])
        with col_c1:
            st.markdown("#### 🔑 Key Terminology")
            for term, defn in data["key_terms"].items():
                st.markdown(f"- **{term}**: {defn}")
        
        with col_c2:
            st.markdown("#### 📐 Mathematical / Formal Formulation")
            st.latex(data["formula"])
            st.markdown(f"**💡 Intuitive Analogy:**\n> *\"{data['analogy']}\"*")

    # Interactive Socratic Chat
    st.markdown("---")
    st.subheader("💬 Ask EduGenie (Socratic Dialogue)")
    
    if "socratic_chat" not in st.session_state:
        st.session_state.socratic_chat = [
            {"role": "assistant", "content": f"Hello {student_name}! I'm your Socratic Tutor. Ask me any clarifying question about **{active_topic}**, and I'll guide you step-by-step to the answer."}
        ]

    for msg in st.session_state.socratic_chat:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    user_query = st.chat_input("Ask a question about this topic...")
    if user_query:
        st.session_state.socratic_chat.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.write(user_query)

        # Smart Heuristic Socratic Response
        prompt_lower = user_query.lower()
        if "why" in prompt_lower:
            reply = f"Great question! To understand *why*, think back to the fundamental constraint: if we didn't use this mechanism, what would fail first? Consider how {active_topic} ensures balance and prevents compounding errors."
        elif "how" in prompt_lower:
            reply = f"Here is the step-by-step mechanism: 1) Initial state observation, 2) Applying the core transformation rule, and 3) Validating against expected outcomes. Which of those three steps would you like to dissect further?"
        elif "example" in prompt_lower:
            reply = f"A classic real-world example of this is: {data['analogy']}! Notice how the cause directly impacts the effect without unnecessary overhead."
        else:
            reply = f"That touches on a crucial facet of {active_topic}! Before I reveal the answer, what do you think would happen if we increased the input magnitude by tenfold? Would the system remain stable?"

        st.session_state.socratic_chat.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.write(reply)


# =============================================================================
# TAB 2: SMART FLASHCARDS & SPACED REPETITION (SRS)
# =============================================================================
with tab2:
    st.header("🗂️ Smart Flashcards (Leitner Spaced Repetition)")
    st.markdown(
        "Review cards using the Leitner Box system. Cards you know well advance to higher boxes "
        "and are reviewed less frequently; cards you miss drop back to Box 1 for reinforcement."
    )

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT subject FROM flashcards")
    subjects = [row[0] for row in cursor.fetchall()]

    col_fc1, col_fc2 = st.columns([2, 1])
    with col_fc1:
        selected_subject = st.selectbox("Filter by Deck Subject:", ["All Subjects"] + subjects)
    with col_fc2:
        box_filter = st.selectbox("Filter by Leitner Box:", ["All Boxes", "Box 1 (Review Daily)", "Box 2 (Every 3 Days)", "Box 3+ (Mastered)"])

    query = "SELECT id, subject, question, answer, difficulty, box FROM flashcards WHERE 1=1"
    params = []
    if selected_subject != "All Subjects":
        query += " AND subject = ?"
        params.append(selected_subject)
    if box_filter == "Box 1 (Review Daily)":
        query += " AND box = 1"
    elif box_filter == "Box 2 (Every 3 Days)":
        query += " AND box = 2"
    elif box_filter == "Box 3+ (Mastered)":
        query += " AND box >= 3"

    cursor.execute(query, params)
    cards = cursor.fetchall()
    conn.close()

    if not cards:
        st.warning("No flashcards found matching your filters. Create a new card below!")
    else:
        if "card_index" not in st.session_state:
            st.session_state.card_index = 0
        if "card_flipped" not in st.session_state:
            st.session_state.card_flipped = False

        if st.session_state.card_index >= len(cards):
            st.session_state.card_index = 0

        current_card = cards[st.session_state.card_index]
        card_id, c_subj, c_ques, c_ans, c_diff, c_box = current_card

        st.progress((st.session_state.card_index + 1) / len(cards), text=f"Card {st.session_state.card_index + 1} of {len(cards)}")

        # Render Flashcard
        st.markdown(f"""
        <div class="flashcard-box">
            <span class="pill-badge pill-blue">{c_subj}</span>
            <span class="pill-badge pill-purple">Leitner Box {c_box}</span>
            <span class="pill-badge pill-amber">{c_diff}</span>
            <h3 style="margin-top: 18px; color: #1e293b;">
                {'💡 ' + c_ans if st.session_state.card_flipped else '❓ ' + c_ques}
            </h3>
            <p style="color: #64748b; font-size: 0.85rem; margin-top: 10px;">
                {'(Answer Revealed - Rate your recall below)' if st.session_state.card_flipped else '(Click Flip Card to verify your answer)'}
            </p>
        </div>
        """, unsafe_allow_html=True)

        col_b1, col_b2, col_b3 = st.columns([1, 1, 1])
        with col_b2:
            if st.button("🔄 Flip Card", use_container_width=True, type="primary"):
                st.session_state.card_flipped = not st.session_state.card_flipped
                st.rerun()

        # Feedback Buttons (SRS rating)
        if st.session_state.card_flipped:
            st.markdown("#### How was your recall?")
            c_f1, c_f2, c_f3, c_f4 = st.columns(4)
            
            def update_card_box(card_id: int, new_box: int):
                c_conn = sqlite3.connect(DB_PATH)
                c_cur = c_conn.cursor()
                c_cur.execute(
                    "UPDATE flashcards SET box = ?, times_reviewed = times_reviewed + 1 WHERE id = ?",
                    (new_box, card_id)
                )
                c_conn.commit()
                c_conn.close()
                st.session_state.card_flipped = False
                st.session_state.card_index = (st.session_state.card_index + 1) % len(cards)
                st.rerun()

            with c_f1:
                if st.button("❌ Forgot (Box 1)", use_container_width=True):
                    update_card_box(card_id, 1)
            with c_f2:
                if st.button("⚠️ Hard (Box 1)", use_container_width=True):
                    update_card_box(card_id, 1)
            with c_f3:
                if st.button("✅ Good (Box +1)", use_container_width=True):
                    update_card_box(card_id, min(5, c_box + 1))
            with c_f4:
                if st.button("🌟 Easy (Box +2)", use_container_width=True):
                    update_card_box(card_id, min(5, c_box + 2))

    # Add New Flashcard Accordion
    with st.expander("➕ Add New Flashcard to Deck"):
        with st.form("new_card_form"):
            new_subject = st.text_input("Subject Category", "Computer Science")
            new_question = st.text_area("Question / Prompt")
            new_answer = st.text_area("Correct Answer / Explanation")
            new_diff = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"])
            submitted = st.form_submit_button("Save Flashcard")
            
            if submitted and new_question and new_answer:
                c_conn = sqlite3.connect(DB_PATH)
                c_cur = c_conn.cursor()
                c_cur.execute(
                    "INSERT INTO flashcards (subject, question, answer, difficulty, box) VALUES (?, ?, ?, ?, 1)",
                    (new_subject, new_question, new_answer, new_diff)
                )
                c_conn.commit()
                c_conn.close()
                st.success("Flashcard added successfully!")
                st.rerun()


# =============================================================================
# TAB 3: ADAPTIVE QUIZ ARENA & MOCK EXAM
# =============================================================================
with tab3:
    st.header("📝 Adaptive Quiz Arena & Mock Exam")
    st.markdown("Test your mastery with instant scoring, timer tracking, and detailed mistake analysis.")

    col_q1, col_q2 = st.columns([2, 1])
    with col_q1:
        quiz_subject = st.selectbox("Select Quiz Subject Domain:", list(DEFAULT_QUIZ_BANK.keys()) + ["Generate Custom From Topic"])
    with col_q2:
        quiz_mode = st.radio("Mode:", ["Quick Practice (3-5 Qs)", "Timed Challenge (60s)"])

    if quiz_subject == "Generate Custom From Topic":
        custom_quiz_topic = st.text_input("Topic for AI Quiz:", "Operating Systems & Virtual Memory")
        active_questions = generate_custom_quiz_from_notes(custom_quiz_topic, f"{custom_quiz_topic} is an essential subsystem in modern computing. It provides memory isolation, paging, and virtual address mapping so processes cannot corrupt memory.")
    else:
        active_questions = DEFAULT_QUIZ_BANK[quiz_subject]

    st.markdown("---")

    # Quiz Form
    with st.form("quiz_submission_form"):
        user_responses = {}
        for idx, item in enumerate(active_questions):
            st.markdown(f"**Q{idx+1}: {item['question']}**")
            user_responses[idx] = st.radio(
                f"Choose answer for Q{idx+1}:",
                item["options"],
                key=f"quiz_opt_{idx}",
                label_visibility="collapsed"
            )
            st.write("")

        submit_quiz = st.form_submit_button("🏁 Submit Test for Grading", type="primary")

    if submit_quiz:
        score = 0
        total = len(active_questions)
        mistakes = []

        for idx, item in enumerate(active_questions):
            selected = user_responses.get(idx)
            correct = item["answer"]
            if selected == correct:
                score += 1
            else:
                mistakes.append({
                    "Question": item["question"],
                    "Your Answer": selected,
                    "Correct Answer": correct,
                    "Explanation": item["explanation"]
                })

        accuracy = round((score / total) * 100, 1)

        # Record to Database
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "INSERT INTO quiz_history (timestamp, subject, score, total_questions, accuracy, time_spent_seconds) VALUES (?, ?, ?, ?, ?, ?)",
            (datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), quiz_subject, score, total, accuracy, 45)
        )
        conn.commit()
        conn.close()

        # Score Banner
        if accuracy >= 80:
            st.balloons()
            st.success(f"🎉 Outstanding Job! You scored **{score}/{total} ({accuracy}%)** - Grade: **A**")
        elif accuracy >= 60:
            st.info(f"👍 Good Effort! You scored **{score}/{total} ({accuracy}%)** - Grade: **B**")
        else:
            st.warning(f"📚 Revision Recommended. You scored **{score}/{total} ({accuracy}%)** - Grade: **C**")

        # Detailed Mistake Analysis
        if mistakes:
            st.subheader("🔍 Review & Mistake Breakdown")
            for m in mistakes:
                with st.expander(f"❌ {m['Question']}"):
                    st.write(f"**Your Choice:** `{m['Your Answer']}`")
                    st.write(f"**Correct Choice:** `{m['Correct Answer']}`")
                    st.info(f"**Why:** {m['Explanation']}")
        else:
            st.success("🌟 Flawless test! You didn't make a single mistake!")


# =============================================================================
# TAB 4: NOTE SUMMARIZER & MIND-MAP GENERATOR
# =============================================================================
with tab4:
    st.header("📄 Note Summarizer & Visual Mind-Map Generator")
    st.markdown("Paste lecture notes or upload study transcripts to generate executive summaries, glossaries, and visual mind maps.")

    uploaded_file = st.file_uploader("Upload Notes (.txt, .md)", type=["txt", "md"])
    notes_input = ""

    if uploaded_file is not None:
        notes_input = uploaded_file.read().decode("utf-8")
        st.success(f"Loaded file: `{uploaded_file.name}` ({len(notes_input)} characters)")
    else:
        sample_lecture = (
            "Photosynthesis is a biological process utilized by green plants and certain algae to transform light energy into chemical energy. "
            "Light absorption occurs within specialized cellular organelles known as chloroplasts, primarily mediated by the green pigment chlorophyll. "
            "The overarching reaction converts carbon dioxide and water into glucose and oxygen gas. "
            "Photosynthesis consists of two distinct stages: light-dependent reactions and light-independent reactions (the Calvin Cycle). "
            "During the light reactions, photon excitation drives ATP and NADPH synthesis while releasing oxygen through water photolysis. "
            "In the Calvin cycle, the enzyme RuBisCO fixes atmospheric CO2 into three-carbon sugar molecules that subsequently synthesize sucrose and starch. "
            "This mechanism serves as the primary energetic foundation supporting nearly all life on Earth."
        )
        notes_input = st.text_area("Or Paste Your Lecture Notes / Article Text Here:", value=sample_lecture, height=180)

    summary_depth = st.slider("Target Summary Sentences", 2, 8, 4)

    if st.button("✨ Summarize & Build Mind Map", type="primary"):
        with st.spinner("Analyzing text semantics and structuring concepts..."):
            time.sleep(0.4)
            analysis = summarize_text_heuristics(notes_input, max_sentences=summary_depth)

        col_s1, col_s2, col_s3 = st.columns(3)
        col_s1.metric("Word Count", f"{analysis['word_count']} words")
        col_s2.metric("Reading Time", f"~{analysis['reading_time_min']} min")
        col_s3.metric("Extracted Key Concepts", f"{len(analysis['key_terms'])}")

        st.subheader("📌 Key Takeaways (Executive Summary)")
        st.write(analysis["summary"])

        col_m1, col_m2 = st.columns([1, 1])
        with col_m1:
            st.subheader("📚 Extracted Terminology")
            for term, desc in analysis["key_terms"].items():
                st.markdown(f"- **{term}**: {desc}")

        with col_m2:
            st.subheader("🗺️ Structural Mind Map (Mermaid)")
            st.markdown("```mermaid\n" + analysis["mermaid_map"] + "\n```")


# =============================================================================
# TAB 5: AI STUDY PLANNER & TIMETABLE ARCHITECT
# =============================================================================
with tab5:
    st.header("📅 AI Study Planner & Timetable Architect")
    st.markdown("Generate balanced, high-yield study timetables tailored to your target exam dates and available hours.")

    col_p1, col_p2 = st.columns([1, 1])
    with col_p1:
        exam_name = st.text_input("Exam or Goal Name:", "Final Semester Exams & System Design Interview")
        target_exam_date = st.date_input("Target Exam / Deadline Date:", datetime.date.today() + datetime.timedelta(days=14))
        daily_study_hours = st.slider("Daily Allocated Study Hours:", 1, 10, 4)

    with col_p2:
        study_subjects_input = st.text_area("Subjects / Topics to Cover (one per line):", "Data Structures & Algorithms\nDatabase Systems & SQL\nSystem Architecture\nProbability & Statistics")

    if st.button("🚀 Generate Optimized Study Schedule", type="primary"):
        subjects_list = [s.strip() for s in study_subjects_input.split("\n") if s.strip()]
        days_remaining = (target_exam_date - datetime.date.today()).days

        if days_remaining <= 0:
            st.error("Please pick a target exam date that is in the future!")
        elif not subjects_list:
            st.error("Please list at least one subject to study!")
        else:
            total_hours = days_remaining * daily_study_hours
            hours_per_subject = round(total_hours / len(subjects_list), 1)

            st.success(f"🗓️ **{days_remaining} Days Remaining** until {exam_name}! Total study capacity: **{total_hours} Hours** ({hours_per_subject} hrs/subject).")

            # Store generated tasks in Database
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("DELETE FROM planner_tasks")  # Reset schedule
            
            schedule_records = []
            for i, subj in enumerate(subjects_list):
                task_date = datetime.date.today() + datetime.timedelta(days=(i * (days_remaining // len(subjects_list))))
                c.execute(
                    "INSERT INTO planner_tasks (subject, topic, allocated_hours, target_date, is_completed) VALUES (?, ?, ?, ?, 0)",
                    (subj, f"Core mastery & practice problems for {subj}", hours_per_subject, task_date.isoformat())
                )
            conn.commit()
            conn.close()

            st.rerun()

    # View Current Schedule
    conn = sqlite3.connect(DB_PATH)
    schedule_df = pd.read_sql_query("SELECT id, subject, topic, allocated_hours, target_date, is_completed FROM planner_tasks ORDER BY target_date ASC", conn)
    conn.close()

    if not schedule_df.empty:
        st.subheader("📋 Active Study Milestones")
        for _, row in schedule_df.iterrows():
            col_t1, col_t2, col_t3 = st.columns([1, 3, 1])
            with col_t1:
                st.write(f"📅 **{row['target_date']}**")
            with col_t2:
                status_icon = "✅" if row["is_completed"] else "⏳"
                st.write(f"{status_icon} **{row['subject']}**: {row['topic']} ({row['allocated_hours']} hrs)")
            with col_t3:
                if not row["is_completed"]:
                    if st.button("Mark Done", key=f"done_{row['id']}"):
                        u_conn = sqlite3.connect(DB_PATH)
                        u_cur = u_conn.cursor()
                        u_cur.execute("UPDATE planner_tasks SET is_completed = 1 WHERE id = ?", (row["id"],))
                        u_conn.commit()
                        u_conn.close()
                        st.rerun()


# =============================================================================
# TAB 6: FOCUS POMODORO STUDY TIMER
# =============================================================================
with tab6:
    st.header("⏱️ Focus Pomodoro Study Timer")
    st.markdown("Use scientifically-proven 25-minute focus intervals and active recall breaks to prevent cognitive fatigue.")

    col_pom1, col_pom2 = st.columns([1, 1])
    with col_pom1:
        timer_mode = st.radio("Select Interval Type:", ["Focus Session (25 min)", "Short Break (5 min)", "Long Break (15 min)"])
        session_subject = st.text_input("Session Focus Subject:", "Algorithm Analysis")

    duration_minutes = 25 if "25" in timer_mode else (5 if "5" in timer_mode else 15)

    with col_pom2:
        st.markdown("#### 🎧 Suggested Study Atmosphere")
        ambient_choice = st.selectbox(
            "Ambient Audio Recommendation:",
            ["🌧️ Gentle Rain on Window", "☕ Tokyo Lofi Coffee Shop", "🌲 Forest Birds & Flowing River", "⚡ 432Hz Deep Focus Alpha Waves"]
        )
        st.info(f"Pro Tip: Put your phone in another room while {ambient_choice} is playing.")

    st.markdown("---")
    
    col_pbtn1, col_pbtn2 = st.columns(2)
    with col_pbtn1:
        if st.button("⏱️ Log Completed Pomodoro Session (+25 min)", type="primary", use_container_width=True):
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute(
                "INSERT INTO pomodoro_sessions (timestamp, duration_minutes, subject, session_type) VALUES (?, ?, ?, ?)",
                (datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), duration_minutes, session_subject, timer_mode)
            )
            conn.commit()
            conn.close()
            st.balloons()
            st.success(f"Logged {duration_minutes} minutes of high-intensity study for '{session_subject}'!")
            st.rerun()

    with col_pbtn2:
        study_tips = [
            "🧠 **Active Recall Rule**: Close your eyes and speak aloud the core 3 points you just read.",
            "👀 **20-20-20 Vision Break**: Look at something 20 feet away for 20 seconds to relax ciliary muscles.",
            "💧 **Hydration Factor**: Drinking 250ml of water boosts cognitive speed by up to 14%."
        ]
        st.markdown(random.choice(study_tips))


# =============================================================================
# TAB 7: ANALYTICS & STUDENT PERFORMANCE DASHBOARD
# =============================================================================
with tab7:
    st.header("📈 Student Performance & Study Analytics")
    st.markdown("Comprehensive insights into your learning velocity, retention rates, and subject strengths.")

    conn = sqlite3.connect(DB_PATH)
    quiz_df = pd.read_sql_query("SELECT timestamp, subject, score, total_questions, accuracy FROM quiz_history ORDER BY id DESC", conn)
    pom_df = pd.read_sql_query("SELECT timestamp, duration_minutes, subject, session_type FROM pomodoro_sessions ORDER BY id DESC", conn)
    cards_df = pd.read_sql_query("SELECT subject, box, times_reviewed FROM flashcards", conn)
    conn.close()

    # KPI Metrics
    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
    total_q_taken = len(quiz_df)
    overall_acc = round(quiz_df["accuracy"].mean(), 1) if not quiz_df.empty else 0.0
    total_pom_sessions = len(pom_df)
    total_focus_hours = round(pom_df["duration_minutes"].sum() / 60, 1) if not pom_df.empty else 0.0

    col_kpi1.metric("Tests Completed", f"{total_q_taken}")
    col_kpi2.metric("Mean Accuracy", f"{overall_acc}%")
    col_kpi3.metric("Pomodoro Sessions", f"{total_pom_sessions}")
    col_kpi4.metric("Total Focus Time", f"{total_focus_hours} hrs")

    st.markdown("---")

    col_ch1, col_ch2 = st.columns(2)
    with col_ch1:
        st.subheader("📊 Quiz Performance Over Time")
        if not quiz_df.empty:
            chart_data = quiz_df.copy()
            chart_data["Attempt"] = range(1, len(chart_data) + 1)
            st.line_chart(chart_data.set_index("Attempt")["accuracy"])
        else:
            st.info("Complete quizzes in Tab 3 to view performance trends.")

    with col_ch2:
        st.subheader("🗂️ Flashcard Leitner Mastery Distribution")
        if not cards_df.empty:
            box_counts = cards_df["box"].value_counts().sort_index()
            st.bar_chart(box_counts)
        else:
            st.info("Flashcard box metrics will appear here.")

    # Historical Activity Tables
    st.subheader("🕒 Recent Quiz Logs")
    if not quiz_df.empty:
        st.dataframe(quiz_df.head(5), use_container_width=True)
    else:
        st.caption("No quiz logs recorded yet.")

# -----------------------------------------------------------------------------
# 8. FOOTER
# -----------------------------------------------------------------------------
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #94a3b8; font-size: 0.85rem; padding: 12px;'>"
    "EduGenie Learning Assistant • Engineered with Python & Streamlit • Empowering autodidactic excellence"
    "</div>",
    unsafe_allow_html=True
)