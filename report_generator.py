# report_generator.py
from datetime import datetime
import os

def generate_simple_report(filename, ai_result, blockchain_result):
    """
    Generate a simple PDF report using FPDF's built-in fonts only
    """
    try:
        from fpdf import FPDF
        
        pdf = FPDF()
        pdf.add_page()
        
        # ===== HEADER =====
        pdf.set_font('Helvetica', 'B', 20)
        pdf.set_text_color(44, 62, 80)  # Dark blue
        pdf.cell(0, 15, 'VIDEO VERIFICATION REPORT', 0, 1, 'C')
        pdf.ln(5)
        
        # ===== REPORT INFO =====
        pdf.set_font('Helvetica', '', 12)
        pdf.set_text_color(0, 0, 0)  # Black
        
        # Report ID and Date
        pdf.cell(0, 8, f'Report ID: VR-{datetime.now().strftime("%Y%m%d%H%M%S")}', 0, 1)
        pdf.cell(0, 8, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 1)
        pdf.cell(0, 8, f'Video File: {filename}', 0, 1)
        pdf.ln(10)
        
        # ===== VIDEO INFORMATION =====
        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_text_color(41, 128, 185)  # Blue
        pdf.cell(0, 10, '1. VIDEO INFORMATION', 0, 1)
        
        pdf.set_font('Helvetica', '', 11)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 7, f'Filename: {filename}', 0, 1)
        pdf.cell(0, 7, f'SHA-256 Hash: {ai_result.get("hash", "N/A")[:32]}...', 0, 1)
        pdf.cell(0, 7, f'Analysis Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 1)
        pdf.ln(8)
        
        # ===== AI DEEPFAKE ANALYSIS =====
        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_text_color(41, 128, 185)  # Blue
        pdf.cell(0, 10, '2. AI DEEPFAKE ANALYSIS', 0, 1)
        
        pdf.set_font('Helvetica', '', 11)
        
        is_fake = ai_result.get('is_fake', False)
        fake_prob = ai_result.get('fake_probability', 0)
        
        # AI Result with color
        if is_fake:
            pdf.set_text_color(231, 76, 60)  # Red for FAKE
            result_text = 'FAKE'
        else:
            pdf.set_text_color(39, 174, 96)  # Green for REAL
            result_text = 'REAL'
        
        pdf.cell(0, 7, f'Result: {result_text}', 0, 1)
        pdf.set_text_color(0, 0, 0)  # Reset to black
        
        # Confidence
        if is_fake:
            pdf.cell(0, 7, f'Fake Probability: {fake_prob:.1f}%', 0, 1)
        else:
            pdf.cell(0, 7, f'Real Confidence: {100-fake_prob:.1f}%', 0, 1)
        
        pdf.cell(0, 7, f'Frames Analyzed: {ai_result.get("frame_count", "N/A")}', 0, 1)
        pdf.cell(0, 7, f'Model: EfficientNet-B0', 0, 1)
        pdf.ln(8)
        
        # ===== BLOCKCHAIN VERIFICATION =====
        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_text_color(41, 128, 185)  # Blue
        pdf.cell(0, 10, '3. BLOCKCHAIN VERIFICATION', 0, 1)
        
        pdf.set_font('Helvetica', '', 11)
        
        is_verified = blockchain_result.get('verified', False)
        
        if is_verified:
            pdf.set_text_color(39, 174, 96)  # Green for VERIFIED
            pdf.cell(0, 7, 'Status: VERIFIED', 0, 1)
            pdf.set_text_color(0, 0, 0)  # Reset to black
            
            if blockchain_result.get('description'):
                pdf.cell(0, 7, f'Description: {blockchain_result.get("description")}', 0, 1)
            
            if blockchain_result.get('uploader'):
                uploader = blockchain_result.get('uploader', '')
                pdf.cell(0, 7, f'Registered by: {uploader[:10]}...{uploader[-8:]}', 0, 1)
            
            if blockchain_result.get('registered_date'):
                pdf.cell(0, 7, f'Registration Date: {blockchain_result.get("registered_date")}', 0, 1)
        else:
            pdf.set_text_color(231, 76, 60)  # Red for NOT VERIFIED
            pdf.cell(0, 7, 'Status: NOT VERIFIED', 0, 1)
            pdf.set_text_color(0, 0, 0)  # Reset to black
            pdf.cell(0, 7, 'Video hash not found on blockchain', 0, 1)
        
        pdf.cell(0, 7, f'Blockchain: Ethereum (Ganache)', 0, 1)
        pdf.cell(0, 7, f'Contract: {blockchain_result.get("contract_address", "N/A")[:20]}...', 0, 1)
        pdf.ln(10)
        
        # ===== FINAL CONCLUSION =====
        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_text_color(41, 128, 185)  # Blue
        pdf.cell(0, 10, '4. FINAL VERIFICATION SUMMARY', 0, 1)
        
        pdf.set_font('Helvetica', 'B', 12)
        
        # Determine conclusion with color
        if not is_fake and is_verified:
            pdf.set_text_color(39, 174, 96)  # Green
            conclusion = 'AUTHENTIC CONTENT'
            explanation = 'Video passes both AI analysis and blockchain verification.'
        elif not is_fake and not is_verified:
            pdf.set_text_color(243, 156, 18)  # Orange
            conclusion = 'UNVERIFIED'
            explanation = 'AI detects as real but not registered on blockchain.'
        elif is_fake and not is_verified:
            pdf.set_text_color(231, 76, 60)  # Red
            conclusion = 'SUSPECTED DEEPFAKE'
            explanation = 'Both AI and blockchain suggest video is not authentic.'
        else:
            pdf.set_text_color(155, 89, 182)  # Purple for conflict
            conclusion = 'CONFLICT'
            explanation = 'AI detects as fake but video is registered on blockchain.'
        
        pdf.cell(0, 8, f'Conclusion: {conclusion}', 0, 1)
        pdf.set_text_color(0, 0, 0)  # Reset to black
        
        pdf.set_font('Helvetica', '', 11)
        pdf.multi_cell(0, 6, explanation)
        pdf.ln(5)
        
        # ===== RECOMMENDATION =====
        pdf.set_font('Helvetica', 'I', 11)
        pdf.set_text_color(52, 73, 94)  # Dark gray
        
        if not is_fake and is_verified:
            recommendation = 'Recommendation: Video can be trusted for sharing.'
        elif not is_fake and not is_verified:
            recommendation = 'Recommendation: Contact content owner for blockchain registration.'
        elif is_fake and not is_verified:
            recommendation = 'Recommendation: Do not share. Likely manipulated content.'
        else:
            recommendation = 'Recommendation: Investigate possible video manipulation.'
        
        pdf.cell(0, 7, recommendation, 0, 1)
        pdf.ln(15)
        
        # ===== FOOTER =====
        pdf.set_font('Helvetica', 'I', 9)
        pdf.set_text_color(149, 165, 166)  # Light gray
        pdf.cell(0, 5, 'Generated by Deepfake Detection & Blockchain Verification System', 0, 1, 'C')
        pdf.cell(0, 5, 'Academic Project - For Demonstration Purposes Only', 0, 1, 'C')
        pdf.cell(0, 5, 'System combines AI deepfake detection with blockchain verification', 0, 1, 'C')
        
        # ===== SAVE PDF =====
        # Create reports directory if it doesn't exist
        reports_dir = 'static/reports'
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir)
        
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f'verification_{timestamp}.pdf'
        report_path = os.path.join(reports_dir, report_filename)
        
        pdf.output(report_path)
        
        print(f"✅ Report generated: {report_path}")
        return report_path
        
    except Exception as e:
        print(f"❌ Report generation error: {str(e)}")
        # Fallback to text report
        return generate_text_report(filename, ai_result, blockchain_result)

def generate_text_report(filename, ai_result, blockchain_result):
    """
    Generate a simple text report as fallback
    """
    try:
        # Create ASCII art report
        report_content = f"""
{'='*60}
            VIDEO VERIFICATION REPORT
{'='*60}

REPORT INFORMATION:
------------------
Report ID: VR-{datetime.now().strftime('%Y%m%d%H%M%S')}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Video File: {filename}

VIDEO INFORMATION:
-----------------
Filename: {filename}
Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

AI DEEPFAKE ANALYSIS:
--------------------
Result: {'FAKE' if ai_result.get('is_fake') else 'REAL'}
Fake Probability: {ai_result.get('fake_probability', 0):.1f}%
Frames Analyzed: {ai_result.get('frame_count', 'N/A')}
Model: EfficientNet-B0

BLOCKCHAIN VERIFICATION:
-----------------------
Status: {'VERIFIED' if blockchain_result.get('verified') else 'NOT VERIFIED'}
{ f"Description: {blockchain_result.get('description', '')}" if blockchain_result.get('description') else "Reason: Video not registered on blockchain"}
{ f"Registered by: {blockchain_result.get('uploader', '')}" if blockchain_result.get('uploader') else ""}
{ f"Registration Date: {blockchain_result.get('registered_date', '')}" if blockchain_result.get('registered_date') else ""}
Blockchain: Ethereum (Ganache)

FINAL CONCLUSION:
----------------
"""
        
        # Add conclusion
        is_fake = ai_result.get('is_fake', False)
        is_verified = blockchain_result.get('verified', False)
        
        if not is_fake and is_verified:
            conclusion = "[AUTHENTIC] Video is verified as real and registered."
            status = "PASS"
        elif not is_fake and not is_verified:
            conclusion = "[UNVERIFIED] AI detects as real but not registered."
            status = "CAUTION"
        elif is_fake and not is_verified:
            conclusion = "[SUSPECTED DEEPFAKE] Likely manipulated content."
            status = "FAIL"
        else:
            conclusion = "[CONFLICT] AI detects as fake but video is registered."
            status = "INVESTIGATE"
        
        report_content += f"""
{conclusion}
Status: {status}

{'='*60}
Generated by Deepfake Detection & Blockchain Verification System
Academic Project - For Demonstration Purposes Only
{'='*60}
"""
        
        # Save text file
        reports_dir = 'static/reports'
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f'verification_{timestamp}.txt'
        report_path = os.path.join(reports_dir, report_filename)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"✅ Text report generated: {report_path}")
        return report_path
        
    except Exception as e:
        print(f"❌ Text report generation error: {str(e)}")
        return None