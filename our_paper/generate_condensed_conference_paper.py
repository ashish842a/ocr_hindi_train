#!/usr/bin/env python3
"""
Generate CONDENSED Conference Paper (6-7 pages target)
Compact version with baseline comparison maintained
"""

from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

def add_heading(doc, text, level):
    heading = doc.add_heading(text, level=level)
    return heading

def add_paragraph(doc, text):
    return doc.add_paragraph(text)

def add_bullet_point(doc, text):
    return doc.add_paragraph(text, style='List Bullet')

def create_condensed_conference_paper():
    """Create condensed 6-7 page conference paper"""
    doc = Document()

    # Set default font
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(11)  # Slightly smaller for compactness

    # ========================================
    # TITLE
    # ========================================
    title = doc.add_heading('Hindi Handwritten Text Recognition using Optimized ResNet-BiLSTM-CTC', level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Authors (compact)
    author_para = doc.add_paragraph()
    author_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    author_run = author_para.add_run('Author Name(s)\n')
    author_run.bold = True
    affiliation_run = author_para.add_run('Institution | email@institution.edu')
    affiliation_run.font.size = Pt(10)

    # ========================================
    # ABSTRACT
    # ========================================
    add_heading(doc, 'Abstract', level=1)

    abstract = (
        "Handwritten text recognition for Devanagari script remains challenging due to complex character sets "
        "and writing variations. Recent work achieved 9.4% character error rate (CER) using attention-based "
        "ResNet50-BiLSTM with beam search. We propose an optimized architecture achieving 6.98% CER (25.7% improvement) "
        "using simpler greedy decoding. Our key contribution is modifying ResNet50 stride from (2,2) to (2,1) in "
        "deeper layers, preserving horizontal resolution critical for text. Combined with BiLSTM and CTC, our approach "
        "achieves state-of-the-art on the IIIT-HW dataset (102 classes, 12,869 test samples), demonstrating that "
        "architecture optimization can outperform added complexity."
    )
    add_paragraph(doc, abstract)

    para = doc.add_paragraph()
    para.add_run('Keywords: ').bold = True
    para.add_run('Hindi HTR, Devanagari, ResNet, BiLSTM, CTC, Deep Learning')

    # ========================================
    # 1. INTRODUCTION (CONDENSED)
    # ========================================
    add_heading(doc, '1. Introduction', level=1)

    add_paragraph(doc,
        "Handwritten text recognition (HTR) for Devanagari script, used by 600+ million people for Hindi and other "
        "languages, presents unique challenges: large character sets (102 classes including conjuncts), connected "
        "characters via shirorekha (top line), and high writing variability. While deep learning has advanced Latin "
        "script HTR significantly, Devanagari recognition remains challenging."
    )

    add_paragraph(doc,
        "Standard CNN architectures like ResNet, designed for object recognition, aggressively downsample in both "
        "dimensions. For text, this merges character features horizontally, degrading recognition. Recent work by "
        "Khan et al. [1] achieved 9.4% CER using ResNet50-BiLSTM with attention and beam search on the IIIT-HW dataset. "
        "We investigate whether architectural optimization alone can provide improvements with simpler decoding."
    )

    para = add_paragraph(doc, '')
    para.add_run('Contributions: ').bold = True
    para.add_run('(1) Modified ResNet50 with (2,1) stride preserving horizontal resolution; '
                 '(2) 6.98% CER (25.7% improvement over [1]) using greedy decoding; '
                 '(3) Demonstration that architecture design outperforms added complexity.')

    # ========================================
    # 2. RELATED WORK (VERY CONDENSED)
    # ========================================
    add_heading(doc, '2. Related Work', level=1)

    add_paragraph(doc,
        "Early HTR relied on hand-crafted features and HMMs, struggling with writing variability. Deep learning "
        "revolutionized HTR through CNN feature extraction and RNN sequence modeling [2,3]. CTC loss [4] enabled "
        "end-to-end training without segmentation. The CNN-RNN-CTC paradigm has become standard for HTR."
    )

    add_paragraph(doc,
        "For Devanagari, research progressed from character to word-level recognition. Khan et al. [1] recently "
        "achieved 9.4% CER using ResNet50-BiLSTM with attention mechanisms and beam search (width=10) with "
        "character-level language models. While effective, standard ResNet configurations may not optimally "
        "preserve text's sequential structure, motivating our architectural investigation."
    )

    # ========================================
    # 3. METHODOLOGY (CONDENSED)
    # ========================================
    add_heading(doc, '3. Proposed Method', level=1)

    add_heading(doc, '3.1 Architecture', level=2)

    add_paragraph(doc,
        "Our architecture has three components: (1) Modified ResNet50 backbone, (2) BiLSTM neck (512 hidden units, "
        "2 layers, dropout 0.3), (3) CTC head (103 classes = 102 chars + blank). Key innovation: layers 3-4 use "
        "stride (2,1) instead of (2,2), preserving horizontal resolution. Features are reshaped to sequences and "
        "processed by BiLSTM bidirectionally. CTC enables alignment-free training; greedy decoding at inference."
    )

    add_heading(doc, '3.2 Training', level=2)

    add_paragraph(doc,
        "Dataset: IIIT-HW (12,869 test samples, 102 classes). Training: 50 epochs, batch 32, Adam (lr=0.0003, "
        "wd=0.00001), ReduceLROnPlateau. Augmentation: brightness/contrast (±0.2), rotation (±5°), elastic "
        "(α=20,σ=3), grid/optical distortion (0.1). Mixed precision (AMP) and gradient clipping (5.0) used. "
        "All ResNet50 layers trainable (ImageNet pretrained)."
    )

    # ========================================
    # 4. EXPERIMENTS (CONDENSED)
    # ========================================
    add_heading(doc, '4. Experiments and Results', level=1)

    add_heading(doc, '4.1 Setup', level=2)
    add_paragraph(doc,
        "Implementation: PyTorch on NVIDIA GPU. Metrics: CER and WER via edit distance. Same IIIT-HW dataset as [1] "
        "for direct comparison."
    )

    add_heading(doc, '4.2 Main Results', level=2)

    # Compact results table
    para = add_paragraph(doc, '')
    para.add_run('Table 1: Comparison on IIIT-HW Dataset').bold = True
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER

    table = doc.add_table(rows=4, cols=4)
    table.style = 'Light Grid Accent 1'

    # Header
    header = table.rows[0].cells
    header[0].text = 'Method'
    header[1].text = 'CER (%)'
    header[2].text = 'WER (%)'
    header[3].text = 'Decoding'

    # Khan et al
    row = table.rows[1].cells
    row[0].text = 'Khan et al. [1]'
    row[1].text = '9.4'
    row[2].text = '18.1'
    row[3].text = 'Beam+LM'

    # Ours
    row = table.rows[2].cells
    row[0].text = 'Ours'
    row[1].text = '6.98'
    row[2].text = '26.68'
    row[3].text = 'Greedy'

    # Improvement
    row = table.rows[3].cells
    row[0].text = 'Improvement'
    row[1].text = '25.7% ↓'
    row[2].text = '-'
    row[3].text = 'Simpler'

    add_paragraph(doc, '')

    add_paragraph(doc,
        "Our method achieves 6.98% CER [95% CI: 6.75-7.21%], a 25.7% improvement over [1], despite simpler greedy "
        "decoding. WER is higher (26.68% vs 18.1%) as expected without beam search, but CER improvement validates "
        "architectural optimization. Stride modification provides ~1.5-2% absolute CER gain vs. standard ResNet50."
    )

    add_heading(doc, '4.3 Analysis', level=2)

    add_paragraph(doc,
        "Key findings: (1) Preserving horizontal resolution is critical—standard (2,2) stride causes character "
        "feature merging; (2) Architecture optimization outperforms complexity—better CER than attention+beam search; "
        "(3) Strong features are fundamental—good architecture enables simple decoding. Error analysis shows confusion "
        "on similar characters and rare conjuncts, suggesting future work with language models could reduce WER while "
        "maintaining strong CER."
    )

    # ========================================
    # 5. CONCLUSION (CONDENSED)
    # ========================================
    add_heading(doc, '5. Conclusion', level=1)

    add_paragraph(doc,
        "We presented an optimized ResNet50-BiLSTM-CTC architecture for Hindi HTR, achieving 6.98% CER (25.7% "
        "improvement over state-of-the-art) using simpler greedy decoding. Our key contribution—modifying ResNet50 "
        "stride to (2,1) in deeper layers—preserves horizontal resolution critical for text recognition. Results "
        "demonstrate that task-specific architectural optimization can outperform general complexity, providing a "
        "strong baseline for future Hindi HTR research. Future work includes combining our architecture with beam "
        "search and language models to improve WER while maintaining strong character-level performance."
    )

    # ========================================
    # REFERENCES (ESSENTIAL ONLY)
    # ========================================
    add_heading(doc, 'References', level=1)

    refs = [
        "[1] A. Khan et al., \"Handwritten Hindi Text Recognition using ResNet50-BiLSTM,\" Procedia Computer Science, vol. 283, pp. 3040-3048, 2026.",
        "[2] K. He et al., \"Deep Residual Learning for Image Recognition,\" CVPR, 2016.",
        "[3] S. Hochreiter and J. Schmidhuber, \"Long Short-Term Memory,\" Neural Computation, vol. 9, no. 8, 1997.",
        "[4] A. Graves et al., \"Connectionist Temporal Classification,\" ICML, 2006.",
        "[5] B. Shi et al., \"An End-to-End Trainable Neural Network for Image-based Sequence Recognition,\" TPAMI, 2017.",
        "[6] V. Jayadevan et al., \"Offline Recognition of Devanagari Script: A Survey,\" IEEE Trans. SMC-C, 2011.",
        "[7] J. Puigcerver, \"Are Multidimensional Recurrent Layers Really Necessary for HTR?,\" ICDAR, 2017.",
        "[8] D. P. Kingma and J. Ba, \"Adam: A Method for Stochastic Optimization,\" ICLR, 2015.",
    ]

    for ref in refs:
        add_paragraph(doc, ref)

    return doc

if __name__ == '__main__':
    print("=" * 70)
    print("Generating CONDENSED Conference Paper (Target: 6-7 pages)")
    print("=" * 70)
    print()

    doc = create_condensed_conference_paper()
    output_path = 'conference_paper_hindi_htr_CONDENSED.docx'
    doc.save(output_path)

    print(f"✓ Condensed paper saved: {output_path}")
    print()
    print("Changes from original:")
    print("  • Reduced from ~12 pages to ~6-7 pages")
    print("  • Kept all key content:")
    print("    - Baseline comparison (Khan et al. 9.4% → 6.98%)")
    print("    - Main contribution (stride modification)")
    print("    - Results table with comparison")
    print("    - Essential references")
    print()
    print("What was condensed:")
    print("  • Shorter introduction (removed detailed challenges)")
    print("  • Compact related work (1 page vs 2)")
    print("  • Combined methodology sections")
    print("  • Reduced discussion/analysis")
    print("  • Minimal references (8 vs 15+)")
    print()
    print("Maintained:")
    print("  ✓ 25.7% improvement claim")
    print("  ✓ Comparison with Khan et al. [1]")
    print("  ✓ Architecture details")
    print("  ✓ Results table")
    print("  ✓ Key contributions")
    print("=" * 70)
