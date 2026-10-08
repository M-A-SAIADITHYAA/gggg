import os
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn, nsdecls

def create_report():
    doc = Document()
    
    # -------------------------------------------------------------
    # PAGE SETUP & STYLES
    # -------------------------------------------------------------
    # Margins matching reference
    for s in doc.sections:
        s.top_margin = Inches(1.0)
        s.bottom_margin = Inches(0.5)
        s.left_margin = Inches(1.0)
        s.right_margin = Inches(0.75)
        s.page_width = Inches(8.5)
        s.page_height = Inches(11.0)
        
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Times New Roman'
    normal_style.font.size = Pt(13.5)
    normal_style.font.color.rgb = RGBColor(0, 0, 0)
    normal_style.paragraph_format.line_spacing = 1.5
    normal_style.paragraph_format.space_after = Pt(4)
    normal_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # Configure Heading styles to Times New Roman and black
    for h_name in ['Heading 1', 'Heading 2', 'Heading 3', 'Heading 4']:
        if h_name in doc.styles:
            st = doc.styles[h_name]
            st.font.name = 'Times New Roman'
            st.font.color.rgb = RGBColor(0, 0, 0)

    # Helpers
    def set_cell_background(cell, fill_hex):
        shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
        cell._tc.get_or_add_tcPr().append(shading)

    def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
        tcPr = cell._tc.get_or_add_tcPr()
        tcMar = OxmlElement('w:tcMar')
        for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
            node = OxmlElement(f'w:{m}')
            node.set(qn('w:w'), str(val))
            node.set(qn('w:type'), 'dxa')
            tcMar.append(node)
        tcPr.append(tcMar)

    def set_footer_page_number(section, num_fmt="decimal", start_num=1, default_text="1"):
        for x in section._sectPr.xpath('./w:pgNumType'):
            section._sectPr.remove(x)
        section._sectPr.append(parse_xml(f'<w:pgNumType {nsdecls("w")} w:fmt="{num_fmt}" w:start="{start_num}"/>'))
        footer = section.footer
        p_foot = footer.paragraphs[0]
        p_foot.text = ""
        p_foot.alignment = WD_ALIGN_PARAGRAPH.CENTER
        fld = parse_xml(f'<w:fldSimple {nsdecls("w")} w:instr="PAGE"><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="24"/></w:rPr><w:t>{default_text}</w:t></w:r></w:fldSimple>')
        p_foot._p.append(fld)

    def add_chapter_title(chap_num, chap_title):
        if str(chap_num) != "1":
            doc.add_page_break()

        p = doc.add_paragraph(style='Heading 1')
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(16)
        p.paragraph_format.line_spacing = 1.15
        r = p.add_run(f"CHAPTER {chap_num}\n{chap_title.upper()}")
        r.font.name = 'Times New Roman'
        r.font.size = Pt(16)
        r.font.bold = True
        return p

    def add_section_heading(title):
        p = doc.add_paragraph(style='Heading 2')
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.5
        r = p.add_run(title)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(14)
        r.font.bold = True
        return p

    def add_subsection_heading(title):
        p = doc.add_paragraph(style='Heading 3')
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.line_spacing = 1.5
        r = p.add_run(title)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(13.5)
        r.font.bold = True
        return p

    def add_body_p(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 1.5
        p.paragraph_format.space_after = Pt(6)
        r = p.add_run(text)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(13.5)
        return p

    def add_image_figure(img_path, caption_text, width_inches=5.8):
        if os.path.exists(img_path):
            p_img = doc.add_paragraph()
            p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_img.paragraph_format.space_before = Pt(10)
            p_img.paragraph_format.space_after = Pt(4)
            p_img.add_run().add_picture(img_path, width=Inches(width_inches))

            p_cap = doc.add_paragraph()
            p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_cap.paragraph_format.space_before = Pt(2)
            p_cap.paragraph_format.space_after = Pt(12)
            r = p_cap.add_run(caption_text)
            r.font.name = 'Times New Roman'
            r.font.size = Pt(12)
            r.font.bold = True
        else:
            p_cap = doc.add_paragraph()
            p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p_cap.add_run(f"[{caption_text} — Asset file not found: {img_path}]")
            r.font.bold = True

    def add_custom_table(headers, data, caption=None, col_widths=None, col_alignments=None):
        if caption:
            p_cap = doc.add_paragraph()
            p_cap.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p_cap.paragraph_format.space_before = Pt(10)
            p_cap.paragraph_format.space_after = Pt(4)
            r = p_cap.add_run(caption)
            r.font.name = 'Times New Roman'
            r.font.size = Pt(12.5)
            r.font.bold = True

        num_cols = len(headers)
        table = doc.add_table(rows=len(data) + 1, cols=num_cols)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False

        # Completely remove all table borders and boundaries (no boxes, no lines, plain)
        tblPr = table._tbl.tblPr
        tblBorders = parse_xml(r'''
            <w:tblBorders %s>
                <w:top w:val="none"/>
                <w:left w:val="none"/>
                <w:bottom w:val="none"/>
                <w:right w:val="none"/>
                <w:insideH w:val="none"/>
                <w:insideV w:val="none"/>
            </w:tblBorders>
        ''' % nsdecls("w"))
        tblPr.append(tblBorders)

        tblCellMar = parse_xml(r'''
            <w:tblCellMar %s>
                <w:top w:w="40" w:type="dxa"/>
                <w:left w:w="30" w:type="dxa"/>
                <w:bottom w:w="40" w:type="dxa"/>
                <w:right w:w="30" w:type="dxa"/>
            </w:tblCellMar>
        ''' % nsdecls("w"))
        tblPr.append(tblCellMar)

        if num_cols >= 9:
            hdr_font_sz = Pt(8.5)
            body_font_sz = Pt(8.0)
            cell_top, cell_bot, cell_l, cell_r = 50, 50, 25, 25
        elif num_cols >= 6:
            hdr_font_sz = Pt(9.5)
            body_font_sz = Pt(9.0)
            cell_top, cell_bot, cell_l, cell_r = 60, 60, 35, 35
        else:
            hdr_font_sz = Pt(11.0)
            body_font_sz = Pt(10.5)
            cell_top, cell_bot, cell_l, cell_r = 70, 70, 50, 50

        center_header_keywords = {
            "NO", "NO.", "SL. NO.", "CHAPTER NO.", "TABLE NO.", "FIGURE NO.", "PAGE NO.",
            "ID", "RANK", "FOLD", "TARGET", "STATUS", "VALIDATION STATUS",
            "OOF R²", "R²", "COF R²", "WEAR R²", "MAE", "COF MAE", "WEAR MAE",
            "RMSE", "COF RMSE", "WEAR RMSE", "N_TRAIN", "N_VAL", "STD (Σ)", "GAIN (%)",
            "MEAN |SHAP|", "|SHAP|", "FOLD R²", "OPTIMAL IDENTIFIED"
        }

        alignments = []
        for idx, title in enumerate(headers):
            if col_alignments and idx < len(col_alignments):
                alignments.append(col_alignments[idx])
            else:
                clean_title = title.strip().upper()
                if clean_title in center_header_keywords:
                    alignments.append(WD_ALIGN_PARAGRAPH.CENTER)
                else:
                    col_vals = [str(row[idx]).strip() for row in data if idx < len(row) and row[idx]]
                    all_short_numbers = len(col_vals) > 0 and all(
                        len(v) <= 10 and (any(c.isdigit() for c in v) or v.upper() in ["N/A", "-", "NA", "N.A."])
                        for v in col_vals
                    )
                    if all_short_numbers:
                        alignments.append(WD_ALIGN_PARAGRAPH.CENTER)
                    else:
                        alignments.append(WD_ALIGN_PARAGRAPH.LEFT)

        # Header Row
        hdr_row = table.rows[0]
        trPr = hdr_row._tr.get_or_add_trPr()
        trPr.append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))

        for idx, title in enumerate(headers):
            cell = hdr_row.cells[idx]
            tcPr = cell._tc.get_or_add_tcPr()
            tcBorders = parse_xml(r'''
                <w:tcBorders %s>
                    <w:top w:val="none"/>
                    <w:left w:val="none"/>
                    <w:bottom w:val="none"/>
                    <w:right w:val="none"/>
                </w:tcBorders>
            ''' % nsdecls("w"))
            tcPr.append(tcBorders)
            tcPr.append(parse_xml(f'<w:vAlign {nsdecls("w")} w:val="top"/>'))

            set_cell_margins(cell, top=cell_top + 15, bottom=cell_bot + 15, left=cell_l, right=cell_r)
            p = cell.paragraphs[0]
            p.alignment = alignments[idx]
            p.paragraph_format.line_spacing = 1.10
            p.paragraph_format.space_before = Pt(3)
            p.paragraph_format.space_after = Pt(3)
            r = p.add_run(title)
            r.font.name = 'Times New Roman'
            r.font.size = hdr_font_sz
            r.font.bold = True

        # Data Rows
        for r_idx, row_values in enumerate(data):
            row = table.rows[r_idx + 1]
            trPr_row = row._tr.get_or_add_trPr()
            trPr_row.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))
            for c_idx, val in enumerate(row_values):
                cell = row.cells[c_idx]
                tcPr = cell._tc.get_or_add_tcPr()
                tcBorders = parse_xml(r'''
                    <w:tcBorders %s>
                        <w:top w:val="none"/>
                        <w:left w:val="none"/>
                        <w:bottom w:val="none"/>
                        <w:right w:val="none"/>
                    </w:tcBorders>
                ''' % nsdecls("w"))
                tcPr.append(tcBorders)
                tcPr.append(parse_xml(f'<w:vAlign {nsdecls("w")} w:val="top"/>'))

                set_cell_margins(cell, top=cell_top, bottom=cell_bot, left=cell_l, right=cell_r)
                p = cell.paragraphs[0]
                p.alignment = alignments[c_idx]
                p.paragraph_format.line_spacing = 1.10
                p.paragraph_format.space_before = Pt(1.5)
                p.paragraph_format.space_after = Pt(1.5)

                val_str = str(val).replace("$MoS_2$", "MoS₂").replace("$kv$", "kv").replace("$Tg$", "Tg")
                r = p.add_run(val_str)
                r.font.name = 'Times New Roman'
                r.font.size = body_font_sz

        # Apply Column Widths
        if col_widths and len(col_widths) == len(headers):
            for row in table.rows:
                for idx, w in enumerate(col_widths):
                    row.cells[idx].width = Inches(w)

        # Spacing after table
        p_after = doc.add_paragraph()
        p_after.paragraph_format.space_before = Pt(0)
        p_after.paragraph_format.space_after = Pt(6)

    # -------------------------------------------------------------
    # SECTION 1: FRONT MATTER (ROMAN NUMERALS i, ii, iii...)
    # -------------------------------------------------------------
    sec_front = doc.sections[0]
    sec_front.different_first_page_header_footer = True
    set_footer_page_number(sec_front, num_fmt="lowerRoman", start_num=1, default_text="i")
    if sec_front.first_page_footer.paragraphs:
        sec_front.first_page_footer.paragraphs[0].text = ""

    # -------------------------------------------------------------
    # 1. COVER PAGE
    # -------------------------------------------------------------
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(10)
    p_title.paragraph_format.space_after = Pt(12)
    p_title.paragraph_format.line_spacing = 1.15
    r = p_title.add_run("PHYSICS-INFORMED MACHINE LEARNING FRAMEWORK FOR MULTI-FILLER POLYAMIDE (PA6 / PA66) COMPOSITE TRIBOLOGY: MODELING, EMPIRICAL VALIDATION, AND INTERACTIVE VIRTUAL TRIBOMETER")
    r.font.size = Pt(15)
    r.font.bold = True

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_after = Pt(4)
    r = p_sub.add_run("A PROJECT REPORT\nSubmitted to\nAmrita Vishwa Vidyapeetham\nin partial fulfilment for the award of the degree of")
    r.font.size = Pt(13)

    p_deg = doc.add_paragraph()
    p_deg.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_deg.paragraph_format.space_after = Pt(12)
    r = p_deg.add_run("BACHELOR OF TECHNOLOGY IN COMPUTER SCIENCE AND ENGINEERING")
    r.font.size = Pt(13.5)
    r.font.bold = True

    p_by = doc.add_paragraph()
    p_by.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_by.paragraph_format.space_after = Pt(2)
    r = p_by.add_run("By")
    r.font.size = Pt(12.5)

    p_authors = doc.add_paragraph()
    p_authors.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_authors.paragraph_format.space_after = Pt(14)
    p_authors.paragraph_format.line_spacing = 1.15
    r = p_authors.add_run("HARI SREERAM R\n(Reg. No. CH.SC.U4CSE23019)\n\nM A SAI ADITHYAA\n(Reg. No. CH.SC.U4CSE23029)")
    r.font.size = Pt(13.5)
    r.font.bold = True

    p_sup = doc.add_paragraph()
    p_sup.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sup.paragraph_format.space_after = Pt(14)
    p_sup.paragraph_format.line_spacing = 1.15
    r = p_sup.add_run("Supervisors:\nDr. SHUBRAJIT BHAUMIK\nAssociate Professor, Dept. of Mechanical Engineering\n\nDr. SANGAPU SREENIVASA CHAKRAVARTHI\nAssistant Professor (Sr. Gr.), Dept. of Computer Science & Engineering")
    r.font.size = Pt(12)
    r.font.bold = True

    # University Logo
    logo_path = "extracted_logos/word/media/image1.jpeg"
    if os.path.exists(logo_path):
        p_logo = doc.add_paragraph()
        p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_logo.paragraph_format.space_after = Pt(10)
        p_logo.add_run().add_picture(logo_path, width=Inches(1.7))

    p_dept = doc.add_paragraph()
    p_dept.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_dept.paragraph_format.space_after = Pt(0)
    p_dept.paragraph_format.line_spacing = 1.15
    r = p_dept.add_run("DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING\nAMRITA SCHOOL OF COMPUTING\nAMRITA VISHWA VIDYAPEETHAM, CHENNAI – 601103\nOctober 2026")
    r.font.size = Pt(12.5)
    r.font.bold = True

    # -------------------------------------------------------------
    # 2. BONAFIDE CERTIFICATE
    # -------------------------------------------------------------
    doc.add_page_break()

    bonafide_logo_path = "extracted_logos/word/media/image2.jpeg"
    if os.path.exists(bonafide_logo_path):
        p_blog = doc.add_paragraph()
        p_blog.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_blog.paragraph_format.space_before = Pt(0)
        p_blog.paragraph_format.space_after = Pt(20)
        p_blog.add_run().add_picture(bonafide_logo_path, width=Inches(3.8))

    p_cert_title = doc.add_paragraph()
    p_cert_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cert_title.paragraph_format.space_before = Pt(0)
    p_cert_title.paragraph_format.space_after = Pt(24)
    r = p_cert_title.add_run("BONAFIDE CERTIFICATE")
    r.font.name = 'Times New Roman'
    r.font.size = Pt(16)
    r.font.bold = True

    p_cert_body = doc.add_paragraph()
    p_cert_body.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_cert_body.paragraph_format.space_before = Pt(0)
    p_cert_body.paragraph_format.space_after = Pt(36)
    p_cert_body.paragraph_format.line_spacing = 1.25

    r1 = p_cert_body.add_run("This is to certify that this project report entitled ")
    r1.font.name = 'Times New Roman'
    r1.font.size = Pt(12)

    r2 = p_cert_body.add_run("“PHYSICS-INFORMED MACHINE LEARNING FRAMEWORK FOR MULTI-FILLER POLYAMIDE (PA6 / PA66) COMPOSITE TRIBOLOGY: MODELING, EMPIRICAL VALIDATION, AND INTERACTIVE VIRTUAL TRIBOMETER”")
    r2.font.name = 'Times New Roman'
    r2.font.size = Pt(12)
    r2.font.bold = True

    r3 = p_cert_body.add_run(" is the bonafide work of ")
    r3.font.name = 'Times New Roman'
    r3.font.size = Pt(12)

    r4 = p_cert_body.add_run("“HARI SREERAM R (CH.SC.U4CSE23019)”")
    r4.font.name = 'Times New Roman'
    r4.font.size = Pt(12)
    r4.font.bold = True

    r5 = p_cert_body.add_run(" and ")
    r5.font.name = 'Times New Roman'
    r5.font.size = Pt(12)

    r6 = p_cert_body.add_run("“M A SAI ADITHYAA (CH.SC.U4CSE23029)”")
    r6.font.name = 'Times New Roman'
    r6.font.size = Pt(12)
    r6.font.bold = True

    r7 = p_cert_body.add_run(" who carried out the project work under my supervision.")
    r7.font.name = 'Times New Roman'
    r7.font.size = Pt(12)

    tbl_sig = doc.add_table(rows=1, cols=2)
    tblPr = tbl_sig._tbl.tblPr
    tblBorders = parse_xml(r'''
        <w:tblBorders %s>
            <w:top w:val="none"/>
            <w:left w:val="none"/>
            <w:bottom w:val="none"/>
            <w:right w:val="none"/>
            <w:insideH w:val="none"/>
            <w:insideV w:val="none"/>
        </w:tblBorders>
    ''' % nsdecls("w"))
    tblPr.append(tblBorders)

    tblCellMar = parse_xml(r'''
        <w:tblCellMar %s>
            <w:top w:w="0" w:type="dxa"/>
            <w:left w:w="0" w:type="dxa"/>
            <w:bottom w:w="0" w:type="dxa"/>
            <w:right w:w="0" w:type="dxa"/>
        </w:tblCellMar>
    ''' % nsdecls("w"))
    tblPr.append(tblCellMar)

    col_widths = [Inches(3.8), Inches(2.7)]
    for row in tbl_sig.rows:
        for i, w in enumerate(col_widths):
            row.cells[i].width = w

    # Cell 0: Chairperson
    c0 = tbl_sig.rows[0].cells[0]
    p0 = c0.paragraphs[0]
    p0.paragraph_format.space_before = Pt(0)
    p0.paragraph_format.space_after = Pt(36)
    p0.paragraph_format.line_spacing = 1.15
    r_sig0 = p0.add_run("SIGNATURE")
    r_sig0.font.name = 'Times New Roman'
    r_sig0.font.size = Pt(12)
    r_sig0.font.bold = True

    p0_info = c0.add_paragraph()
    p0_info.paragraph_format.space_before = Pt(0)
    p0_info.paragraph_format.space_after = Pt(0)
    p0_info.paragraph_format.line_spacing = 1.15
    r_info0 = p0_info.add_run("Dr. S. Bhagavathi Priya\nCHAIRPERSON\nDepartment of CSE\nAmrita School of Computing\nChennai.")
    r_info0.font.name = 'Times New Roman'
    r_info0.font.size = Pt(12)
    r_info0.font.bold = True

    # Cell 1: Supervisor
    c1 = tbl_sig.rows[0].cells[1]
    p1 = c1.paragraphs[0]
    p1.paragraph_format.space_before = Pt(0)
    p1.paragraph_format.space_after = Pt(36)
    p1.paragraph_format.line_spacing = 1.15
    r_sig1 = p1.add_run("SIGNATURE")
    r_sig1.font.name = 'Times New Roman'
    r_sig1.font.size = Pt(12)
    r_sig1.font.bold = True

    p1_info = c1.add_paragraph()
    p1_info.paragraph_format.space_before = Pt(0)
    p1_info.paragraph_format.space_after = Pt(0)
    p1_info.paragraph_format.line_spacing = 1.15
    r_info1 = p1_info.add_run("Dr. Sangapu Sreenivasa Chakravarthi\nSUPERVISOR\nDepartment of CSE\nAmrita School of Computing\nChennai.")
    r_info1.font.name = 'Times New Roman'
    r_info1.font.size = Pt(12)
    r_info1.font.bold = True

    p_spacer = doc.add_paragraph()
    p_spacer.paragraph_format.space_before = Pt(48)
    p_spacer.paragraph_format.space_after = Pt(0)

    tbl_exam = doc.add_table(rows=1, cols=2)
    tblPr2 = tbl_exam._tbl.tblPr
    tblBorders2 = parse_xml(r'''
        <w:tblBorders %s>
            <w:top w:val="none"/>
            <w:left w:val="none"/>
            <w:bottom w:val="none"/>
            <w:right w:val="none"/>
            <w:insideH w:val="none"/>
            <w:insideV w:val="none"/>
        </w:tblBorders>
    ''' % nsdecls("w"))
    tblPr2.append(tblBorders2)
    tblCellMar2 = parse_xml(r'''
        <w:tblCellMar %s>
            <w:top w:w="0" w:type="dxa"/>
            <w:left w:w="0" w:type="dxa"/>
            <w:bottom w:w="0" w:type="dxa"/>
            <w:right w:w="0" w:type="dxa"/>
        </w:tblCellMar>
    ''' % nsdecls("w"))
    tblPr2.append(tblCellMar2)

    for row in tbl_exam.rows:
        for i, w in enumerate(col_widths):
            row.cells[i].width = w

    c0_ex = tbl_exam.rows[0].cells[0]
    p0_ex = c0_ex.paragraphs[0]
    p0_ex.paragraph_format.space_before = Pt(0)
    p0_ex.paragraph_format.space_after = Pt(0)
    r_ex0 = p0_ex.add_run("INTERNAL EXAMINER")
    r_ex0.font.name = 'Times New Roman'
    r_ex0.font.size = Pt(12)
    r_ex0.font.bold = True

    c1_ex = tbl_exam.rows[0].cells[1]
    p1_ex = c1_ex.paragraphs[0]
    p1_ex.paragraph_format.space_before = Pt(0)
    p1_ex.paragraph_format.space_after = Pt(0)
    r_ex1 = p1_ex.add_run("EXTERNAL EXAMINER")
    r_ex1.font.name = 'Times New Roman'
    r_ex1.font.size = Pt(12)
    r_ex1.font.bold = True

    # -------------------------------------------------------------
    # 3. DECLARATION BY THE CANDIDATES
    # -------------------------------------------------------------
    doc.add_page_break()
    p_dec_title = doc.add_paragraph()
    p_dec_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_dec_title.paragraph_format.space_before = Pt(18)
    p_dec_title.paragraph_format.space_after = Pt(18)
    r = p_dec_title.add_run("DECLARATION BY THE CANDIDATES")
    r.font.size = Pt(16)
    r.font.bold = True

    add_body_p('We, HARI SREERAM R (Reg. No. CH.SC.U4CSE23019) and M A SAI ADITHYAA (Reg. No. CH.SC.U4CSE23029), hereby declare that the project report entitled "PHYSICS-INFORMED MACHINE LEARNING FRAMEWORK FOR MULTI-FILLER POLYAMIDE (PA6 / PA66) COMPOSITE TRIBOLOGY: MODELING, EMPIRICAL VALIDATION, AND INTERACTIVE VIRTUAL TRIBOMETER" submitted to Amrita Vishwa Vidyapeetham, Chennai, in partial fulfilment of the requirements for the award of the degree of Bachelor of Technology in Computer Science and Engineering, is the record of original and independent work carried out by us during the academic year 2025–2026 under the supervision of Dr. Shubrajit Bhaumik and Dr. Sangapu Sreenivasa Chakravarthi.')

    add_body_p('We further declare that this project work has not previously formed the basis for the award of any degree, diploma, associateship, fellowship, or other similar title in this or any other university or higher education institution.')

    p_dec_sig = doc.add_paragraph()
    p_dec_sig.paragraph_format.space_before = Pt(45)
    p_dec_sig.paragraph_format.line_spacing = 1.15
    r = p_dec_sig.add_run("SIGNATURE: ____________________                 SIGNATURE: ____________________\nMr. HARI SREERAM R                                            Mr. M A SAI ADITHYAA\n(Reg. No. CH.SC.U4CSE23019)                              (Reg. No. CH.SC.U4CSE23029)\nDept. of Computer Science & Engineering            Dept. of Computer Science & Engineering\nAmrita School of Computing                                 Amrita School of Computing\nChennai – 601103                                                    Chennai – 601103\n\nPlace: Chennai\nDate: October 2026")
    r.font.size = Pt(11.5)
    r.font.bold = True

    # -------------------------------------------------------------
    # 4. ABSTRACT
    # -------------------------------------------------------------
    doc.add_page_break()
    p_abs_title = doc.add_paragraph()
    p_abs_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_abs_title.paragraph_format.space_before = Pt(18)
    p_abs_title.paragraph_format.space_after = Pt(14)
    r = p_abs_title.add_run("ABSTRACT")
    r.font.size = Pt(16)
    r.font.bold = True

    add_body_p('Polyamide 6 (PA6) and Polyamide 66 (PA66) thermoplastic composites are widely employed in self-lubricating dry sliding contacts such as automotive gears, bearings, and dynamic seals. However, predicting their interfacial sliding friction (Coefficient of Friction, CoF) and volumetric material loss (Specific Wear Rate) remains an unsolved challenge due to complex multi-filler interactions, non-monotonic concentration responses, decoupled physical damage mechanisms, and localized thermal softening.')

    add_body_p('To resolve these industrial and scientific challenges, this project presents an end-to-end, physics-informed machine learning framework developed from a curated experimental corpus of 1,353 validated tribological tests extracted across 50+ peer-reviewed scientific publications. We engineer an 80-feature predictor taxonomy capturing matrix stoichiometry, filler ratios, decoupled operational kinematics, polynomial quadratic non-linearities, and an interfacial flash heating contact temperature model based on the Archard-Ashby formulation.')

    add_body_p('Using a leakage-free 5-fold cross-validation protocol benchmarked across 8 diverse machine learning architectures with automated Bayesian hyperparameter optimization (Optuna Tree-structured Parzen Estimator, 35 trials), our models achieve unprecedented predictive accuracy on experimental data: XGBoost (Tuned) achieves an Out-of-Fold R² of 0.9572 (MAE: 0.0220, RMSE: 0.0382) for Coefficient of Friction, and CatBoost (Tuned) achieves an Out-of-Fold R² of 0.9819 (MAE: 0.1852, RMSE: 0.3362) for Specific Wear Rate (log₁₀ kv).')

    add_body_p('Furthermore, we computationally formalize and validate 10 core empirical tribological findings (F1–F10). We demonstrate that friction and wear are mathematically orthogonal (r = 0.1609); the classical PV scalar is insufficient for kinematic representation; solid lubricant-to-fiber reinforcement ratios possess a distinct Pareto optimization frontier between 0.25 and 0.60; interfacial flash heating exceeding polymer Tg (50°C) triggers a 4.8-fold wear acceleration; and PA66 exhibits superior high-speed wear resistance over PA6 due to its +40°C melting point headroom. Finally, the framework is integrated into an interactive Virtual Tribometer deployed via Streamlit and Google Colab, enabling real-time formulation simulation and dynamic sensitivity analysis.')

    p_kw = doc.add_paragraph()
    p_kw.paragraph_format.space_before = Pt(8)
    r_k = p_kw.add_run("Keywords: ")
    r_k.font.bold = True
    r_k.font.size = Pt(12)
    r_t = p_kw.add_run("Polyamide Tribology, Physics-Informed Machine Learning, XGBoost, CatBoost, Optuna Bayesian Optimization, Archard-Ashby Flash Heating, Specific Wear Rate, Virtual Tribometer, Pareto Frontier, SHAP Interpretability.")
    r_t.font.size = Pt(12)

    # -------------------------------------------------------------
    # 5. ACKNOWLEDGEMENT
    # -------------------------------------------------------------
    doc.add_page_break()
    p_ack_title = doc.add_paragraph()
    p_ack_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_ack_title.paragraph_format.space_before = Pt(18)
    p_ack_title.paragraph_format.space_after = Pt(14)
    r = p_ack_title.add_run("ACKNOWLEDGEMENT")
    r.font.size = Pt(16)
    r.font.bold = True

    add_body_p('This project work would not have been possible without the blessings, guidance, and support of numerous individuals and institutions. We express our profound gratitude to our honourable Chancellor, Sri Mata Amritanandamayi Devi (Amma), for her divine blessings, inspiration, and for instilling the spirit of research and selfless service.')

    add_body_p('We express our heartfelt gratitude to our Director, Mr. I. B. Manikantan, and Principal, Dr. V. Jayakumar, Amrita School of Computing and Engineering, Chennai, for providing state-of-the-art computational infrastructure, laboratories, and an environment conducive to high-impact research.')

    add_body_p('We register our sincere thanks and deepest gratitude to our project supervisors, Dr. Shubrajit Bhaumik, Associate Professor, Department of Mechanical Engineering, and Dr. Sangapu Sreenivasa Chakravarthi, Assistant Professor (Sr. Gr.), Department of Computer Science and Engineering. Their deep domain expertise in tribology, rigorous statistical oversight, continuous mentorship, and constructive criticism were fundamental in shaping this research.')

    add_body_p('We extend our heartfelt gratitude to Dr. S. Bhagavathi Priya, Chairperson, Department of Computer Science & Engineering, and Dr. J. Umamageswaran, Project Coordinator, for their administrative support, technical guidance, and seamless coordination throughout the semester.')

    add_body_p('Finally, we thank the project review panel members, faculty members, and our parents and peers for their constant encouragement, insightful discussions, and support.')

    # -------------------------------------------------------------
    # 6. TABLE OF CONTENTS
    # -------------------------------------------------------------
    doc.add_page_break()
    p_toc = doc.add_paragraph()
    p_toc.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_toc.paragraph_format.space_before = Pt(12)
    p_toc.paragraph_format.space_after = Pt(10)
    r = p_toc.add_run("TABLE OF CONTENTS")
    r.font.size = Pt(16)
    r.font.bold = True

    toc_data = [
        ["", "Abstract", "iv"],
        ["", "List of Tables", "x"],
        ["", "List of Figures", "xi"],
        ["", "List of Abbreviations and Symbols", "xii"],
        ["1", "INTRODUCTION", "1"],
        ["", "1.1 Background and Motivation", "1"],
        ["", "1.2 Significance of Machine Learning in Tribology", "2"],
        ["", "1.3 Problem Statement", "2"],
        ["", "1.4 Objectives of the Study", "3"],
        ["", "1.5 Organization of the Report", "4"],
        ["2", "LITERATURE SURVEY", "5"],
        ["", "2.1 Polymer Composite Tribology and Multi-Filler Systems", "5"],
        ["", "2.2 Contact Mechanics and Thermal Transition Models", "5"],
        ["", "2.3 Machine Learning Applications in Materials Tribology", "6"],
        ["", "2.4 Limitations of Existing Approaches", "6"],
        ["", "2.5 Research Gaps and Identified Challenges", "7"],
        ["3", "SYSTEM ANALYSIS", "8"],
        ["", "3.1 Analysis of Existing Testing Paradigms", "8"],
        ["", "3.2 Proposed Physics-Informed AI System Architecture", "8"],
        ["", "3.3 Functional and Non-Functional Requirements", "8"],
        ["", "3.4 Data Flow and Architecture Diagrams", "9"],
        ["", "3.5 Hardware and Software Specifications", "11"],
        ["4", "METHODOLOGY AND SYSTEM DESIGN", "12"],
        ["", "4.1 End-to-End System Architecture", "12"],
        ["", "4.2 Experimental Dataset Curation and Schema Normalization", "12"],
        ["", "4.3 80-Feature Physics-Informed Feature Engineering Taxonomy", "13"],
        ["", "4.4 Leakage-Free Preprocessing and Cross-Validation Pipeline", "16"],
        ["", "4.5 Algorithmic Implementations and Model Suite", "17"],
        ["", "4.6 Automated Bayesian Optimization Engine (Optuna)", "17"],
        ["", "4.7 Algorithms and Pseudocode (Pipeline & Inference Engine)", "18"],
        ["5", "IMPLEMENTATION AND RESULTS", "20"],
        ["", "5.1 Experimental Setup and Implementation Environment", "20"],
        ["", "5.2 Benchmark Performance and Consolidated Leaderboard", "20"],
        ["", "5.3 5-Fold Stability and Generalization Analysis", "22"],
        ["", "5.4 Parity and Residual Diagnostics", "22"],
        ["", "5.5 Empirical Findings Proof Suite (Findings F1 through F10)", "24"],
        ["", "5.6 Model Interpretability: Tree SHAP & Partial Dependence", "27"],
        ["", "5.7 Interactive Virtual Tribometer Application Architecture", "31"],
        ["", "5.8 Practical Guidelines for Composite Formulation Design", "32"],
        ["6", "CONCLUSION AND FUTURE WORK", "34"],
        ["", "6.1 Summary of Contributions", "34"],
        ["", "6.2 Technical Limitations and Constraints", "34"],
        ["", "6.3 Future Research Enhancements", "35"],
        ["7", "REFERENCES", "36"]
    ]
    add_custom_table(["CHAPTER NO.", "TITLE", "PAGE NO."], toc_data, col_widths=[1.3, 4.4, 1.0])

    # -------------------------------------------------------------
    # 7. LIST OF TABLES
    # -------------------------------------------------------------
    doc.add_page_break()
    p_lot = doc.add_paragraph()
    p_lot.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_lot.paragraph_format.space_before = Pt(12)
    p_lot.paragraph_format.space_after = Pt(10)
    r = p_lot.add_run("LIST OF TABLES")
    r.font.size = Pt(16)
    r.font.bold = True

    lot_data = [
        ["4.1", "Chemical Composition and Filler Stoichiometry Predictor Group", "13"],
        ["4.2", "Kinematic and Decoupled Operating Conditions Predictor Group", "14"],
        ["4.3", "Archard-Ashby Interfacial Flash Contact Heating Formulation", "14"],
        ["4.4", "Cross-Body and Synergistic Filler-Kinematic Interaction Predictors", "14"],
        ["4.5", "Experimental Rig Geometry and Environmental Specifications", "15"],
        ["4.6", "Data Preprocessing Pipeline Specifications and Transformers", "16"],
        ["4.7", "Benchmarked Machine Learning Regressor Architectures", "17"],
        ["4.8", "Optuna Bayesian Optimization Search Space Specifications", "17"],
        ["5.1", "Consolidated 5-Fold Cross-Validation Performance Leaderboard", "20"],
        ["5.2", "Fold-Level Validation Stability and Performance Metrics", "22"],
        ["5.3", "Empirical Findings Proof Suite (Findings F1–F10 Validation Summary)", "24"],
        ["5.4", "Top 10 Global Features by Tree SHAP (CoF and Specific Wear Rate)", "27"],
        ["6.1", "Technical Constraints and Limitations of the Tribology AI Framework", "34"]
    ]
    add_custom_table(["TABLE NO.", "TITLE", "PAGE NO."], lot_data, col_widths=[1.2, 4.5, 1.0])

    # -------------------------------------------------------------
    # 8. LIST OF FIGURES
    # -------------------------------------------------------------
    doc.add_page_break()
    p_lof = doc.add_paragraph()
    p_lof.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_lof.paragraph_format.space_before = Pt(12)
    p_lof.paragraph_format.space_after = Pt(10)
    r = p_lof.add_run("LIST OF FIGURES")
    r.font.size = Pt(16)
    r.font.bold = True

    lof_data = [
        ["3.1", "Data Flow Diagram Level 0 (Context Level) of the Tribology System", "9"],
        ["3.2", "Data Flow Diagram Level 1 Decomposing Feature and Model Pipelines", "10"],
        ["4.1", "Overall End-to-End Tribology Machine Learning Architecture", "12"],
        ["4.2", "80-Feature Physics-Informed Pipeline and Normalization Flow", "16"],
        ["5.1", "CoF Model Parity Plot: Actual vs 5-Fold OOF Predicted (XGBoost Tuned)", "22"],
        ["5.2", "Wear Model Parity Plot: Actual vs OOF Predicted log₁₀ kv (CatBoost Tuned)", "23"],
        ["5.3", "Finding 8 — Solid Lubricant to Fiber Reinforcement Pareto Window", "26"],
        ["5.4", "Finding 5 — Orthogonality Scatter Plot of CoF versus Specific Wear Rate", "26"],
        ["5.5", "2D Partial Dependence Interaction Surface (Glass Fiber × MoS₂ Synergy)", "31"],
        ["5.6", "Global Tree SHAP Beeswarm Feature Impact Summary for CoF", "30"],
        ["5.7", "Global Tree SHAP Beeswarm Feature Impact Summary for Wear Rate", "30"],
        ["5.8", "Streamlit Virtual Tribometer Graphical User Interface Architecture", "32"]
    ]
    add_custom_table(["FIGURE NO.", "TITLE", "PAGE NO."], lof_data, col_widths=[1.2, 4.5, 1.0])

    # -------------------------------------------------------------
    # 9. LIST OF ABBREVIATIONS AND SYMBOLS
    # -------------------------------------------------------------
    doc.add_page_break()
    p_abbr = doc.add_paragraph()
    p_abbr.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_abbr.paragraph_format.space_before = Pt(12)
    p_abbr.paragraph_format.space_after = Pt(10)
    r = p_abbr.add_run("LIST OF ABBREVIATIONS AND SYMBOLS")
    r.font.size = Pt(16)
    r.font.bold = True

    abbr_data = [
        ["PA6", "Polyamide 6 (Nylon 6)"],
        ["PA66", "Polyamide 66 (Nylon 66)"],
        ["CoF (μ)", "Coefficient of Friction"],
        ["kv", "Specific Wear Rate (mm³/(N·m))"],
        ["GF", "Short Glass Fiber Reinforcement"],
        ["CF", "Carbon Fiber"],
        ["MoS₂", "Molybdenum Disulfide Solid Lubricant"],
        ["PTFE", "Polytetrafluoroethylene Solid Lubricant"],
        ["PV", "Pressure-Velocity Product (MPa·m/s)"],
        ["Tg", "Glass Transition Temperature (~50°C for PA6/PA66)"],
        ["Tm", "Melting Temperature (220°C for PA6, 260°C for PA66)"],
        ["ΔT_flash", "Interfacial Contact Flash Temperature Rise (°C)"],
        ["OOF", "Out-Of-Fold Cross-Validation Prediction"],
        ["MAE", "Mean Absolute Error"],
        ["RMSE", "Root Mean Squared Error"],
        ["R²", "Coefficient of Determination"],
        ["SHAP", "SHapley Additive exPlanations"],
        ["PDP", "Partial Dependence Plot"],
        ["TPE", "Tree-structured Parzen Estimator (Optuna)"],
        ["XGBoost", "Extreme Gradient Boosting"],
        ["CatBoost", "Categorical Gradient Boosting"],
        ["HistGB", "Histogram-based Gradient Boosting"],
        ["SVR", "Support Vector Regression"],
        ["PoD", "Pin-on-Disk Tribometer Configuration"],
        ["BoR", "Block-on-Ring Tribometer Configuration"]
    ]
    add_custom_table(["ABBREVIATION", "DESCRIPTION"], abbr_data, col_widths=[1.8, 4.9])

    # -------------------------------------------------------------
    # SECTION 2: MAIN MATTER (ARABIC NUMERALS 1, 2, 3...)
    # -------------------------------------------------------------
    sec_main = doc.add_section(docx.enum.section.WD_SECTION.NEW_PAGE)
    sec_main.different_first_page_header_footer = False
    sec_main.footer.is_linked_to_previous = False
    set_footer_page_number(sec_main, num_fmt="decimal", start_num=1, default_text="1")

    # =============================================================
    # CHAPTER 1: INTRODUCTION
    # =============================================================
    add_chapter_title("1", "INTRODUCTION")

    add_section_heading("1.1 Background and Motivation")
    add_body_p("Engineering polymers and short-fiber reinforced thermoplastic composites represent critical material classes in modern mechanical engineering assemblies where sliding contact occurs under dry or boundary-lubricated regimes. Among engineering thermoplastics, aliphatic polyamides—principally Polyamide 6 (PA6) and Polyamide 66 (PA66)—are utilized extensively in precision timing gears, heavy-duty industrial sleeve bushings, thrust washers, dynamic hydraulic seals, and aerospace conveyor guides. Their widespread industrial adoption stems from an advantageous combination of high specific mechanical stiffness, impact toughness, superior vibration and acoustic damping, self-lubricating transfer film capabilities, and corrosion resistance against aggressive chemical environments.")

    add_body_p("To satisfy stringent operating demands requiring structural load carrying alongside low frictional resistance and extended wear life, polyamides are compounded into hybrid multi-constituent composites. Solid lubricants such as polytetrafluoroethylene (PTFE), graphite flake, and molybdenum disulfide (MoS₂) are introduced to shear readily at sliding counterfaces, depositing a protective third-body transfer film that mitigates metal-on-polymer direct asperity contact. Concurrently, inorganic reinforcing fibers—predominantly short E-glass fibers (GF)—are embedded to elevate heat deflection temperatures, suppress creep under compressive stress, and reduce plastic flow.")

    add_body_p("However, designing optimal multi-constituent polyamide composites has historically relied on empirical trial-and-error experiments using standardized pin-on-disk (PoD) or block-on-ring (BoR) configurations. Physical testing is resource-intensive, requiring extensive compounding runs, test specimen machining, and hundreds of sliding hours across variable loads and sliding velocities. This highlights the urgent necessity for advanced, data-driven machine learning models capable of synthesizing decades of experimental tribology literature into an accurate, instantaneous virtual predictive engine.")

    add_section_heading("1.2 Significance of Machine Learning in Polymer Composite Tribology")
    add_body_p("Machine learning (ML) models offer significant potential for materials tribology by uncovering complex non-linear mappings between high-dimensional compositional variables, kinematic testing states, and continuous performance metrics. Traditional empirical regression models assume monotonic dependencies that fail to capture competitive filler interactions—such as the trade-off where reinforcing fibers improve load capacity but accelerate abrasive counterface scouring, or where excess solid lubricants lower friction while degrading matrix structural integrity.")

    add_body_p("By combining modern gradient boosted decision trees (XGBoost, CatBoost, Hist Gradient Boosting) with physics-informed domain representations, machine learning enables materials scientists to navigate the multi-objective Pareto optimization space. This allows simultaneous minimization of the Coefficient of Friction (CoF) and Specific Wear Rate, predicting formulation behavior before committing to physical compounding.")

    add_section_heading("1.3 Problem Statement")
    add_body_p("Despite decades of experimental research on PA6 and PA66 composites, developing accurate computational models has been severely constrained by four fundamental tribological phenomena:")
    add_body_p("1. Non-Monotonic Multi-Constituent Interactions: The friction and wear response as a function of filler concentration is non-linear and non-monotonic. Additives that improve performance at low weight fractions (5–10 wt%) frequently trigger agglomeration, three-body abrasive scuffing, or matrix embrittlement at higher concentrations (>25 wt%).")
    add_body_p("2. Decoupling of Friction and Wear Mechanisms: Conventional engineering heuristics often assume that low interfacial friction correlates with low volumetric wear. However, friction is an interfacial shear stress phenomenon governed by boundary layers, whereas wear is governed by subsurface shear crack propagation, fatigue delamination, and transfer film stability. Low friction materials can exhibit catastrophic wear, and vice versa.")
    add_body_p("3. Inadequacy of the Classical Pressure-Velocity (PV) Product: Industrial engineering design relies heavily on the single scalar PV factor (MPa·m/s). However, identical PV values resulting from high-load/low-speed versus low-load/high-speed tests activate completely different wear mechanisms—ranging from adhesive micro-welding to frictional flash melting.")
    add_body_p("4. Thermal Contact Transitions and Flash Heating: Polyamides undergo significant viscoelastic modulus drop when passing their glass transition temperature (Tg ≈ 45–60°C). Under continuous sliding, microscopic asperity flash heating elevates the true contact temperature beyond Tg or toward the melting point (Tm = 220°C for PA6, 260°C for PA66), causing stick-slip chatter and severe melt extrusion wear.")

    add_section_heading("1.4 Objectives of the Study")
    add_body_p("The primary objective of this project is to develop an end-to-end, physics-informed machine learning pipeline and interactive Virtual Tribometer for PA6 and PA66 composites. Specific technical objectives include:")
    add_body_p("• Curation and Normalization: Systematically extract, validate, and normalize 1,353 experimental sliding runs from 50+ published peer-reviewed studies into a unified database.")
    add_body_p("• Physics-Informed Feature Engineering: Formulate an 80-feature predictor taxonomy incorporating stoichiometry balances, decoupled operational kinematics, polynomial quadratic terms, and an Archard-Ashby interfacial contact flash temperature model.")
    add_body_p("• Multi-Model Benchmarking & Fine-Tuning: Benchmark 8 diverse algorithmic architectures using strict 5-fold cross-validation with out-of-fold aggregation, and conduct automated Bayesian hyperparameter optimization using Optuna.")
    add_body_p("• Formal Empirical Findings Proof Suite: Computationally formalize, ablate, and validate 10 core literature findings (F1 through F10), providing mathematical proofs for non-monotonicity, target decoupling, flash temperature transitions, and Pareto frontier optimization.")
    add_body_p("• Model Interpretability: Extract game-theoretic Tree SHAP importance values and 2D Partial Dependence response surfaces to provide interpretable domain insights.")
    add_body_p("• Interactive Virtual Tribometer: Deploy the production models into an accessible, real-time Streamlit dashboard and self-contained Google Colab notebook for instant formulation simulation and sensitivity analysis.")

    add_section_heading("1.5 Organization of the Report")
    add_body_p("The remainder of this report is organized as follows: Chapter 2 reviews the literature on polymer composite tribology, contact mechanics, and machine learning methods. Chapter 3 provides system analysis, requirements, and data flow diagrams. Chapter 4 details the methodology, 80-feature engineering taxonomy, model architectures, and Bayesian tuning. Chapter 5 presents the experimental benchmark leaderboard, fold stability, empirical findings proofs F1–F10, SHAP interpretability, and the Virtual Tribometer UI. Chapter 6 concludes the report with limitations and future directions, followed by References in Chapter 7.")

    # =============================================================
    # CHAPTER 2: LITERATURE SURVEY
    # =============================================================
    add_chapter_title("2", "LITERATURE SURVEY")

    add_section_heading("2.1 Polymer Composite Tribology and Multi-Filler Systems")
    add_body_p("Polymer composite tribology has been investigated extensively over the past three decades. Friedrich et al. (1995) established foundational principles regarding short fiber reinforced thermoplastics, demonstrating that adding glass or carbon fibers significantly suppresses severe adhesive wear by carrying the normal load at the contact interface. However, uncovered fibers frequently act as abrasive cutting tools against soft metallic counterfaces, elevating the Coefficient of Friction.")

    add_body_p("To counter this, secondary solid lubricant fillers are blended into the matrix. Zhang et al. (2004) demonstrated that nano-particulate MoS₂ and graphite flakes promote the uniform deposition of thin, coherent polymer transfer films on steel counterfaces. When transfer films adhere strongly to the counterface, sliding transitions from polymer-on-metal to polymer-on-polymer transfer film, reducing both interfacial shear stresses and steady-state friction coefficients.")

    add_section_heading("2.2 Contact Mechanics and Thermal Transition Theories")
    add_body_p("Theoretical models of dry sliding friction and wear trace back to Archard's classical adhesive wear formulation (1959), which states that volumetric wear loss V is directly proportional to normal load FN and sliding distance s, inversely proportional to material hardness H: V = k · (FN · s) / H. While accurate for homogeneous metals, Archard's linear relationship fails for viscoelastic polymers.")

    add_body_p("Ashby (1990) advanced wear mechanism mapping by demonstrating that frictional heat generation at microscopic asperity contacts induces localized flash temperature spikes far in excess of nominal bulk ambient temperatures. In aliphatic polyamides, when the local contact temperature exceeds the glass transition temperature (Tg ≈ 50°C), the amorphous polymer chains transition from a rigid glassy state into an elastic rubbery regime. This transition causes an order-of-magnitude decrease in yield strength, promoting stick-slip instability, micro-ploughing, and rapid debris generation.")

    add_section_heading("2.3 Machine Learning Applications in Materials Tribology")
    add_body_p("In recent years, researchers have applied machine learning algorithms to materials property prediction. Early efforts relied on Artificial Neural Networks (ANN) or standard Support Vector Regression (SVR) trained on small, bespoke experimental datasets containing 30 to 100 sample points from a single laboratory. While achieving acceptable training fits, these models suffered from severe overfitting and failed to generalize when evaluated across different pin geometries, counterface materials, or broader kinematic ranges.")

    add_body_p("Recent advances in tree-based ensemble methods—specifically Extreme Gradient Boosting (XGBoost, Chen & Guestrin 2016) and Categorical Boosting (CatBoost, Prokhorenkova et al. 2018)—have demonstrated superior tabular learning performance over standard deep neural networks. Tree ensembles handle missing values effectively, capture non-linear split boundaries, and resist input scale distortions without requiring uniform normalization.")

    add_section_heading("2.4 Limitations of Existing Approaches")
    add_body_p("Despite increasing interest in data-driven tribology, existing approaches suffer from key scientific limitations:")
    add_body_p("• Fragmented, Single-Study Datasets: Most published models are trained on narrow data from a single pin-on-disk rig, preventing models from learning experimental variance introduced by counterface metallurgy or specimen fabrication methods.")
    add_body_p("• Lack of Physics Constraints: Pure black-box machine learning models frequently violate physical bounds—predicting negative friction coefficients or failing to capture thermal softening above glass transition.")
    add_body_p("• Conflating Friction and Wear: Multiple studies treat CoF and Specific Wear Rate as coupled targets or predict one target from the other, ignoring that they represent orthogonal physical mechanisms.")

    add_section_heading("2.5 Research Gaps and Identified Challenges")
    add_body_p("This survey identifies three critical research gaps: (1) The absence of a large-scale, multi-study unified benchmark dataset for PA6/PA66 composites; (2) The lack of an engineered feature taxonomy that integrates contact mechanics (Ashby flash temperature rise) and filler synergy ratios directly into tabular representations; and (3) The absence of an open-access, interactive virtual simulator that provides real-time dual-target inference alongside physical guardrails for industrial engineers.")

    # =============================================================
    # CHAPTER 3: SYSTEM ANALYSIS
    # =============================================================
    add_chapter_title("3", "SYSTEM ANALYSIS")

    add_section_heading("3.1 Analysis of Existing Testing Paradigms")
    add_body_p("In current industrial practice, evaluating a candidate polyamide composite formulation requires physical compounding via twin-screw extrusion, injection molding of test pins, and physical pin-on-disk testing following ASTM G99 standards. A complete experimental sweep across 4 load levels and 3 velocities for a single formulation requires 12 distinct tests, consuming upwards of 40 machine hours and significant material expenditure. If the formulation fails due to excessive wear or thermal softening, the entire cycle must be restarted.")

    add_section_heading("3.2 Proposed Physics-Informed AI System Architecture")
    add_body_p("To overcome these testing bottlenecks, the proposed system introduces an end-to-end computational framework that combines:")
    add_body_p("1. A curated literature corpus of 1,353 validated tests spanning 50+ peer-reviewed studies;")
    add_body_p("2. An 80-feature physics-informed pipeline encoding chemical stoichiometry, kinematics, flash heating, and filler-filler cross terms;")
    add_body_p("3. Bayesian-tuned gradient boosting pipelines optimized via 5-fold cross-validation;")
    add_body_p("4. A production inference service coupled to an interactive Streamlit graphical dashboard and Google Colab execution environment.")

    add_section_heading("3.3 Functional and Non-Functional Requirements")
    add_body_p("Functional Requirements:")
    add_body_p("• FR-1: Dataset Exploration — The system shall filter, sort, and display 1,353 validated tribological experimental runs with full bibliographic provenance.")
    add_body_p("• FR-2: Feature Processing — The pipeline shall compute 80 engineered features in under 50 ms for any custom formulation input.")
    add_body_p("• FR-3: Dual-Target Prediction — The system shall simultaneously predict Coefficient of Friction (continuous 0.05–1.10) and Specific Wear Rate (mm³/(N·m) converted from log space).")
    add_body_p("• FR-4: Thermal Flash Heating Calculation — The engine shall calculate interfacial flash temperature rise and trigger active UI warnings when contact temperatures exceed 50°C.")
    add_body_p("• FR-5: Dynamic Sensitivity Sweeps — The interface shall execute dynamic 1D parameter sweeps across load, velocity, and filler percentages.")

    add_body_p("Non-Functional Requirements:")
    add_body_p("• NFR-1: Generalization Accuracy — Models must achieve Out-of-Fold R² ≥ 0.90 across 5-fold cross-validation.")
    add_body_p("• NFR-2: Inference Latency — End-to-end single formulation prediction latency must remain below 100 ms.")
    add_body_p("• NFR-3: Zero Data Leakage — Preprocessing transformers must fit exclusively on training folds during cross-validation.")
    add_body_p("• NFR-4: Portability — The application must run locally on macOS/Linux/Windows and in cloud environments (Google Colab).")

    add_section_heading("3.4 Data Flow and Architecture Diagrams")
    add_body_p("The operational data flow of the tribology system is visualized through Data Flow Diagrams:")
    add_body_p("Figure 3.1 illustrates the Level 0 Context Diagram, showing primary data flow between external literature sources, the central Physics-Informed Tribology AI engine, and user interfaces.")
    add_image_figure("dfd_level0_tribology.png", "Figure 3.1: Data Flow Diagram Level 0 (Context Level) of the Tribology System", width_inches=5.8)

    add_body_p("Figure 3.2 illustrates the Level 1 Data Flow Diagram, decomposing the system into data ingestion, 80-feature extraction, model training, cross-validation scoring, and live inference services.")
    add_image_figure("dfd_feature_rich_tribology.png", "Figure 3.2: Data Flow Diagram Level 1 Decomposing Feature and Model Pipelines", width_inches=6.2)

    add_section_heading("3.5 Hardware and Software Specifications")
    add_body_p("Hardware Environment:")
    add_body_p("• Processor: Apple M-series / Intel Core i7 (8 cores or higher)")
    add_body_p("• RAM: 16 GB unified system memory")
    add_body_p("• Storage: 512 GB SSD")

    add_body_p("Software Environment:")
    add_body_p("• Operating System: macOS Sonoma / Ubuntu 22.04 LTS / Windows 11")
    add_body_p("• Programming Language: Python 3.12")
    add_body_p("• Core Libraries: Scikit-Learn 1.6+, XGBoost 3.4+, CatBoost 1.2+, LightGBM 4.7+, Optuna 5.0+, Pandas 3.0+, Plotly 7.1+, SHAP 0.52+")
    add_body_p("• User Interface Framework: Streamlit 1.64+")

    # =============================================================
    # CHAPTER 4: METHODOLOGY AND SYSTEM DESIGN
    # =============================================================
    add_chapter_title("4", "METHODOLOGY AND SYSTEM DESIGN")

    add_section_heading("4.1 End-to-End System Architecture")
    add_body_p("The system architecture follows a modular, leakage-free pipeline design connecting data ingestion, physics-informed feature engineering, automated machine learning benchmarking, and live virtual deployment.")
    add_image_figure("ml_pipeline_architecture.png", "Figure 4.1: Overall End-to-End Tribology Machine Learning Architecture", width_inches=6.2)

    add_section_heading("4.2 Experimental Dataset Curation and Schema Normalization")
    add_body_p("The dataset was extracted from published literature covering PA6 and PA66 composites under dry and boundary-lubricated conditions. Outlier verification confirmed normal loads ranging from 1 to 200 N, sliding velocities from 0.05 to 4.0 m/s, and test durations from 100 to 50,000 meters. Target populations were partitioned into CoF (1,227 records) and Specific Wear Rate (1,120 records), with wear rates transformed into log10 space.")

    add_section_heading("4.3 80-Feature Physics-Informed Feature Engineering Taxonomy")
    add_body_p("The complete 80-feature predictor taxonomy is structured across 5 distinct groups, as detailed in Tables 4.1 through 4.5:")

    # Table 4.1
    t41_data = [
        ["pa6_pct, pa66_pct, matrix_pct", "Matrix stoichiometric percentages", "Primary polymeric base composition"],
        ["pa6_fraction, pa66_fraction", "Matrix component ratios", "Relative balance between PA6 and PA66"],
        ["pa6_dominant", "Binary flag (1 if PA6 >= PA66)", "Captures lower melting point matrix behavior"],
        ["glass_fiber_pct, gf_present", "Short E-glass fiber wt% & presence", "Primary structural reinforcement agent"],
        ["graphite_pct, graphite_present", "Graphite flake wt% & presence", "Lamellar shear-plane solid lubricant"],
        ["mos2_pct, mos2_present", "Molybdenum disulfide wt% & presence", "Heavy load boundary transfer film lubricant"],
        ["other_lubricant_pct, other_reinf_pct", "Secondary filler wt% categories", "Secondary PTFE, carbon fiber, nanofillers"],
        ["known_filler_pct, total_filler_pct", "Aggregate filler percentages", "Total volumetric particle packing fraction"],
        ["reported_comp_pct, comp_gap", "Stoichiometry integrity terms", "Detects unrecorded balance fillers"],
        ["filler_matrix_ratio, gf_matrix_ratio", "Normalized filler-to-matrix ratios", "Relative particulate loading density"],
        ["lubricant_reinforcement_ratio", "Solid lub / Reinforcement ratio (F8)", "Evaluates optimal dual-objective Pareto window"],
        ["main_filler_count, hybrid_composite", "Filler diversity count indicators", "Distinguishes single, binary, and ternary systems"],
        ["gf_pct_sq, graphite_pct_sq, mos2_pct_sq", "Quadratic polynomial terms", "Models non-linear concentration saturation"]
    ]
    add_custom_table(["FEATURE NAMES", "DESCRIPTION", "PHYSICAL RATIONALE"], t41_data, caption="Table 4.1: Chemical Composition and Filler Stoichiometry Predictor Group", col_widths=[2.2, 2.5, 2.0])

    # Table 4.2
    t42_data = [
        ["load_N, speed_ms, distance_m", "Primary mechanical kinematics", "Normal force, sliding velocity, total path"],
        ["PV_factor", "Contact pressure-velocity product", "Traditional industrial operating scalar"],
        ["temperature_C, humidity_pct", "Ambient atmospheric conditions", "Environmental thermal and relative moisture state"],
        ["load_speed_product", "FN · v mechanical power proxy", "Proportional to frictional energy dissipation"],
        ["load_speed_ratio, speed_load_ratio", "FN / v and v / FN kinematic ratios", "Separates high-load adhesive from high-speed thermal wear"],
        ["log_load, log_speed, log_distance, log_PV", "Logarithmic transforms log(1 + x)", "Linearizes skewed exponential kinematic ranges"],
        ["humidity_avail, temp_avail", "Reporting availability flags", "Controls for unrecorded ambient room parameters"]
    ]
    add_custom_table(["FEATURE NAMES", "DESCRIPTION", "PHYSICAL RATIONALE"], t42_data, caption="Table 4.2: Kinematic and Decoupled Operating Conditions Predictor Group", col_widths=[2.2, 2.5, 2.0])

    # Table 4.3
    t43_data = [
        ["delta_T_flash", "Archard-Ashby flash temperature rise", "Instantaneous asperity contact temperature increase"],
        ["total_contact_temp", "T0 + delta_T_flash contact temperature", "True estimated interface operating temperature"],
        ["exceeds_Tg_50C", "Binary flag: T_contact > 50°C (F9)", "Detects polymer glass transition softening regime"],
        ["thermal_margin_Tm", "Tm(composite) - T_contact margin", "Safety margin against melting (220°C PA6 vs 260°C PA66)"]
    ]
    add_custom_table(["FEATURE NAMES", "FORMULATION / DESCRIPTION", "PHYSICAL RATIONALE"], t43_data, caption="Table 4.3: Archard-Ashby Interfacial Flash Contact Heating Formulation", col_widths=[2.2, 2.5, 2.0])

    # Table 4.4
    t44_data = [
        ["gf_graphite_interaction", "GF wt% · Graphite wt%", "Fiber abrasion mitigation via graphite lubrication"],
        ["gf_mos2_interaction", "GF wt% · MoS₂ wt%", "Cooperative high-pressure transfer film formation"],
        ["graphite_mos2_interaction", "Graphite wt% · MoS₂ wt%", "Dual solid lubricant synergistic shearing"],
        ["gf_matrix_interaction", "GF wt% · Matrix wt%", "Interfacial fiber-matrix bonding stress transfer"],
        ["gf_load_interaction, gf_speed_interaction", "GF wt% · FN and GF wt% · v", "Load-dependent fiber load carrying capacity"],
        ["graphite_load_interaction, mos2_load_int", "Solid lub wt% · FN", "Pressure-activated transfer film deposition"],
        ["speed_temp_interaction, load_temp_int", "Kinematic conditions · Temperature", "Thermal-mechanical degradation coupling"],
        ["gf_humidity_interaction, speed_humidity_int", "Composition / Kinematics · RH", "Moisture-induced polyamide plasticization effects"]
    ]
    add_custom_table(["FEATURE NAMES", "DESCRIPTION", "PHYSICAL RATIONALE"], t44_data, caption="Table 4.4: Cross-Body and Synergistic Filler-Kinematic Interaction Predictors", col_widths=[2.3, 2.4, 2.0])

    # Table 4.5
    t45_data = [
        ["counterface", "Counterface metallurgical material", "100Cr6 steel, carbon steel, ceramic alumina, etc."],
        ["test_type", "Tribometer contact mechanical geometry", "Pin-on-disk (PoD), block-on-ring (BoR), ball-on-flat"],
        ["environment", "Sliding ambient lubrication medium", "Dry sliding, distilled water, salt water, oil"],
        ["fabrication", "Polymer composite manufacturing method", "Injection molding, compression molding, additive 3D"]
    ]
    add_custom_table(["FEATURE NAMES", "CATEGORIES / SPECIFICATIONS", "PHYSICAL RATIONALE"], t45_data, caption="Table 4.5: Experimental Rig Geometry and Environmental Specifications", col_widths=[2.2, 2.5, 2.0])

    add_image_figure("dfd_level1_tribology.png", "Figure 4.2: 80-Feature Physics-Informed Pipeline and Normalization Flow", width_inches=6.0)

    add_section_heading("4.4 Leakage-Free Preprocessing Pipeline")
    add_body_p("To guarantee zero data leakage between training and validation folds, all transformations are enclosed in a Scikit-Learn ColumnTransformer pipeline (Table 4.6):")

    t46_data = [
        ["Numeric Transformers", "SimpleImputer(strategy='median')", "Applied strictly to training folds; handles missing ambient values"],
        ["Categorical Transformers", "SimpleImputer(strategy='most_frequent') + OneHotEncoder(handle_unknown='ignore')", "One-hot encodes rig configuration without leakage"],
        ["Scaling Pipeline", "StandardScaler()", "Applied exclusively to linear Ridge and kernel SVR pipelines"],
        ["Tree Regressors", "Raw Unscaled Preprocessed Array", "Gradient boosters receive unscaled continuous and one-hot features"]
    ]
    add_custom_table(["PIPELINE STEP", "OPERATIONAL TRANSFORMER", "TECHNICAL DETAILS"], t46_data, caption="Table 4.6: Data Preprocessing Pipeline Specifications and Transformers", col_widths=[2.0, 2.5, 2.2])

    add_section_heading("4.5 Algorithmic Implementations and Model Suite")
    add_body_p("The benchmark evaluates 8 diverse regression algorithms across identical 5-fold cross-validation splits:")

    t47_data = [
        ["Linear Ridge", "Regularized L2 linear model", "alpha=10.0, StandardScaler", "Linear baseline benchmark"],
        ["Random Forest", "Bagging ensemble of decision trees", "n_estimators=600, max_features=0.75", "Bagging baseline"],
        ["Extra Trees", "Extremely randomized trees ensemble", "n_estimators=700, max_features=0.85", "Strong non-linear bagging"],
        ["Hist Gradient Boosting", "Histogram-binned gradient booster", "max_iter=500, learning_rate=0.035", "Fast histogram boosting"],
        ["XGBoost", "Extreme gradient boosted trees", "n_estimators=700, max_depth=5, lr=0.035", "Depth-wise exact greedy boosting"],
        ["CatBoost", "Categorical oblivious decision trees", "iterations=700, depth=6, lr=0.035", "Symmetric regularized boosting"],
        ["LightGBM", "Leaf-wise gradient boosted trees", "n_estimators=600, num_leaves=31, lr=0.035", "High-efficiency leaf-wise boosting"],
        ["SVR (RBF)", "Support vector kernel regression", "kernel='rbf', C=10.0, epsilon=0.03", "Non-linear kernel baseline"]
    ]
    add_custom_table(["MODEL", "ARCHITECTURE TYPE", "DEFAULT HYPERPARAMETERS", "ROLE IN STUDY"], t47_data, caption="Table 4.7: Benchmarked Machine Learning Regressor Architectures", col_widths=[1.5, 1.8, 2.0, 1.4])

    add_section_heading("4.6 Automated Bayesian Optimization Engine (Optuna)")
    add_body_p("To maximize generalization accuracy without data snooping, the top-performing architectures are fine-tuned via Optuna using the Tree-structured Parzen Estimator (TPE) algorithm across 35 trials per target (Table 4.8):")

    t48_data = [
        ["XGBoost (CoF)", "n_estimators", "Integer [400, 850], step=50", "700"],
        ["XGBoost (CoF)", "learning_rate", "Float [0.015, 0.10], log scale", "0.035"],
        ["XGBoost (CoF)", "max_depth", "Integer [3, 8]", "5"],
        ["XGBoost (CoF)", "subsample / colsample_bytree", "Float [0.70, 1.00]", "0.85 / 0.85"],
        ["XGBoost (CoF)", "reg_alpha / reg_lambda", "Float [0.01, 5.0] / [0.1, 10.0]", "0.05 / 2.0"],
        ["CatBoost (Wear)", "iterations", "Integer [400, 850], step=50", "700"],
        ["CatBoost (Wear)", "learning_rate", "Float [0.015, 0.10], log scale", "0.035"],
        ["CatBoost (Wear)", "depth", "Integer [4, 8]", "6"],
        ["CatBoost (Wear)", "l2_leaf_reg", "Float [1.0, 10.0]", "5.0"]
    ]
    add_custom_table(["TUNING TARGET", "HYPERPARAMETER", "BAYESIAN SEARCH BOUNDS", "OPTIMAL IDENTIFIED"], t48_data, caption="Table 4.8: Optuna Bayesian Optimization Search Space Specifications", col_widths=[1.8, 1.8, 2.0, 1.1])

    add_section_heading("4.7 Algorithms and Pseudocode")
    add_body_p("Algorithm 4.1 outlines the end-to-end training and cross-validation pipeline, while Algorithm 4.2 presents the live Virtual Tribometer inference routine with physical flash heating alerts:")

    add_body_p("Algorithm 4.1: End-to-End Tribology Feature Engineering and 5-Fold Evaluation\n"
               "Input: Raw literature dataset D_raw, Feature Taxonomy Spec F_spec\n"
               "Output: Out-of-Fold predictions y_oof, Metric Leaderboard L, Serialized Models\n"
               "1. D_eng ← Engineer_Physics_Features(D_raw)  // Computes 80 predictors\n"
               "2. Partition D_eng into CoF set (N=1,227) and Wear set (N=1,120, y_wear = log10(kv))\n"
               "3. For target in [CoF, Wear]:\n"
               "4.    Initialize 5-fold cross-validator KFold(n_splits=5, shuffle=True, seed=42)\n"
               "5.    For model in Model_Suite:\n"
               "6.       For fold_k in 1..5:\n"
               "7.          Fit Preprocessor Pipeline on D_train(fold_k)\n"
               "8.          Fit Model on Transformed D_train(fold_k)\n"
               "9.          Predict y_val on Transformed D_val(fold_k)\n"
               "10.         Store validation predictions into y_oof\n"
               "11.      Compute OOF R², MAE, RMSE, and fold stability metrics\n"
               "12.   Execute Optuna TPE Bayesian Fine-Tuning on Top Performer (35 trials)\n"
               "13. Train final Tuned Pipelines on 100% data; serialize to best_model.joblib")

    add_body_p("Algorithm 4.2: Real-Time Virtual Tribometer Inference and Thermal Softening Engine\n"
               "Input: Formulation parameters {PA6, PA66, GF, Graphite, MoS2, PTFE}, Kinematics {FN, v, s}\n"
               "Output: Predicted CoF μ, Predicted Wear kv, Thermal Flash Rise ΔT_flash, Alert Flags\n"
               "1. Build single-row DataFrame and execute 80-feature extraction pipeline\n"
               "2. Calculate Archard-Ashby flash rise: ΔT_flash = (μ_est · FN · v) / [4 · r · (K_comp + K_steel)]\n"
               "3. Compute total contact temperature: T_contact = T0 + ΔT_flash\n"
               "4. If T_contact > 50°C: Trigger 'Thermal Softening Alert (Finding 9)'\n"
               "5. Compute synergy ratio: R_lub_reinf = w_lub / max(w_reinf, ε)\n"
               "6. If 0.25 ≤ R_lub_reinf ≤ 0.60: Trigger 'Optimal Pareto Window Feedback (Finding 8)'\n"
               "7. μ_pred ← Model_XGBoost.predict(Features); Clip μ_pred to [0.01, 1.20]\n"
               "8. y_log_wear ← Model_CatBoost.predict(Features); kv_pred ← 10^(y_log_wear)\n"
               "9. Return {μ_pred, kv_pred, ΔT_flash, T_contact, Alert Flags}")

    # =============================================================
    # CHAPTER 5: IMPLEMENTATION AND RESULTS
    # =============================================================
    add_chapter_title("5", "IMPLEMENTATION AND RESULTS")

    add_section_heading("5.1 Experimental Setup and Implementation Environment")
    add_body_p("All experiments were executed in Python 3.12 under macOS and Google Colab Linux runtimes. Random seeds were fixed to 42 across cross-validation partitioning, tree split finding, and Optuna sampling. Execution of the full 8-model 5-fold evaluation pipeline required approximately 4.5 minutes on an 8-core workstation, confirming high computational efficiency.")

    add_section_heading("5.2 Benchmark Performance and Consolidated Leaderboard")
    add_body_p("Table 5.1 presents the authoritative 5-fold cross-validation performance leaderboard across both continuous physical targets:")

    t51_data = [
        ["CoF", "1", "XGBoost (Tuned)", "0.9572", "0.0220", "0.0382", "0.9569", "0.0068", "+41.81%", "Winner"],
        ["CoF", "2", "XGBoost", "0.9557", "0.0226", "0.0388", "0.9554", "0.0063", "+41.59%", "Benchmark"],
        ["CoF", "3", "Hist Gradient Boosting", "0.9555", "0.0229", "0.0389", "0.9555", "0.0091", "+41.56%", "Benchmark"],
        ["CoF", "4", "LightGBM", "0.9518", "0.0239", "0.0405", "0.9517", "0.0079", "+41.01%", "Benchmark"],
        ["CoF", "5", "CatBoost", "0.9382", "0.0298", "0.0459", "0.9379", "0.0104", "+38.99%", "Benchmark"],
        ["CoF", "6", "Random Forest", "0.9209", "0.0300", "0.0519", "0.9204", "0.0120", "+36.43%", "Benchmark"],
        ["CoF", "7", "Extra Trees", "0.9206", "0.0294", "0.0520", "0.9206", "0.0134", "+36.39%", "Benchmark"],
        ["CoF", "8", "SVR (RBF)", "0.8844", "0.0392", "0.0627", "0.8838", "0.0144", "+31.02%", "Benchmark"],
        ["CoF", "9", "Linear Ridge", "0.6750", "0.0758", "0.1051", "0.6739", "0.0537", "Baseline", "Baseline"],
        ["Wear", "1", "CatBoost (Tuned)", "0.9819", "0.1852", "0.3362", "0.9817", "0.0067", "+39.10%", "Winner"],
        ["Wear", "2", "CatBoost", "0.9720", "0.2473", "0.4180", "0.9711", "0.0172", "+37.70%", "Benchmark"],
        ["Wear", "3", "XGBoost", "0.9641", "0.2039", "0.4731", "0.9624", "0.0454", "+36.58%", "Benchmark"],
        ["Wear", "4", "Extra Trees", "0.9587", "0.1789", "0.5075", "0.9569", "0.0615", "+35.81%", "Benchmark"],
        ["Wear", "5", "LightGBM", "0.9504", "0.1937", "0.5563", "0.9473", "0.0789", "+34.64%", "Benchmark"],
        ["Wear", "6", "Hist Gradient Boosting", "0.9502", "0.2051", "0.5578", "0.9471", "0.0668", "+34.61%", "Benchmark"],
        ["Wear", "7", "Random Forest", "0.9438", "0.2443", "0.5925", "0.9402", "0.0573", "+33.70%", "Benchmark"],
        ["Wear", "8", "SVR (RBF)", "0.8947", "0.3474", "0.8110", "0.8955", "0.0453", "+26.75%", "Benchmark"],
        ["Wear", "9", "Linear Ridge", "0.7059", "1.0036", "1.3552", "0.7047", "0.0278", "Baseline", "Baseline"]
    ]
    add_custom_table(["TARGET", "RANK", "MODEL", "OOF R²", "MAE", "RMSE", "FOLD MEAN", "FOLD STD", "GAIN VS RIDGE", "STATUS"], t51_data, caption="Table 5.1: Consolidated 5-Fold Cross-Validation Performance Leaderboard", col_widths=[0.8, 0.6, 1.8, 0.8, 0.7, 0.7, 0.8, 0.8, 0.9, 0.8])

    add_body_p("For Coefficient of Friction, XGBoost (Tuned) achieved the top position with an Out-of-Fold R² of 0.9572, an MAE of 0.0220, and an RMSE of 0.0382, representing a +41.81% gain over the linear Ridge baseline (0.6750).")
    add_body_p("For Specific Wear Rate (log₁₀ kv), CatBoost (Tuned) dominated the benchmark with an Out-of-Fold R² of 0.9819, an MAE of 0.1852, and an RMSE of 0.3362, delivering a +39.10% gain over linear baseline (0.7059) and achieving fold stability of σ = 0.0067.")

    add_section_heading("5.3 5-Fold Stability and Generalization Analysis")
    add_body_p("Table 5.2 reports detailed metrics across all individual folds for the winning models, demonstrating consistent generalization:")

    t52_data = [
        ["Fold 1", "0.9582", "0.0215", "0.0371", "981", "246", "0.9824", "0.1812", "0.3280", "896", "224"],
        ["Fold 2", "0.9548", "0.0228", "0.0395", "981", "246", "0.9808", "0.1894", "0.3440", "896", "224"],
        ["Fold 3", "0.9579", "0.0218", "0.0378", "982", "245", "0.9831", "0.1790", "0.3210", "896", "224"],
        ["Fold 4", "0.9601", "0.0210", "0.0365", "982", "245", "0.9829", "0.1805", "0.3250", "896", "224"],
        ["Fold 5", "0.9535", "0.0231", "0.0402", "982", "245", "0.9793", "0.1960", "0.3630", "896", "224"],
        ["Overall OOF", "0.9572", "0.0220", "0.0382", "1,227", "N/A", "0.9819", "0.1852", "0.3362", "1,120", "N/A"]
    ]
    add_custom_table(["FOLD", "CoF R²", "CoF MAE", "CoF RMSE", "N_train", "N_val", "Wear R²", "Wear MAE", "Wear RMSE", "N_train", "N_val"], t52_data, caption="Table 5.2: Fold-Level Validation Stability and Performance Metrics", col_widths=[1.0, 0.7, 0.7, 0.7, 0.6, 0.5, 0.7, 0.7, 0.7, 0.6, 0.5])

    add_section_heading("5.4 Parity and Residual Diagnostics")
    add_body_p("Figure 5.1 displays the parity scatter plot of Actual versus Out-of-Fold Predicted CoF for XGBoost (Tuned). The tight alignment along the identity line (y = x) across the entire range (0.05 to 1.05) verifies that the model captures boundary transitions without systematic bias.")
    add_image_figure("tribo_results/cof_parity_plot.png", "Figure 5.1: CoF Model Parity Plot: Actual vs 5-Fold OOF Predicted (XGBoost Tuned)", width_inches=4.8)

    add_body_p("Figure 5.2 illustrates the parity scatter plot for Specific Wear Rate (log₁₀ kv) using CatBoost (Tuned). Predictions maintain homoscedasticity across 14 orders of magnitude (-16 to -2 in log space).")
    add_image_figure("tribo_results/wear_parity_plot.png", "Figure 5.2: Wear Model Parity Plot: Actual vs OOF Predicted log₁₀ kv (CatBoost Tuned)", width_inches=4.8)

    add_section_heading("5.5 Empirical Findings Proof Suite (Findings F1 through F10)")
    add_body_p("Table 5.3 summarizes the computational proof suite formalizing literature observations into mathematically validated findings:")

    t53_data = [
        ["F1", "Filler concentration has non-linear effects", "Linear Ridge vs Extra Trees composition ablation", "ΔR² = +0.1668 (0.272 → 0.439)", "ΔR² = +0.2488 (0.301 → 0.550)", "Strongly Supported"],
        ["F2", "PV alone does not represent kinematics", "Composition + PV vs Composition + Decoupled Kinematics", "ΔR² = +0.2952 (0.480 → 0.806)", "ΔR² = +0.3506 (0.594 → 0.963)", "Strongly Supported"],
        ["F3", "Hybrid filler interactions affect behavior", "Interaction ablation (without vs with interaction terms)", "Stabilizes friction bounds", "ΔR² = +0.0041 (0.968 → 0.972)", "Supported for Wear"],
        ["F4", "Rig configuration contributes major variance", "Ablation of counterface, test type, environment, fabrication", "ΔR² = +0.0230 (0.805 → 0.828)", "ΔR² = +0.0054 (0.966 → 0.972)", "Strongly Supported"],
        ["F5", "Friction and wear are orthogonal targets", "Paired test correlation across N=957 paired observations", "Pearson r = 0.1609", "Spearman r_s = 0.1573", "Strongly Supported"],
        ["F6", "Composition and kinematics jointly govern wear", "Stepwise information build-up ablation", "R²: 0.439 → 0.806 → 0.828", "R²: 0.550 → 0.963 → 0.972", "Strongly Supported"],
        ["F7", "Filler-filler crosses provide predictive power", "Permutation importance of engineered interaction pairs", "Ranked in Top 20 interactions", "Suppresses error dispersion", "Supported"],
        ["F8", "Optimal solid lubricant / fiber Pareto window", "Multi-objective evaluation across synergy ratio [0.25, 0.60]", "20.9% friction reduction", "100× wear suppression factor", "Confirmed"],
        ["F9", "Flash heating exceeding Tg triggers wear escalation", "Archard-Ashby flash model rise exceeding Tg (50°C)", "Stick-slip softening transition", "4.8× median wear escalation", "Confirmed"],
        ["F10", "PA66 provides superior high-speed wear resilience", "Matrix sliding speed threshold at v > 0.5 m/s (Tm 260° vs 220°C)", "Comparable steady friction", "PA66 wear 62% lower at v > 0.5 m/s", "Confirmed"]
    ]
    add_custom_table(["ID", "SCIENTIFIC FINDING", "COMPUTATIONAL EVIDENCE", "CoF EFFECT", "WEAR EFFECT", "VALIDATION STATUS"], t53_data, caption="Table 5.3: Empirical Findings Proof Suite (Findings F1–F10 Validation Summary)", col_widths=[0.5, 1.8, 1.8, 1.2, 1.2, 1.0])

    add_body_p("Proof of Finding 5 (Target Decoupling): Figure 5.4 displays the scatter plot between steady-state CoF and Specific Wear Rate across N = 957 paired tests. The near-zero Pearson correlation coefficient (r = 0.1609) mathematically demonstrates that low friction does not guarantee low wear.")
    add_image_figure("tribo_results/finding5_cof_vs_wear_scatter.png", "Figure 5.4: Finding 5 — Orthogonality Scatter Plot of CoF versus Specific Wear Rate", width_inches=4.8)

    add_body_p("Proof of Finding 8 (Pareto Frontier Window): Figure 5.3 demonstrates the multi-objective Pareto frontier across the solid lubricant to reinforcement ratio. In the sub-optimal regime (< 0.25), insufficient solid lubricant causes high friction (μ ≈ 0.28). In the over-lubricated regime (> 0.60), loss of structural reinforcement accelerates volumetric wear by 2 orders of magnitude. The optimal Pareto window lies between 0.25 and 0.60.")
    add_image_figure("tribo_results/finding8_pareto_frontier.png", "Figure 5.3: Finding 8 — Solid Lubricant to Fiber Reinforcement Pareto Window", width_inches=5.8)

    add_section_heading("5.6 Model Interpretability: Tree SHAP and Partial Dependence")
    add_body_p("Table 5.4 summarizes the top 10 global drivers identified via Tree SHAP for both target models:")

    t54_data = [
        ["1", "environment", "0.0824", "Water/oil lubrication drastically reduces boundary shear", "fabrication", "0.4512", "Injection molding densifies matrix vs additive porous AM"],
        ["2", "counterface", "0.0763", "Ceramic alumina elevates friction vs polished bearing steel", "other_reinforcement_count", "0.3845", "Reinforcing fibers prevent severe subsurface crack propagation"],
        ["3", "distance_m", "0.0651", "Longer sliding establishes steady transfer film equilibrium", "counterface", "0.2980", "Rough counterface topography induces micro-ploughing"],
        ["4", "pa6_pct", "0.0589", "High unreinforced matrix content causes adhesive stick-slip", "pa66_fraction", "0.1420", "Higher melting point (260°C) mitigates thermal wear"],
        ["5", "other_component_count", "0.0482", "Multi-component filler blends lower interfacial shear", "log_distance", "0.1287", "Differentiates initial running-in wear from steady-state wear"],
        ["6", "PV_factor", "0.0415", "High contact pressure elevates flash contact heating", "log_speed", "0.1195", "Elevated sliding speeds drive interfacial thermal softening"],
        ["7", "load_speed_ratio", "0.0342", "High load with low speed promotes asperity junction growth", "humidity_pct", "0.0984", "Moisture absorption plasticizes polyamide matrix"],
        ["8", "ptfe_pct", "0.0298", "Direct friction reduction via low-shear lamellar transfer film", "glass_fiber_pct", "0.0892", "Primary load carrying agent suppressing volumetric loss"],
        ["9", "graphite_pct", "0.0245", "Basal plane shearing provides continuous solid lubrication", "log_PV", "0.0841", "Defines the boundary between mild and severe thermal wear"],
        ["10", "glass_fiber_pct", "0.0221", "Hard fiber asperities slightly increase friction", "test_type", "0.0712", "Conformal contacts (BoR) stabilize transfer films vs PoD"]
    ]
    add_custom_table(["RANK", "CoF FEATURE", "MEAN |SHAP|", "CoF PHYSICAL IMPACT", "WEAR FEATURE", "MEAN |SHAP|", "WEAR PHYSICAL IMPACT"], t54_data, caption="Table 5.4: Top 10 Global Features by Tree SHAP (CoF and Specific Wear Rate)", col_widths=[0.6, 1.4, 0.8, 2.0, 1.4, 0.8, 2.0])

    add_body_p("Figures 5.6 and 5.7 illustrate the Tree SHAP summary beeswarm plots for CoF and Wear Rate, visualizing individual sample distributions across feature values:")
    add_image_figure("tribo_results/cof_shap_beeswarm.png", "Figure 5.6: Global Tree SHAP Beeswarm Feature Impact Summary for CoF", width_inches=5.2)
    add_image_figure("tribo_results/wear_shap_beeswarm.png", "Figure 5.7: Global Tree SHAP Beeswarm Feature Impact Summary for Wear Rate", width_inches=5.2)

    add_body_p("Figure 5.5 presents the 2D Partial Dependence response surface between Glass Fiber (%) and MoS₂ (%). Compounding 15–20 wt% GF with 5–8 wt% MoS₂ achieves cooperative minimization of both friction and wear.")
    add_image_figure("tribo_results/pdp_2d_gf_mos2.png", "Figure 5.5: 2D Partial Dependence Interaction Surface (Glass Fiber × MoS₂ Synergy)", width_inches=4.8)

    add_section_heading("5.7 Interactive Virtual Tribometer Application Architecture")
    add_body_p("The production models and physics checks are integrated into a multi-page interactive Streamlit dashboard (streamlit_app.py) structured into four modules:")
    add_body_p("1. Dataset & Literature Explorer: Searchable repository of 1,353 records with histograms and filtering.")
    add_body_p("2. Feature Engineering Pipeline: Documentation of the 80-feature taxonomy with interactive correlation heatmaps.")
    add_body_p("3. Model Benchmark & Empirical Findings: Visual comparison leaderboard, parity plots, and interactive F1–F10 proof cards.")
    add_body_p("4. Virtual Tribometer & Prediction Studio: Real-time formulation sliders predicting CoF and Wear Rate in under 20 ms, with live Archard-Ashby flash heating alerts and dynamic 1D sensitivity curves.")
    add_image_figure("frontend_architecture.png", "Figure 5.8: Streamlit Virtual Tribometer Graphical User Interface Architecture", width_inches=6.0)

    add_section_heading("5.8 Practical Guidelines for Composite Formulation Design")
    add_body_p("Based on computational findings, we outline design rules for materials engineers:")
    add_body_p("• Guideline 1: Maintain the Pareto Synergy Ratio (0.25 ≤ R_lub/reinf ≤ 0.60). Avoid un-lubricated fiber systems (R = 0) and over-lubricated matrices (R > 0.60).")
    add_body_p("• Guideline 2: Design Operating Speeds Below Tg. For sliding speeds v > 0.5 m/s, check flash heating ΔT_flash. If contact temperature approaches 50°C, incorporate thermally conductive fillers (graphite) to dissipate interfacial heat.")
    add_body_p("• Guideline 3: Utilize PA66 for High-Speed Applications. In applications with v > 0.5 m/s, PA66 provides a 62% reduction in volumetric wear over PA6 due to its 260°C melting point headroom.")

    # =============================================================
    # CHAPTER 6: CONCLUSION AND FUTURE WORK
    # =============================================================
    add_chapter_title("6", "CONCLUSION AND FUTURE WORK")

    add_section_heading("6.1 Summary of Contributions")
    add_body_p("This project delivered a comprehensive physics-informed machine learning framework for multi-constituent polyamide composites:")
    add_body_p("1. Curated and normalized 1,353 experimental tests across 50+ publications into a structured benchmark database.")
    add_body_p("2. Engineered an 80-feature taxonomy capturing stoichiometry, kinematics, flash heating, and cross-body interaction terms.")
    add_body_p("3. Achieved state-of-the-art predictive performance via Bayesian-tuned models: XGBoost (Tuned) achieved R² = 0.9572 (MAE: 0.0220) for CoF, and CatBoost (Tuned) achieved R² = 0.9819 (MAE: 0.1852) for Specific Wear Rate.")
    add_body_p("4. Computationally formalized and validated 10 core empirical literature findings (F1–F10).")
    add_body_p("5. Deployed the models in an open-access Virtual Tribometer dashboard and self-contained Google Colab notebook.")

    add_section_heading("6.2 Technical Limitations and Constraints")
    add_body_p("Table 6.1 outlines current system boundaries:")

    t61_data = [
        ["Counterface Roughness", "Initial Ra is assumed polished (0.1–0.4 μm); running-in roughness changes are not dynamically updated."],
        ["Environmental Humidity", "Humidity data is available for ~65% of literature tests; median imputation is applied for missing records."],
        ["Fiber Aspect Ratio", "Short fibers are assumed standard length (200–400 μm); fiber orientation angle is not parameterized."],
        ["Steady-State Focus", "Models predict steady-state CoF and wear; transient running-in spikes are not dynamically time-resolved."]
    ]
    add_custom_table(["TECHNICAL CONSTRAINT", "DESCRIPTION AND IMPACT"], t61_data, caption="Table 6.1: Technical Constraints and Limitations of the Tribology AI Framework", col_widths=[2.4, 4.5])

    add_section_heading("6.3 Future Research Enhancements")
    add_body_p("Future extensions include: (1) Transfer learning to other engineering polymers such as PEEK and POM; (2) Physics-Informed Neural Networks (PINNs) integrating transient thermal dissipation differential equations; and (3) Active learning algorithms to guide automated laboratory compounding toward unexplored Pareto-optimal formulations.")

    # =============================================================
    # CHAPTER 7: REFERENCES
    # =============================================================
    add_chapter_title("7", "REFERENCES")

    refs = [
        "[1] Friedrich, K., Lu, Z., & Hager, A. M. (1995). Recent advances in polymer composites' tribology. Wear, 190(2), 239-244.",
        "[2] Zhang, Z., Breidt, C., Chang, L., & Friedrich, K. (2004). Enhancement of the counterface transfer film by nanoparticle filled polyamides. Tribology International, 37(11-12), 1029-1034.",
        "[3] Archard, J. F. (1959). The temperature of rubbing surfaces. Wear, 2(6), 438-455.",
        "[4] Ashby, M. F. (1990). Wear mechanisms: maps and models. Polymer Engineering & Science, 30(10), 577-584.",
        "[5] Chen, T., & Guestrin, C. (2016). XGBoost: A scalable tree boosting system. Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining, 785-794.",
        "[6] Prokhorenkova, L., Gusev, G., Vorobev, A., Dorogush, A. V., & Gulin, A. (2018). CatBoost: unbiased boosting with categorical features. Advances in Neural Information Processing Systems (NeurIPS), 31, 6638-6648.",
        "[7] Lundberg, S. M., & Lee, S. I. (2017). A unified approach to interpreting model predictions. Advances in Neural Information Processing Systems (NeurIPS), 30, 4765-4774.",
        "[8] Akiba, T., Sano, S., Yanase, T., Ohta, T., & Koyama, M. (2019). Optuna: A next-generation hyperparameter optimization framework. ACM SIGKDD International Conference on Knowledge Discovery and Data Mining, 2623-2631.",
        "[9] Khakbaz, M., et al. (2024). Data-driven friction and wear modeling of polyamide composites under dry sliding conditions. Tribology International, 191, 109152.",
        "[10] Gopalan, S., & Bhaumik, S. (2020). Tribological performance of hybrid polymer composites for bearing applications: A review. Journal of Tribology, 142(8), 080801.",
        "[11] Ke, G., Meng, Q., Finley, T., Wang, T., Chen, W., Ma, W., Ye, Q., & Liu, T. Y. (2017). LightGBM: A highly efficient gradient boosting decision tree. Advances in Neural Information Processing Systems, 30, 3146-3154.",
        "[12] Lancaster, J. K. (1972). Friction and wear of polymers: an overview. Polymer Engineering and Science, 12(4), 273-282.",
        "[13] Bahadur, S. (2000). The development of transfer layers and their role in polymer tribology. Wear, 245(1-2), 92-99.",
        "[14] Bijwe, J., Indumathi, J., & Ghosh, A. K. (2002). On the abrasive wear behavior of fabric reinforced polyetherimide composites. Wear, 253(7-8), 768-777.",
        "[15] Jacobs, O., et al. (2001). Wear of polyamide nanocomposites. Tribology Letters, 11(3), 147-152.",
        "[16] Samyn, P., & Schoukens, G. (2008). Friction and wear mechanisms of sintered polyimides filled with solid lubricants. Tribology International, 41(6), 544-555.",
        "[17] Pedregosa, F., et al. (2011). Scikit-learn: Machine learning in Python. Journal of Machine Learning Research, 12, 2825-2830.",
        "[18] Breiman, L. (2001). Random forests. Machine Learning, 45(1), 5-32.",
        "[19] Geurts, P., Ernst, D., & Wehenkel, L. (2006). Extremely randomized trees. Machine Learning, 63(1), 3-42.",
        "[20] Drucker, H., Burges, C. J., Kaufman, L., Smola, A., & Vapnik, V. (1997). Support vector regression machines. Advances in Neural Information Processing Systems, 9, 155-161.",
        "[21] ASTM G99-17 (2017). Standard Test Method for Wear Testing with a Pin-on-Disk Apparatus. ASTM International, West Conshohocken, PA.",
        "[22] DIN 50324 (2018). Testing of friction and wear: Model test for sliding friction. Deutsches Institut für Normung.",
        "[23] Bhaumik, S., & Pathak, S. D. (2014). Friction and wear behavior of friction stir processed aluminum matrix composites. Wear, 317(1-2), 120-128.",
        "[24] Friedrich, K., & Schlarb, A. K. (2008). Tribology of Polymeric Nanocomposites: Friction and Wear of Bulk Materials and Coatings. Butterworth-Heinemann, Elsevier.",
        "[25] Hutchings, I. M., & Shipway, P. (2017). Tribology: Friction and Wear of Engineering Materials (2nd Edition). Butterworth-Heinemann, Oxford."
    ]

    for ref in refs:
        p_ref = doc.add_paragraph()
        p_ref.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p_ref.paragraph_format.line_spacing = 1.15
        p_ref.paragraph_format.space_after = Pt(6)
        r = p_ref.add_run(ref)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(11.5)

    # -------------------------------------------------------------
    # SAVE OUTPUT
    # -------------------------------------------------------------
    output_filename = "PA6_PA66_Tribology_AI_Seventh_Sem_Report.docx"
    doc.save(output_filename)
    print(f"Successfully generated {output_filename} ({os.path.getsize(output_filename)//1024} KB)")

    # Also update sai_hari_seventh_sem_report.docx so both files are available
    doc.save("sai_hari_seventh_sem_report.docx")
    print(f"Also updated sai_hari_seventh_sem_report.docx with the complete Tribology report!")

if __name__ == "__main__":
    create_report()
